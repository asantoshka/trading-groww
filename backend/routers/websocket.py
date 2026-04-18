import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect

import mock_data
from services.telegram_notifier import telegram
from services.websocket_manager import (
    broadcast_agent_log,
    broadcast_agent_status,
    broadcast_ltp_update,
    broadcast_new_signal,
    broadcast_order_filled,
    broadcast_pnl_update,
    manager,
)


router = APIRouter(tags=["websocket"])
_ = FastAPI


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await manager.send_personal(
            websocket,
            {
                "type": "connected",
                "message": "Connected to Groww Agent Trading feed",
                "connections": manager.connection_count(),
                "timestamp": _utc_iso(),
            },
        )

        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                continue

            if parsed.get("type") == "ping":
                await manager.send_personal(
                    websocket,
                    {
                        "type": "pong",
                        "timestamp": _utc_iso(),
                    },
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@router.get("/api/debug/ws/status")
async def websocket_status() -> dict[str, object]:
    return {
        "connections": manager.connection_count(),
        "status": "ok",
    }


@router.post("/api/debug/telegram/test")
async def test_telegram() -> dict[str, object]:
    result = await telegram.test_connection()
    return {
        "sent": result,
        "enabled": telegram.enabled,
    }


@router.post("/api/debug/ws/fire")
async def fire_event(
    body: Optional[Dict[str, Any]] = Body(default=None),
) -> dict[str, object]:
    request_body = body or {}
    event_type = request_body.get("event_type")
    payload = request_body.get("payload") or {}

    try:
        if event_type == "ltp_update":
            await broadcast_ltp_update(
                payload.get("symbol", "NHPC"),
                payload.get("ltp", 86.20),
                payload.get("change", 0.50),
                payload.get("change_pct", 0.58),
            )
        elif event_type == "agent_log":
            await broadcast_agent_log(
                payload.get("agent", "market_scanner"),
                payload.get("level", "info"),
                payload.get("msg", "Test log message"),
            )
        elif event_type == "new_signal":
            await broadcast_new_signal(payload or mock_data.MOCK_SIGNALS[0])
        elif event_type == "order_filled":
            await broadcast_order_filled(
                payload.get("order_id", "TEST-001"),
                payload.get("symbol", "NHPC"),
                payload.get("qty", 10),
                payload.get("price", 86.20),
                payload.get("action", "BUY"),
                payload.get("mode", "paper"),
            )
        elif event_type == "pnl_update":
            await broadcast_pnl_update(
                payload.get("total_pnl", 342.50),
                payload.get("total_pnl_pct", 6.85),
                payload.get("available_capital", 3241.50),
            )
        elif event_type == "agent_status":
            await broadcast_agent_status(
                payload.get("agent", "market_scanner"),
                payload.get("status", "running"),
                payload.get("last_run"),
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown event type: {event_type}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "fired": event_type,
        "connections_notified": manager.connection_count(),
    }


@router.post("/api/debug/ws/simulate")
async def simulate_feed() -> dict[str, object]:
    events = [
        lambda: broadcast_agent_log(
            "market_scanner",
            "info",
            "Starting market scan for watchlist symbols",
        ),
        lambda: broadcast_agent_log(
            "market_scanner",
            "info",
            "Fetching LTP for: NHPC, IRCTC, SAIL, RELIANCE",
        ),
        lambda: broadcast_ltp_update("NHPC", 86.45, 0.25, 0.29),
        lambda: broadcast_agent_log(
            "market_scanner",
            "success",
            "Signal generated: BUY NHPC @ ₹84.10 | RSI: 31.2 | Confidence: 78%",
        ),
        lambda: broadcast_new_signal(mock_data.MOCK_SIGNALS[0]),
        lambda: broadcast_agent_log(
            "risk_gatekeeper",
            "success",
            "Signal approved — RR: 1.91, Risk: ₹207, Capital used: 15.1%",
        ),
        lambda: broadcast_agent_log(
            "execution",
            "success",
            "Order placed: BUY 9 NHPC @ ₹84.10 — Order ID: GRW8821",
        ),
        lambda: broadcast_order_filled("GRW8821", "NHPC", 9, 84.10, "BUY", "paper"),
        lambda: broadcast_pnl_update(342.50, 6.85, 3241.50),
    ]

    for index, event in enumerate(events):
        await event()
        if index < len(events) - 1:
            await asyncio.sleep(0.5)

    return {
        "simulated": True,
        "events_fired": 9,
        "connections_notified": manager.connection_count(),
    }
