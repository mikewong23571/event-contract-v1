from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

import math
import pytest

from backend.src.lib.signal_generation.probability_calculator import (
    ProbabilityCalculator,
)
from backend.src.models.market_data import MarketData


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


def make_series(n: int = 50, price: Decimal = Decimal("100.0")) -> List[MarketData]:
    return [make_candle(price=price, volume=Decimal("100")) for _ in range(n)]


def test_analyze_indicator_keys_present():
    calc = ProbabilityCalculator()
    data = make_series(50)
    indicators: Dict[str, Any] = {
        "rsi": 50.0,
        "macd": {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0},
        "bollinger_bands": {
            "upper_band": 105.0,
            "middle_band": 100.0,
            "lower_band": 95.0,
        },
        "price_momentum": 0.0,
        "volume_sma": 100.0,
        "volatility": 0.02,
    }

    result = calc.calculate_probability(data, indicators)
    comp = result["component_signals"]

    # Expected component keys
    for key in [
        "rsi",
        "macd",
        "bollinger",
        "momentum",
        "volume",
        "volatility",
    ]:
        assert key in comp


def test_rsi_overbought_and_oversold_signals():
    calc = ProbabilityCalculator()
    data = make_series(50)

    # Overbought -> negative RSI signal
    indicators_ob = {
        "rsi": 80.0,
        "macd": {"macd_line": 0.0, "signal_line": 0.0},
        "bollinger_bands": {"upper_band": 101.0, "middle_band": 100.0, "lower_band": 99.0},
        "price_momentum": 0.0,
        "volume_sma": 100.0,
        "volatility": 0.02,
    }
    comp_ob = calc.calculate_probability(data, indicators_ob)["component_signals"]
    assert math.isclose(comp_ob["rsi"], -0.8, rel_tol=1e-6)

    # Oversold -> positive RSI signal
    indicators_os = {
        "rsi": 20.0,
        "macd": {"macd_line": 0.0, "signal_line": 0.0},
        "bollinger_bands": {"upper_band": 101.0, "middle_band": 100.0, "lower_band": 99.0},
        "price_momentum": 0.0,
        "volume_sma": 100.0,
        "volatility": 0.02,
    }
    comp_os = calc.calculate_probability(data, indicators_os)["component_signals"]
    assert math.isclose(comp_os["rsi"], 0.8, rel_tol=1e-6)


def test_volume_signal_logic():
    calc = ProbabilityCalculator()
    data = make_series(50)

    base = {
        "rsi": 50.0,
        "macd": {"macd_line": 0.0, "signal_line": 0.0},
        "bollinger_bands": {"upper_band": 101.0, "middle_band": 100.0, "lower_band": 99.0},
        "price_momentum": 0.0,
        "volatility": 0.02,
    }

    # High volume (>1.5x SMA)
    comp_high = calc.calculate_probability(
        data, {**base, "volume_sma": 100.0, "current_volume": 160.0}
    )["component_signals"]
    assert math.isclose(comp_high["volume"], 0.5, rel_tol=1e-6)

    # Low volume (<0.5x SMA)
    comp_low = calc.calculate_probability(
        data, {**base, "volume_sma": 100.0, "current_volume": 40.0}
    )["component_signals"]
    assert math.isclose(comp_low["volume"], -0.3, rel_tol=1e-6)

    # Normal volume (~1x SMA)
    comp_norm = calc.calculate_probability(
        data, {**base, "volume_sma": 100.0, "current_volume": 100.0}
    )["component_signals"]
    assert math.isclose(comp_norm["volume"], 0.0, rel_tol=1e-6)


def test_volatility_signal_logic():
    calc = ProbabilityCalculator()
    data = make_series(50)
    base = {
        "rsi": 50.0,
        "macd": {"macd_line": 0.0, "signal_line": 0.0},
        "bollinger_bands": {"upper_band": 101.0, "middle_band": 100.0, "lower_band": 99.0},
        "price_momentum": 0.0,
        "volume_sma": 100.0,
    }

    comp_high = calc.calculate_probability(data, {**base, "volatility": 0.06})[
        "component_signals"
    ]
    assert math.isclose(comp_high["volatility"], -0.4, rel_tol=1e-6)

    comp_low = calc.calculate_probability(data, {**base, "volatility": 0.005})[
        "component_signals"
    ]
    assert math.isclose(comp_low["volatility"], 0.2, rel_tol=1e-6)

    comp_mid = calc.calculate_probability(data, {**base, "volatility": 0.02})[
        "component_signals"
    ]
    assert math.isclose(comp_mid["volatility"], 0.0, rel_tol=1e-6)


def test_weighted_probability_and_direction_deterministic():
    calc = ProbabilityCalculator()
    data = make_series(50)

    # Construct indicators to produce deterministic component signals
    indicators = {
        "rsi": 30.0,  # Neutral (0.0)
        "macd": {"macd_line": 1.0, "signal_line": 0.0},  # +0.6
        "bollinger_bands": {"upper_band": 102.0, "middle_band": 100.0, "lower_band": 98.0},
        "current_price": 98.0,  # At lower band => positive
        "price_momentum": 5.0,  # tanh(1.0) ~ 0.7616
        "volume_sma": 100.0,
        "current_volume": 150.0,  # 1.5x -> borderline, treat as not >1.5 => 0.0 per code (strict >)
        "volatility": 0.01,  # low => +0.2
    }

    result = calc.calculate_probability(data, indicators)
    comp = result["component_signals"]

    # Expected component contributions
    expected_comp = {
        "rsi": (50 - 30.0) / 20.0,  # 1.0
        "macd": 0.6,
        # current_price == lower_band -> handled as below lower: +0.7
        "bollinger": 0.7,
        "momentum": math.tanh(5.0 / 5.0),  # ~0.761594
        "volume": 0.0,  # exactly 1.5x should be 0.0 due to strict > in code
        "volatility": 0.2,
    }

    # Verify component signals approximate expectations
    for k, v in expected_comp.items():
        assert math.isclose(comp[k], v, rel_tol=1e-4)

    # Weighted total and probability mapping
    weights = {
        "rsi": 0.15,
        "macd": 0.20,
        "bollinger": 0.15,
        "momentum": 0.20,
        "volume": 0.10,
        "volatility": 0.20,
    }
    total = sum(expected_comp[k] * w for k, w in weights.items())
    expected_probability = max(0.5, min(0.95, 0.5 + total * 0.45))

    assert math.isclose(result["probability"], expected_probability, rel_tol=1e-4)
    assert result["direction"] == ("UP" if total > 0 else "DOWN")


def test_confidence_metrics_calculation():
    calc = ProbabilityCalculator()

    # Build stable price series for deterministic consistency
    data = make_series(60, price=Decimal("100.0"))
    probability = 0.7
    strength = 0.5

    metrics = calc.calculate_confidence_metrics(probability, strength, data)

    assert set(metrics.keys()) == {
        "overall_confidence",
        "data_quality",
        "price_consistency",
        "signal_strength_normalized",
    }

    # With 60 points, data_quality caps at 1.0
    assert math.isclose(metrics["data_quality"], 1.0, rel_tol=1e-6)
    # Stable prices -> zero std -> price_consistency == 1.0
    assert math.isclose(metrics["price_consistency"], 1.0, rel_tol=1e-6)
    assert math.isclose(metrics["signal_strength_normalized"], strength, rel_tol=1e-6)

    expected_overall = probability * 0.4 + strength * 0.3 + 1.0 * 0.2 + 1.0 * 0.1
    assert math.isclose(metrics["overall_confidence"], expected_overall, rel_tol=1e-6)

