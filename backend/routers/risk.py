from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from mock_data import MOCK_CAPITAL
from models import Config, Signal
from services.risk_gatekeeper import RiskConfig, RiskGatekeeper


router = APIRouter(prefix="/api/risk", tags=["risk"])


def build_risk_config(config: Optional[Config]) -> RiskConfig:
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="Config not initialized. Run seed.py first.",
        )

    return RiskConfig(
        capital_limit=config.capital_limit,
        max_trade_value=config.max_trade_value,
        max_loss_per_trade=config.max_loss_per_trade,
        min_rr_ratio=config.min_rr_ratio,
        confidence_threshold=config.confidence_threshold,
        max_capital_pct=0.40,
        mode=config.mode,
    )


@router.post("/evaluate")
def evaluate_risk(body: dict, db: Session = Depends(get_db)) -> dict:
    config = db.query(Config).filter(Config.id == 1).first()
    risk_config = build_risk_config(config)
    available_capital = body.get("available_capital", MOCK_CAPITAL["available"])
    signal = body.get("signal")

    if not isinstance(signal, dict):
        raise HTTPException(status_code=422, detail="signal must be an object")

    gatekeeper = RiskGatekeeper(risk_config)
    try:
        result = gatekeeper.evaluate_from_dict(signal, available_capital)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return gatekeeper.result_to_dict(result)


@router.post("/evaluate/{signal_id}")
def evaluate_signal_by_id(signal_id: str, db: Session = Depends(get_db)) -> dict:
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")

    config = db.query(Config).filter(Config.id == 1).first()
    risk_config = build_risk_config(config)
    gatekeeper = RiskGatekeeper(risk_config)

    signal_dict = {
        "symbol": signal.symbol,
        "action": signal.action,
        "entry_price": signal.entry_price,
        "target": signal.target,
        "stoploss": signal.stoploss,
        "qty": signal.qty,
        "confidence": signal.confidence if signal.confidence is not None else 0,
        "mode": signal.mode or "paper",
    }

    result = gatekeeper.evaluate_from_dict(
        signal_dict,
        MOCK_CAPITAL["available"],
    )

    signal.risk_status = "approved" if result.approved else "rejected"
    signal.reject_reason = result.reject_reason or None
    db.commit()

    return {"signal_id": signal_id, **gatekeeper.result_to_dict(result)}


@router.get("/config")
def get_risk_config(db: Session = Depends(get_db)) -> dict:
    config = db.query(Config).filter(Config.id == 1).first()
    risk_config = build_risk_config(config)

    return {
        "capital_limit": risk_config.capital_limit,
        "max_trade_value": risk_config.max_trade_value,
        "max_loss_per_trade": risk_config.max_loss_per_trade,
        "min_rr_ratio": risk_config.min_rr_ratio,
        "confidence_threshold": risk_config.confidence_threshold,
        "max_capital_pct": risk_config.max_capital_pct,
        "mode": risk_config.mode,
    }
