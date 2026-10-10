"""Volatility-based trading strategy.

This strategy identifies trading opportunities based on volatility patterns,
volatility breakouts, and volatility mean reversion.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
import math

from .base_strategy import BaseStrategy, StrategySignal, TechnicalIndicators, StrategyConfig
from ..loaders.data_loader import HistoricalDataPoint


class VolatilityStrategyConfig(StrategyConfig):
    """Configuration for volatility strategy."""
    
    def __init__(self, **kwargs):
        # Set default parameters for volatility strategy
        default_params = {
            "volatility_period": 20,
            "volatility_threshold_high": 0.03,  # 3% high volatility threshold
            "volatility_threshold_low": 0.01,   # 1% low volatility threshold
            "atr_period": 14,
            "atr_multiplier": 2.0,
            "bollinger_period": 20,
            "bollinger_std_dev": 2.0,
            "rsi_period": 14,
            "volume_spike_threshold": 2.0,  # 2x average volume
            "breakout_confirmation_periods": 2,
            "volatility_regime_periods": 50,
            "min_price_move": 0.005,  # 0.5% minimum price move
            "strategy_mode": "breakout"  # "breakout" or "mean_reversion"
        }
        
        # Merge with provided parameters
        if 'parameters' in kwargs:
            default_params.update(kwargs['parameters'])
        kwargs['parameters'] = default_params
        
        # Set strategy-specific defaults
        kwargs.setdefault('name', 'VolatilityStrategy')
        kwargs.setdefault('description', 'Volatility-based strategy using ATR and volatility breakouts')
        kwargs.setdefault('min_confidence', 'MEDIUM')
        kwargs.setdefault('min_probability', 0.62)
        
        super().__init__(**kwargs)


class VolatilityStrategy(BaseStrategy):
    """Volatility trading strategy implementation.
    
    This strategy can operate in two modes:
    1. Breakout Mode: Trades volatility expansions and breakouts
    2. Mean Reversion Mode: Trades volatility contractions and reversions
    
    Signal Logic:
    - Breakout Mode: High volatility + price breakout + volume confirmation
    - Mean Reversion Mode: Low volatility + oversold/overbought + volatility expansion expected
    """
    
    def __init__(self, config: Optional[VolatilityStrategyConfig] = None):
        if config is None:
            config = VolatilityStrategyConfig()
        super().__init__(config)
        
        # Extract strategy parameters
        params = self.config.parameters
        self.volatility_period = params['volatility_period']
        self.volatility_threshold_high = params['volatility_threshold_high']
        self.volatility_threshold_low = params['volatility_threshold_low']
        self.atr_period = params['atr_period']
        self.atr_multiplier = params['atr_multiplier']
        self.bollinger_period = params['bollinger_period']
        self.bollinger_std_dev = params['bollinger_std_dev']
        self.rsi_period = params['rsi_period']
        self.volume_spike_threshold = params['volume_spike_threshold']
        self.breakout_confirmation_periods = params['breakout_confirmation_periods']
        self.volatility_regime_periods = params['volatility_regime_periods']
        self.min_price_move = params['min_price_move']
        self.strategy_mode = params['strategy_mode']
        
        # Track volatility regime
        self._volatility_regime = "NORMAL"  # LOW, NORMAL, HIGH
        self._last_volatility_update = None
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        """Generate volatility-based trading signal."""
        # Update data and calculate indicators
        self.update_data(data_point)
        
        # Need sufficient history for analysis
        required_history = max(self.volatility_period, self.atr_period, 
                             self.bollinger_period, self.volatility_regime_periods) + 5
        if len(self._price_history) < required_history:
            return None
        
        indicators = self.get_indicators()
        if not indicators:
            return None
        
        # Update volatility regime
        self._update_volatility_regime(indicators)
        
        # Analyze volatility conditions based on strategy mode
        if self.strategy_mode == "breakout":
            signal_direction = self._analyze_volatility_breakout(indicators, data_point)
        else:  # mean_reversion
            signal_direction = self._analyze_volatility_mean_reversion(indicators, data_point)
        
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
        """Calculate technical indicators for volatility analysis."""
        indicators = TechnicalIndicators()
        
        # Volatility measures
        indicators.volatility = self._calculate_volatility(self.volatility_period)
        indicators.atr = self._calculate_atr(self.atr_period)
        
        # Bollinger Bands for volatility context
        bb_middle, bb_upper, bb_lower = self._calculate_bollinger_bands()
        indicators.bb_middle = bb_middle
        indicators.bb_upper = bb_upper
        indicators.bb_lower = bb_lower
        
        # RSI for momentum context
        indicators.rsi = self._calculate_rsi(self.rsi_period)
        
        # Moving averages
        indicators.sma_20 = self._calculate_sma(20)
        
        # Price and volume analysis
        current_price = float(data_point.close_price)
        
        # Volume analysis
        if hasattr(data_point, 'volume') and data_point.volume:
            indicators.volume_sma = self._calculate_volume_sma(20)
            if indicators.volume_sma:
                indicators.volume_ratio = float(data_point.volume) / indicators.volume_sma
        
        # Custom volatility indicators
        indicators.custom = {
            'volatility_percentile': self._calculate_volatility_percentile(),
            'volatility_regime': self._volatility_regime,
            'atr_ratio': self._calculate_atr_ratio(),
            'price_efficiency': self._calculate_price_efficiency(),
            'volatility_breakout_score': self._calculate_volatility_breakout_score(current_price),
            'volatility_mean_reversion_score': self._calculate_volatility_mean_reversion_score(),
            'volume_volatility_correlation': self._calculate_volume_volatility_correlation()
        }
        
        return indicators
    
    def _analyze_volatility_breakout(self, indicators: TechnicalIndicators, 
                                   data_point: HistoricalDataPoint) -> Optional[str]:
        """Analyze volatility breakout conditions."""
        current_price = float(data_point.close_price)
        
        # Check volatility conditions
        if not indicators.volatility or not indicators.atr:
            return None
        
        # High volatility environment
        high_volatility = indicators.volatility > self.volatility_threshold_high
        
        # ATR breakout conditions
        atr_breakout = self._check_atr_breakout(indicators, current_price)
        
        # Bollinger Band breakout
        bb_breakout_direction = self._check_bollinger_breakout(indicators, current_price)
        
        # Volume confirmation
        volume_spike = (indicators.volume_ratio and 
                       indicators.volume_ratio > self.volume_spike_threshold)
        
        # Price momentum
        price_momentum = self._check_price_momentum(current_price)
        
        # Volatility regime support
        regime_support = self._volatility_regime in ["NORMAL", "HIGH"]
        
        # UP breakout conditions
        up_conditions = [
            high_volatility or atr_breakout,
            bb_breakout_direction == "UP",
            volume_spike,
            price_momentum == "UP",
            regime_support
        ]
        
        # DOWN breakout conditions
        down_conditions = [
            high_volatility or atr_breakout,
            bb_breakout_direction == "DOWN",
            volume_spike,
            price_momentum == "DOWN",
            regime_support
        ]
        
        # Check conditions (require at least 3 out of 5)
        if sum(up_conditions) >= 3:
            return "UP"
        elif sum(down_conditions) >= 3:
            return "DOWN"
        
        return None
    
    def _analyze_volatility_mean_reversion(self, indicators: TechnicalIndicators, 
                                         data_point: HistoricalDataPoint) -> Optional[str]:
        """Analyze volatility mean reversion conditions."""
        current_price = float(data_point.close_price)
        
        # Check volatility conditions
        if not indicators.volatility:
            return None
        
        # Low volatility environment (expecting expansion)
        low_volatility = indicators.volatility < self.volatility_threshold_low
        
        # Volatility percentile
        vol_percentile = indicators.custom.get('volatility_percentile', 0.5)
        low_vol_percentile = vol_percentile < 0.3  # Bottom 30%
        
        # Price at extremes (expecting reversion)
        price_extreme = self._check_price_extremes(indicators, current_price)
        
        # RSI extremes
        rsi_extreme = None
        if indicators.rsi:
            if indicators.rsi < 30:
                rsi_extreme = "OVERSOLD"
            elif indicators.rsi > 70:
                rsi_extreme = "OVERBOUGHT"
        
        # Volatility expansion signals
        vol_expansion_expected = low_volatility or low_vol_percentile
        
        # UP signal conditions (oversold + low volatility)
        if (vol_expansion_expected and 
            (price_extreme == "OVERSOLD" or rsi_extreme == "OVERSOLD")):
            return "UP"
        
        # DOWN signal conditions (overbought + low volatility)
        if (vol_expansion_expected and 
            (price_extreme == "OVERBOUGHT" or rsi_extreme == "OVERBOUGHT")):
            return "DOWN"
        
        return None
    
    def _calculate_signal_strength(self, indicators: TechnicalIndicators, 
                                 direction: str) -> tuple[str, float]:
        """Calculate signal confidence and probability."""
        strength_score = 0.0
        max_score = 0.0
        
        # Volatility strength
        if indicators.volatility:
            if self.strategy_mode == "breakout":
                vol_strength = min(indicators.volatility / self.volatility_threshold_high, 2.0)
            else:
                vol_strength = max(0, (self.volatility_threshold_low - indicators.volatility) / self.volatility_threshold_low + 1)
            strength_score += vol_strength * 20  # Max 40 points for breakout, 20 for mean reversion
            max_score += 40 if self.strategy_mode == "breakout" else 20
        
        # ATR strength
        atr_ratio = indicators.custom.get('atr_ratio', 1.0)
        atr_strength = min(atr_ratio, 2.0) if self.strategy_mode == "breakout" else max(0, 2.0 - atr_ratio)
        strength_score += atr_strength * 15  # Max 30 points for breakout, 15 for mean reversion
        max_score += 30 if self.strategy_mode == "breakout" else 15
        
        # Volume confirmation strength
        if indicators.volume_ratio:
            vol_strength = min(indicators.volume_ratio / self.volume_spike_threshold, 2.0)
            strength_score += vol_strength * 15  # Max 30 points
            max_score += 30
        
        # Volatility regime alignment
        regime_score = 0
        if self.strategy_mode == "breakout":
            if self._volatility_regime == "HIGH":
                regime_score = 20
            elif self._volatility_regime == "NORMAL":
                regime_score = 10
        else:  # mean_reversion
            if self._volatility_regime == "LOW":
                regime_score = 20
            elif self._volatility_regime == "NORMAL":
                regime_score = 10
        
        strength_score += regime_score
        max_score += 20
        
        # Strategy-specific scores
        if self.strategy_mode == "breakout":
            breakout_score = indicators.custom.get('volatility_breakout_score', 0)
            strength_score += breakout_score * 15  # Max 15 points
            max_score += 15
        else:
            mean_reversion_score = indicators.custom.get('volatility_mean_reversion_score', 0)
            strength_score += mean_reversion_score * 15  # Max 15 points
            max_score += 15
        
        # Calculate final scores
        if max_score > 0:
            normalized_score = strength_score / max_score
        else:
            normalized_score = 0.5
        
        # Determine confidence level
        if normalized_score >= 0.8:
            confidence = "HIGH"
            probability = 0.72 + (normalized_score - 0.8) * 0.65  # 0.72-0.85
        elif normalized_score >= 0.6:
            confidence = "MEDIUM"
            probability = 0.62 + (normalized_score - 0.6) * 0.5  # 0.62-0.72
        else:
            confidence = "LOW"
            probability = 0.52 + normalized_score * 0.17  # 0.52-0.62
        
        return confidence, min(probability, 0.90)
    
    def _generate_signal_reason(self, indicators: TechnicalIndicators, 
                              direction: str) -> str:
        """Generate human-readable signal reason."""
        reasons = []
        
        # Volatility analysis
        if indicators.volatility:
            vol_pct = indicators.volatility * 100
            reasons.append(f"Current volatility: {vol_pct:.2f}%")
        
        # Volatility regime
        regime = indicators.custom.get('volatility_regime', 'UNKNOWN')
        reasons.append(f"Volatility regime: {regime}")
        
        # Strategy mode specific reasons
        if self.strategy_mode == "breakout":
            breakout_score = indicators.custom.get('volatility_breakout_score', 0)
            reasons.append(f"Breakout score: {breakout_score:.2f}")
            
            if indicators.volume_ratio:
                reasons.append(f"Volume spike: {indicators.volume_ratio:.1f}x average")
        else:
            mean_reversion_score = indicators.custom.get('volatility_mean_reversion_score', 0)
            reasons.append(f"Mean reversion score: {mean_reversion_score:.2f}")
            
            vol_percentile = indicators.custom.get('volatility_percentile', 0.5)
            reasons.append(f"Volatility percentile: {vol_percentile:.1%}")
        
        # ATR analysis
        atr_ratio = indicators.custom.get('atr_ratio', 1.0)
        reasons.append(f"ATR ratio: {atr_ratio:.2f}")
        
        return "; ".join(reasons)
    
    def _get_conditions_met(self, indicators: TechnicalIndicators, 
                          direction: str) -> List[str]:
        """Get list of conditions that were met for the signal."""
        conditions = []
        
        # Volatility conditions
        if indicators.volatility:
            if self.strategy_mode == "breakout":
                if indicators.volatility > self.volatility_threshold_high:
                    conditions.append("HIGH_VOLATILITY")
            else:
                if indicators.volatility < self.volatility_threshold_low:
                    conditions.append("LOW_VOLATILITY")
        
        # Volume conditions
        if indicators.volume_ratio and indicators.volume_ratio > self.volume_spike_threshold:
            conditions.append("VOLUME_SPIKE")
        
        # ATR conditions
        atr_ratio = indicators.custom.get('atr_ratio', 1.0)
        if atr_ratio > 1.5:
            conditions.append("ATR_EXPANSION")
        
        # Volatility regime
        regime = indicators.custom.get('volatility_regime', 'UNKNOWN')
        conditions.append(f"VOLATILITY_REGIME_{regime}")
        
        # Strategy-specific conditions
        if self.strategy_mode == "breakout":
            breakout_score = indicators.custom.get('volatility_breakout_score', 0)
            if breakout_score > 0.7:
                conditions.append("STRONG_BREAKOUT_SIGNAL")
        else:
            vol_percentile = indicators.custom.get('volatility_percentile', 0.5)
            if vol_percentile < 0.3:
                conditions.append("LOW_VOLATILITY_PERCENTILE")
        
        return conditions
    
    def _assess_risk_level(self, indicators: TechnicalIndicators) -> str:
        """Assess risk level based on volatility conditions."""
        risk_factors = 0
        
        # Extreme volatility increases risk
        if indicators.volatility:
            if indicators.volatility > 0.05:  # 5% volatility
                risk_factors += 2
            elif indicators.volatility > 0.03:  # 3% volatility
                risk_factors += 1
        
        # Volatility regime risk
        regime = indicators.custom.get('volatility_regime', 'NORMAL')
        if regime == "HIGH":
            risk_factors += 1
        
        # Volume risk
        if indicators.volume_ratio:
            if indicators.volume_ratio > 5.0:  # Extreme volume spike
                risk_factors += 1
            elif indicators.volume_ratio < 0.5:  # Very low volume
                risk_factors += 1
        
        # ATR risk
        atr_ratio = indicators.custom.get('atr_ratio', 1.0)
        if atr_ratio > 3.0:
            risk_factors += 1
        
        if risk_factors >= 3:
            return "HIGH"
        elif risk_factors >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_atr(self, periods: int) -> Optional[float]:
        """Calculate Average True Range."""
        if len(self._price_history) < periods + 1:
            return None
        
        true_ranges = []
        for i in range(len(self._price_history) - periods, len(self._price_history)):
            if i == 0:
                continue
            
            current = self._price_history[i]
            previous = self._price_history[i-1]
            
            high = float(current.high_price) if hasattr(current, 'high_price') else float(current.close_price)
            low = float(current.low_price) if hasattr(current, 'low_price') else float(current.close_price)
            prev_close = float(previous.close_price)
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_ranges.append(max(tr1, tr2, tr3))
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else None
    
    def _calculate_bollinger_bands(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands."""
        if len(self._price_history) < self.bollinger_period:
            return None, None, None
        
        prices = [float(dp.close_price) for dp in self._price_history[-self.bollinger_period:]]
        sma = sum(prices) / len(prices)
        
        variance = sum((price - sma) ** 2 for price in prices) / len(prices)
        std_dev = math.sqrt(variance)
        
        upper_band = sma + (self.bollinger_std_dev * std_dev)
        lower_band = sma - (self.bollinger_std_dev * std_dev)
        
        return sma, upper_band, lower_band
    
    def _calculate_volatility_percentile(self) -> float:
        """Calculate current volatility percentile over historical period."""
        if len(self._price_history) < self.volatility_regime_periods:
            return 0.5
        
        # Calculate historical volatilities
        historical_vols = []
        for i in range(self.volatility_period, len(self._price_history) - self.volatility_period + 1):
            period_prices = [float(dp.close_price) for dp in 
                           self._price_history[i-self.volatility_period:i]]
            if len(period_prices) >= 2:
                returns = [(period_prices[j] - period_prices[j-1]) / period_prices[j-1] 
                          for j in range(1, len(period_prices))]
                vol = math.sqrt(sum(r**2 for r in returns) / len(returns)) if returns else 0
                historical_vols.append(vol)
        
        if not historical_vols:
            return 0.5
        
        current_vol = self._calculate_volatility(self.volatility_period) or 0
        
        # Calculate percentile
        lower_count = sum(1 for vol in historical_vols if vol < current_vol)
        return lower_count / len(historical_vols)
    
    def _calculate_atr_ratio(self) -> float:
        """Calculate current ATR relative to historical average."""
        current_atr = self._calculate_atr(self.atr_period)
        if not current_atr:
            return 1.0
        
        # Calculate historical ATR average
        if len(self._price_history) < self.atr_period * 3:
            return 1.0
        
        historical_atrs = []
        for i in range(self.atr_period * 2, len(self._price_history) - self.atr_period + 1, 5):
            period_data = self._price_history[i-self.atr_period:i]
            if len(period_data) >= self.atr_period:
                # Temporarily set price history for ATR calculation
                temp_history = self._price_history
                self._price_history = period_data
                atr = self._calculate_atr(self.atr_period)
                self._price_history = temp_history
                
                if atr:
                    historical_atrs.append(atr)
        
        if not historical_atrs:
            return 1.0
        
        avg_atr = sum(historical_atrs) / len(historical_atrs)
        return current_atr / avg_atr if avg_atr > 0 else 1.0
    
    def _calculate_price_efficiency(self) -> float:
        """Calculate price movement efficiency (0-1)."""
        if len(self._price_history) < 10:
            return 0.5
        
        # Calculate net price movement vs total price movement
        prices = [float(dp.close_price) for dp in self._price_history[-10:]]
        
        net_movement = abs(prices[-1] - prices[0])
        total_movement = sum(abs(prices[i] - prices[i-1]) for i in range(1, len(prices)))
        
        return net_movement / total_movement if total_movement > 0 else 0
    
    def _calculate_volatility_breakout_score(self, current_price: float) -> float:
        """Calculate volatility breakout score (0-1)."""
        score = 0.0
        
        # ATR breakout component
        atr_ratio = self._calculate_atr_ratio()
        score += min(atr_ratio / 2.0, 0.4)  # Max 0.4
        
        # Volatility percentile component
        vol_percentile = self._calculate_volatility_percentile()
        score += vol_percentile * 0.3  # Max 0.3
        
        # Price efficiency component (trending vs choppy)
        price_efficiency = self._calculate_price_efficiency()
        score += price_efficiency * 0.3  # Max 0.3
        
        return min(score, 1.0)
    
    def _calculate_volatility_mean_reversion_score(self) -> float:
        """Calculate volatility mean reversion score (0-1)."""
        score = 0.0
        
        # Low volatility percentile component
        vol_percentile = self._calculate_volatility_percentile()
        score += max(0, (0.5 - vol_percentile) * 2) * 0.4  # Max 0.4
        
        # ATR compression component
        atr_ratio = self._calculate_atr_ratio()
        score += max(0, (1.5 - atr_ratio) / 1.5) * 0.3  # Max 0.3
        
        # Time since last volatility spike
        score += 0.3  # Simplified - could track actual time since spike
        
        return min(score, 1.0)
    
    def _calculate_volume_volatility_correlation(self) -> float:
        """Calculate correlation between volume and volatility."""
        if len(self._price_history) < 20:
            return 0.0
        
        # Simplified correlation calculation
        # In practice, you'd calculate proper correlation coefficient
        recent_data = self._price_history[-20:]
        
        volume_increases = 0
        volatility_increases = 0
        
        for i in range(1, len(recent_data)):
            if hasattr(recent_data[i], 'volume') and hasattr(recent_data[i-1], 'volume'):
                if recent_data[i].volume > recent_data[i-1].volume:
                    volume_increases += 1
            
            # Simple volatility proxy using price range
            current_range = abs(float(recent_data[i].close_price) - float(recent_data[i-1].close_price))
            prev_range = abs(float(recent_data[i-1].close_price) - float(recent_data[i-2].close_price)) if i > 1 else current_range
            
            if current_range > prev_range:
                volatility_increases += 1
        
        # Simple correlation proxy
        return min(volume_increases, volatility_increases) / max(volume_increases, volatility_increases, 1)
    
    def _update_volatility_regime(self, indicators: TechnicalIndicators):
        """Update volatility regime classification."""
        if not indicators.volatility:
            return
        
        vol_percentile = indicators.custom.get('volatility_percentile', 0.5)
        
        if vol_percentile > 0.7:
            self._volatility_regime = "HIGH"
        elif vol_percentile < 0.3:
            self._volatility_regime = "LOW"
        else:
            self._volatility_regime = "NORMAL"
        
        self._last_volatility_update = datetime.now()
    
    def _check_atr_breakout(self, indicators: TechnicalIndicators, current_price: float) -> bool:
        """Check if current price represents an ATR breakout."""
        if not indicators.atr or not indicators.sma_20:
            return False
        
        atr_distance = indicators.atr * self.atr_multiplier
        upper_threshold = indicators.sma_20 + atr_distance
        lower_threshold = indicators.sma_20 - atr_distance
        
        return current_price > upper_threshold or current_price < lower_threshold
    
    def _check_bollinger_breakout(self, indicators: TechnicalIndicators, 
                                 current_price: float) -> Optional[str]:
        """Check Bollinger Band breakout direction."""
        if not (indicators.bb_upper and indicators.bb_lower):
            return None
        
        if current_price > indicators.bb_upper:
            return "UP"
        elif current_price < indicators.bb_lower:
            return "DOWN"
        
        return None
    
    def _check_price_momentum(self, current_price: float) -> Optional[str]:
        """Check price momentum direction."""
        if len(self._price_history) < 3:
            return None
        
        recent_prices = [float(dp.close_price) for dp in self._price_history[-3:]]
        
        # Check if price is moving consistently in one direction
        if recent_prices[-1] > recent_prices[-2] > recent_prices[-3]:
            return "UP"
        elif recent_prices[-1] < recent_prices[-2] < recent_prices[-3]:
            return "DOWN"
        
        return None
    
    def _check_price_extremes(self, indicators: TechnicalIndicators, 
                            current_price: float) -> Optional[str]:
        """Check if price is at extreme levels."""
        if not (indicators.bb_upper and indicators.bb_lower):
            return None
        
        bb_range = indicators.bb_upper - indicators.bb_lower
        if bb_range == 0:
            return None
        
        position = (current_price - indicators.bb_lower) / bb_range
        
        if position < 0.1:  # Bottom 10%
            return "OVERSOLD"
        elif position > 0.9:  # Top 10%
            return "OVERBOUGHT"
        
        return None
    
    def _calculate_volume_sma(self, periods: int) -> Optional[float]:
        """Calculate volume simple moving average."""
        if len(self._price_history) < periods:
            return None
        
        volumes = []
        for data_point in self._price_history[-periods:]:
            if hasattr(data_point, 'volume') and data_point.volume:
                volumes.append(float(data_point.volume))
        
        return sum(volumes) / len(volumes) if volumes else None