import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import WebSocket

from database import get_db
from models import AgentLog


VALID_AGENTS = {"market_scanner", "risk_gatekeeper", "execution"}
VALID_LEVELS = {"info", "success", "warning", "error"}
logger = logging.getLogger(__name__)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ist_time() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M:%S")


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("[WS] Client connected. Total: %s", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("[WS] Client disconnected. Total: %s", len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        json_string = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json_string)
            except Exception:
                self.disconnect(connection)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)

    def connection_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()


async def broadcast_ltp_update(
    symbol: str,
    ltp: float,
    change: float,
    change_pct: float,
) -> None:
    await manager.broadcast(
        {
            "type": "ltp_update",
            "symbol": symbol,
            "ltp": ltp,
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "timestamp": _utc_iso(),
        }
    )


async def broadcast_agent_log(agent: str, level: str, msg: str) -> None:
    if agent not in VALID_AGENTS:
        raise ValueError(f"Invalid agent: {agent}")
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid level: {level}")

    payload = {
        "type": "agent_log",
        "agent": agent,
        "level": level,
        "msg": msg,
        "time": _ist_time(),
        "timestamp": _utc_iso(),
    }

    db_generator = get_db()
    db = next(db_generator)
    try:
        db.add(
            AgentLog(
                time=payload["time"],
                agent=agent,
                level=level,
                msg=msg,
            )
        )
        db.commit()
    finally:
        db.close()
        db_generator.close()

    await manager.broadcast(payload)


async def broadcast_new_signal(signal_dict: dict) -> None:
    await manager.broadcast(
        {
            "type": "new_signal",
            "signal": signal_dict,
            "timestamp": _utc_iso(),
        }
    )


async def broadcast_order_filled(
    order_id: str,
    symbol: str,
    qty: int,
    price: float,
    action: str,
    mode: str,
) -> None:
    await manager.broadcast(
        {
            "type": "order_filled",
            "order_id": order_id,
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "action": action,
            "mode": mode,
            "timestamp": _utc_iso(),
        }
    )


async def broadcast_pnl_update(
    total_pnl: float,
    total_pnl_pct: float,
    available_capital: float,
) -> None:
    await manager.broadcast(
        {
            "type": "pnl_update",
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "available_capital": round(available_capital, 2),
            "timestamp": _utc_iso(),
        }
    )


async def broadcast_agent_status(
    agent: str,
    status: str,
    last_run: str = None,
) -> None:
    await manager.broadcast(
        {
            "type": "agent_status",
            "agent": agent,
            "status": status,
            "last_run": last_run,
            "timestamp": _utc_iso(),
        }
    )
