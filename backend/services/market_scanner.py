import asyncio
import json
import logging
import uuid
import warnings
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="pandas_ta",
)
warnings.filterwarnings(
    "ignore",
    module="pandas_ta",
)

import pandas_ta as ta

from database import SessionLocal
from models import Config, Signal
from services.groww_client import groww_client
from services.llm_client import llm_client
from services.risk_gatekeeper import RiskConfig, RiskGatekeeper, SignalInput
from services.telegram_notifier import telegram
from services.websocket_manager import (
    broadcast_agent_log,
    broadcast_agent_status,
    broadcast_new_signal,
)


logger = logging.getLogger(__name__)

DEFAULT_WATCHLIST = ["NHPC", "SAIL", "IRCTC", "RELIANCE"]

SCANNER_SYSTEM_PROMPT = """
You are an intraday stock market analyst for a trading
system operating on NSE India with ₹{capital} capital.

You will receive pre-computed technical indicator data
for multiple symbols. Your job is to identify the single
best intraday opportunity — either BUY or SELL.

BUY SIGNAL CONDITIONS (all must be true):
- RSI < {rsi_oversold} (oversold)
- RSI rising over last 3 candles (momentum up)
- MACD bullish crossover in last 2 candles
  (macd_line crossed above signal_line)

SELL SIGNAL CONDITIONS (all must be true):
- RSI > {rsi_overbought} (overbought)
- RSI falling over last 3 candles (momentum down)
- MACD bearish crossover in last 2 candles
  (macd_line crossed below signal_line)

ENTRY/EXIT CALCULATION:
For BUY:
  entry = current LTP
  target = entry × 1.018   (1.8% above)
  stoploss = entry × 0.988 (1.2% below)

For SELL (short):
  entry = current LTP
  target = entry × 0.982   (1.8% below)
  stoploss = entry × 1.012 (1.2% above)

QUANTITY:
  qty = floor(max_trade_value / entry_price)
  Minimum qty = 1

CONFIDENCE SCORING:
BUY signals:
  RSI < 25 + strong MACD cross = 85-95
  RSI < 30 + MACD cross = 70-84
  RSI < {rsi_oversold} + weak MACD = 55-69

SELL signals:
  RSI > 75 + strong MACD bearish cross = 85-95
  RSI > 70 + MACD bearish cross = 70-84
  RSI > {rsi_overbought} + weak MACD = 55-69

PRIORITY:
If both BUY and SELL conditions are met on different
symbols, pick the one with higher confidence score.

STRICT OUTPUT FORMAT:
Respond with a single JSON object only.
No markdown. No explanation. Just JSON.

If signal found:
{{
  "signal": true,
  "symbol": "SYMBOL",
  "action": "BUY" or "SELL",
  "entry_price": 0.00,
  "target": 0.00,
  "stoploss": 0.00,
  "qty": 0,
  "rsi": 0.0,
  "macd_state": "bullish_cross" or "bearish_cross",
  "confidence": 0,
  "reasoning": "one sentence max"
}}

If no signal:
{{
  "signal": false,
  "reasoning": "one sentence"
}}
"""


class MarketScanner:
    def __init__(self):
        self.is_running = False
        self._last_run: datetime | None = None
        self._last_signal: dict | None = None

    def _load_config(self, db: Session) -> tuple[Config | None, RiskConfig]:
        config = db.query(Config).filter(Config.id == 1).first()
        if not config:
            return None, RiskConfig()

        risk_config = RiskConfig(
            capital_limit=config.capital_limit,
            max_trade_value=config.max_trade_value,
            max_loss_per_trade=config.max_loss_per_trade,
            min_rr_ratio=config.min_rr_ratio,
            confidence_threshold=config.confidence_threshold,
            mode=config.mode,
        )
        return config, risk_config

    def _compute_indicators(self, candles: list[dict]) -> dict:
        df = pd.DataFrame(candles)
        if df.empty:
            return {"error": "insufficient data", "candle_count": 0}

        expected_cols = ["open", "high", "low", "close", "volume"]
        for column in expected_cols:
            if column not in df.columns:
                return {"error": f"missing column: {column}", "candle_count": len(df)}

        df = df[expected_cols].copy()
        for column in expected_cols:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.replace([np.inf, -np.inf], np.nan)

        if len(df) < 30:
            return {"error": "insufficient data", "candle_count": len(df)}

        df["rsi"] = ta.rsi(df["close"], length=14)

        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        if macd is None or macd.empty:
            return {"error": "macd calculation failed", "candle_count": len(df)}

        df["macd_line"] = macd["MACD_12_26_9"]
        df["macd_signal"] = macd["MACDs_12_26_9"]
        df["macd_hist"] = macd["MACDh_12_26_9"]

        recent = df.tail(5).copy().dropna()
        if recent.empty:
            return {"error": "all NaN after dropna"}

        last = recent.iloc[-1]
        rsi_now = round(float(last["rsi"]), 2)
        macd_line_now = float(last["macd_line"])
        macd_signal_now = float(last["macd_signal"])

        if len(recent) >= 3:
            rsi_rising = recent.iloc[-1]["rsi"] > recent.iloc[-3]["rsi"]
            rsi_falling = recent.iloc[-1]["rsi"] < recent.iloc[-3]["rsi"]
        else:
            rsi_rising = False
            rsi_falling = False

        if len(recent) >= 2:
            prev = recent.iloc[-2]
            curr = recent.iloc[-1]
            bullish_cross = (
                prev["macd_line"] <= prev["macd_signal"]
                and curr["macd_line"] > curr["macd_signal"]
            )
            bearish_cross = (
                prev["macd_line"] >= prev["macd_signal"]
                and curr["macd_line"] < curr["macd_signal"]
            )
            macd_above = curr["macd_line"] > curr["macd_signal"]
        else:
            bullish_cross = False
            bearish_cross = False
            macd_above = False

        if bullish_cross:
            macd_state = "bullish_cross"
        elif bearish_cross:
            macd_state = "bearish_cross"
        elif macd_above:
            macd_state = "bullish"
        else:
            macd_state = "bearish"

        return {
            "rsi": rsi_now,
            "rsi_rising": bool(rsi_rising),
            "rsi_falling": bool(rsi_falling),
            "macd_line": round(macd_line_now, 4),
            "macd_signal": round(macd_signal_now, 4),
            "macd_hist": round(float(last["macd_hist"]), 4),
            "macd_state": macd_state,
            "bullish_cross": bool(bullish_cross),
            "bearish_cross": bool(bearish_cross),
            "candle_count": len(df),
            "last_close": round(float(last["close"]), 2),
        }

    async def _analyze_symbol(
        self,
        symbol: str,
        ltp: float,
        config: Config | None,
    ) -> dict:
        _ = config
        end_time = datetime.now()
        start_time = end_time - timedelta(days=5)
        fmt = "%Y-%m-%d %H:%M:%S"

        try:
            candles = await asyncio.wait_for(
                groww_client.get_historical_data(
                    symbol=symbol,
                    start_time=start_time.strftime(fmt),
                    end_time=end_time.strftime(fmt),
                    interval_in_minutes=5,
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            await broadcast_agent_log(
                "market_scanner",
                "warning",
                f"{symbol}: data fetch timeout, skipping",
            )
            return {
                "symbol": symbol,
                "ltp": ltp,
                "error": "timeout",
                "indicators": {},
            }

        if not candles:
            return {
                "symbol": symbol,
                "ltp": ltp,
                "error": "no historical data",
                "indicators": {},
            }

        indicators = self._compute_indicators(candles)
        return {
            "symbol": symbol,
            "ltp": ltp,
            "indicators": indicators,
            "candle_count": len(candles),
        }

    async def _call_claude(
        self,
        symbol_data: list[dict],
        config: Config | None,
    ) -> dict | None:
        system = SCANNER_SYSTEM_PROMPT.format(
            capital=config.capital_limit if config else 5000,
            rsi_oversold=config.rsi_oversold if config else 35,
            rsi_overbought=config.rsi_overbought if config else 65,
            max_trade_value=config.max_trade_value if config else 2000,
        )

        lines: list[str] = []
        for item in symbol_data:
            indicators = item.get("indicators", {})
            if "error" in indicators:
                lines.append(f"{item['symbol']}: insufficient data")
                continue
            lines.append(
                f"{item['symbol']}:\n"
                f"  LTP: ₹{item['ltp']}\n"
                f"  RSI(14): {indicators.get('rsi', 'N/A')}\n"
                f"  RSI Rising: {indicators.get('rsi_rising')}\n"
                f"  RSI Falling: {indicators.get('rsi_falling')}\n"
                f"  MACD State: {indicators.get('macd_state')}\n"
                f"  Bullish Cross: {indicators.get('bullish_cross')}\n"
                f"  Bearish Cross: {indicators.get('bearish_cross')}\n"
                f"  Candles: {indicators.get('candle_count')}"
            )

        user_msg = (
            "Analyze the following symbols and identify "
            "the best BUY or SELL opportunity if conditions are met:"
            f"\n\n{(chr(10) * 2).join(lines)}\n\n"
            "Respond with JSON only."
        )

        try:
            response = llm_client.create(
                system=system,
                messages=[{"role": "user", "content": user_msg}],
                max_tokens=500,
                tier="sonnet",
            )
            text = llm_client.extract_text(response)
        except Exception as exc:
            logger.error("Claude API error: %s", exc)
            return None

        try:
            clean = text.strip()
            if clean.startswith("```"):
                parts = clean.split("```")
                if len(parts) >= 2:
                    clean = parts[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
            return json.loads(clean.strip())
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning("Could not parse Claude response: %s", text)
            return None

    async def _save_signal(
        self,
        signal_data: dict,
        risk_result,
        mode: str,
        db: Session,
    ) -> Signal:
        signal = Signal(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().strftime("%H:%M:%S"),
            symbol=signal_data["symbol"],
            exchange="NSE",
            action=signal_data["action"],
            entry_price=float(signal_data["entry_price"]),
            target=float(signal_data["target"]),
            stoploss=float(signal_data["stoploss"]),
            qty=int(signal_data["qty"]),
            rsi=float(signal_data.get("rsi", 0)),
            macd_state=signal_data.get("macd_state", "unknown"),
            confidence=int(signal_data.get("confidence", 0)),
            risk_status="approved" if risk_result.approved else "rejected",
            reject_reason=risk_result.reject_reason or None,
            executed=False,
            mode=mode,
            created_at=datetime.now(timezone.utc),
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal

    async def run_scan(self) -> Signal | None:
        db = SessionLocal()
        try:
            self.is_running = True
            self._last_run = datetime.now(timezone.utc)
            last_run_iso = self._last_run.isoformat()

            await broadcast_agent_status("market_scanner", "running", last_run_iso)
            await broadcast_agent_log("market_scanner", "info", "Market scan started")

            config, risk_config = self._load_config(db)
            watchlist = config.get_watchlist() if config else DEFAULT_WATCHLIST
            mode = config.mode if config else "paper"

            await broadcast_agent_log(
                "market_scanner",
                "info",
                f"Scanning {len(watchlist)} symbols: {', '.join(watchlist)}",
            )
            await telegram.notify_scan_started(len(watchlist))

            ltp_data = await groww_client.get_ltp(watchlist)
            ltp_str = ", ".join([f"{s}: ₹{ltp_data.get(s, 'N/A')}" for s in watchlist])
            await broadcast_agent_log(
                "market_scanner",
                "info",
                f"Live prices — {ltp_str}",
            )

            tradeable = []
            for symbol in watchlist:
                ltp = ltp_data.get(symbol, 0)
                if ltp == 0:
                    await broadcast_agent_log(
                        "market_scanner",
                        "warning",
                        f"{symbol}: no LTP data, skipping",
                    )
                    continue
                if not (10 <= ltp <= 1000):
                    await broadcast_agent_log(
                        "market_scanner",
                        "info",
                        f"{symbol}: price ₹{ltp} outside range ₹10-₹1000, skipping",
                    )
                    continue
                tradeable.append(symbol)

            await broadcast_agent_log(
                "market_scanner",
                "info",
                "Computing technical indicators...",
            )
            symbol_data = []
            for i, symbol in enumerate(tradeable):
                ltp = ltp_data.get(symbol, 0)
                data = await self._analyze_symbol(symbol, ltp, config)
                symbol_data.append(data)

                indicators = data.get("indicators", {})
                if "error" not in indicators:
                    await broadcast_agent_log(
                        "market_scanner",
                        "info",
                        f"{symbol} — RSI: {indicators.get('rsi', 'N/A')} | "
                        f"MACD: {indicators.get('macd_state', 'N/A')} | "
                        f"Rising: {indicators.get('rsi_rising')} | "
                        f"Falling: {indicators.get('rsi_falling')}",
                    )
                else:
                    await broadcast_agent_log(
                        "market_scanner",
                        "warning",
                        f"{symbol} — {indicators.get('error')}",
                    )

                if i < len(tradeable) - 1:
                    await asyncio.sleep(0.3)

            await broadcast_agent_log(
                "market_scanner",
                "info",
                "Sending indicators to Claude for analysis...",
            )
            result = await self._call_claude(symbol_data, config)
            if result is None:
                await broadcast_agent_log(
                    "market_scanner",
                    "warning",
                    "Claude returned no parseable result",
                )
                return None

            if not result.get("signal"):
                await broadcast_agent_log(
                    "market_scanner",
                    "info",
                    f"No signal: {result.get('reasoning', 'N/A')}",
                )
                await telegram.notify_no_signal(
                    result.get("reasoning", "No conditions met")
                )
                return None

            required = [
                "symbol",
                "action",
                "entry_price",
                "target",
                "stoploss",
                "qty",
                "confidence",
            ]
            missing = [field for field in required if field not in result]
            if missing:
                await broadcast_agent_log(
                    "market_scanner",
                    "warning",
                    f"Signal missing fields: {missing}",
                )
                return None

            await broadcast_agent_log(
                "risk_gatekeeper",
                "info",
                f"Evaluating: {result['action']} {result['symbol']} "
                f"@ ₹{result['entry_price']} qty={result['qty']}",
            )

            margin = await groww_client.get_margin()
            available_capital = margin.get(
                "available_margin",
                risk_config.capital_limit,
            )

            gk = RiskGatekeeper(risk_config)
            signal_input = SignalInput(
                symbol=result["symbol"],
                action=result["action"],
                entry_price=float(result["entry_price"]),
                target=float(result["target"]),
                stoploss=float(result["stoploss"]),
                qty=int(result["qty"]),
                confidence=int(result["confidence"]),
                mode=mode,
            )
            risk_result = gk.evaluate(signal_input, available_capital)

            if risk_result.approved:
                await broadcast_agent_log(
                    "risk_gatekeeper",
                    "success",
                    f"APPROVED — RR: {risk_result.rr_ratio:.2f}, "
                    f"Risk: ₹{risk_result.risk_amount:.2f}, "
                    f"Capital: {risk_result.capital_pct:.1f}%",
                )
                await telegram.notify_signal_found(
                    symbol=result["symbol"],
                    action=result["action"],
                    entry=float(result["entry_price"]),
                    target=float(result["target"]),
                    stoploss=float(result["stoploss"]),
                    qty=int(result["qty"]),
                    rsi=float(result.get("rsi", 0)),
                    confidence=int(result.get("confidence", 0)),
                    mode=mode,
                )
            else:
                await broadcast_agent_log(
                    "risk_gatekeeper",
                    "warning",
                    f"REJECTED — {risk_result.reject_reason}",
                )
                await telegram.notify_signal_rejected(
                    symbol=result["symbol"],
                    action=result["action"],
                    entry=float(result["entry_price"]),
                    reason=risk_result.reject_reason,
                )

            signal = await self._save_signal(result, risk_result, mode, db)
            self._last_signal = result

            signal_dict = {
                "id": signal.id,
                "symbol": signal.symbol,
                "action": signal.action,
                "entry_price": signal.entry_price,
                "target": signal.target,
                "stoploss": signal.stoploss,
                "qty": signal.qty,
                "rsi": signal.rsi,
                "macd_state": signal.macd_state,
                "confidence": signal.confidence,
                "risk_status": signal.risk_status,
                "reject_reason": signal.reject_reason,
                "executed": signal.executed,
                "mode": signal.mode,
                "timestamp": signal.timestamp,
            }
            await broadcast_new_signal(signal_dict)

            await broadcast_agent_log(
                "market_scanner",
                "success",
                f"Signal {'approved' if risk_result.approved else 'rejected'}: "
                f"{signal.action} {signal.symbol} "
                f"@ ₹{signal.entry_price} "
                f"[conf: {signal.confidence}%]",
            )

            if risk_result.approved:
                from services.execution_agent import execution_agent

                await broadcast_agent_log(
                    "market_scanner",
                    "info",
                    "Passing approved signal to Execution Agent...",
                )
                asyncio.create_task(execution_agent.execute(signal, db))

            return signal if risk_result.approved else None
        except Exception as exc:
            import traceback

            logger.error(f"Scanner failed: {exc}")
            logger.error(traceback.format_exc())
            await broadcast_agent_log(
                "market_scanner",
                "error",
                f"Scanner error: {str(exc)}",
            )
            await telegram.notify_scanner_error(str(exc))
            raise
        finally:
            db.close()
            self.is_running = False
            await broadcast_agent_status(
                "market_scanner",
                "stopped",
                self._last_run.isoformat() if self._last_run else None,
            )

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "last_signal": self._last_signal,
        }


market_scanner = MarketScanner()
