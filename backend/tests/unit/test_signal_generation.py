from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

import pytest

from backend.src.lib.signal_generation.signal_generator import SignalGenerator
from backend.src.models.market_data import MarketData
from backend.src.models.trading_signal import TradingSignal


def make_candle(price: Decimal = Decimal("100.0"), volume: Decimal = Decimal("100")) -> MarketData:
    return MarketData(
        symbol="TEST",
        timestamp=datetime.utcnow(),
        open_price=price,
        high_price=price,
        low_price=price,
        close_price=price,
        volume=volume,
        quote_volume=volume,
        trade_count=10,
        source="unit-test",
    )


def make_series(n: int = 30) -> List[MarketData]:
    return [make_candle() for _ in range(n)]


def test_generate_signal_insufficient_data_returns_none(caplog):
    gen = SignalGenerator()
    data = make_series(10)  # fewer than 20
    signal = gen.generate_signal(data, symbol="TEST")
    assert signal is None


def test_generate_signal_low_probability_returns_none(monkeypatch):
    gen = SignalGenerator()

    # Force low-probability outcome
    def fake_calc(market_data, indicators):
        return {"probability": 0.54, "direction": "UP", "signal_strength": 0.1, "component_signals": {}}

    monkeypatch.setattr(gen, "probability_calculator", type("PC", (), {"calculate_probability": staticmethod(fake_calc)})())

    data = make_series(30)
    assert gen.generate_signal(data, symbol="TEST") is None


@pytest.mark.parametrize(
    "prob,expected_conf",
    [
        (0.76, "HIGH"),
        (0.70, "MEDIUM"),
        (0.60, "LOW"),
    ],
)
def test_generate_signal_success_returns_signal_with_confidence(monkeypatch, prob, expected_conf):
    gen = SignalGenerator()

    def fake_calc(market_data, indicators):
        return {
            "probability": prob,
            "direction": "UP",
            "signal_strength": 0.4,
            "component_signals": {},
        }

    monkeypatch.setattr(gen, "probability_calculator", type("PC", (), {"calculate_probability": staticmethod(fake_calc)})())

    data = make_series(30)
    signal = gen.generate_signal(data, symbol="BTCUSDT", expiry_minutes=5)
    assert signal is not None
    assert isinstance(signal, TradingSignal)
    assert signal.symbol == "BTCUSDT"
    assert signal.direction == "UP"
    assert signal.predicted_probability == pytest.approx(prob)
    assert signal.confidence_level == expected_conf
    assert signal.expiry_time > datetime.utcnow()


def test_batch_generate_signals(monkeypatch):
    gen = SignalGenerator()

    # Set up calculator: one symbol passes, one fails (low prob), one insufficient data
    def fake_calc(market_data, indicators):
        return {"probability": 0.65, "direction": "DOWN", "signal_strength": 0.3, "component_signals": {}}

    monkeypatch.setattr(gen, "probability_calculator", type("PC", (), {"calculate_probability": staticmethod(fake_calc)})())

    data_ok = make_series(25)
    data_low = make_series(25)
    data_short = make_series(10)

    # Override for low probability case
    def fake_calc_low(market_data, indicators):
        return {"probability": 0.54, "direction": "UP", "signal_strength": 0.1, "component_signals": {}}

    # Build market data dict
    market_map = {
        "OK": data_ok,
        "LOW": data_low,
        "SHORT": data_short,
    }

    # Monkeypatch generate_signal to vary by symbol
    orig_generate = gen.generate_signal

    def gen_wrapper(series, symbol, expiry_minutes=15):
        if symbol == "LOW":
            # temporarily swap calc
            monkeypatch.setattr(gen, "probability_calculator", type("PC", (), {"calculate_probability": staticmethod(fake_calc_low)})())
            try:
                return orig_generate(series, symbol, expiry_minutes)
            finally:
                monkeypatch.setattr(gen, "probability_calculator", type("PC", (), {"calculate_probability": staticmethod(fake_calc)})())
        return orig_generate(series, symbol, expiry_minutes)

    monkeypatch.setattr(gen, "generate_signal", gen_wrapper)

    signals = gen.batch_generate_signals(market_map, expiry_minutes=10)
    # Only "OK" should produce a signal
    assert len(signals) == 1
    assert signals[0].symbol == "OK"
    assert signals[0].direction == "DOWN"


def test_validate_signal_quality():
    gen = SignalGenerator()

    valid_signal = TradingSignal(
        timestamp=datetime.utcnow(),
        symbol="ETHUSDT",
        direction="UP",
        predicted_probability=0.6,
        confidence_level="LOW",
        expiry_time=datetime.utcnow() + timedelta(minutes=5),
        strategy_version="v1.0",
        technical_indicators={},
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    assert gen.validate_signal_quality(valid_signal) is True

    invalid_prob = valid_signal.copy(update={"predicted_probability": 0.49})
    assert gen.validate_signal_quality(invalid_prob) is False

    expired = valid_signal.copy(update={"expiry_time": datetime.utcnow() - timedelta(seconds=1)})
    assert gen.validate_signal_quality(expired) is False

    bad_dir = valid_signal.copy(update={"direction": "SIDEWAYS"})
    assert gen.validate_signal_quality(bad_dir) is False

