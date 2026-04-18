import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from env_validator import env_validator
from mock_data import MOCK_AGENTS
from routers import agents, config, positions, signals, trades
from routers.risk import router as risk_router
from routers.scheduler import router as scheduler_router
from routers.websocket import router as ws_router
from scheduler import trading_scheduler
from services.websocket_manager import manager


logger = logging.getLogger(__name__)
app = FastAPI(title="Groww Agent Trading API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_environment() -> None:
    load_dotenv()


@app.on_event("startup")
async def startup() -> None:
    from database import Base, SessionLocal, engine
    from models import Config
    import models  # noqa: F401

    env_validator.validate_and_exit()
    Base.metadata.create_all(bind=engine)
    mode_from_env = os.getenv("MODE", "paper").lower()
    db = SessionLocal()
    try:
        config = db.query(Config).filter(Config.id == 1).first()
        if config and config.mode != mode_from_env:
            config.mode = mode_from_env
            db.commit()
            print(f"[Startup] Mode set to {mode_from_env} from env")
    finally:
        db.close()
    logger.info("Database tables created / verified")
    await trading_scheduler.start()
    print("[Startup] Scheduler started")


@app.on_event("shutdown")
async def shutdown() -> None:
    trading_scheduler.shutdown()
    print("[Shutdown] Scheduler stopped")


def get_mode() -> str:
    try:
        from database import SessionLocal
        from models import Config

        db = SessionLocal()
        try:
            config = db.query(Config).filter(Config.id == 1).first()
            if config:
                return config.mode
            return os.getenv("MODE", "paper")
        finally:
            db.close()
    except Exception:
        return os.getenv("MODE", "paper")


@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "1.0.0"
    response.headers["X-Trading-Mode"] = get_mode()
    return response


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Groww Agent Trading API",
        "version": "1.0.0",
        "mode": get_mode(),
    }


@app.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": MOCK_AGENTS,
        "mode": get_mode(),
        "ws_connections": manager.connection_count(),
    }


app.include_router(agents.router, prefix="/api")
app.include_router(positions.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(risk_router)
app.include_router(scheduler_router)
app.include_router(ws_router)
