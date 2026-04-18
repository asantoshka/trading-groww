import os

import pytest

os.environ["MODE"] = "paper"

from services.groww_client import GrowwClient, _mock_ltp


@pytest.fixture
def client():
    return GrowwClient()


def test_mock_ltp_known_symbol():
    price = _mock_ltp("NHPC")
    assert 70.0 < price < 100.0


def test_mock_ltp_unknown_symbol():
    price = _mock_ltp("UNKNOWN")
    assert price > 0
    assert isinstance(price, float)


def test_mock_ltp_randomness():
    p1 = _mock_ltp("NHPC")
    p2 = _mock_ltp("NHPC")
    assert p1 > 0 and p2 > 0


@pytest.mark.asyncio
async def test_get_ltp_paper_mode(client):
    if os.getenv("TEST_LIVE") != "1":
        pytest.skip("Read methods now use real API. Set TEST_LIVE=1 to run.")

    result = await client.get_ltp(["NHPC", "SAIL"])
    assert "NHPC" in result
    assert "SAIL" in result
    assert result["NHPC"] > 0
    assert result["SAIL"] > 0


@pytest.mark.asyncio
async def test_get_ltp_multiple_symbols(client):
    if os.getenv("TEST_LIVE") != "1":
        pytest.skip("Read methods now use real API. Set TEST_LIVE=1 to run.")

    symbols = ["NHPC", "IRCTC", "RELIANCE", "TCS"]
    result = await client.get_ltp(symbols)
    assert len(result) == 4
    assert all(value > 0 for value in result.values())


@pytest.mark.asyncio
async def test_get_quote_paper_mode(client):
    if os.getenv("TEST_LIVE") != "1":
        pytest.skip("Read methods now use real API. Set TEST_LIVE=1 to run.")

    result = await client.get_quote("NHPC")
    assert "last_price" in result
    assert "ohlc" in result
    assert result["last_price"] > 0
    assert result["ohlc"]["high"] >= result["ohlc"]["low"]


@pytest.mark.asyncio
async def test_get_historical_data_paper_mode(client):
    if os.getenv("TEST_LIVE") != "1":
        pytest.skip("Read methods now use real API. Set TEST_LIVE=1 to run.")

    candles = await client.get_historical_data(
        "NHPC",
        "2026-03-01 09:15:00",
        "2026-03-01 15:30:00",
        5,
    )
    assert len(candles) > 0
    assert all("open" in c for c in candles)
    assert all("close" in c for c in candles)
    assert all("open" in candle for candle in candles)
    assert all("close" in candle for candle in candles)
    assert all(candle["high"] >= candle["low"] for candle in candles)


@pytest.mark.asyncio
async def test_place_order_paper_mode(client):
    result = await client.place_order("NHPC", 10, 84.10, "BUY")
    assert "groww_order_id" in result
    assert result["groww_order_id"].startswith("PAPER-")
    assert result["order_status"] == "OPEN"
    assert result["paper"] is True


@pytest.mark.asyncio
async def test_place_order_reference_id_format(client):
    result = await client.place_order("RELIANCE", 1, 1342.0, "BUY")
    ref = result["order_reference_id"]
    assert ref.startswith("BOT-")
    assert len(ref) >= 8
    assert ref.count("-") <= 2


@pytest.mark.asyncio
async def test_place_gtt_stoploss_paper(client):
    result = await client.place_gtt_stoploss("NHPC", 10, 81.00)
    assert result["smart_order_id"].startswith("GTT-PAPER-")
    assert result["status"] == "ACTIVE"
    assert result["trigger_price"] == "81.0"
    assert result["paper"] is True


@pytest.mark.asyncio
async def test_cancel_order_paper(client):
    result = await client.cancel_order("PAPER-ABC123")
    assert result["order_status"] == "CANCELLED"
    assert result["paper"] is True


@pytest.mark.asyncio
async def test_get_margin_paper(client):
    result = await client.get_margin()
    assert result["available_margin"] > 0
    assert result["total_margin"] == 5000.0


@pytest.mark.asyncio
async def test_get_positions_paper(client):
    result = await client.get_positions()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_ohlc_candle_integrity(client):
    if os.getenv("TEST_LIVE") != "1":
        pytest.skip("Read methods now use real API. Set TEST_LIVE=1 to run.")

    candles = await client.get_historical_data(
        "SAIL",
        "2025-01-01 09:15:00",
        "2025-01-01 15:30:00",
        5,
    )
    for candle in candles:
        assert candle["high"] >= candle["open"]
        assert candle["high"] >= candle["close"]
        assert candle["low"] <= candle["open"]
        assert candle["low"] <= candle["close"]


@pytest.mark.asyncio
async def test_live_ltp_smoke():
    if os.getenv("TEST_LIVE") != "1":
        pytest.skip("Set TEST_LIVE=1 to run live tests")

    previous_mode = os.getenv("MODE")
    os.environ["MODE"] = "live"
    try:
        client = GrowwClient()
        result = await client.get_ltp(["NHPC"])
        assert "NHPC" in result
        assert result["NHPC"] > 0
        print(f"Live NHPC LTP: ₹{result['NHPC']}")
    finally:
        if previous_mode is None:
            os.environ.pop("MODE", None)
        else:
            os.environ["MODE"] = previous_mode
