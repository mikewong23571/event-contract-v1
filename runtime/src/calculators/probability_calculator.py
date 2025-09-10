import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy import stats
from pydantic import BaseModel, Field

from ..processors.market_data_processor import ProcessedMarketData
from ..engines.signal_detector import DetectedSignal
from ..config.settings import get_settings

settings = get_settings()


logger = logging.getLogger(__name__)


class ProbabilityModel(str, Enum):
    """Available probability calculation models."""

    TECHNICAL_INDICATORS = "technical_indicators"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    ENSEMBLE = "ensemble"
    MONTE_CARLO = "monte_carlo"


@dataclass
class HistoricalOutcome:
    """Represents a historical trading outcome for backtesting probability models."""

    signal_id: str
    symbol: str
    direction: str
    predicted_probability: float
    actual_outcome: bool
    price_at_signal: float
    price_at_expiry: float
    return_percentage: float
    timestamp: datetime


class ProbabilityResult(BaseModel):
    """Result of probability calculation."""

    symbol: str
    direction: str
    base_probability: float
    adjusted_probability: float
    confidence_score: float
    risk_adjusted_probability: float
    probability_model: ProbabilityModel
    factors: Dict[str, float]
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class ProbabilityCalculator:
    """
    Advanced probability calculation engine that refines trading signal probabilities
    using multiple models and historical performance data.
    """

    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.historical_outcomes: List[HistoricalOutcome] = []
        self.model_performance: Dict[ProbabilityModel, float] = {}
        self.symbol_performance: Dict[str, Dict[str, float]] = {}

        # Model weights for ensemble calculation
        self.model_weights = {
            ProbabilityModel.TECHNICAL_INDICATORS: 0.30,
            ProbabilityModel.VOLATILITY_ADJUSTED: 0.25,
            ProbabilityModel.CONFIDENCE_WEIGHTED: 0.20,
            ProbabilityModel.MONTE_CARLO: 0.25,
        }

        # Calculation parameters
        self.volatility_decay_factor = 0.95
        self.confidence_multiplier = 1.2
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.market_regime_threshold = 0.03  # 3% volatility threshold

    async def calculate_probability(
        self,
        signal: DetectedSignal,
        market_data: ProcessedMarketData,
        model: ProbabilityModel = ProbabilityModel.ENSEMBLE,
    ) -> ProbabilityResult:
        """
        Calculate refined probability for a trading signal using specified model.

        Args:
            signal: The detected trading signal
            market_data: Current market data with technical indicators
            model: Probability calculation model to use

        Returns:
            ProbabilityResult with refined probability and analysis
        """
        base_probability = signal.predicted_probability

        if model == ProbabilityModel.TECHNICAL_INDICATORS:
            result = await self._calculate_technical_probability(
                signal, market_data, base_probability
            )
        elif model == ProbabilityModel.VOLATILITY_ADJUSTED:
            result = await self._calculate_volatility_adjusted_probability(
                signal, market_data, base_probability
            )
        elif model == ProbabilityModel.CONFIDENCE_WEIGHTED:
            result = await self._calculate_confidence_weighted_probability(
                signal, market_data, base_probability
            )
        elif model == ProbabilityModel.MONTE_CARLO:
            result = await self._calculate_monte_carlo_probability(
                signal, market_data, base_probability
            )
        elif model == ProbabilityModel.ENSEMBLE:
            result = await self._calculate_ensemble_probability(
                signal, market_data, base_probability
            )
        else:
            # Fallback to base probability
            result = ProbabilityResult(
                symbol=signal.symbol,
                direction=signal.direction,
                base_probability=base_probability,
                adjusted_probability=base_probability,
                confidence_score=0.5,
                risk_adjusted_probability=base_probability,
                probability_model=model,
                factors={},
            )

        # Apply historical performance adjustment
        result = await self._apply_historical_adjustment(result)

        return result

    async def _calculate_technical_probability(
        self, signal: DetectedSignal, market_data: ProcessedMarketData, base_prob: float
    ) -> ProbabilityResult:
        """Calculate probability based on technical indicator strength."""
        factors = {}

        # RSI factor
        rsi_factor = await self._calculate_rsi_factor(market_data.rsi, signal.direction)
        factors["rsi_factor"] = rsi_factor

        # MACD factor
        macd_factor = await self._calculate_macd_factor(
            market_data.macd, market_data.macd_signal, signal.direction
        )
        factors["macd_factor"] = macd_factor

        # Bollinger Band factor
        bollinger_factor = await self._calculate_bollinger_factor(
            market_data, signal.direction
        )
        factors["bollinger_factor"] = bollinger_factor

        # Volume factor
        volume_factor = await self._calculate_volume_factor(market_data)
        factors["volume_factor"] = volume_factor

        # Combine factors
        technical_adjustment = (
            rsi_factor * 0.3
            + macd_factor * 0.3
            + bollinger_factor * 0.25
            + volume_factor * 0.15
        )

        adjusted_prob = base_prob * (1 + technical_adjustment)
        adjusted_prob = max(0.1, min(0.9, adjusted_prob))  # Clamp between 0.1 and 0.9

        confidence_score = (
            abs(technical_adjustment) * 2
        )  # Higher adjustment = higher confidence
        confidence_score = max(0.1, min(1.0, confidence_score))

        risk_adjusted_prob = adjusted_prob * (1 - market_data.volatility * 2)
        risk_adjusted_prob = max(0.1, min(0.9, risk_adjusted_prob))

        return ProbabilityResult(
            symbol=signal.symbol,
            direction=signal.direction,
            base_probability=base_prob,
            adjusted_probability=adjusted_prob,
            confidence_score=confidence_score,
            risk_adjusted_probability=risk_adjusted_prob,
            probability_model=ProbabilityModel.TECHNICAL_INDICATORS,
            factors=factors,
        )

    async def _calculate_volatility_adjusted_probability(
        self, signal: DetectedSignal, market_data: ProcessedMarketData, base_prob: float
    ) -> ProbabilityResult:
        """Calculate probability adjusted for market volatility conditions."""
        volatility = market_data.volatility

        # Determine market regime
        regime_factor = 1.0
        if volatility > self.market_regime_threshold:
            # High volatility regime - reduce probability confidence
            regime_factor = 0.8
        elif volatility < self.market_regime_threshold * 0.3:
            # Low volatility regime - signals may be less reliable
            regime_factor = 0.9

        # Volatility decay adjustment
        volatility_adjustment = math.exp(-volatility * 10) * 0.2  # Exponential decay

        # Price change momentum factor
        momentum_factor = min(0.3, abs(float(market_data.price_change_percent)) / 10)

        factors = {
            "volatility": volatility,
            "regime_factor": regime_factor,
            "volatility_adjustment": volatility_adjustment,
            "momentum_factor": momentum_factor,
        }

        # Apply adjustments
        adjusted_prob = base_prob * regime_factor

        if signal.direction == "UP" and float(market_data.price_change_percent) > 0:
            adjusted_prob += momentum_factor
        elif signal.direction == "DOWN" and float(market_data.price_change_percent) < 0:
            adjusted_prob += momentum_factor

        adjusted_prob = max(0.1, min(0.9, adjusted_prob))

        # Confidence decreases with higher volatility
        confidence_score = max(0.1, 1.0 - volatility * 5)

        # Risk adjustment using Sharpe-like ratio
        risk_adjusted_prob = adjusted_prob * (
            1 - volatility / 0.1
        )  # Normalize by 10% volatility
        risk_adjusted_prob = max(0.1, min(0.9, risk_adjusted_prob))

        return ProbabilityResult(
            symbol=signal.symbol,
            direction=signal.direction,
            base_probability=base_prob,
            adjusted_probability=adjusted_prob,
            confidence_score=confidence_score,
            risk_adjusted_probability=risk_adjusted_prob,
            probability_model=ProbabilityModel.VOLATILITY_ADJUSTED,
            factors=factors,
        )

    async def _calculate_confidence_weighted_probability(
        self, signal: DetectedSignal, market_data: ProcessedMarketData, base_prob: float
    ) -> ProbabilityResult:
        """Calculate probability weighted by signal confidence and strength."""

        # Convert confidence level to numeric
        confidence_numeric = {"LOW": 0.3, "MEDIUM": 0.6, "HIGH": 0.9}.get(
            signal.confidence_level, 0.5
        )

        # Signal strength normalization (assuming max strength around 10)
        strength_factor = min(1.0, signal.signal_strength / 10.0)

        # Rule priority factor (higher priority = more reliable)
        rule_priority_factor = await self._get_rule_priority_factor(signal.rule_name)

        # Time-based decay (signals lose reliability over time)
        time_since_signal = (
            datetime.utcnow() - signal.timestamp
        ).total_seconds() / 60  # minutes
        time_decay = math.exp(-time_since_signal / 30)  # 30-minute half-life

        factors = {
            "confidence_numeric": confidence_numeric,
            "strength_factor": strength_factor,
            "rule_priority_factor": rule_priority_factor,
            "time_decay": time_decay,
        }

        # Weighted combination
        weight_adjustment = (
            confidence_numeric * 0.4
            + strength_factor * 0.3
            + rule_priority_factor * 0.2
            + time_decay * 0.1
        )

        adjusted_prob = base_prob * (
            0.5 + weight_adjustment
        )  # Scale between 0.5x and 1.5x
        adjusted_prob = max(0.1, min(0.9, adjusted_prob))

        confidence_score = confidence_numeric * strength_factor * rule_priority_factor

        # Risk adjustment considers uncertainty
        uncertainty_factor = 1.0 - confidence_numeric
        risk_adjusted_prob = adjusted_prob * (1 - uncertainty_factor * 0.3)
        risk_adjusted_prob = max(0.1, min(0.9, risk_adjusted_prob))

        return ProbabilityResult(
            symbol=signal.symbol,
            direction=signal.direction,
            base_probability=base_prob,
            adjusted_probability=adjusted_prob,
            confidence_score=confidence_score,
            risk_adjusted_probability=risk_adjusted_prob,
            probability_model=ProbabilityModel.CONFIDENCE_WEIGHTED,
            factors=factors,
        )

    async def _calculate_monte_carlo_probability(
        self, signal: DetectedSignal, market_data: ProcessedMarketData, base_prob: float
    ) -> ProbabilityResult:
        """Calculate probability using Monte Carlo simulation."""

        # Parameters for simulation
        num_simulations = 1000
        time_horizon = 15  # minutes (signal expiry)

        # Current price and volatility
        current_price = float(market_data.raw_data.close_price)
        annual_volatility = market_data.volatility * math.sqrt(
            365 * 24 * 60
        )  # Annualize minute volatility

        # Monte Carlo simulation
        successful_outcomes = 0

        for _ in range(num_simulations):
            # Generate random price path using geometric Brownian motion
            dt = time_horizon / (365 * 24 * 60)  # Convert minutes to years
            random_shock = np.random.normal(0, 1)

            # Simulate final price
            final_price = current_price * math.exp(
                (self.risk_free_rate - 0.5 * annual_volatility**2) * dt
                + annual_volatility * math.sqrt(dt) * random_shock
            )

            # Check if outcome matches signal direction
            if signal.direction == "UP" and final_price > current_price:
                successful_outcomes += 1
            elif signal.direction == "DOWN" and final_price < current_price:
                successful_outcomes += 1

        monte_carlo_prob = successful_outcomes / num_simulations

        # Blend with original probability
        blending_factor = 0.7  # 70% Monte Carlo, 30% original
        adjusted_prob = monte_carlo_prob * blending_factor + base_prob * (
            1 - blending_factor
        )
        adjusted_prob = max(0.1, min(0.9, adjusted_prob))

        # Confidence based on simulation variance
        simulation_variance = monte_carlo_prob * (1 - monte_carlo_prob)
        confidence_score = max(
            0.1, 1.0 - simulation_variance * 4
        )  # Lower variance = higher confidence

        factors = {
            "monte_carlo_prob": monte_carlo_prob,
            "successful_outcomes": successful_outcomes,
            "total_simulations": num_simulations,
            "simulation_variance": simulation_variance,
            "annual_volatility": annual_volatility,
        }

        risk_adjusted_prob = adjusted_prob * (1 - simulation_variance)
        risk_adjusted_prob = max(0.1, min(0.9, risk_adjusted_prob))

        return ProbabilityResult(
            symbol=signal.symbol,
            direction=signal.direction,
            base_probability=base_prob,
            adjusted_probability=adjusted_prob,
            confidence_score=confidence_score,
            risk_adjusted_probability=risk_adjusted_prob,
            probability_model=ProbabilityModel.MONTE_CARLO,
            factors=factors,
        )

    async def _calculate_ensemble_probability(
        self, signal: DetectedSignal, market_data: ProcessedMarketData, base_prob: float
    ) -> ProbabilityResult:
        """Calculate probability using ensemble of all models."""

        # Calculate probabilities from each model
        technical_result = await self._calculate_technical_probability(
            signal, market_data, base_prob
        )
        volatility_result = await self._calculate_volatility_adjusted_probability(
            signal, market_data, base_prob
        )
        confidence_result = await self._calculate_confidence_weighted_probability(
            signal, market_data, base_prob
        )
        monte_carlo_result = await self._calculate_monte_carlo_probability(
            signal, market_data, base_prob
        )

        # Weighted ensemble
        ensemble_prob = (
            technical_result.adjusted_probability
            * self.model_weights[ProbabilityModel.TECHNICAL_INDICATORS]
            + volatility_result.adjusted_probability
            * self.model_weights[ProbabilityModel.VOLATILITY_ADJUSTED]
            + confidence_result.adjusted_probability
            * self.model_weights[ProbabilityModel.CONFIDENCE_WEIGHTED]
            + monte_carlo_result.adjusted_probability
            * self.model_weights[ProbabilityModel.MONTE_CARLO]
        )

        # Weighted confidence score
        ensemble_confidence = (
            technical_result.confidence_score
            * self.model_weights[ProbabilityModel.TECHNICAL_INDICATORS]
            + volatility_result.confidence_score
            * self.model_weights[ProbabilityModel.VOLATILITY_ADJUSTED]
            + confidence_result.confidence_score
            * self.model_weights[ProbabilityModel.CONFIDENCE_WEIGHTED]
            + monte_carlo_result.confidence_score
            * self.model_weights[ProbabilityModel.MONTE_CARLO]
        )

        # Weighted risk-adjusted probability
        ensemble_risk_adjusted = (
            technical_result.risk_adjusted_probability
            * self.model_weights[ProbabilityModel.TECHNICAL_INDICATORS]
            + volatility_result.risk_adjusted_probability
            * self.model_weights[ProbabilityModel.VOLATILITY_ADJUSTED]
            + confidence_result.risk_adjusted_probability
            * self.model_weights[ProbabilityModel.CONFIDENCE_WEIGHTED]
            + monte_carlo_result.risk_adjusted_probability
            * self.model_weights[ProbabilityModel.MONTE_CARLO]
        )

        # Combine factors from all models
        combined_factors = {
            "technical": technical_result.factors,
            "volatility": volatility_result.factors,
            "confidence": confidence_result.factors,
            "monte_carlo": monte_carlo_result.factors,
            "model_weights": dict(self.model_weights),
        }

        return ProbabilityResult(
            symbol=signal.symbol,
            direction=signal.direction,
            base_probability=base_prob,
            adjusted_probability=ensemble_prob,
            confidence_score=ensemble_confidence,
            risk_adjusted_probability=ensemble_risk_adjusted,
            probability_model=ProbabilityModel.ENSEMBLE,
            factors=combined_factors,
        )

    # Helper methods for individual indicator calculations

    async def _calculate_rsi_factor(self, rsi: float, direction: str) -> float:
        """Calculate RSI contribution factor."""
        if direction == "UP":
            # For UP signals, lower RSI is better (oversold bounce)
            return (50 - min(50, rsi)) / 50 * 0.5  # Max 0.5 adjustment
        else:
            # For DOWN signals, higher RSI is better (overbought reversal)
            return (max(50, rsi) - 50) / 50 * 0.5

    async def _calculate_macd_factor(
        self, macd: float, macd_signal: float, direction: str
    ) -> float:
        """Calculate MACD contribution factor."""
        macd_diff = macd - macd_signal

        if direction == "UP" and macd_diff > 0:
            return min(0.3, abs(macd_diff) * 100)  # Scale and cap
        elif direction == "DOWN" and macd_diff < 0:
            return min(0.3, abs(macd_diff) * 100)
        else:
            return -0.1  # Slight penalty for opposing MACD signal

    async def _calculate_bollinger_factor(
        self, market_data: ProcessedMarketData, direction: str
    ) -> float:
        """Calculate Bollinger Band contribution factor."""
        price = float(market_data.raw_data.close_price)
        upper_band = float(market_data.bollinger_upper)
        lower_band = float(market_data.bollinger_lower)

        if direction == "UP" and price > upper_band:
            return 0.2  # Breakout confirmation
        elif direction == "DOWN" and price < lower_band:
            return 0.2  # Breakdown confirmation
        else:
            # Calculate position within bands
            band_width = upper_band - lower_band
            if band_width > 0:
                position = (price - lower_band) / band_width
                if direction == "UP":
                    return (1 - position) * 0.1  # Better if closer to lower band
                else:
                    return position * 0.1  # Better if closer to upper band
        return 0.0

    async def _calculate_volume_factor(self, market_data: ProcessedMarketData) -> float:
        """Calculate volume contribution factor."""
        if market_data.volume_sma > 0:
            volume_ratio = float(market_data.raw_data.volume) / float(
                market_data.volume_sma
            )
            return min(0.2, (volume_ratio - 1) * 0.1)  # Higher volume = higher factor
        return 0.0

    async def _get_rule_priority_factor(self, rule_name: str) -> float:
        """Get priority factor for a specific rule."""
        rule_priorities = {
            "RSI_OVERSOLD_BOUNCE": 0.8,
            "RSI_OVERBOUGHT_REVERSAL": 0.8,
            "BOLLINGER_BREAKOUT_UP": 0.7,
            "BOLLINGER_BREAKOUT_DOWN": 0.7,
            "MACD_BULLISH_CROSSOVER": 0.6,
            "MACD_BEARISH_CROSSOVER": 0.6,
            "VOLATILITY_SPIKE_UP": 0.5,
            "VOLATILITY_SPIKE_DOWN": 0.5,
            "VOLUME_PRICE_CONFLUENCE": 0.6,
        }
        return rule_priorities.get(rule_name, 0.5)

    async def _apply_historical_adjustment(
        self, result: ProbabilityResult
    ) -> ProbabilityResult:
        """Apply historical performance adjustment to the result."""
        # Get symbol-specific performance
        symbol_perf = self.symbol_performance.get(result.symbol, {})
        model_perf = self.model_performance.get(result.probability_model, 0.5)

        direction_perf = symbol_perf.get(f"{result.direction}_accuracy", 0.5)

        # Apply adjustment (small impact to avoid overfitting)
        historical_adjustment = (
            direction_perf + model_perf - 1.0
        ) * 0.1  # Max 10% adjustment

        result.adjusted_probability += historical_adjustment
        result.adjusted_probability = max(0.1, min(0.9, result.adjusted_probability))

        result.risk_adjusted_probability += historical_adjustment * 0.5
        result.risk_adjusted_probability = max(
            0.1, min(0.9, result.risk_adjusted_probability)
        )

        return result

    def add_historical_outcome(self, outcome: HistoricalOutcome) -> None:
        """Add a historical outcome for model improvement."""
        self.historical_outcomes.append(outcome)

        # Keep only recent outcomes
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        self.historical_outcomes = [
            outcome
            for outcome in self.historical_outcomes
            if outcome.timestamp >= cutoff_date
        ]

        # Update performance metrics
        asyncio.create_task(self._update_performance_metrics())

    async def _update_performance_metrics(self) -> None:
        """Update model and symbol performance metrics."""
        if not self.historical_outcomes:
            return

        # Calculate symbol-specific performance
        symbol_stats = {}
        for outcome in self.historical_outcomes:
            symbol = outcome.symbol
            direction = outcome.direction

            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    "UP_correct": 0,
                    "UP_total": 0,
                    "DOWN_correct": 0,
                    "DOWN_total": 0,
                }

            if outcome.actual_outcome:
                symbol_stats[symbol][f"{direction}_correct"] += 1
            symbol_stats[symbol][f"{direction}_total"] += 1

        # Calculate accuracy rates
        self.symbol_performance = {}
        for symbol, stats in symbol_stats.items():
            self.symbol_performance[symbol] = {}

            if stats["UP_total"] > 0:
                self.symbol_performance[symbol]["UP_accuracy"] = (
                    stats["UP_correct"] / stats["UP_total"]
                )

            if stats["DOWN_total"] > 0:
                self.symbol_performance[symbol]["DOWN_accuracy"] = (
                    stats["DOWN_correct"] / stats["DOWN_total"]
                )

    def get_model_stats(self) -> Dict[str, Any]:
        """Get probability calculator statistics."""
        return {
            "historical_outcomes": len(self.historical_outcomes),
            "lookback_days": self.lookback_days,
            "model_weights": dict(self.model_weights),
            "symbol_performance": dict(self.symbol_performance),
            "model_performance": dict(self.model_performance),
        }


# Factory function for creating calculator instances
def create_probability_calculator(lookback_days: int = 30) -> ProbabilityCalculator:
    """Create and return a configured ProbabilityCalculator instance."""
    return ProbabilityCalculator(lookback_days=lookback_days)


# CLI entry point
async def main() -> None:
    """CLI entry point for the probability calculator."""
    import sys
    import json
    from decimal import Decimal
    from ..processors.market_data_processor import (
        PriceData,
        create_market_data_processor,
    )
    from ..engines.signal_detector import create_signal_detector

    calculator = create_probability_calculator()
    processor = create_market_data_processor()
    detector = create_signal_detector()

    # Example usage
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

    # Process data and detect signal
    processed_data = await processor.process_market_data(sample_data)
    detected_signal = await detector.analyze_market_data(processed_data)

    if detected_signal:
        # Calculate probabilities with different models
        for model in ProbabilityModel:
            result = await calculator.calculate_probability(
                detected_signal, processed_data, model
            )
            print(f"\n{model.value.upper()} Model:")
            print(
                json.dumps(
                    {
                        "symbol": result.symbol,
                        "direction": result.direction,
                        "base_probability": result.base_probability,
                        "adjusted_probability": result.adjusted_probability,
                        "confidence_score": result.confidence_score,
                        "risk_adjusted_probability": result.risk_adjusted_probability,
                    },
                    indent=2,
                )
            )


if __name__ == "__main__":
    asyncio.run(main())
