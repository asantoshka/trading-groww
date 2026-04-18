from fastapi import APIRouter

from scheduler import trading_scheduler
from services.market_hours import fetch_nse_holidays, get_market_status, next_market_open

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
def get_scheduler_status() -> dict:
    return trading_scheduler.get_status()


@router.post("/pause")
def pause_scheduler() -> dict[str, str]:
    trading_scheduler.pause_scans()
    return {"message": "Scan jobs paused", "status": "paused"}


@router.post("/resume")
def resume_scheduler() -> dict[str, str]:
    trading_scheduler.resume_scans()
    return {"message": "Scan jobs resumed", "status": "running"}


@router.post("/trigger")
async def trigger_scheduler_now() -> dict[str, object]:
    result = await trading_scheduler.trigger_now()
    return {
        "message": "Scan triggered immediately" if result else "Trigger failed",
        "success": result,
    }


@router.post("/reload")
async def reload_scheduler() -> dict[str, object]:
    await trading_scheduler.reload_scan_times()
    return {"message": "Schedule reloaded", "status": trading_scheduler.get_status()}


router_market = APIRouter(prefix="/api/market", tags=["market"])


@router_market.get("/status")
async def market_status() -> dict:
    status = get_market_status()
    status["next_open"] = next_market_open()
    return status


@router_market.post("/refresh-holidays")
async def refresh_holidays() -> dict:
    await fetch_nse_holidays()
    status = get_market_status()
    return {
        "message": "Holiday cache refreshed",
        "holidays_loaded": status["holiday_count"],
    }
