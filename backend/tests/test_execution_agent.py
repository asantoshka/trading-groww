from datetime import datetime as real_datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.execution_agent import ExecutionAgent


@pytest.fixture
def agent():
    return ExecutionAgent()


@pytest.fixture
def mock_signal():
    signal = MagicMock()
    signal.id = "sig-test-001"
    signal.symbol = "NHPC"
    signal.action = "BUY"
    signal.entry_price = 84.10
    signal.target = 89.50
    signal.stoploss = 81.00
    signal.qty = 9
    signal.confidence = 78
    signal.mode = "paper"
    return signal


@pytest.fixture
def mock_order():
    return {
        "groww_order_id": "PAPER-ABC123",
        "order_status": "OPEN",
        "order_reference_id": "BOT-123-NHPC",
        "paper": True,
    }


@pytest.fixture
def mock_gtt():
    return {
        "smart_order_id": "GTT-PAPER-XYZ",
        "status": "ACTIVE",
        "paper": True,
    }


def _frozen_datetime(year, month, day, hour, minute):
    class FrozenDateTime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            dt = real_datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
            if tz is not None:
                return dt.astimezone(tz)
            return dt

    return FrozenDateTime


def test_agent_init():
    agent = ExecutionAgent()
    assert agent.is_running is False
    assert agent._active_positions == {}
    assert agent._monitoring_task is None


@pytest.mark.asyncio
async def test_place_entry_order_success(agent, mock_signal, mock_order):
    with patch(
        "services.execution_agent.groww_client.place_order",
        new=AsyncMock(return_value=mock_order),
    ), patch("services.execution_agent.broadcast_agent_log", new=AsyncMock()):
        order = await agent._place_entry_order(mock_signal, MagicMock())

    assert order is not None
    assert order["groww_order_id"] == "PAPER-ABC123"


@pytest.mark.asyncio
async def test_place_entry_order_failure(agent, mock_signal):
    with patch(
        "services.execution_agent.groww_client.place_order",
        new=AsyncMock(side_effect=Exception("failed")),
    ), patch("services.execution_agent.broadcast_agent_log", new=AsyncMock()):
        order = await agent._place_entry_order(mock_signal, MagicMock())

    assert order is None


@pytest.mark.asyncio
async def test_place_gtt_stoploss_success(agent, mock_signal, mock_gtt):
    with patch(
        "services.execution_agent.groww_client.place_gtt_stoploss",
        new=AsyncMock(return_value=mock_gtt),
    ), patch("services.execution_agent.broadcast_agent_log", new=AsyncMock()):
        gtt = await agent._place_gtt_stoploss(mock_signal, "PAPER-ABC123")

    assert gtt is not None
    assert gtt["smart_order_id"] == "GTT-PAPER-XYZ"


@pytest.mark.asyncio
async def test_place_gtt_failure_non_fatal(agent, mock_signal):
    with patch(
        "services.execution_agent.groww_client.place_gtt_stoploss",
        new=AsyncMock(side_effect=Exception("gtt failed")),
    ), patch("services.execution_agent.broadcast_agent_log", new=AsyncMock()):
        gtt = await agent._place_gtt_stoploss(mock_signal, "PAPER-ABC123")

    assert gtt is None


def test_is_squareoff_time_before(agent):
    with patch(
        "services.execution_agent.datetime",
        _frozen_datetime(2026, 4, 17, 8, 30),
    ):
        assert agent._is_squareoff_time() is False


def test_is_squareoff_time_after(agent):
    with patch(
        "services.execution_agent.datetime",
        _frozen_datetime(2026, 4, 17, 9, 45),
    ):
        assert agent._is_squareoff_time() is True


def test_is_squareoff_time_exact(agent):
    with patch(
        "services.execution_agent.datetime",
        _frozen_datetime(2026, 4, 17, 9, 40),
    ):
        assert agent._is_squareoff_time() is True


@pytest.mark.asyncio
async def test_check_target_hit_not_reached(agent):
    position = {
        "id": "pos-001",
        "symbol": "NHPC",
        "qty": 9,
        "entry_price": 84.10,
        "target": 89.50,
        "stoploss": 81.00,
        "gtt_order_id": "GTT-XYZ",
        "mode": "paper",
    }
    with patch("services.execution_agent.broadcast_agent_log", new=AsyncMock()):
        result = await agent._check_target_hit(position, 86.00)

    assert result is False


@pytest.mark.asyncio
async def test_check_target_hit_reached(agent, mock_order):
    position = {
        "id": "pos-001",
        "symbol": "NHPC",
        "qty": 9,
        "entry_price": 84.10,
        "target": 89.50,
        "stoploss": 81.00,
        "gtt_order_id": "GTT-XYZ",
        "mode": "paper",
    }
    mock_db = MagicMock()
    with patch(
        "services.execution_agent.groww_client.place_order",
        new=AsyncMock(return_value=mock_order),
    ), patch(
        "services.execution_agent.groww_client.cancel_gtt",
        new=AsyncMock(return_value={"status": "CANCELLED"}),
    ), patch(
        "services.execution_agent.broadcast_agent_log", new=AsyncMock()
    ), patch(
        "services.execution_agent.SessionLocal", return_value=mock_db
    ), patch.object(
        agent, "_close_position", new=AsyncMock(return_value=True)
    ):
        result = await agent._check_target_hit(position, 89.60)

    assert result is True


def test_get_status_initial(agent):
    status = agent.get_status()
    assert status["is_running"] is False
    assert status["active_positions"] == 0
    assert status["monitoring"] is False


def test_get_active_positions_empty(agent):
    positions = agent.get_active_positions()
    assert positions == []


@pytest.mark.asyncio
async def test_execute_insufficient_margin(agent, mock_signal):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with patch(
        "services.execution_agent.SessionLocal", return_value=mock_db
    ), patch(
        "services.execution_agent.groww_client.get_margin",
        new=AsyncMock(return_value={"available_margin": 100.0}),
    ), patch(
        "services.execution_agent.broadcast_agent_log", new=AsyncMock()
    ), patch(
        "services.execution_agent.broadcast_agent_status", new=AsyncMock()
    ):
        result = await agent.execute(mock_signal, MagicMock())

    assert result is None
    assert agent.is_running is False


@pytest.mark.asyncio
async def test_execute_full_flow_paper(agent, mock_signal, mock_order, mock_gtt):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_position = MagicMock()
    with patch(
        "services.execution_agent.SessionLocal", return_value=mock_db
    ), patch(
        "services.execution_agent.groww_client.get_margin",
        new=AsyncMock(return_value={"available_margin": 5000.0}),
    ), patch.object(
        agent, "_place_entry_order", new=AsyncMock(return_value=mock_order)
    ), patch.object(
        agent, "_place_gtt_stoploss", new=AsyncMock(return_value=mock_gtt)
    ), patch.object(
        agent, "_create_position", new=AsyncMock(return_value=mock_position)
    ), patch.object(
        agent, "_monitor_positions", new=AsyncMock(return_value=None)
    ), patch(
        "services.execution_agent.broadcast_agent_log", new=AsyncMock()
    ), patch(
        "services.execution_agent.broadcast_agent_status", new=AsyncMock()
    ):
        result = await agent.execute(mock_signal, MagicMock())

    assert result is mock_position
    assert agent.is_running is False


@pytest.mark.asyncio
async def test_monitoring_task_started(agent, mock_signal, mock_order, mock_gtt):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_position = MagicMock()
    with patch(
        "services.execution_agent.SessionLocal", return_value=mock_db
    ), patch(
        "services.execution_agent.groww_client.get_margin",
        new=AsyncMock(return_value={"available_margin": 5000.0}),
    ), patch.object(
        agent, "_place_entry_order", new=AsyncMock(return_value=mock_order)
    ), patch.object(
        agent, "_place_gtt_stoploss", new=AsyncMock(return_value=mock_gtt)
    ), patch.object(
        agent, "_create_position", new=AsyncMock(return_value=mock_position)
    ), patch.object(
        agent, "_monitor_positions", new=AsyncMock(return_value=None)
    ), patch(
        "services.execution_agent.broadcast_agent_log", new=AsyncMock()
    ), patch(
        "services.execution_agent.broadcast_agent_status", new=AsyncMock()
    ):
        await agent.execute(mock_signal, MagicMock())

    assert agent._monitoring_task is not None
    agent._monitoring_task.cancel()
