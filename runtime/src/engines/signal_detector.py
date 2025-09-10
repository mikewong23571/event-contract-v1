import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any, Tuple
from uuid import uuid4
from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel, Field

from ..processors.market_data_processor import ProcessedMarketData
from ..config.settings import get_settings

settings = get_settings()


logger = logging.getLogger(__name__)


@dataclass
class SignalRule:
    """Definition of a signal detection rule."""

    name: str
    description: str
    priority: int
    min_confidence: float
    indicators: List[str]


class DetectedSignal(BaseModel):
    """Represents a detected trading signal."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    timestamp: datetime
    direction: str  # "UP" or "DOWN"
    predicted_probability: float
    confidence_level: str  # "LOW", "MEDIUM", "HIGH"
    strategy_name: str
    rule_name: str
    technical_indicators: Dict[str, Any]
    expiry_time: datetime
    signal_strength: float
    market_conditions: Dict[str, Any]
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class SignalDetector:
    """
    Real-time signal detection engine that analyzes processed market data
    and generates trading signals based on technical analysis patterns.
    """

    def __init__(self, signal_expiry_minutes: int = 15):
        self.signal_expiry_minutes = signal_expiry_minutes
        self.active_signals: Dict[str, List[DetectedSignal]] = {}
        self.signal_callbacks: List[Callable[[DetectedSignal], None]] = []
        self.detection_rules: List[SignalRule] = self._initialize_detection_rules()
        self.running = False

        # Signal detection parameters
        self.rsi_oversold = 30.0
        self.rsi_overbought = 70.0
        self.volatility_threshold = 0.02
        self.volume_spike_threshold = 2.0
        self.macd_signal_threshold = 0.001

    def _initialize_detection_rules(self) -> List[SignalRule]:
        """Initialize the signal detection rules."""
        return [
            SignalRule(
                name="RSI_OVERSOLD_BOUNCE",
                description="RSI indicates oversold conditions with potential upward bounce",
                priority=8,
                min_confidence=0.65,
                indicators=["rsi", "volume_sma", "bollinger_lower"],
            ),
            SignalRule(
                name="RSI_OVERBOUGHT_REVERSAL",
                description="RSI indicates overbought conditions with potential downward reversal",
                priority=8,
                min_confidence=0.65,
                indicators=["rsi", "volume_sma", "bollinger_upper"],
            ),
            SignalRule(
                name="BOLLINGER_BREAKOUT_UP",
                description="Price breaks above upper Bollinger Band with volume confirmation",
                priority=7,
                min_confidence=0.70,
                indicators=["bollinger_upper", "volume_sma", "volatility"],
            ),
            SignalRule(
                name="BOLLINGER_BREAKOUT_DOWN",
                description="Price breaks below lower Bollinger Band with volume confirmation",
                priority=7,
                min_confidence=0.70,
                indicators=["bollinger_lower", "volume_sma", "volatility"],
            ),
            SignalRule(
                name="MACD_BULLISH_CROSSOVER",
                description="MACD line crosses above signal line indicating bullish momentum",
                priority=6,
                min_confidence=0.60,
                indicators=["macd", "macd_signal", "volume_sma"],
            ),
            SignalRule(
                name="MACD_BEARISH_CROSSOVER",
                description="MACD line crosses below signal line indicating bearish momentum",
                priority=6,
                min_confidence=0.60,
                indicators=["macd", "macd_signal", "volume_sma"],
            ),
            SignalRule(
                name="VOLATILITY_SPIKE_UP",
                description="High volatility spike with upward price movement",
                priority=5,
                min_confidence=0.55,
                indicators=["volatility", "price_change_percent", "volume_sma"],
            ),
            SignalRule(
                name="VOLATILITY_SPIKE_DOWN",
                description="High volatility spike with downward price movement",
                priority=5,
                min_confidence=0.55,
                indicators=["volatility", "price_change_percent", "volume_sma"],
            ),
            SignalRule(
                name="VOLUME_PRICE_CONFLUENCE",
                description="Volume spike coincides with significant price movement",
                priority=6,
                min_confidence=0.62,
                indicators=["volume_sma", "price_change_percent", "volatility"],
            ),
        ]

    def add_signal_callback(self, callback: Callable[[DetectedSignal], None]) -> None:
        """Add a callback function to be called when a signal is detected."""
        self.signal_callbacks.append(callback)

    def remove_signal_callback(
        self, callback: Callable[[DetectedSignal], None]
    ) -> None:
        """Remove a signal callback."""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)

    async def analyze_market_data(
        self, data: ProcessedMarketData
    ) -> Optional[DetectedSignal]:
        """
        Analyze processed market data and detect trading signals.

        Args:
            data: Processed market data with technical indicators

        Returns:
            DetectedSignal if a signal is detected, None otherwise
        """
        if not self.running:
            return None

        # Clean up expired signals
        await self._cleanup_expired_signals()

        # Check each detection rule
        for rule in self.detection_rules:
            signal = await self._check_signal_rule(data, rule)
            if signal:
                # Avoid duplicate signals for the same symbol
                if not await self._is_duplicate_signal(signal):
                    await self._add_active_signal(signal)

                    # Notify callbacks
                    for callback in self.signal_callbacks:
                        try:
                            await asyncio.create_task(
                                self._safe_callback(callback, signal)
                            )
                        except Exception as e:
                            logger.error(f"Error in signal callback: {e}")

                    return signal

        return None

    async def _safe_callback(self, callback: Callable, signal: DetectedSignal) -> None:
        """Safely execute callback, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(callback):
            await callback(signal)
        else:
            callback(signal)

    async def _check_signal_rule(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check if market data matches a specific signal rule."""
        try:
            signal = None

            if rule.name == "RSI_OVERSOLD_BOUNCE":
                signal = await self._check_rsi_oversold_bounce(data, rule)
            elif rule.name == "RSI_OVERBOUGHT_REVERSAL":
                signal = await self._check_rsi_overbought_reversal(data, rule)
            elif rule.name == "BOLLINGER_BREAKOUT_UP":
                signal = await self._check_bollinger_breakout_up(data, rule)
            elif rule.name == "BOLLINGER_BREAKOUT_DOWN":
                signal = await self._check_bollinger_breakout_down(data, rule)
            elif rule.name == "MACD_BULLISH_CROSSOVER":
                signal = await self._check_macd_bullish_crossover(data, rule)
            elif rule.name == "MACD_BEARISH_CROSSOVER":
                signal = await self._check_macd_bearish_crossover(data, rule)
            elif rule.name == "VOLATILITY_SPIKE_UP":
                signal = await self._check_volatility_spike_up(data, rule)
            elif rule.name == "VOLATILITY_SPIKE_DOWN":
                signal = await self._check_volatility_spike_down(data, rule)
            elif rule.name == "VOLUME_PRICE_CONFLUENCE":
                signal = await self._check_volume_price_confluence(data, rule)

            return signal

        except Exception as e:
            logger.error(f"Error checking signal rule {rule.name}: {e}")
            return None

    async def _check_rsi_oversold_bounce(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for RSI oversold bounce signal."""
        if data.rsi <= self.rsi_oversold and float(data.raw_data.close_price) <= float(
            data.bollinger_lower
        ):
            confidence = 0.7 if data.rsi <= 20 else 0.6
            probability = min(0.85, 0.5 + (self.rsi_oversold - data.rsi) / 50)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="UP",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_rsi_overbought_reversal(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for RSI overbought reversal signal."""
        if data.rsi >= self.rsi_overbought and float(
            data.raw_data.close_price
        ) >= float(data.bollinger_upper):
            confidence = 0.7 if data.rsi >= 80 else 0.6
            probability = min(0.85, 0.5 + (data.rsi - self.rsi_overbought) / 50)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="DOWN",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_bollinger_breakout_up(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for upward Bollinger Band breakout."""
        close_price = float(data.raw_data.close_price)
        bollinger_upper = float(data.bollinger_upper)
        volume_ratio = (
            float(data.raw_data.volume) / float(data.volume_sma)
            if data.volume_sma > 0
            else 1.0
        )

        if close_price > bollinger_upper and volume_ratio > self.volume_spike_threshold:
            confidence = min(
                0.8, 0.6 + (volume_ratio - self.volume_spike_threshold) * 0.1
            )
            probability = min(0.8, 0.55 + data.volatility * 10)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="UP",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_bollinger_breakout_down(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for downward Bollinger Band breakout."""
        close_price = float(data.raw_data.close_price)
        bollinger_lower = float(data.bollinger_lower)
        volume_ratio = (
            float(data.raw_data.volume) / float(data.volume_sma)
            if data.volume_sma > 0
            else 1.0
        )

        if close_price < bollinger_lower and volume_ratio > self.volume_spike_threshold:
            confidence = min(
                0.8, 0.6 + (volume_ratio - self.volume_spike_threshold) * 0.1
            )
            probability = min(0.8, 0.55 + data.volatility * 10)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="DOWN",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_macd_bullish_crossover(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for MACD bullish crossover."""
        if (
            data.macd > data.macd_signal
            and abs(data.macd - data.macd_signal) > self.macd_signal_threshold
        ):
            confidence = 0.65
            probability = min(0.75, 0.55 + abs(data.macd - data.macd_signal) * 100)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="UP",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_macd_bearish_crossover(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for MACD bearish crossover."""
        if (
            data.macd < data.macd_signal
            and abs(data.macd - data.macd_signal) > self.macd_signal_threshold
        ):
            confidence = 0.65
            probability = min(0.75, 0.55 + abs(data.macd - data.macd_signal) * 100)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="DOWN",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_volatility_spike_up(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for upward volatility spike."""
        if (
            data.volatility > self.volatility_threshold
            and float(data.price_change_percent) > 2.0
        ):
            confidence = min(0.7, 0.5 + data.volatility * 10)
            probability = min(0.7, 0.5 + float(data.price_change_percent) / 10)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="UP",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_volatility_spike_down(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for downward volatility spike."""
        if (
            data.volatility > self.volatility_threshold
            and float(data.price_change_percent) < -2.0
        ):
            confidence = min(0.7, 0.5 + data.volatility * 10)
            probability = min(0.7, 0.5 + abs(float(data.price_change_percent)) / 10)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction="DOWN",
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _check_volume_price_confluence(
        self, data: ProcessedMarketData, rule: SignalRule
    ) -> Optional[DetectedSignal]:
        """Check for volume and price confluence."""
        volume_ratio = (
            float(data.raw_data.volume) / float(data.volume_sma)
            if data.volume_sma > 0
            else 1.0
        )
        price_change = abs(float(data.price_change_percent))

        if volume_ratio > self.volume_spike_threshold and price_change > 1.5:
            direction = "UP" if float(data.price_change_percent) > 0 else "DOWN"
            confidence = min(
                0.75, 0.5 + (volume_ratio - self.volume_spike_threshold) * 0.15
            )
            probability = min(0.75, 0.5 + price_change / 20)

            return await self._create_signal(
                data=data,
                rule=rule,
                direction=direction,
                probability=probability,
                confidence=confidence,
                signal_strength=rule.priority * confidence,
            )
        return None

    async def _create_signal(
        self,
        data: ProcessedMarketData,
        rule: SignalRule,
        direction: str,
        probability: float,
        confidence: float,
        signal_strength: float,
    ) -> DetectedSignal:
        """Create a detected signal from the analysis."""
        confidence_level = (
            "HIGH" if confidence >= 0.7 else "MEDIUM" if confidence >= 0.55 else "LOW"
        )

        return DetectedSignal(
            symbol=data.symbol,
            timestamp=data.timestamp,
            direction=direction,
            predicted_probability=probability,
            confidence_level=confidence_level,
            strategy_name="TECHNICAL_ANALYSIS",
            rule_name=rule.name,
            technical_indicators={
                "rsi": data.rsi,
                "macd": data.macd,
                "macd_signal": data.macd_signal,
                "volatility": data.volatility,
                "price_change_percent": str(data.price_change_percent),
                "bollinger_upper": str(data.bollinger_upper),
                "bollinger_lower": str(data.bollinger_lower),
                "volume_sma": str(data.volume_sma),
                "price_sma": str(data.price_sma),
            },
            expiry_time=data.timestamp + timedelta(minutes=self.signal_expiry_minutes),
            signal_strength=signal_strength,
            market_conditions={
                "symbol": data.symbol,
                "current_price": str(data.raw_data.close_price),
                "volume": str(data.raw_data.volume),
                "source": data.raw_data.source,
            },
        )

    async def _is_duplicate_signal(self, signal: DetectedSignal) -> bool:
        """Check if a similar signal already exists for the symbol."""
        if signal.symbol not in self.active_signals:
            return False

        for existing_signal in self.active_signals[signal.symbol]:
            if (
                existing_signal.direction == signal.direction
                and existing_signal.rule_name == signal.rule_name
                and (signal.timestamp - existing_signal.timestamp).total_seconds() < 300
            ):  # 5 minutes
                return True
        return False

    async def _add_active_signal(self, signal: DetectedSignal) -> None:
        """Add a signal to the active signals list."""
        if signal.symbol not in self.active_signals:
            self.active_signals[signal.symbol] = []

        self.active_signals[signal.symbol].append(signal)
        logger.info(
            f"Signal detected: {signal.symbol} {signal.direction} {signal.rule_name}"
        )

    async def _cleanup_expired_signals(self) -> None:
        """Remove expired signals from the active signals list."""
        current_time = datetime.utcnow()

        for symbol in list(self.active_signals.keys()):
            self.active_signals[symbol] = [
                signal
                for signal in self.active_signals[symbol]
                if signal.expiry_time > current_time
            ]

            if not self.active_signals[symbol]:
                del self.active_signals[symbol]

    async def start_detection(self) -> None:
        """Start the signal detection engine."""
        self.running = True
        logger.info("Signal detection engine started")

    async def stop_detection(self) -> None:
        """Stop the signal detection engine."""
        self.running = False
        logger.info("Signal detection engine stopped")

    def get_active_signals(self, symbol: Optional[str] = None) -> List[DetectedSignal]:
        """Get currently active signals."""
        if symbol:
            return self.active_signals.get(symbol, [])

        all_signals = []
        for signals in self.active_signals.values():
            all_signals.extend(signals)
        return all_signals

    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection engine statistics."""
        total_signals = sum(len(signals) for signals in self.active_signals.values())

        return {
            "running": self.running,
            "active_symbols": len(self.active_signals),
            "total_active_signals": total_signals,
            "detection_rules": len(self.detection_rules),
            "signal_expiry_minutes": self.signal_expiry_minutes,
        }


# Factory function for creating detector instances
def create_signal_detector(signal_expiry_minutes: int = 15) -> SignalDetector:
    """Create and return a configured SignalDetector instance."""
    return SignalDetector(signal_expiry_minutes=signal_expiry_minutes)


# CLI entry point
async def main() -> None:
    """CLI entry point for the signal detector."""
    import sys
    import json
    from decimal import Decimal
    from ..processors.market_data_processor import (
        PriceData,
        create_market_data_processor,
    )

    detector = create_signal_detector()
    processor = create_market_data_processor()

    def print_detected_signal(signal: DetectedSignal) -> None:
        print(
            json.dumps(
                {
                    "signal_id": signal.id,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "probability": signal.predicted_probability,
                    "confidence": signal.confidence_level,
                    "rule": signal.rule_name,
                    "expiry": signal.expiry_time.isoformat(),
                },
                indent=2,
            )
        )

    detector.add_signal_callback(print_detected_signal)

    async def analyze_data(processed_data) -> None:
        await detector.analyze_market_data(processed_data)

    processor.add_data_callback(analyze_data)

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

    await detector.start_detection()
    processed = await processor.process_market_data(sample_data)
    await detector.analyze_market_data(processed)
    await detector.stop_detection()


if __name__ == "__main__":
    asyncio.run(main())
