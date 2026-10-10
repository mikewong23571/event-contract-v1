"""Mean reversion trading strategy.

This strategy identifies trading opportunities when prices deviate significantly
from their historical mean and are likely to revert back.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
import math

from .base_strategy import BaseStrategy, StrategySignal, TechnicalIndicators, StrategyConfig
from ..loaders.data_loader import HistoricalDataPoint


class MeanReversionStrategyConfig(StrategyConfig):
    """Configuration for mean reversion strategy."""
    
    def __init__(self, **kwargs):
        # Set default parameters for mean reversion strategy
        default_params = {
            "lookback_period": 20,
            "bollinger_period": 20,
            "bollinger_std_dev": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 25,
            "rsi_overbought": 75,
            "mean_reversion_threshold": 1.5,  # Standard deviations from mean
            "min_price_deviation": 0.015,  # 1.5% minimum deviation
            "volume_confirmation": True,
            "trend_filter": True,
            "max_consecutive_signals": 3
        }
        
        # Merge with provided parameters
        if 'parameters' in kwargs:
            default_params.update(kwargs['parameters'])
        kwargs['parameters'] = default_params
        
        # Set strategy-specific defaults
        kwargs.setdefault('name', 'MeanReversionStrategy')
        kwargs.setdefault('description', 'Mean reversion strategy using Bollinger Bands and RSI')
        kwargs.setdefault('min_confidence', 'MEDIUM')
        kwargs.setdefault('min_probability', 0.60)
        
        super().__init__(**kwargs)


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion trading strategy implementation.
    
    This strategy generates signals based on:
    1. Bollinger Bands for price deviation detection
    2. RSI for momentum confirmation
    3. Statistical mean reversion analysis
    4. Volume and trend filters
    
    Signal Logic:
    - UP signal: Price below lower Bollinger Band, RSI oversold, mean reversion expected
    - DOWN signal: Price above upper Bollinger Band, RSI overbought, mean reversion expected
    """
    
    def __init__(self, config: Optional[MeanReversionStrategyConfig] = None):
        if config is None:
            config = MeanReversionStrategyConfig()
        super().__init__(config)
        
        # Extract strategy parameters
        params = self.config.parameters
        self.lookback_period = params['lookback_period']
        self.bollinger_period = params['bollinger_period']
        self.bollinger_std_dev = params['bollinger_std_dev']
        self.rsi_period = params['rsi_period']
        self.rsi_oversold = params['rsi_oversold']
        self.rsi_overbought = params['rsi_overbought']
        self.mean_reversion_threshold = params['mean_reversion_threshold']
        self.min_price_deviation = params['min_price_deviation']
        self.volume_confirmation = params['volume_confirmation']
        self.trend_filter = params['trend_filter']
        self.max_consecutive_signals = params['max_consecutive_signals']
        
        # Track consecutive signals
        self._consecutive_signals = 0
        self._last_signal_direction = None
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        """Generate mean reversion trading signal."""
        # Update data and calculate indicators
        self.update_data(data_point)
        
        # Need sufficient history for analysis
        required_history = max(self.bollinger_period, self.rsi_period, self.lookback_period) + 5
        if len(self._price_history) < required_history:
            return None
        
        indicators = self.get_indicators()
        if not indicators:
            return None
        
        # Analyze mean reversion conditions
        signal_direction = self._analyze_mean_reversion(indicators, data_point)
        if not signal_direction:
            return None
        
        # Check consecutive signal limits
        if self._should_skip_consecutive_signal(signal_direction):
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
        
        # Update consecutive signal tracking
        self._update_consecutive_signals(signal_direction)
        
        self._signals_generated += 1
        self._last_signal_time = data_point.timestamp
        
        return signal
    
    def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
        """Calculate technical indicators for mean reversion analysis."""
        indicators = TechnicalIndicators()
        
        # Bollinger Bands
        bb_middle, bb_upper, bb_lower = self._calculate_bollinger_bands()
        indicators.bb_middle = bb_middle
        indicators.bb_upper = bb_upper
        indicators.bb_lower = bb_lower
        
        # RSI
        indicators.rsi = self._calculate_rsi(self.rsi_period)
        
        # Moving averages for trend filter
        indicators.sma_20 = self._calculate_sma(20)
        indicators.sma_50 = self._calculate_sma(50) if len(self._price_history) >= 50 else None
        
        # Price statistics
        current_price = float(data_point.close_price)
        indicators.price_mean = self._calculate_price_mean(self.lookback_period)
        indicators.price_std = self._calculate_price_std(self.lookback_period)
        
        # Price position relative to bands
        if bb_upper and bb_lower and bb_upper != bb_lower:
            indicators.bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
        
        # Volatility
        indicators.volatility = self._calculate_volatility(20)
        
        # Volume analysis
        if hasattr(data_point, 'volume') and data_point.volume:
            indicators.volume_sma = self._calculate_volume_sma(10)
            if indicators.volume_sma:
                indicators.volume_ratio = float(data_point.volume) / indicators.volume_sma
        
        # Custom mean reversion indicators
        indicators.custom = {
            'mean_reversion_score': self._calculate_mean_reversion_score(current_price),
            'price_z_score': self._calculate_price_z_score(current_price),
            'reversion_probability': self._calculate_reversion_probability(current_price),
            'trend_strength': self._calculate_trend_strength()
        }
        
        return indicators
    
    def _analyze_mean_reversion(self, indicators: TechnicalIndicators, 
                               data_point: HistoricalDataPoint) -> Optional[str]:
        """Analyze mean reversion conditions to determine signal direction."""
        current_price = float(data_point.close_price)
        
        # Check Bollinger Bands conditions
        if not (indicators.bb_upper and indicators.bb_lower and indicators.bb_middle):
            return None
        
        # Price deviation from mean
        price_z_score = indicators.custom.get('price_z_score', 0)
        
        # RSI conditions
        if not indicators.rsi:
            return None
        
        # Trend filter (if enabled)
        if self.trend_filter and not self._check_trend_filter(indicators):
            return None
        
        # Volume confirmation (if enabled)
        if self.volume_confirmation and not self._check_volume_confirmation(indicators):
            return None
        
        # UP signal conditions (price oversold, expect reversion up)
        up_conditions = [
            current_price < indicators.bb_lower,  # Below lower Bollinger Band
            indicators.rsi < self.rsi_oversold,   # RSI oversold
            price_z_score < -self.mean_reversion_threshold,  # Significantly below mean
            abs(current_price - indicators.bb_middle) / indicators.bb_middle > self.min_price_deviation
        ]
        
        # DOWN signal conditions (price overbought, expect reversion down)
        down_conditions = [
            current_price > indicators.bb_upper,  # Above upper Bollinger Band
            indicators.rsi > self.rsi_overbought, # RSI overbought
            price_z_score > self.mean_reversion_threshold,   # Significantly above mean
            abs(current_price - indicators.bb_middle) / indicators.bb_middle > self.min_price_deviation
        ]
        
        # Check signal conditions
        if all(up_conditions):
            return "UP"
        elif all(down_conditions):
            return "DOWN"
        
        return None
    
    def _calculate_signal_strength(self, indicators: TechnicalIndicators, 
                                 direction: str) -> tuple[str, float]:
        """Calculate signal confidence and probability."""
        strength_score = 0.0
        max_score = 0.0
        
        current_price = float(self._price_history[-1].close_price)
        
        # Bollinger Band position strength
        if indicators.bb_position is not None:
            if direction == "UP":
                bb_strength = max(0, -indicators.bb_position) * 2  # Below 0 is good for UP
            else:
                bb_strength = max(0, (indicators.bb_position - 1) * 2)  # Above 1 is good for DOWN
            strength_score += min(bb_strength * 25, 25)  # Max 25 points
            max_score += 25
        
        # RSI extremity strength
        if indicators.rsi:
            if direction == "UP":
                rsi_strength = max(0, (self.rsi_oversold - indicators.rsi) / self.rsi_oversold)
            else:
                rsi_strength = max(0, (indicators.rsi - self.rsi_overbought) / (100 - self.rsi_overbought))
            strength_score += rsi_strength * 20  # Max 20 points
            max_score += 20
        
        # Z-score strength
        price_z_score = indicators.custom.get('price_z_score', 0)
        z_score_strength = min(abs(price_z_score) / 3.0, 1.0)  # Normalize to max 3 std devs
        strength_score += z_score_strength * 20  # Max 20 points
        max_score += 20
        
        # Mean reversion probability
        reversion_prob = indicators.custom.get('reversion_probability', 0.5)
        strength_score += (reversion_prob - 0.5) * 40  # Max 20 points
        max_score += 20
        
        # Volatility consideration (higher volatility = higher potential)
        if indicators.volatility:
            vol_strength = min(indicators.volatility * 100, 15)  # Max 15 points
            strength_score += vol_strength
            max_score += 15
        
        # Calculate final scores
        if max_score > 0:
            normalized_score = strength_score / max_score
        else:
            normalized_score = 0.5
        
        # Determine confidence level
        if normalized_score >= 0.75:
            confidence = "HIGH"
            probability = 0.70 + (normalized_score - 0.75) * 0.6  # 0.70-0.85
        elif normalized_score >= 0.55:
            confidence = "MEDIUM"
            probability = 0.60 + (normalized_score - 0.55) * 0.5  # 0.60-0.70
        else:
            confidence = "LOW"
            probability = 0.50 + normalized_score * 0.18  # 0.50-0.60
        
        return confidence, min(probability, 0.90)
    
    def _generate_signal_reason(self, indicators: TechnicalIndicators, 
                              direction: str) -> str:
        """Generate human-readable signal reason."""
        reasons = []
        current_price = float(self._price_history[-1].close_price)
        
        # Bollinger Bands analysis
        if indicators.bb_upper and indicators.bb_lower and indicators.bb_middle:
            if direction == "UP":
                deviation = (indicators.bb_lower - current_price) / indicators.bb_middle * 100
                reasons.append(f"Price {deviation:.1f}% below lower Bollinger Band")
            else:
                deviation = (current_price - indicators.bb_upper) / indicators.bb_middle * 100
                reasons.append(f"Price {deviation:.1f}% above upper Bollinger Band")
        
        # RSI analysis
        if indicators.rsi:
            if direction == "UP":
                reasons.append(f"RSI oversold at {indicators.rsi:.1f}")
            else:
                reasons.append(f"RSI overbought at {indicators.rsi:.1f}")
        
        # Z-score analysis
        price_z_score = indicators.custom.get('price_z_score', 0)
        reasons.append(f"Price Z-score: {price_z_score:.2f} std devs from mean")
        
        # Reversion probability
        reversion_prob = indicators.custom.get('reversion_probability', 0.5)
        reasons.append(f"Mean reversion probability: {reversion_prob:.1%}")
        
        return "; ".join(reasons)
    
    def _get_conditions_met(self, indicators: TechnicalIndicators, 
                          direction: str) -> List[str]:
        """Get list of conditions that were met for the signal."""
        conditions = []
        current_price = float(self._price_history[-1].close_price)
        
        # Bollinger Band conditions
        if direction == "UP" and current_price < indicators.bb_lower:
            conditions.append("BELOW_LOWER_BB")
        elif direction == "DOWN" and current_price > indicators.bb_upper:
            conditions.append("ABOVE_UPPER_BB")
        
        # RSI conditions
        if indicators.rsi:
            if direction == "UP" and indicators.rsi < self.rsi_oversold:
                conditions.append("RSI_OVERSOLD")
            elif direction == "DOWN" and indicators.rsi > self.rsi_overbought:
                conditions.append("RSI_OVERBOUGHT")
        
        # Z-score conditions
        price_z_score = indicators.custom.get('price_z_score', 0)
        if abs(price_z_score) > self.mean_reversion_threshold:
            conditions.append("EXTREME_PRICE_DEVIATION")
        
        # Minimum deviation
        if indicators.bb_middle:
            deviation = abs(current_price - indicators.bb_middle) / indicators.bb_middle
            if deviation > self.min_price_deviation:
                conditions.append("MIN_DEVIATION_MET")
        
        # Volume confirmation
        if self.volume_confirmation and indicators.volume_ratio and indicators.volume_ratio > 1.0:
            conditions.append("VOLUME_CONFIRMATION")
        
        # Trend filter
        if self.trend_filter and self._check_trend_filter(indicators):
            conditions.append("TREND_FILTER_PASSED")
        
        return conditions
    
    def _assess_risk_level(self, indicators: TechnicalIndicators) -> str:
        """Assess risk level based on market conditions."""
        risk_factors = 0
        
        # High volatility increases risk
        if indicators.volatility and indicators.volatility > 0.04:  # 4% volatility
            risk_factors += 1
        
        # Extreme price positions increase risk
        if indicators.bb_position is not None:
            if indicators.bb_position < -0.2 or indicators.bb_position > 1.2:
                risk_factors += 1
        
        # Strong trend against mean reversion increases risk
        trend_strength = indicators.custom.get('trend_strength', 0)
        if trend_strength > 0.7:
            risk_factors += 1
        
        # Low volume increases risk
        if indicators.volume_ratio and indicators.volume_ratio < 0.7:
            risk_factors += 1
        
        if risk_factors >= 3:
            return "HIGH"
        elif risk_factors >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_bollinger_bands(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands (middle, upper, lower)."""
        if len(self._price_history) < self.bollinger_period:
            return None, None, None
        
        # Calculate SMA (middle band)
        prices = [float(dp.close_price) for dp in self._price_history[-self.bollinger_period:]]
        sma = sum(prices) / len(prices)
        
        # Calculate standard deviation
        variance = sum((price - sma) ** 2 for price in prices) / len(prices)
        std_dev = math.sqrt(variance)
        
        # Calculate bands
        upper_band = sma + (self.bollinger_std_dev * std_dev)
        lower_band = sma - (self.bollinger_std_dev * std_dev)
        
        return sma, upper_band, lower_band
    
    def _calculate_price_mean(self, periods: int) -> Optional[float]:
        """Calculate price mean over specified periods."""
        if len(self._price_history) < periods:
            return None
        
        prices = [float(dp.close_price) for dp in self._price_history[-periods:]]
        return sum(prices) / len(prices)
    
    def _calculate_price_std(self, periods: int) -> Optional[float]:
        """Calculate price standard deviation over specified periods."""
        if len(self._price_history) < periods:
            return None
        
        prices = [float(dp.close_price) for dp in self._price_history[-periods:]]
        mean_price = sum(prices) / len(prices)
        
        variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
        return math.sqrt(variance)
    
    def _calculate_price_z_score(self, current_price: float) -> float:
        """Calculate Z-score of current price relative to historical mean."""
        price_mean = self._calculate_price_mean(self.lookback_period)
        price_std = self._calculate_price_std(self.lookback_period)
        
        if not price_mean or not price_std or price_std == 0:
            return 0.0
        
        return (current_price - price_mean) / price_std
    
    def _calculate_mean_reversion_score(self, current_price: float) -> float:
        """Calculate mean reversion score (0-1)."""
        z_score = abs(self._calculate_price_z_score(current_price))
        
        # Higher Z-score = higher mean reversion potential
        # Normalize to 0-1 range (3 std devs = max score)
        return min(z_score / 3.0, 1.0)
    
    def _calculate_reversion_probability(self, current_price: float) -> float:
        """Calculate probability of mean reversion based on historical patterns."""
        if len(self._price_history) < self.lookback_period * 2:
            return 0.5
        
        # Analyze historical mean reversion patterns
        reversion_count = 0
        total_extremes = 0
        
        # Look at historical extreme deviations
        for i in range(self.lookback_period, len(self._price_history) - 5):
            historical_prices = [float(dp.close_price) for dp in self._price_history[i-self.lookback_period:i]]
            mean_price = sum(historical_prices) / len(historical_prices)
            std_price = math.sqrt(sum((p - mean_price) ** 2 for p in historical_prices) / len(historical_prices))
            
            if std_price == 0:
                continue
            
            current_z = (float(self._price_history[i].close_price) - mean_price) / std_price
            
            # Check if this was an extreme deviation
            if abs(current_z) > self.mean_reversion_threshold:
                total_extremes += 1
                
                # Check if price reverted in next 5 periods
                future_prices = [float(dp.close_price) for dp in self._price_history[i+1:i+6]]
                if future_prices:
                    avg_future = sum(future_prices) / len(future_prices)
                    
                    # Check if price moved back toward mean
                    if current_z > 0 and avg_future < float(self._price_history[i].close_price):
                        reversion_count += 1
                    elif current_z < 0 and avg_future > float(self._price_history[i].close_price):
                        reversion_count += 1
        
        if total_extremes == 0:
            return 0.5
        
        base_probability = reversion_count / total_extremes
        
        # Adjust based on current Z-score extremity
        current_z = abs(self._calculate_price_z_score(current_price))
        extremity_bonus = min(current_z / 3.0, 0.2)  # Max 20% bonus
        
        return min(base_probability + extremity_bonus, 0.95)
    
    def _calculate_trend_strength(self) -> float:
        """Calculate overall trend strength (0-1)."""
        if len(self._price_history) < 20:
            return 0.0
        
        # Calculate trend using linear regression slope
        prices = [float(dp.close_price) for dp in self._price_history[-20:]]
        n = len(prices)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, prices))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Normalize slope to 0-1 range
        normalized_slope = abs(slope) / (y_mean / n) if y_mean > 0 else 0
        return min(normalized_slope, 1.0)
    
    def _check_trend_filter(self, indicators: TechnicalIndicators) -> bool:
        """Check if trend filter conditions are met."""
        if not self.trend_filter:
            return True
        
        # Allow mean reversion signals only in sideways or weak trend markets
        trend_strength = indicators.custom.get('trend_strength', 0)
        return trend_strength < 0.6  # Allow signals only in weak trend conditions
    
    def _check_volume_confirmation(self, indicators: TechnicalIndicators) -> bool:
        """Check if volume confirmation conditions are met."""
        if not self.volume_confirmation:
            return True
        
        # Require above-average volume for mean reversion signals
        return indicators.volume_ratio and indicators.volume_ratio > 0.8
    
    def _should_skip_consecutive_signal(self, direction: str) -> bool:
        """Check if we should skip this signal due to consecutive signal limits."""
        if self._last_signal_direction == direction:
            return self._consecutive_signals >= self.max_consecutive_signals
        return False
    
    def _update_consecutive_signals(self, direction: str):
        """Update consecutive signal tracking."""
        if self._last_signal_direction == direction:
            self._consecutive_signals += 1
        else:
            self._consecutive_signals = 1
            self._last_signal_direction = direction
    
    def _calculate_volume_sma(self, periods: int) -> Optional[float]:
        """Calculate volume simple moving average."""
        if len(self._price_history) < periods:
            return None
        
        volumes = []
        for data_point in self._price_history[-periods:]:
            if hasattr(data_point, 'volume') and data_point.volume:
                volumes.append(float(data_point.volume))
        
        return sum(volumes) / len(volumes) if volumes else None