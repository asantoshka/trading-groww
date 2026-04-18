from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Trade
from schemas import TradeResponse


router = APIRouter(tags=["trades"])


@router.get("/trades")
def get_trades(
    mode: str = "all",
    symbol: str = "",
    result: str = "all",
    db: Session = Depends(get_db),
) -> dict[str, object]:
    query = db.query(Trade)

    if mode.lower() != "all":
        query = query.filter(Trade.mode == mode)

    if symbol:
        query = query.filter(Trade.symbol.ilike(f"%{symbol}%"))

    if result.lower() == "winners":
        query = query.filter(Trade.pnl > 0)
    elif result.lower() == "losers":
        query = query.filter(Trade.pnl < 0)

    total = query.count()
    trades = query.order_by(Trade.created_at.desc()).all()
    return {
        "trades": [TradeResponse.model_validate(trade).model_dump() for trade in trades],
        "total": total,
    }


@router.get("/trades/stats")
def get_trade_stats(db: Session = Depends(get_db)) -> dict[str, object]:
    trades = db.query(Trade).all()
    total_trades = len(trades)

    if total_trades == 0:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "avg_pnl": 0.0,
            "total_pnl": 0.0,
            "best_trade": None,
            "worst_trade": None,
        }

    pnl_values = [trade.pnl for trade in trades if trade.pnl is not None]
    winning_trades = sum(1 for trade in trades if trade.pnl is not None and trade.pnl > 0)
    losing_trades = sum(1 for trade in trades if trade.pnl is not None and trade.pnl < 0)
    total_pnl = round(sum(pnl_values), 2) if pnl_values else 0.0
    avg_pnl = round(sum(pnl_values) / len(pnl_values), 2) if pnl_values else 0.0
    win_rate = round((winning_trades / total_trades) * 100, 2) if total_trades else 0.0

    best_trade_row = max(
        (trade for trade in trades if trade.pnl is not None),
        key=lambda trade: trade.pnl,
        default=None,
    )
    worst_trade_row = min(
        (trade for trade in trades if trade.pnl is not None),
        key=lambda trade: trade.pnl,
        default=None,
    )

    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "avg_pnl": avg_pnl,
        "total_pnl": total_pnl,
        "best_trade": (
            TradeResponse.model_validate(best_trade_row).model_dump()
            if best_trade_row is not None
            else None
        ),
        "worst_trade": (
            TradeResponse.model_validate(worst_trade_row).model_dump()
            if worst_trade_row is not None
            else None
        ),
    }


@router.get("/trades/{trade_id}")
def get_trade(trade_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")

    return TradeResponse.model_validate(trade).model_dump()
