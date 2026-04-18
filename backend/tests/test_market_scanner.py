import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.market_scanner import MarketScanner


@pytest.fixture
def scanner():
    return MarketScanner()


@pytest.fixture
def mock_config():
    c = MagicMock()
    c.capital_limit = 5000.0
    c.max_trade_value = 2000.0
    c.max_loss_per_trade = 300.0
    c.min_rr_ratio = 1.5
    c.confidence_threshold = 70
    c.rsi_oversold = 35.0
    c.mode = "paper"
    c.get_watchlist.return_value = ["NHPC", "SAIL"]
    return c


@pytest.fixture
def sample_candles():
    import numpy as np

    candles = []
    price = 84.50
    for _ in range(50):
        change = price * np.random.uniform(-0.003, 0.003)
        open_price = round(price, 2)
        close_price = round(price + change, 2)
        high_price = round(max(open_price, close_price) * 1.002, 2)
        low_price = round(min(open_price, close_price) * 0.998, 2)
        candles.append(
            {
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 100000,
            }
        )
        price = close_price
    return candles


@pytest.fixture
def good_signal():
    return {
        "signal": True,
        "symbol": "NHPC",
        "action": "BUY",
        "entry_price": 84.10,
        "target": 89.50,
        "stoploss": 81.00,
        "qty": 9,
        "rsi": 31.2,
        "macd_state": "bullish_cross",
        "confidence": 78,
        "reasoning": "RSI oversold + MACD cross",
    }


def _make_response(text: str):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def _make_saved_signal(risk_status: str = "approved", confidence: int = 78):
    return SimpleNamespace(
        id="sig-new",
        symbol="NHPC",
        action="BUY",
        entry_price=84.10,
        target=89.50,
        stoploss=81.00,
        qty=9,
        rsi=31.2,
        macd_state="bullish_cross",
        confidence=confidence,
        risk_status=risk_status,
        reject_reason=None if risk_status == "approved" else "Rejected",
        executed=False,
        mode="paper",
        timestamp="10:00:00",
    )


def test_scanner_init():
    scanner = MarketScanner()
    assert scanner.is_running is False
    assert scanner._last_run is None
    assert scanner._last_signal is None


def test_compute_indicators_valid(scanner, sample_candles):
    indicators = scanner._compute_indicators(sample_candles)
    assert "rsi" in indicators
    assert "macd_state" in indicators
    assert "bullish_cross" in indicators
    assert 0 <= indicators["rsi"] <= 100
    assert indicators["macd_state"] in ["bullish_cross", "bullish", "bearish"]


def test_compute_indicators_insufficient_data(scanner, sample_candles):
    indicators = scanner._compute_indicators(sample_candles[:10])
    assert "error" in indicators
    assert indicators["error"] == "insufficient data"


def test_compute_indicators_macd_cross_detection(scanner):
    candles = []
    price = 100.0
    for index in range(50):
        if index < 40:
            price -= 0.6
        else:
            price += 1.2
        open_price = round(price - 0.2, 2)
        close_price = round(price, 2)
        high_price = round(max(open_price, close_price) * 1.002, 2)
        low_price = round(min(open_price, close_price) * 0.998, 2)
        candles.append(
            {
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 100000,
            }
        )

    indicators = scanner._compute_indicators(candles)
    assert "bullish_cross" in indicators
    assert isinstance(indicators["bullish_cross"], bool)


@pytest.mark.asyncio
async def test_analyze_symbol_no_candles(scanner, mock_config):
    with patch(
        "services.market_scanner.groww_client.get_historical_data",
        new=AsyncMock(return_value=[]),
    ):
        result = await scanner._analyze_symbol("NHPC", 84.50, mock_config)

    assert result["symbol"] == "NHPC"
    assert "error" in result
    assert result["error"] == "no historical data"


@pytest.mark.asyncio
async def test_analyze_symbol_with_data(scanner, mock_config, sample_candles):
    with patch(
        "services.market_scanner.groww_client.get_historical_data",
        new=AsyncMock(return_value=sample_candles),
    ):
        result = await scanner._analyze_symbol("NHPC", 84.50, mock_config)

    assert result["symbol"] == "NHPC"
    assert result["ltp"] == 84.50
    assert "indicators" in result
    assert "error" not in result["indicators"]


@pytest.mark.asyncio
async def test_call_claude_valid_signal(scanner, mock_config, good_signal):
    with patch(
        "services.market_scanner.llm_client.create",
        return_value=_make_response(json.dumps(good_signal)),
    ), patch(
        "services.market_scanner.llm_client.extract_text",
        return_value=json.dumps(good_signal),
    ):
        result = await scanner._call_claude(
            [
                {
                    "symbol": "NHPC",
                    "ltp": 84.50,
                    "indicators": {
                        "rsi": 31.2,
                        "macd_state": "bullish_cross",
                        "rsi_rising": True,
                        "bullish_cross": True,
                        "candle_count": 50,
                    },
                }
            ],
            mock_config,
        )

    assert result["signal"] is True
    assert result["symbol"] == "NHPC"


@pytest.mark.asyncio
async def test_call_claude_no_signal(scanner, mock_config):
    payload = json.dumps({"signal": False, "reasoning": "No oversold conditions"})
    with patch(
        "services.market_scanner.llm_client.create",
        return_value=_make_response(payload),
    ), patch(
        "services.market_scanner.llm_client.extract_text",
        return_value=payload,
    ):
        result = await scanner._call_claude(
            [{"symbol": "NHPC", "ltp": 84.50, "indicators": {}}],
            mock_config,
        )

    assert result["signal"] is False


@pytest.mark.asyncio
async def test_call_claude_api_error(scanner, mock_config):
    with patch(
        "services.market_scanner.llm_client.create",
        side_effect=Exception("API Error"),
    ):
        result = await scanner._call_claude(
            [{"symbol": "NHPC", "ltp": 84.50, "indicators": {}}],
            mock_config,
        )

    assert result is None


@pytest.mark.asyncio
async def test_call_claude_invalid_json(scanner, mock_config):
    with patch(
        "services.market_scanner.llm_client.create",
        return_value=_make_response("not json at all"),
    ), patch(
        "services.market_scanner.llm_client.extract_text",
        return_value="not json at all",
    ):
        result = await scanner._call_claude(
            [{"symbol": "NHPC", "ltp": 84.50, "indicators": {}}],
            mock_config,
        )

    assert result is None


def test_get_status():
    scanner = MarketScanner()
    status = scanner.get_status()
    assert "is_running" in status
    assert "last_run" in status
    assert "last_signal" in status
    assert status["is_running"] is False


@pytest.mark.asyncio
async def test_run_scan_no_signal(scanner, mock_config):
    mock_db = MagicMock()
    no_signal = {"signal": False, "reasoning": "No oversold conditions"}

    with patch(
        "services.market_scanner.SessionLocal",
        return_value=mock_db,
    ), patch.object(
        scanner, "_load_config", return_value=(mock_config, MagicMock(capital_limit=5000.0))
    ), patch(
        "services.market_scanner.groww_client.get_ltp",
        new=AsyncMock(return_value={"NHPC": 84.50}),
    ), patch.object(
        scanner,
        "_analyze_symbol",
        new=AsyncMock(
            return_value={
                "symbol": "NHPC",
                "ltp": 84.50,
                "indicators": {
                    "rsi": 31.2,
                    "macd_state": "bullish_cross",
                    "rsi_rising": True,
                    "bullish_cross": True,
                    "candle_count": 50,
                },
            }
        ),
    ), patch.object(
        scanner, "_call_claude", new=AsyncMock(return_value=no_signal)
    ), patch(
        "services.market_scanner.broadcast_agent_log", new=AsyncMock()
    ), patch(
        "services.market_scanner.broadcast_agent_status", new=AsyncMock()
    ), patch(
        "services.market_scanner.broadcast_new_signal", new=AsyncMock()
    ):
        result = await scanner.run_scan()

    assert result is None
    assert scanner.is_running is False
    mock_db.close.assert_called_once()


@pytest.mark.asyncio
async def test_run_scan_is_running_resets(scanner, mock_config):
    mock_db = MagicMock()

    with patch(
        "services.market_scanner.SessionLocal",
        return_value=mock_db,
    ), patch.object(
        scanner, "_load_config", return_value=(mock_config, MagicMock(capital_limit=5000.0))
    ), patch(
        "services.market_scanner.groww_client.get_ltp",
        new=AsyncMock(return_value={"NHPC": 84.50}),
    ), patch.object(
        scanner,
        "_analyze_symbol",
        new=AsyncMock(side_effect=Exception("boom")),
    ), patch(
        "services.market_scanner.broadcast_agent_log", new=AsyncMock()
    ), patch(
        "services.market_scanner.broadcast_agent_status", new=AsyncMock()
    ), patch(
        "services.market_scanner.broadcast_new_signal", new=AsyncMock()
    ):
        with pytest.raises(Exception, match="boom"):
            await scanner.run_scan()

    assert scanner.is_running is False
    mock_db.close.assert_called_once()
