from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from mock_data import MOCK_POSITIONS
from models import Position
from services.execution_agent import execution_agent


router = APIRouter(tags=["positions"])


@router.get("/positions")
def get_positions(db: Session = Depends(get_db)) -> dict[str, object]:
    db_positions = db.query(Position).filter(Position.status == "open").all()
    if not db_positions:
        total_pnl = round(sum(position["pnl"] for position in MOCK_POSITIONS), 2)
        return {
            "positions": MOCK_POSITIONS,
            "total": len(MOCK_POSITIONS),
            "total_pnl": total_pnl,
        }

    active = execution_agent._active_positions
    merged_positions = []
    for db_position in db_positions:
        active_data = active.get(db_position.id, {})
        ltp = active_data.get("current_ltp", db_position.entry_price)
        action = getattr(db_position, "action", None) or "BUY"
        if action == "BUY":
            pnl = (ltp - db_position.entry_price) * db_position.qty
        else:
            pnl = (db_position.entry_price - ltp) * db_position.qty
        pnl_pct = (pnl / (db_position.entry_price * db_position.qty)) * 100
        merged_positions.append(
            {
                "id": db_position.id,
                "symbol": db_position.symbol,
                "exchange": db_position.exchange,
                "action": action,
                "qty": db_position.qty,
                "entry_price": db_position.entry_price,
                "ltp": round(ltp, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "product": db_position.product,
                "mode": db_position.mode,
                "entry_time": db_position.entry_time.strftime("%H:%M:%S")
                if db_position.entry_time
                else None,
                "target": db_position.target,
                "stoploss": db_position.stoploss,
                "status": db_position.status,
            }
        )

    total_pnl = round(sum(position["pnl"] for position in merged_positions), 2)
    return {
        "positions": merged_positions,
        "total": len(merged_positions),
        "total_pnl": total_pnl,
    }


@router.post("/positions/{position_id}/close")
async def close_position(position_id: str) -> dict[str, str]:
    result = await execution_agent.manual_squareoff(position_id)
    if result:
        return {
            "message": "Position closed",
            "position_id": position_id,
            "mode": "live",
        }

    position = next(
        (item for item in MOCK_POSITIONS if item["id"] == position_id),
        None,
    )
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")

    return {
        "message": "Position closed (paper)",
        "position_id": position["id"],
        "symbol": position["symbol"],
        "mode": "paper",
    }


@router.get("/margin")
def get_margin() -> dict[str, object]:
    return {
        "used": 1758.50,
        "available": 3241.50,
        "total": 5000.00,
        "currency": "INR",
    }
