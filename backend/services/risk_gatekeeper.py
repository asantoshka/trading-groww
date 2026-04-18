from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class RiskConfig:
    capital_limit: float = 5000.0
    max_trade_value: float = 2000.0
    max_loss_per_trade: float = 300.0
    min_rr_ratio: float = 1.5
    confidence_threshold: int = 70
    max_capital_pct: float = 0.40
    mode: str = "paper"


@dataclass
class SignalInput:
    symbol: str
    action: str
    entry_price: float
    target: float
    stoploss: float
    qty: int
    confidence: int
    mode: str = "paper"


@dataclass
class RiskResult:
    approved: bool
    reject_reason: str
    trade_value: float
    risk_amount: float
    reward_amount: float
    rr_ratio: float
    capital_pct: float
    checks: Dict[str, bool]
    evaluated_at: str


class RiskGatekeeper:
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    def evaluate(self, signal: SignalInput, available_capital: float) -> RiskResult:
        action = signal.action.upper()
        trade_value = signal.entry_price * signal.qty

        if action == "SELL":
            risk_amount = (signal.stoploss - signal.entry_price) * signal.qty
            reward_amount = (signal.entry_price - signal.target) * signal.qty
        else:
            risk_amount = (signal.entry_price - signal.stoploss) * signal.qty
            reward_amount = (signal.target - signal.entry_price) * signal.qty

        rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0.0
        capital_pct = (trade_value / self.config.capital_limit) * 100

        checks = {
            "trade_value_ok": trade_value <= self.config.max_trade_value,
            "capital_ok": trade_value <= available_capital,
            "risk_ok": risk_amount <= self.config.max_loss_per_trade,
            "rr_ratio_ok": rr_ratio >= self.config.min_rr_ratio,
            "confidence_ok": signal.confidence >= self.config.confidence_threshold,
            "capital_pct_ok": (
                trade_value / self.config.capital_limit
            ) <= self.config.max_capital_pct,
        }

        reject_reason = ""
        if not checks["capital_ok"]:
            reject_reason = (
                f"Insufficient capital: trade ₹{trade_value:.2f} "
                f"exceeds available ₹{available_capital:.2f}"
            )
        elif not checks["trade_value_ok"]:
            reject_reason = (
                f"Trade value ₹{trade_value:.2f} exceeds "
                f"max ₹{self.config.max_trade_value:.2f}"
            )
        elif not checks["capital_pct_ok"]:
            reject_reason = (
                f"Trade uses {capital_pct:.1f}% of capital, "
                f"max allowed is {self.config.max_capital_pct * 100:.0f}%"
            )
        elif not checks["risk_ok"]:
            reject_reason = (
                f"Risk ₹{risk_amount:.2f} exceeds max "
                f"₹{self.config.max_loss_per_trade:.2f}"
            )
        elif not checks["rr_ratio_ok"]:
            reject_reason = (
                f"R:R ratio {rr_ratio:.2f} below minimum "
                f"{self.config.min_rr_ratio:.2f}"
            )
        elif not checks["confidence_ok"]:
            reject_reason = (
                f"Confidence {signal.confidence}% below "
                f"threshold {self.config.confidence_threshold}%"
            )

        return RiskResult(
            approved=all(checks.values()),
            reject_reason=reject_reason,
            trade_value=trade_value,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            rr_ratio=rr_ratio,
            capital_pct=capital_pct,
            checks=checks,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    def evaluate_from_dict(
        self,
        signal_dict: Dict[str, Any],
        available_capital: float,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        if config_dict is not None:
            config = RiskConfig(
                capital_limit=config_dict.get("capital_limit", 5000.0),
                max_trade_value=config_dict.get("max_trade_value", 2000.0),
                max_loss_per_trade=config_dict.get("max_loss_per_trade", 300.0),
                min_rr_ratio=config_dict.get("min_rr_ratio", 1.5),
                confidence_threshold=config_dict.get("confidence_threshold", 70),
                max_capital_pct=config_dict.get("max_capital_pct", 0.40),
                mode=config_dict.get("mode", "paper"),
            )
            gatekeeper = RiskGatekeeper(config)
        else:
            gatekeeper = self

        signal = SignalInput(
            symbol=signal_dict["symbol"],
            action=signal_dict["action"],
            entry_price=signal_dict["entry_price"],
            target=signal_dict["target"],
            stoploss=signal_dict["stoploss"],
            qty=signal_dict["qty"],
            confidence=signal_dict["confidence"],
            mode=signal_dict.get("mode", "paper"),
        )
        return gatekeeper.evaluate(signal, available_capital)

    def result_to_dict(self, result: RiskResult) -> Dict[str, Any]:
        return {
            "approved": result.approved,
            "reject_reason": result.reject_reason,
            "trade_value": round(result.trade_value, 2),
            "risk_amount": round(result.risk_amount, 2),
            "reward_amount": round(result.reward_amount, 2),
            "rr_ratio": round(result.rr_ratio, 2),
            "capital_pct": round(result.capital_pct, 2),
            "checks": dict(result.checks),
            "evaluated_at": result.evaluated_at,
        }
