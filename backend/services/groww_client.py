import asyncio
import logging
import os
import random
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx

from services.token_manager import token_manager

GROWW_BASE_URL = os.getenv("GROWW_BASE_URL", "https://api.groww.in")
logger = logging.getLogger(__name__)


def _is_paper_mode() -> bool:
    try:
        from database import SessionLocal
        from models import Config

        db = SessionLocal()
        try:
            config = db.query(Config).filter(Config.id == 1).first()
            if config:
                return config.mode == "paper"
            return True
        finally:
            db.close()
    except Exception:
        return True


def _mock_ltp(symbol: str) -> float:
    base_prices = {
        "NHPC": 84.50,
        "IRCTC": 748.00,
        "SAIL": 127.40,
        "RELIANCE": 1342.00,
        "TCS": 3412.00,
        "INFY": 1521.00,
        "IDEA": 9.85,
        "NIFTY": 22450.00,
        "SENSEX": 73800.00,
    }
    base = base_prices.get(symbol.upper(), 100.0)
    return round(base * (1 + random.uniform(-0.005, 0.005)), 2)


class GrowwClient:
    def __init__(self):
        self.base_url = GROWW_BASE_URL
        self.timeout = 10

    async def _get_headers(self) -> dict:
        token = await token_manager.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-API-VERSION": "1.0",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        headers = await self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers=headers,
                    params=params,
                    json=json,
                )
        except httpx.TimeoutException as exc:
            raise Exception(
                f"Groww API timeout after {self.timeout}s for {path}"
            ) from exc
        except httpx.ConnectError as exc:
            raise Exception(
                "Cannot connect to Groww API. Check internet connection."
            ) from exc

        if response.status_code == 401:
            await token_manager.invalidate()
            raise Exception("Token expired (401). Token invalidated, retry.")

        if response.status_code == 429:
            logger.warning(
                "[GrowwClient] Rate limited on %s. Waiting 5s before retry...",
                path,
            )
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers=headers,
                    params=params,
                    json=json,
                )
            if response.status_code == 429:
                raise Exception(
                    "Rate limit exceeded after retry. Too many API calls. "
                    "Reduce watchlist size or increase delay between calls."
                )

        if response.status_code not in (200, 201):
            raise Exception(
                f"Groww API error {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()
        if isinstance(data, dict) and data.get("status") == "FAILURE":
            error = data.get("error", {})
            raise Exception(
                "Groww API failure: "
                f"{error.get('code')} - {error.get('message')}"
            )

        return data.get("payload", data) if isinstance(data, dict) else data

    async def get_ltp(
        self,
        symbols: list[str],
        segment: str = "CASH",
        exchange: str = "NSE",
    ) -> dict:
        exchange_symbols = [f"{exchange}_{symbol}" for symbol in symbols]
        payload = await self._request(
            "GET",
            "/v1/live-data/ltp",
            params={
                "segment": segment,
                "exchange_symbols": ",".join(exchange_symbols),
            },
        )
        return {key.split("_", 1)[1]: value for key, value in payload.items()}

    async def get_quote(
        self,
        symbol: str,
        segment: str = "CASH",
        exchange: str = "NSE",
    ) -> dict:
        return await self._request(
            "GET",
            "/v1/live-data/quote",
            params={
                "exchange": exchange,
                "segment": segment,
                "trading_symbol": symbol,
            },
        )

    async def get_historical_data(self,
        symbol: str,
        start_time: str,
        end_time: str,
        interval_in_minutes: int = 5,
        segment: str = "CASH",
        exchange: str = "NSE") -> list[dict]:
        async def fetch_candles(
            range_start: str,
            range_end: str,
        ) -> list[dict]:
            payload = await self._request(
                "GET",
                "/v1/historical/candle/range",
                params={
                    "exchange": exchange,
                    "segment": segment,
                    "trading_symbol": symbol,
                    "start_time": range_start,
                    "end_time": range_end,
                    "interval_in_minutes": interval_in_minutes,
                },
            )

            raw_candles = payload.get("candles", []) if isinstance(payload, dict) else []
            candles = []
            for candle in raw_candles:
                candles.append(
                    {
                        "timestamp": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                    }
                )
            return candles

        candles = await fetch_candles(start_time, end_time)
        if candles:
            return candles

        # Real API reads can legitimately return no candles for weekends or
        # market holidays. Retry a few prior sessions before giving up.
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return candles

        for days_back in range(1, 8):
            retry_start = (start_dt - timedelta(days=days_back)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            retry_end = (end_dt - timedelta(days=days_back)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            candles = await fetch_candles(retry_start, retry_end)
            if candles:
                return candles

        return []

    async def get_positions(self, segment: str = "CASH") -> list[dict]:
        if _is_paper_mode():
            from mock_data import MOCK_POSITIONS

            return [dict(position) for position in MOCK_POSITIONS]

        payload = await self._request(
            "GET",
            "/v1/portfolio/positions",
            params={"segment": segment},
        )
        return payload.get("positions", [])

    async def get_margin(self) -> dict:
        if _is_paper_mode():
            return {
                "available_margin": 3241.50,
                "used_margin": 1758.50,
                "total_margin": 5000.00,
                "currency": "INR",
            }

        return await self._request(
            "GET",
            "/v1/user/margin",
            params={"segment": "CASH"},
        )

    async def place_order(
        self,
        symbol: str,
        qty: int,
        price: float,
        action: str,
        product: str = "MIS",
        order_type: str = "LIMIT",
        segment: str = "CASH",
        exchange: str = "NSE",
        trigger_price: float = None,
    ) -> dict:
        ts = str(int(time.time()))[-6:]
        ref_id = f"BOT-{ts}-{symbol[:4].upper()}"

        if _is_paper_mode():
            await asyncio.sleep(random.uniform(0.1, 0.3))
            mock_order_id = f"PAPER-{uuid.uuid4().hex[:8].upper()}"
            print(f"[PAPER] {action} {qty} {symbol} @ ₹{price} | ref: {ref_id}")
            return {
                "groww_order_id": mock_order_id,
                "order_status": "OPEN",
                "order_reference_id": ref_id,
                "remark": "Paper trade — not sent to exchange",
                "paper": True,
                "symbol": symbol,
                "qty": qty,
                "price": price,
                "action": action,
                "product": product,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        body = {
            "trading_symbol": symbol,
            "quantity": qty,
            "price": price,
            "validity": "DAY",
            "exchange": exchange,
            "segment": segment,
            "product": product,
            "order_type": order_type,
            "transaction_type": action,
            "order_reference_id": ref_id,
        }
        if trigger_price is not None:
            body["trigger_price"] = trigger_price

        return await self._request("POST", "/v1/order/create", json=body)

    async def cancel_order(self, order_id: str, segment: str = "CASH") -> dict:
        if _is_paper_mode():
            return {
                "groww_order_id": order_id,
                "order_status": "CANCELLED",
                "paper": True,
            }

        return await self._request(
            "POST",
            "/v1/order/cancel",
            json={
                "segment": segment,
                "groww_order_id": order_id,
            },
        )

    async def get_order_status(self, order_id: str, segment: str = "CASH") -> dict:
        if _is_paper_mode():
            return {
                "groww_order_id": order_id,
                "order_status": "COMPLETE",
                "filled_quantity": 0,
                "remark": "Paper order",
                "paper": True,
            }

        return await self._request(
            "GET",
            f"/v1/order/status/{order_id}",
            params={"segment": segment},
        )

    async def place_gtt_stoploss(
        self,
        symbol: str,
        qty: int,
        stoploss: float,
        product: str = "MIS",
        segment: str = "CASH",
        exchange: str = "NSE",
        position_action: str = "BUY",
    ) -> dict:
        ts = str(int(time.time()))[-6:]
        ref_id = f"GTT-{ts}-{symbol[:4].upper()}"

        # For long (BUY) positions: trigger when price drops to SL → SELL to close
        # For short (SELL) positions: trigger when price rises to SL → BUY to close
        if position_action == "BUY":
            trigger_direction = "DOWN"
            transaction_type = "SELL"
        else:
            trigger_direction = "UP"
            transaction_type = "BUY"

        if _is_paper_mode():
            mock_gtt_id = f"GTT-PAPER-{uuid.uuid4().hex[:6].upper()}"
            if position_action == "BUY":
                print(
                    f"[PAPER] GTT SL: SELL {qty} "
                    f"{symbol} if price <= ₹{stoploss}"
                )
            else:
                print(
                    f"[PAPER] GTT SL: BUY {qty} "
                    f"{symbol} if price >= ₹{stoploss}"
                )
            return {
                "smart_order_id": mock_gtt_id,
                "smart_order_type": "GTT",
                "status": "ACTIVE",
                "trading_symbol": symbol,
                "trigger_price": str(stoploss),
                "trigger_direction": trigger_direction,
                "paper": True,
                "remark": "Paper GTT — not sent to exchange",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        body = {
            "reference_id": ref_id,
            "smart_order_type": "GTT",
            "segment": segment,
            "trading_symbol": symbol,
            "quantity": qty,
            "trigger_price": str(stoploss),
            "trigger_direction": trigger_direction,
            "order": {
                "order_type": "MARKET",
                "price": None,
                "transaction_type": transaction_type,
            },
            "product_type": product,
            "exchange": exchange,
            "duration": "DAY",
        }
        return await self._request("POST", "/v1/order-advance/create", json=body)

    async def cancel_gtt(self, smart_order_id: str, segment: str = "CASH") -> dict:
        if _is_paper_mode():
            return {
                "smart_order_id": smart_order_id,
                "status": "CANCELLED",
                "paper": True,
            }

        return await self._request(
            "POST",
            f"/v1/order-advance/cancel/{segment}/GTT/{smart_order_id}",
        )

    async def get_order_list(self, segment: str = "CASH") -> list[dict]:
        payload = await self._request(
            "GET",
            "/v1/order/list",
            params={
                "segment": segment,
                "page": 0,
                "page_size": 100,
            },
        )
        return payload.get("order_list", [])


groww_client = GrowwClient()
