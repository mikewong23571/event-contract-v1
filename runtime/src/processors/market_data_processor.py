import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any
from uuid import uuid4

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from ..config.settings import get_settings

settings = get_settings()


logger = logging.getLogger(__name__)


class PriceData(BaseModel):
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    source: str


class ProcessedMarketData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    timestamp: datetime
    raw_data: PriceData
    price_change: Decimal
    price_change_percent: Decimal
    volatility: float
    volume_sma: Decimal
    price_sma: Decimal
    bollinger_upper: Decimal
    bollinger_lower: Decimal
    rsi: float
    macd: float
    macd_signal: float
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class MarketDataProcessor:
    """
    Real-time market data processor that applies technical analysis
    and normalization to incoming market data streams.
    """

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.price_history: Dict[str, List[Decimal]] = {}
        self.volume_history: Dict[str, List[Decimal]] = {}
        self.data_callbacks: List[Callable[[ProcessedMarketData], None]] = []
        self.running = False

    def add_data_callback(
        self, callback: Callable[[ProcessedMarketData], None]
    ) -> None:
        """Add a callback function to be called when data is processed."""
        self.data_callbacks.append(callback)

    def remove_data_callback(
        self, callback: Callable[[ProcessedMarketData], None]
    ) -> None:
        """Remove a data callback."""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)

    async def process_market_data(self, price_data: PriceData) -> ProcessedMarketData:
        """
        Process a single market data point with technical indicators.

        Args:
            price_data: Raw price data to process

        Returns:
            ProcessedMarketData with technical indicators calculated
        """
        symbol = price_data.symbol

        # Initialize history for new symbols
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.volume_history[symbol] = []

        # Add current data to history
        self.price_history[symbol].append(price_data.close_price)
        self.volume_history[symbol].append(price_data.volume)

        # Maintain window size
        if len(self.price_history[symbol]) > self.window_size * 2:
            self.price_history[symbol] = self.price_history[symbol][
                -self.window_size * 2 :
            ]
            self.volume_history[symbol] = self.volume_history[symbol][
                -self.window_size * 2 :
            ]

        # Calculate technical indicators
        processed_data = await self._calculate_indicators(price_data)

        # Notify callbacks
        for callback in self.data_callbacks:
            try:
                await asyncio.create_task(self._safe_callback(callback, processed_data))
            except Exception as e:
                logger.error(f"Error in data callback: {e}")

        return processed_data

    async def _safe_callback(
        self, callback: Callable, data: ProcessedMarketData
    ) -> None:
        """Safely execute callback, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(callback):
            await callback(data)
        else:
            callback(data)

    async def _calculate_indicators(self, price_data: PriceData) -> ProcessedMarketData:
        """Calculate technical indicators for the given price data."""
        symbol = price_data.symbol
        prices = self.price_history[symbol]
        volumes = self.volume_history[symbol]

        # Convert to numpy arrays for calculations
        price_array = np.array([float(p) for p in prices])
        volume_array = np.array([float(v) for v in volumes])

        # Price change calculations
        price_change = Decimal("0.0")
        price_change_percent = Decimal("0.0")
        if len(prices) >= 2:
            price_change = prices[-1] - prices[-2]
            if prices[-2] != 0:
                price_change_percent = (price_change / prices[-2]) * Decimal("100")

        # Simple moving averages
        price_sma = await self._calculate_sma(
            prices, min(self.window_size, len(prices))
        )
        volume_sma = await self._calculate_sma(
            volumes, min(self.window_size, len(volumes))
        )

        # Volatility (standard deviation of returns)
        volatility = await self._calculate_volatility(price_array)

        # Bollinger Bands
        bollinger_upper, bollinger_lower = await self._calculate_bollinger_bands(
            prices, price_sma
        )

        # RSI
        rsi = await self._calculate_rsi(price_array)

        # MACD
        macd, macd_signal = await self._calculate_macd(price_array)

        return ProcessedMarketData(
            symbol=symbol,
            timestamp=price_data.timestamp,
            raw_data=price_data,
            price_change=price_change,
            price_change_percent=price_change_percent,
            volatility=volatility,
            volume_sma=volume_sma,
            price_sma=price_sma,
            bollinger_upper=bollinger_upper,
            bollinger_lower=bollinger_lower,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
        )

    async def _calculate_sma(self, values: List[Decimal], period: int) -> Decimal:
        """Calculate Simple Moving Average."""
        if len(values) < period:
            period = len(values)
        if period == 0:
            return Decimal("0.0")

        recent_values = values[-period:]
        return sum(recent_values) / Decimal(str(period))

    async def _calculate_volatility(self, price_array: np.ndarray) -> float:
        """Calculate price volatility (standard deviation of returns)."""
        if len(price_array) < 2:
            return 0.0

        returns = np.diff(price_array) / price_array[:-1]
        return float(np.std(returns))

    async def _calculate_bollinger_bands(
        self, prices: List[Decimal], sma: Decimal
    ) -> tuple[Decimal, Decimal]:
        """Calculate Bollinger Bands (upper and lower)."""
        if len(prices) < 2:
            return sma, sma

        # Calculate standard deviation
        price_floats = [float(p) for p in prices]
        std_dev = Decimal(str(np.std(price_floats)))

        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)

        return upper_band, lower_band

    async def _calculate_rsi(self, price_array: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(price_array) < period + 1:
            return 50.0  # Neutral RSI

        deltas = np.diff(price_array)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    async def _calculate_macd(
        self,
        price_array: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[float, float]:
        """Calculate MACD and MACD Signal line."""
        if len(price_array) < slow_period:
            return 0.0, 0.0

        # Calculate EMAs
        ema_fast = await self._calculate_ema(price_array, fast_period)
        ema_slow = await self._calculate_ema(price_array, slow_period)

        # MACD line
        macd_line = ema_fast - ema_slow

        # MACD signal line (EMA of MACD line)
        # For simplicity, using SMA instead of EMA for signal line
        macd_signal = (
            macd_line  # Simplified - would need MACD history for proper signal
        )

        return float(macd_line), float(macd_signal)

    async def _calculate_ema(self, price_array: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(price_array) < period:
            return float(np.mean(price_array))

        alpha = 2.0 / (period + 1)
        ema = price_array[0]

        for price in price_array[1:]:
            ema = alpha * price + (1 - alpha) * ema

        return float(ema)

    async def start_processing(self) -> None:
        """Start the market data processor."""
        self.running = True
        logger.info("Market data processor started")

    async def stop_processing(self) -> None:
        """Stop the market data processor."""
        self.running = False
        logger.info("Market data processor stopped")

    def get_symbol_stats(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current statistics for a symbol."""
        if symbol not in self.price_history or not self.price_history[symbol]:
            return None

        prices = self.price_history[symbol]
        volumes = self.volume_history[symbol]

        return {
            "symbol": symbol,
            "data_points": len(prices),
            "latest_price": float(prices[-1]),
            "price_range": {"min": float(min(prices)), "max": float(max(prices))},
            "average_volume": float(sum(volumes) / len(volumes)) if volumes else 0.0,
        }

    def clear_history(self, symbol: Optional[str] = None) -> None:
        """Clear price history for a symbol or all symbols."""
        if symbol:
            if symbol in self.price_history:
                self.price_history[symbol] = []
                self.volume_history[symbol] = []
        else:
            self.price_history.clear()
            self.volume_history.clear()


# Factory function for creating processor instances
def create_market_data_processor(window_size: int = 20) -> MarketDataProcessor:
    """Create and return a configured MarketDataProcessor instance."""
    return MarketDataProcessor(window_size=window_size)


# CLI entry point
async def main() -> None:
    """CLI entry point for the market data processor."""
    import sys
    import json

    processor = create_market_data_processor()

    def print_processed_data(data: ProcessedMarketData) -> None:
        print(
            json.dumps(
                {
                    "symbol": data.symbol,
                    "timestamp": data.timestamp.isoformat(),
                    "price_change_percent": str(data.price_change_percent),
                    "volatility": data.volatility,
                    "rsi": data.rsi,
                    "macd": data.macd,
                },
                indent=2,
            )
        )

    processor.add_data_callback(print_processed_data)

    # Example usage - process sample data
    sample_data = PriceData(
        symbol="BTCUSDT",
        timestamp=datetime.utcnow(),
        open_price=Decimal("50000.00"),
        high_price=Decimal("51000.00"),
        low_price=Decimal("49500.00"),
        close_price=Decimal("50500.00"),
        volume=Decimal("100.5"),
        source="binance",
    )

    await processor.start_processing()
    await processor.process_market_data(sample_data)
    await processor.stop_processing()


if __name__ == "__main__":
    asyncio.run(main())
