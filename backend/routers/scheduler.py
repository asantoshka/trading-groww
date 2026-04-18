from fastapi import APIRouter

from scheduler import trading_scheduler


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
