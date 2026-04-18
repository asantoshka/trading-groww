import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from services.market_scanner import market_scanner
from services.telegram_notifier import telegram
from services.token_manager import token_manager
from services.websocket_manager import broadcast_agent_log, broadcast_agent_status


logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

async def job_market_scan():
    """Triggered at configured scan times."""
    logger.info("[Scheduler] Market scan job started")
    await broadcast_agent_log(
        "market_scanner",
        "info",
        "Scheduled scan triggered by APScheduler",
    )
    try:
        await market_scanner.run_scan()
    except Exception as exc:
        logger.error(f"Scheduled scan failed: {exc}")
        await broadcast_agent_log(
            "market_scanner",
            "error",
            f"Scheduled scan error: {str(exc)}",
        )


async def job_token_refresh():
    """Runs at 6:05 AM IST — after Groww resets tokens."""
    logger.info("[Scheduler] Groww token refresh job")
    await broadcast_agent_log(
        "market_scanner",
        "warning",
        "6:05 AM IST — Groww daily token reset occurred. "
        "Invalidating cached token...",
    )
    await token_manager.invalidate()
    await broadcast_agent_log(
        "market_scanner",
        "info",
        "Token invalidated. Will regenerate on next "
        "API call. Please approve today's session at "
        "groww.in/user/profile/trading-apis if required.",
    )
    await telegram.notify_token_refresh()


async def job_squareoff_warning():
    """Runs at 15:05 IST — warns before auto square-off."""
    logger.info("[Scheduler] Square-off warning job")
    await broadcast_agent_log(
        "execution",
        "warning",
        "⚠️ 15:05 IST — Auto square-off in 5 minutes. "
        "All open MIS positions will be closed at 15:10.",
    )
    await broadcast_agent_status("execution", "warning", None)
    await telegram.notify_squareoff_warning()


async def job_market_open_check():
    """Runs at 9:14 AM IST — pre-market check."""
    logger.info("[Scheduler] Market open check")
    await broadcast_agent_log(
        "market_scanner",
        "info",
        "📈 Market opens in 1 minute. "
        "First scan scheduled at 09:15 IST.",
    )
    await telegram.notify_market_open()


class TradingScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=IST)
        self._scan_jobs: list[str] = []
        self._initialized = False

    def setup_jobs(self, scan_times: list[str]):
        for job_id in self._scan_jobs:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
        self._scan_jobs = []

        for i, time_str in enumerate(scan_times):
            hour, minute = time_str.split(":")
            job_id = f"scan_{i}_{time_str.replace(':', '')}"
            self.scheduler.add_job(
                job_market_scan,
                trigger=CronTrigger(
                    hour=int(hour),
                    minute=int(minute),
                    timezone=IST,
                ),
                id=job_id,
                name=f"Market Scan {time_str} IST",
                replace_existing=True,
                misfire_grace_time=300,
            )
            self._scan_jobs.append(job_id)
            logger.info(f"[Scheduler] Scan job added: {time_str} IST")

    async def start(self):
        if self._initialized:
            return

        db = SessionLocal()
        try:
            from models import Config

            config = db.query(Config).filter(Config.id == 1).first()
            scan_times = config.get_scan_times() if config else ["09:15", "11:00", "13:30"]
        finally:
            db.close()

        self.setup_jobs(scan_times)

        self.scheduler.add_job(
            job_token_refresh,
            trigger=CronTrigger(hour=6, minute=5, timezone=IST),
            id="token_refresh",
            name="Groww Token Refresh 6:05 AM",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_market_open_check,
            trigger=CronTrigger(hour=9, minute=14, timezone=IST),
            id="market_open_check",
            name="Market Open Check 9:14 AM",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_squareoff_warning,
            trigger=CronTrigger(hour=15, minute=5, timezone=IST),
            id="squareoff_warning",
            name="Square-off Warning 15:05",
            replace_existing=True,
        )

        self.scheduler.start()
        self._initialized = True

        logger.info("[Scheduler] Started with jobs: %s", len(self.scheduler.get_jobs()))
        await broadcast_agent_log(
            "market_scanner",
            "info",
            f"Scheduler started: {len(scan_times)} scan jobs + "
            "token refresh + square-off warning",
        )

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self._initialized = False
        logger.info("[Scheduler] Shutdown complete")

    def get_status(self) -> dict:
        jobs = self.scheduler.get_jobs()
        job_list = []
        for job in jobs:
            next_run = job.next_run_time
            job_list.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": next_run.isoformat() if next_run else None,
                    "next_run_ist": (
                        next_run.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
                        if next_run
                        else "paused"
                    ),
                }
            )

        return {
            "running": self._initialized,
            "job_count": len(jobs),
            "jobs": job_list,
            "timezone": "Asia/Kolkata",
        }

    async def reload_scan_times(self):
        db = SessionLocal()
        try:
            from models import Config

            config = db.query(Config).filter(Config.id == 1).first()
            if config:
                scan_times = config.get_scan_times()
                self.setup_jobs(scan_times)
                await broadcast_agent_log(
                    "market_scanner",
                    "info",
                    f"Scan schedule updated: {', '.join(scan_times)} IST",
                )
        finally:
            db.close()

    def pause_scans(self):
        for job_id in self._scan_jobs:
            try:
                self.scheduler.pause_job(job_id)
            except Exception:
                pass
        logger.info("[Scheduler] Scan jobs paused")

    def resume_scans(self):
        for job_id in self._scan_jobs:
            try:
                self.scheduler.resume_job(job_id)
            except Exception:
                pass
        logger.info("[Scheduler] Scan jobs resumed")

    async def trigger_now(self) -> bool:
        db = SessionLocal()
        try:
            db.close()
            await job_market_scan()
            return True
        except Exception as exc:
            logger.error(f"Manual trigger failed: {exc}")
            return False


trading_scheduler = TradingScheduler()
