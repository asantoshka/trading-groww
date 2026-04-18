from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Signal
from schemas import ManualSignalRequest, SignalResponse


router = APIRouter(tags=["signals"])


@router.get("/signals")
def get_signals(mode: str = "all", db: Session = Depends(get_db)) -> dict[str, object]:
    query = db.query(Signal)

    if mode.lower() != "all":
        query = query.filter(Signal.mode == mode)

    signals = query.order_by(Signal.created_at.desc()).all()
    return {
        "signals": [SignalResponse.model_validate(signal).model_dump() for signal in signals],
        "total": len(signals),
    }


@router.get("/signals/today")
def get_today_signals(db: Session = Depends(get_db)) -> dict[str, object]:
    today = date.today()
    signals = (
        db.query(Signal)
        .filter(func.date(Signal.created_at) == today)
        .order_by(Signal.created_at.desc())
        .all()
    )
    return {
        "signals": [SignalResponse.model_validate(signal).model_dump() for signal in signals],
        "date": today.isoformat(),
    }


@router.post("/signals/manual")
def inject_manual_signal(
    payload: ManualSignalRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    action = payload.action.upper()

    if action not in {"BUY", "SELL"}:
        raise HTTPException(status_code=422, detail="action must be BUY or SELL")

    if action == "BUY":
        if payload.target <= payload.entry_price:
            raise HTTPException(
                status_code=422,
                detail="target must be greater than entry_price for BUY",
            )
        if payload.stoploss >= payload.entry_price:
            raise HTTPException(
                status_code=422,
                detail="stoploss must be less than entry_price for BUY",
            )

    signal = Signal(
        id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
        symbol=payload.symbol,
        exchange="NSE",
        action=action,
        entry_price=payload.entry_price,
        target=payload.target,
        stoploss=payload.stoploss,
        qty=payload.qty,
        risk_status="pending",
        executed=False,
        mode="paper",
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    return {
        "message": "Manual signal injected",
        "signal": SignalResponse.model_validate(signal).model_dump(),
    }


@router.get("/signals/analytics")
def get_signal_analytics(db: Session = Depends(get_db)) -> dict[str, object]:
    signals = db.query(Signal).all()
    total = len(signals)
    approved = sum(1 for signal in signals if signal.risk_status == "approved")
    rejected = sum(1 for signal in signals if signal.risk_status == "rejected")
    executed = sum(1 for signal in signals if signal.executed)

    confidence_values = [signal.confidence for signal in signals if signal.confidence is not None]
    avg_confidence = (
        round(sum(confidence_values) / len(confidence_values), 2)
        if confidence_values
        else 0.0
    )

    rejection_counts: dict[str, int] = {}
    for signal in signals:
        if signal.risk_status != "rejected":
            continue
        reason = signal.reject_reason or "Unknown"
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

    rejection_reasons = sorted(
        (
            {"reason": reason, "count": count}
            for reason, count in rejection_counts.items()
        ),
        key=lambda item: item["count"],
        reverse=True,
    )

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "executed": executed,
        "avg_confidence": avg_confidence,
        "rejection_reasons": rejection_reasons,
    }
