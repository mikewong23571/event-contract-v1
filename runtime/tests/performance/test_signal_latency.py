import time
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.engines.signal_detector import create_signal_detector
from src.processors.market_data_processor import (
    ProcessedMarketData,
    PriceData,
)


@pytest.mark.asyncio
async def test_signal_detection_latency_under_one_second():
    detector = create_signal_detector(signal_expiry_minutes=5)

    # Construct processed data that should immediately trigger RSI_OVERSOLD_BOUNCE
    price = Decimal("100.0")
    price_data = PriceData(
        symbol="TEST",
        timestamp=datetime.utcnow(),
        open_price=price,
        high_price=price,
        low_price=price,
        close_price=price,
        volume=Decimal("10"),
        source="unit-test",
    )

    processed = ProcessedMarketData(
        symbol="TEST",
        timestamp=datetime.utcnow(),
        raw_data=price_data,
        price_change=Decimal("0"),
        price_change_percent=Decimal("0"),
        volatility=0.01,
        volume_sma=Decimal("10"),
        price_sma=Decimal("100.0"),
        bollinger_upper=Decimal("101.0"),
        bollinger_lower=Decimal("100.0"),
        rsi=20.0,  # oversold
        macd=0.0,
        macd_signal=0.0,
    )

    await detector.start_detection()
    t0 = time.perf_counter()
    signal = await detector.analyze_market_data(processed)
    elapsed = time.perf_counter() - t0
    await detector.stop_detection()

    assert signal is not None, "Expected a signal to be generated"
    assert elapsed < 1.0, f"Signal detection latency too high: {elapsed:.3f}s"
