import pytest

from services.risk_gatekeeper import (
    RiskConfig,
    RiskGatekeeper,
    RiskResult,
    SignalInput,
)


@pytest.fixture
def config():
    return RiskConfig(
        capital_limit=5000.0,
        max_trade_value=2000.0,
        max_loss_per_trade=300.0,
        min_rr_ratio=1.5,
        confidence_threshold=70,
        max_capital_pct=0.40,
        mode="paper",
    )


@pytest.fixture
def good_signal():
    return SignalInput(
        symbol="NHPC",
        action="BUY",
        entry_price=84.10,
        target=89.50,
        stoploss=81.00,
        qty=9,
        confidence=78,
        mode="paper",
    )


def test_good_signal_approved(config, good_signal):
    gk = RiskGatekeeper(config)
    result = gk.evaluate(good_signal, 3241.50)
    assert result.approved is True
    assert result.reject_reason == ""
    assert all(result.checks.values())
    assert result.rr_ratio >= 1.5
    assert result.trade_value == pytest.approx(756.90, rel=1e-2)


def test_insufficient_capital(config, good_signal):
    signal = SignalInput(**{**good_signal.__dict__, "qty": 30})
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 500.00)
    assert result.approved is False
    assert "Insufficient capital" in result.reject_reason
    assert result.checks["capital_ok"] is False


def test_exceeds_max_trade_value(config, good_signal):
    signal = SignalInput(**{**good_signal.__dict__, "qty": 25})
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 5000.00)
    assert result.approved is False
    assert "Trade value" in result.reject_reason
    assert result.checks["trade_value_ok"] is False


def test_exceeds_capital_pct(config, good_signal):
    isolated_config = RiskConfig(**{**config.__dict__, "max_trade_value": 3000.0})
    signal = SignalInput(
        **{
            **good_signal.__dict__,
            "entry_price": 500.0,
            "qty": 5,
            "target": 560.0,
            "stoploss": 470.0,
        }
    )
    gk = RiskGatekeeper(isolated_config)
    result = gk.evaluate(signal, 5000.0)
    assert result.checks["capital_pct_ok"] is False
    assert "capital" in result.reject_reason.lower()


def test_risk_too_high(config, good_signal):
    signal = SignalInput(**{**good_signal.__dict__, "stoploss": 50.00})
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 5000.0)
    assert result.approved is False
    assert "Risk" in result.reject_reason
    assert result.checks["risk_ok"] is False


def test_rr_ratio_too_low(config, good_signal):
    signal = SignalInput(**{**good_signal.__dict__, "target": 85.50})
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 5000.0)
    assert result.approved is False
    assert "R:R" in result.reject_reason
    assert result.checks["rr_ratio_ok"] is False


def test_confidence_too_low(config, good_signal):
    signal = SignalInput(**{**good_signal.__dict__, "confidence": 55})
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 5000.0)
    assert result.approved is False
    assert "Confidence" in result.reject_reason
    assert result.checks["confidence_ok"] is False


def test_zero_risk_rr_calculation(config, good_signal):
    signal = SignalInput(**{**good_signal.__dict__, "stoploss": good_signal.entry_price})
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 3000.0)
    assert result.rr_ratio == 0.0
    assert result.approved is False


def test_sell_signal_metrics(config):
    signal = SignalInput(
        symbol="RELIANCE",
        action="SELL",
        entry_price=2800.0,
        target=2750.0,
        stoploss=2820.0,
        qty=1,
        confidence=75,
        mode="paper",
    )
    sell_config = RiskConfig(**{**config.__dict__, "max_trade_value": 3000.0})
    gk = RiskGatekeeper(sell_config)
    result = gk.evaluate(signal, 5000.0)
    assert result.rr_ratio == pytest.approx(2.5)
    assert result.checks["rr_ratio_ok"] is True


def test_reject_reason_priority(config):
    signal = SignalInput(
        symbol="NHPC",
        action="BUY",
        entry_price=100.0,
        target=110.0,
        stoploss=95.0,
        qty=25,
        confidence=80,
        mode="paper",
    )
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 500.0)
    assert "Insufficient capital" in result.reject_reason


def test_evaluate_from_dict():
    gk = RiskGatekeeper()
    signal_dict = {
        "symbol": "NHPC",
        "action": "BUY",
        "entry_price": 84.10,
        "target": 89.50,
        "stoploss": 81.00,
        "qty": 9,
        "confidence": 78,
        "mode": "paper",
    }
    config_dict = {
        "capital_limit": 5000.0,
        "max_trade_value": 2000.0,
        "max_loss_per_trade": 300.0,
        "min_rr_ratio": 1.5,
        "confidence_threshold": 70,
        "max_capital_pct": 0.40,
        "mode": "paper",
    }
    result = gk.evaluate_from_dict(signal_dict, 3000.0, config_dict)
    assert isinstance(result, RiskResult)
    assert result.approved is True


def test_result_to_dict(config, good_signal):
    gk = RiskGatekeeper(config)
    result = gk.evaluate(good_signal, 3000.0)
    data = gk.result_to_dict(result)
    assert isinstance(data, dict)
    assert "approved" in data
    assert "checks" in data
    assert "rr_ratio" in data
    assert isinstance(data["rr_ratio"], float)


def test_exact_boundary_trade_value(config):
    signal = SignalInput(
        symbol="TCS",
        action="BUY",
        entry_price=200.0,
        target=220.0,
        stoploss=190.0,
        qty=10,
        confidence=80,
        mode="paper",
    )
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 5000.0)
    assert result.checks["trade_value_ok"] is True


def test_exact_boundary_rr_ratio(config):
    signal = SignalInput(
        symbol="SAIL",
        action="BUY",
        entry_price=100.0,
        target=103.0,
        stoploss=98.0,
        qty=10,
        confidence=80,
        mode="paper",
    )
    gk = RiskGatekeeper(config)
    result = gk.evaluate(signal, 5000.0)
    assert result.rr_ratio == pytest.approx(1.5)
    assert result.checks["rr_ratio_ok"] is True


def test_result_has_all_checks(config, good_signal):
    gk = RiskGatekeeper(config)
    result = gk.evaluate(good_signal, 3000.0)
    expected_keys = {
        "trade_value_ok",
        "capital_ok",
        "risk_ok",
        "rr_ratio_ok",
        "confidence_ok",
        "capital_pct_ok",
    }
    assert set(result.checks.keys()) == expected_keys
