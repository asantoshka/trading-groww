import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from mock_data import MOCK_AGENTS
from models import AgentLog
from schemas import AgentLogResponse
from services.execution_agent import execution_agent
from services.market_hours import get_market_status
from services.market_scanner import market_scanner


router = APIRouter(tags=["agents"])

VALID_AGENTS = {"market_scanner", "risk_gatekeeper", "execution"}


def validate_agent_name(name: str) -> None:
    if name not in VALID_AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/agents")
def get_agents(db: Session = Depends(get_db)) -> dict[str, dict[str, object]]:
    _ = db
    scanner_last_run = (
        market_scanner._last_run.isoformat() if market_scanner._last_run else None
    )
    return {
        "market_scanner": {
            "status": "running" if market_scanner.is_running else "stopped",
            "last_run": scanner_last_run,
            "mode": "paper",
        },
        "risk_gatekeeper": MOCK_AGENTS["risk_gatekeeper"],
        "execution": {
            "status": "running" if execution_agent.is_running else "stopped",
            "last_run": None,
            "mode": "paper",
            "active_positions": len(execution_agent._active_positions),
            "monitoring": execution_agent.get_status()["monitoring"],
        },
    }


@router.get("/agents/logs")
def get_agent_logs(
    agent: str = "all",
    level: str = "all",
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    query = db.query(AgentLog)

    if agent.lower() != "all":
        query = query.filter(AgentLog.agent == agent.lower())

    if level.lower() != "all":
        query = query.filter(AgentLog.level == level.lower())

    total = query.count()
    logs = query.order_by(AgentLog.id.desc()).limit(limit).all()

    return {
        "logs": [AgentLogResponse.model_validate(log).model_dump() for log in logs],
        "total": total,
    }


@router.post("/agents/{name}/start")
def start_agent(name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    _ = db
    validate_agent_name(name)
    return {"agent": name, "status": "running", "message": "Agent started"}


@router.post("/agents/{name}/stop")
def stop_agent(name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    _ = db
    validate_agent_name(name)
    return {"agent": name, "status": "stopped", "message": "Agent stopped"}


@router.post("/agents/{name}/restart")
def restart_agent(name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    _ = db
    validate_agent_name(name)
    return {"agent": name, "status": "running", "message": "Agent restarted"}


@router.post("/agents/scanner/trigger")
async def trigger_scanner() -> dict[str, object]:
    try:
        asyncio.create_task(market_scanner.run_scan())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger scan: {exc}",
        ) from exc
    market = get_market_status()
    return {
        "message": "Scan triggered manually",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_status": market["message"],
        "warning": (
            None
            if market["is_open"]
            else f"{market['message']}. Data may be stale."
        ),
    }
