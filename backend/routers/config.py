import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from mock_data import MOCK_AGENTS, MOCK_CAPITAL, MOCK_POSITIONS
from models import Config, Signal, Trade
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
