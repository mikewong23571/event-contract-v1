"""Momentum-based trading strategy.

This strategy identifies trading opportunities based on price momentum and trend analysis.
It uses moving averages, RSI, and price action to generate signals.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List

from .base_strategy import BaseStrategy, StrategySignal, TechnicalIndicators, StrategyConfig
from ..loaders.data_loader import HistoricalDataPoint


class MomentumStrategyConfig(StrategyConfig):
    """Configuration for momentum strategy."""
    
    def __init__(self, **kwargs):
        # Set default parameters for momentum strategy
        default_params = {
            "fast_ma_period": 5,
            "slow_ma_period": 20,
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "min_momentum_threshold": 0.02,  # 2% price change
            "volume_confirmation": True,
            "trend_confirmation_periods": 3
        }
        
        # Merge with provided parameters
        if 'parameters' in kwargs:
            default_params.update(kwargs['parameters'])
        kwargs['parameters'] = default_params
        
        # Set strategy-specific defaults
        kwargs.setdefault('name', 'MomentumStrategy')
        kwargs.setdefault('description', 'Momentum-based trading strategy using MA crossovers and RSI')
        kwargs.setdefault('min_confidence', 'MEDIUM')
        kwargs.setdefault('min_probability', 0.65)
        
        super().__init__(**kwargs)


class MomentumStrategy(BaseStrategy):
    """Momentum trading strategy implementation.
    
    This strategy generates signals based on:
    1. Moving average crossovers (fast MA vs slow MA)
    2. RSI momentum confirmation
    3. Price momentum analysis
    4. Volume confirmation (optional)
    
    Signal Logic:
    - UP signal: Fast MA > Slow MA, RSI not overbought, positive momentum
    - DOWN signal: Fast MA < Slow MA, RSI not oversold, negative momentum
    """
    
    def __init__(self, config: Optional[MomentumStrategyConfig] = None):
        if config is None:
            config = MomentumStrategyConfig()
        super().__init__(config)
        
        # Extract strategy parameters
        params = self.config.parameters
        self.fast_ma_period = params['fast_ma_period']
        self.slow_ma_period = params['slow_ma_period']
        self.rsi_period = params['rsi_period']
        self.rsi_oversold = params['rsi_oversold']
        self.rsi_overbought = params['rsi_overbought']
        self.min_momentum_threshold = params['min_momentum_threshold']
        self.volume_confirmation = params['volume_confirmation']
        self.trend_confirmation_periods = params['trend_confirmation_periods']
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        """Generate momentum-based trading signal."""
        # Update data and calculate indicators
        self.update_data(data_point)
        
        # Need sufficient history for analysis
        if len(self._price_history) < max(self.slow_ma_period, self.rsi_period) + 5:
            return None
        
        indicators = self.get_indicators()
        if not indicators:
            return None
        
        # Analyze momentum conditions
        signal_direction = self._analyze_momentum(indicators, data_point)
        if not signal_direction:
            return None
        
        # Calculate signal strength and confidence
        confidence, probability = self._calculate_signal_strength(indicators, signal_direction)
        
        # Generate signal reason
        signal_reason = self._generate_signal_reason(indicators, signal_direction)
        conditions_met = self._get_conditions_met(indicators, signal_direction)
        
        # Create signal
        signal = StrategySignal(
            timestamp=data_point.timestamp,
            symbol=data_point.symbol,
            direction=signal_direction,
            confidence=confidence,
            probability=probability,
            expiry_minutes=self.config.contract_duration_minutes,
            strategy_name=self.name,
            strategy_version=self.version,
            indicators=indicators,
            entry_price=data_point.close_price,
            signal_reason=signal_reason,
            conditions_met=conditions_met,
            risk_level=self._assess_risk_level(indicators)
        )
        
        # Validate signal meets minimum requirements
        if not self.validate_signal_conditions(signal):
            return None
        
        self._signals_generated += 1
        self._last_signal_time = data_point.timestamp
        
        return signal
    
    def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
        """Calculate technical indicators for momentum analysis."""
        indicators = TechnicalIndicators()
        
        # Moving averages
        indicators.sma_5 = self._calculate_sma(self.fast_ma_period)
        indicators.sma_20 = self._calculate_sma(self.slow_ma_period)
        
        # RSI
        indicators.rsi = self._calculate_rsi(self.rsi_period)
        
        # Price momentum
        current_price = float(data_point.close_price)
        if len(self._price_history) >= 2:
            prev_price = float(self._price_history[-2].close_price)
            indicators.price_change = current_price - prev_price
            indicators.price_change_pct = (current_price - prev_price) / prev_price if prev_price > 0 else 0
        
        # Volatility
        indicators.volatility = self._calculate_volatility(20)
        
        # Volume analysis (if available)
        if hasattr(data_point, 'volume') and data_point.volume:
            indicators.volume_sma = self._calculate_volume_sma(10)
            if indicators.volume_sma:
                indicators.volume_ratio = float(data_point.volume) / indicators.volume_sma
        
        # Custom momentum indicators
        indicators.custom = {
            'momentum_score': self._calculate_momentum_score(),
            'trend_strength': self._calculate_trend_strength(),
            'ma_distance': self._calculate_ma_distance(current_price)
        }
        
        return indicators
    
    def _analyze_momentum(self, indicators: TechnicalIndicators, 
                         data_point: HistoricalDataPoint) -> Optional[str]:
        """Analyze momentum conditions to determine signal direction."""
        if not indicators.sma_5 or not indicators.sma_20 or not indicators.rsi:
            return None
        
        # Check moving average crossover
        ma_bullish = indicators.sma_5 > indicators.sma_20
        ma_bearish = indicators.sma_5 < indicators.sma_20
        
        # Check RSI conditions
        rsi_not_overbought = indicators.rsi < self.rsi_overbought
        rsi_not_oversold = indicators.rsi > self.rsi_oversold
        
        # Check momentum threshold
        momentum_positive = (indicators.price_change_pct or 0) > self.min_momentum_threshold
        momentum_negative = (indicators.price_change_pct or 0) < -self.min_momentum_threshold
        
        # Check trend confirmation
        trend_confirmed = self._check_trend_confirmation()
        
        # Volume confirmation (if enabled)
        volume_ok = True
        if self.volume_confirmation and indicators.volume_ratio:
            volume_ok = indicators.volume_ratio > 1.2  # Above average volume
        
        # UP signal conditions
        if (ma_bullish and rsi_not_overbought and momentum_positive and 
            trend_confirmed and volume_ok):
            return "UP"
        
        # DOWN signal conditions
        if (ma_bearish and rsi_not_oversold and momentum_negative and 
            trend_confirmed and volume_ok):
            return "DOWN"
        
        return None
    
    def _calculate_signal_strength(self, indicators: TechnicalIndicators, 
                                 direction: str) -> tuple[str, float]:
        """Calculate signal confidence and probability."""
        strength_score = 0.0
        max_score = 0.0
        
        # MA separation strength
        if indicators.sma_5 and indicators.sma_20:
            ma_separation = abs(indicators.sma_5 - indicators.sma_20) / indicators.sma_20
            strength_score += min(ma_separation * 100, 20)  # Max 20 points
            max_score += 20
        
        # RSI strength
        if indicators.rsi:
            if direction == "UP":
                rsi_strength = (70 - indicators.rsi) / 40  # Distance from overbought
            else:
                rsi_strength = (indicators.rsi - 30) / 40  # Distance from oversold
            strength_score += max(0, rsi_strength * 20)  # Max 20 points
            max_score += 20
        
        # Momentum strength
        if indicators.price_change_pct:
            momentum_strength = min(abs(indicators.price_change_pct) * 500, 20)  # Max 20 points
            strength_score += momentum_strength
            max_score += 20
        
        # Trend strength
        trend_strength = indicators.custom.get('trend_strength', 0)
        strength_score += trend_strength * 20  # Max 20 points
        max_score += 20
        
        # Volume confirmation
        if indicators.volume_ratio:
            volume_strength = min((indicators.volume_ratio - 1) * 10, 20)  # Max 20 points
            strength_score += max(0, volume_strength)
            max_score += 20
        
        # Calculate final scores
        if max_score > 0:
            normalized_score = strength_score / max_score
        else:
            normalized_score = 0.5
        
        # Determine confidence level
        if normalized_score >= 0.8:
            confidence = "HIGH"
            probability = 0.75 + (normalized_score - 0.8) * 0.5  # 0.75-0.85
        elif normalized_score >= 0.6:
            confidence = "MEDIUM"
            probability = 0.65 + (normalized_score - 0.6) * 0.5  # 0.65-0.75
        else:
            confidence = "LOW"
            probability = 0.55 + normalized_score * 0.17  # 0.55-0.65
        
        return confidence, min(probability, 0.95)
    
    def _generate_signal_reason(self, indicators: TechnicalIndicators, 
                              direction: str) -> str:
        """Generate human-readable signal reason."""
        reasons = []
        
        if indicators.sma_5 and indicators.sma_20:
            if direction == "UP" and indicators.sma_5 > indicators.sma_20:
                reasons.append(f"Fast MA ({indicators.sma_5:.4f}) above Slow MA ({indicators.sma_20:.4f})")
            elif direction == "DOWN" and indicators.sma_5 < indicators.sma_20:
                reasons.append(f"Fast MA ({indicators.sma_5:.4f}) below Slow MA ({indicators.sma_20:.4f})")
        
        if indicators.rsi:
            reasons.append(f"RSI at {indicators.rsi:.1f} (neutral zone)")
        
        if indicators.price_change_pct:
            pct_change = indicators.price_change_pct * 100
            reasons.append(f"Price momentum: {pct_change:+.2f}%")
        
        momentum_score = indicators.custom.get('momentum_score', 0)
        reasons.append(f"Momentum score: {momentum_score:.2f}")
        
        return "; ".join(reasons)
    
    def _get_conditions_met(self, indicators: TechnicalIndicators, 
                          direction: str) -> List[str]:
        """Get list of conditions that were met for the signal."""
        conditions = []
        
        if indicators.sma_5 and indicators.sma_20:
            if direction == "UP" and indicators.sma_5 > indicators.sma_20:
                conditions.append("MA_CROSSOVER_BULLISH")
            elif direction == "DOWN" and indicators.sma_5 < indicators.sma_20:
                conditions.append("MA_CROSSOVER_BEARISH")
        
        if indicators.rsi:
            if direction == "UP" and indicators.rsi < self.rsi_overbought:
                conditions.append("RSI_NOT_OVERBOUGHT")
            elif direction == "DOWN" and indicators.rsi > self.rsi_oversold:
                conditions.append("RSI_NOT_OVERSOLD")
        
        if indicators.price_change_pct:
            if direction == "UP" and indicators.price_change_pct > self.min_momentum_threshold:
                conditions.append("POSITIVE_MOMENTUM")
            elif direction == "DOWN" and indicators.price_change_pct < -self.min_momentum_threshold:
                conditions.append("NEGATIVE_MOMENTUM")
        
        if self._check_trend_confirmation():
            conditions.append("TREND_CONFIRMED")
        
        if indicators.volume_ratio and indicators.volume_ratio > 1.2:
            conditions.append("VOLUME_CONFIRMATION")
        
        return conditions
    
    def _assess_risk_level(self, indicators: TechnicalIndicators) -> str:
        """Assess risk level based on market conditions."""
        risk_factors = 0
        
        # High volatility increases risk
        if indicators.volatility and indicators.volatility > 0.03:  # 3% volatility
            risk_factors += 1
        
        # Extreme RSI increases risk
        if indicators.rsi:
            if indicators.rsi > 80 or indicators.rsi < 20:
                risk_factors += 1
        
        # Low volume increases risk
        if indicators.volume_ratio and indicators.volume_ratio < 0.8:
            risk_factors += 1
        
        if risk_factors >= 2:
            return "HIGH"
        elif risk_factors == 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_momentum_score(self) -> float:
        """Calculate overall momentum score (0-1)."""
        if len(self._price_history) < 5:
            return 0.0
        
        # Calculate price changes over different periods
        current_price = float(self._price_history[-1].close_price)
        
        scores = []
        for period in [1, 3, 5]:
            if len(self._price_history) > period:
                past_price = float(self._price_history[-(period+1)].close_price)
                if past_price > 0:
                    change = (current_price - past_price) / past_price
                    scores.append(change)
        
        if not scores:
            return 0.0
        
        # Average momentum with more weight on recent periods
        weights = [0.5, 0.3, 0.2]
        weighted_momentum = sum(score * weight for score, weight in zip(scores, weights[:len(scores)]))
        
        # Normalize to 0-1 range
        return max(0, min(1, (weighted_momentum + 0.1) / 0.2))
    
    def _calculate_trend_strength(self) -> float:
        """Calculate trend strength (0-1)."""
        if len(self._price_history) < 10:
            return 0.0
        
        # Count consecutive periods in same direction
        consecutive_up = 0
        consecutive_down = 0
        
        for i in range(len(self._price_history) - 1, 0, -1):
            current = float(self._price_history[i].close_price)
            previous = float(self._price_history[i-1].close_price)
            
            if current > previous:
                consecutive_up += 1
                consecutive_down = 0
            elif current < previous:
                consecutive_down += 1
                consecutive_up = 0
            else:
                break
        
        max_consecutive = max(consecutive_up, consecutive_down)
        return min(1.0, max_consecutive / 5.0)  # Normalize to 0-1
    
    def _calculate_ma_distance(self, current_price: float) -> float:
        """Calculate distance from moving averages."""
        if not self._price_history or len(self._price_history) < self.slow_ma_period:
            return 0.0
        
        slow_ma = self._calculate_sma(self.slow_ma_period)
        if not slow_ma:
            return 0.0
        
        return (current_price - slow_ma) / slow_ma
    
    def _check_trend_confirmation(self) -> bool:
        """Check if trend is confirmed over multiple periods."""
        if len(self._price_history) < self.trend_confirmation_periods + 1:
            return False
        
        # Check if price has been moving in same direction
        directions = []
        for i in range(len(self._price_history) - self.trend_confirmation_periods, len(self._price_history)):
            if i > 0:
                current = float(self._price_history[i].close_price)
                previous = float(self._price_history[i-1].close_price)
                directions.append(1 if current > previous else -1 if current < previous else 0)
        
        if not directions:
            return False
        
        # Check if majority of periods are in same direction
        positive_count = sum(1 for d in directions if d > 0)
        negative_count = sum(1 for d in directions if d < 0)
        
        return max(positive_count, negative_count) >= len(directions) * 0.7
    
    def _calculate_volume_sma(self, periods: int) -> Optional[float]:
        """Calculate volume simple moving average."""
        if len(self._price_history) < periods:
            return None
        
        volumes = []
        for data_point in self._price_history[-periods:]:
            if hasattr(data_point, 'volume') and data_point.volume:
                volumes.append(float(data_point.volume))
        
        return sum(volumes) / len(volumes) if volumes else None