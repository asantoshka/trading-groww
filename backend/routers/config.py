import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from mock_data import MOCK_AGENTS, MOCK_CAPITAL, MOCK_POSITIONS
from models import AgentLog, Config, Position, Signal, Trade
from schemas import ConfigResponse, ConfigUpdate
from scheduler import trading_scheduler


router = APIRouter(tags=["config"])


@router.get("/config")
def get_config(db: Session = Depends(get_db)) -> dict[str, object]:
    config = db.query(Config).filter(Config.id == 1).first()
    if config is None:
        raise HTTPException(status_code=500, detail="Config not initialized. Run seed.py first.")

    return ConfigResponse.model_validate(config).model_dump()


@router.post("/config")
async def update_config(payload: ConfigUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    updates = payload.model_dump(exclude_none=True)
    config = db.query(Config).filter(Config.id == 1).first()
    if config is None:
        raise HTTPException(status_code=500, detail="Config not initialized. Run seed.py first.")

    if "mode" in updates and updates["mode"] not in {"paper", "live"}:
        raise HTTPException(status_code=422, detail="mode must be 'paper' or 'live'")

    if "capital_limit" in updates and updates["capital_limit"] <= 0:
        raise HTTPException(status_code=422, detail="capital_limit must be greater than 0")

    if "min_rr_ratio" in updates and updates["min_rr_ratio"] < 1.0:
        raise HTTPException(status_code=422, detail="min_rr_ratio must be at least 1.0")

    for field, value in updates.items():
        if field in {"scan_times", "watchlist"}:
            setattr(config, field, json.dumps(value))
        else:
            setattr(config, field, value)

    config.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(config)

    await trading_scheduler.reload_scan_times()

    return {
        "message": "Config updated",
        "config": ConfigResponse.model_validate(config).model_dump(),
    }


@router.post("/admin/reset-paper-data")
def reset_paper_data(
    x_confirm: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if x_confirm != "RESET":
        raise HTTPException(
            status_code=400,
            detail="Send header X-Confirm: RESET to confirm",
        )

    trades_deleted = db.query(Trade).filter(Trade.mode == "paper").delete()
    signals_deleted = db.query(Signal).delete()
    positions_deleted = db.query(Position).delete()
    logs_deleted = db.query(AgentLog).delete()

    config = db.query(Config).filter(Config.id == 1).first()
    if config:
        from mock_data import MOCK_CONFIG
        config.capital_limit = MOCK_CONFIG["capital_limit"]
        config.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Paper data cleared",
        "deleted": {
            "trades": trades_deleted,
            "signals": signals_deleted,
            "positions": positions_deleted,
            "logs": logs_deleted,
        },
    }


@router.get("/status")
def get_status(db: Session = Depends(get_db)) -> dict[str, object]:
    config = db.query(Config).filter(Config.id == 1).first()
    if config is None:
        raise HTTPException(status_code=500, detail="Config not initialized. Run seed.py first.")

    _open_trades_count = db.query(Trade).filter(Trade.status == "open").count()
    today_signals = db.query(Signal).filter(func.date(Signal.created_at) == date.today()).count()
    _ = _open_trades_count

    return {
        "capital": MOCK_CAPITAL,
        "agents": MOCK_AGENTS,
        "mode": config.mode,
        "today_signals": today_signals,
        "open_positions": len(MOCK_POSITIONS),
    }
