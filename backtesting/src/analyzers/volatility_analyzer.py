"""Volatility Analysis and Trend Reversal Detection.

This module provides advanced volatility analysis and trend reversal detection
specifically optimized for short-term event contract trading, including
real-time volatility calculation, breakout detection, and reversal signals.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from enum import Enum
from dataclasses import dataclass

import numpy as np
from scipy import stats
from pydantic import BaseModel, Field, validator
import structlog

from ..loaders.binance_event_data_processor import ProcessedDataPoint, TimeFrame


logger = structlog.get_logger(__name__)


class VolatilityRegime(str, Enum):
    """Volatility regime classification."""
    LOW = "LOW"              # Low volatility, range-bound
    NORMAL = "NORMAL"        # Normal volatility
    HIGH = "HIGH"            # High volatility, trending
    EXTREME = "EXTREME"      # Extreme volatility, chaotic


class TrendDirection(str, Enum):
    """Trend direction classification."""
    STRONG_UP = "STRONG_UP"      # Strong upward trend
    WEAK_UP = "WEAK_UP"          # Weak upward trend
    SIDEWAYS = "SIDEWAYS"        # No clear trend
    WEAK_DOWN = "WEAK_DOWN"      # Weak downward trend
    STRONG_DOWN = "STRONG_DOWN"  # Strong downward trend


class ReversalType(str, Enum):
    """Type of trend reversal."""
    BULLISH_REVERSAL = "BULLISH_REVERSAL"    # Trend reversing to upward
    BEARISH_REVERSAL = "BEARISH_REVERSAL"    # Trend reversing to downward
    FALSE_BREAKOUT = "FALSE_BREAKOUT"        # Failed breakout
    CONTINUATION = "CONTINUATION"            # Trend continuation


class BreakoutType(str, Enum):
    """Type of price breakout."""
    UPWARD_BREAKOUT = "UPWARD_BREAKOUT"      # Breaking resistance
    DOWNWARD_BREAKOUT = "DOWNWARD_BREAKOUT"  # Breaking support
    RANGE_BREAKOUT = "RANGE_BREAKOUT"        # Breaking out of range
    VOLUME_BREAKOUT = "VOLUME_BREAKOUT"      # Volume-driven breakout


@dataclass
class VolatilityMetrics:
    """Volatility calculation results."""
    timestamp: datetime
    
    # Basic volatility measures
    realized_volatility: Decimal      # Historical volatility
    intraday_volatility: Decimal      # High-low range volatility
    close_to_close_volatility: Decimal  # Close-to-close volatility
    
    # Advanced measures
    garch_volatility: Optional[Decimal] = None  # GARCH model volatility
    parkinson_volatility: Decimal = Decimal('0')  # Parkinson estimator
    garman_klass_volatility: Decimal = Decimal('0')  # Garman-Klass estimator
    
    # Regime classification
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL
    volatility_percentile: Decimal = Decimal('50')  # Percentile vs historical
    
    # Trend analysis
    trend_strength: Decimal = Decimal('0')  # 0-1 scale
    trend_direction: TrendDirection = TrendDirection.SIDEWAYS
    

class ReversalSignal(BaseModel):
    """Trend reversal signal."""
    
    timestamp: datetime
    symbol: str
    
    # Reversal details
    reversal_type: ReversalType
    confidence_score: Decimal  # 0.0 to 1.0
    strength: Decimal         # Signal strength 0.0 to 1.0
    
    # Price levels
    trigger_price: Decimal
    support_level: Optional[Decimal] = None
    resistance_level: Optional[Decimal] = None
    
    # Technical indicators
    rsi_value: Optional[Decimal] = None
    macd_divergence: bool = False
    volume_confirmation: bool = False
    
    # Pattern recognition
    pattern_name: Optional[str] = None
    pattern_completion: Decimal = Decimal('0')  # 0-1 scale
    
    # Risk assessment
    false_signal_probability: Decimal = Decimal('0.5')
    expected_move_percentage: Decimal = Decimal('0')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }


class BreakoutSignal(BaseModel):
    """Price breakout signal."""
    
    timestamp: datetime
    symbol: str
    
    # Breakout details
    breakout_type: BreakoutType
    breakout_level: Decimal
    breakout_strength: Decimal  # 0.0 to 1.0
    
    # Volume analysis
    volume_ratio: Decimal       # Current vs average volume
    volume_confirmation: bool   # Volume supports breakout
    
    # Price action
    price_momentum: Decimal     # Price momentum score
    range_size: Decimal         # Size of broken range
    time_in_range: int          # Minutes spent in range before breakout
    
    # Targets and stops
    target_price: Optional[Decimal] = None
    stop_loss_level: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }


class VolatilityAnalyzerConfig(BaseModel):
    """Configuration for volatility analyzer."""
    
    # Volatility calculation periods
    short_period: int = 10      # Short-term volatility period
    medium_period: int = 20     # Medium-term volatility period
    long_period: int = 50       # Long-term volatility period
    
    # Volatility thresholds
    low_volatility_threshold: Decimal = Decimal('0.01')    # 1%
    high_volatility_threshold: Decimal = Decimal('0.05')   # 5%
    extreme_volatility_threshold: Decimal = Decimal('0.10') # 10%
    
    # Trend analysis
    trend_period: int = 20      # Period for trend analysis
    trend_strength_threshold: Decimal = Decimal('0.6')     # Minimum trend strength
    
    # Reversal detection
    reversal_lookback: int = 10         # Periods to look back for reversals
    min_reversal_confidence: Decimal = Decimal('0.7')  # Minimum confidence
    
    # Breakout detection
    breakout_lookback: int = 20         # Periods for range identification
    min_breakout_volume_ratio: Decimal = Decimal('1.5')  # 1.5x average volume
    breakout_confirmation_periods: int = 3  # Periods to confirm breakout
    
    # Advanced features
    use_garch_model: bool = False       # Enable GARCH volatility modeling
    enable_pattern_recognition: bool = True  # Enable chart pattern recognition
    
    @validator('short_period', 'medium_period', 'long_period', 'trend_period')
    def validate_periods(cls, v):
        if not 5 <= v <= 200:
            raise ValueError('Periods must be between 5 and 200')
        return v


class VolatilityAnalyzer:
    """Advanced volatility analysis and trend reversal detection."""
    
    def __init__(self, config: VolatilityAnalyzerConfig):
        self.config = config
        self._volatility_history: List[VolatilityMetrics] = []
        self._price_history: List[ProcessedDataPoint] = []
        
        logger.info(
            "VolatilityAnalyzer initialized",
            short_period=config.short_period,
            high_vol_threshold=float(config.high_volatility_threshold)
        )
    
    def update_data(self, data_point: ProcessedDataPoint) -> None:
        """Update analyzer with new market data.
        
        Args:
            data_point: New market data point
        """
        self._price_history.append(data_point)
        
        # Keep only required history
        max_history = max(self.config.long_period, self.config.breakout_lookback) * 2
        if len(self._price_history) > max_history:
            self._price_history = self._price_history[-max_history:]
    
    def calculate_volatility_metrics(self, data_point: ProcessedDataPoint) -> VolatilityMetrics:
        """Calculate comprehensive volatility metrics.
        
        Args:
            data_point: Current data point
            
        Returns:
            VolatilityMetrics with calculated values
        """
        if len(self._price_history) < self.config.short_period:
            return VolatilityMetrics(
                timestamp=data_point.timestamp,
                realized_volatility=Decimal('0'),
                intraday_volatility=Decimal('0'),
                close_to_close_volatility=Decimal('0')
            )
        
        # Calculate different volatility measures
        realized_vol = self._calculate_realized_volatility(self.config.medium_period)
        intraday_vol = self._calculate_intraday_volatility(self.config.short_period)
        close_vol = self._calculate_close_to_close_volatility(self.config.medium_period)
        
        # Advanced volatility estimators
        parkinson_vol = self._calculate_parkinson_volatility(self.config.medium_period)
        gk_vol = self._calculate_garman_klass_volatility(self.config.medium_period)
        
        # Determine volatility regime
        vol_regime = self._classify_volatility_regime(realized_vol)
        vol_percentile = self._calculate_volatility_percentile(realized_vol)
        
        # Trend analysis
        trend_strength, trend_direction = self._analyze_trend_strength()
        
        metrics = VolatilityMetrics(
            timestamp=data_point.timestamp,
            realized_volatility=realized_vol,
            intraday_volatility=intraday_vol,
            close_to_close_volatility=close_vol,
            parkinson_volatility=parkinson_vol,
            garman_klass_volatility=gk_vol,
            volatility_regime=vol_regime,
            volatility_percentile=vol_percentile,
            trend_strength=trend_strength,
            trend_direction=trend_direction
        )
        
        self._volatility_history.append(metrics)
        
        # Keep volatility history manageable
        if len(self._volatility_history) > 1000:
            self._volatility_history = self._volatility_history[-500:]
        
        return metrics
    
    def _calculate_realized_volatility(self, period: int) -> Decimal:
        """Calculate realized volatility using close-to-close returns."""
        if len(self._price_history) < period + 1:
            return Decimal('0')
        
        returns = []
        for i in range(len(self._price_history) - period, len(self._price_history)):
            if i > 0:
                current_price = float(self._price_history[i].close_price)
                previous_price = float(self._price_history[i-1].close_price)
                if previous_price > 0:
                    return_val = np.log(current_price / previous_price)
                    returns.append(return_val)
        
        if len(returns) < 2:
            return Decimal('0')
        
        # Calculate standard deviation and annualize
        std_dev = np.std(returns, ddof=1)
        # Annualize assuming 1440 minutes per day, 365 days per year
        annualized_vol = std_dev * np.sqrt(1440 * 365)
        
        return Decimal(str(annualized_vol)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def _calculate_intraday_volatility(self, period: int) -> Decimal:
        """Calculate intraday volatility using high-low ranges."""
        if len(self._price_history) < period:
            return Decimal('0')
        
        ranges = []
        for i in range(len(self._price_history) - period, len(self._price_history)):
            data_point = self._price_history[i]
            high = float(data_point.high_price)
            low = float(data_point.low_price)
            close = float(data_point.close_price)
            
            if close > 0:
                range_pct = (high - low) / close
                ranges.append(range_pct)
        
        if not ranges:
            return Decimal('0')
        
        avg_range = np.mean(ranges)
        return Decimal(str(avg_range)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def _calculate_close_to_close_volatility(self, period: int) -> Decimal:
        """Calculate close-to-close volatility."""
        if len(self._price_history) < period + 1:
            return Decimal('0')
        
        price_changes = []
        for i in range(len(self._price_history) - period, len(self._price_history)):
            if i > 0:
                current_close = float(self._price_history[i].close_price)
                previous_close = float(self._price_history[i-1].close_price)
                if previous_close > 0:
                    change_pct = (current_close - previous_close) / previous_close
                    price_changes.append(change_pct)
        
        if len(price_changes) < 2:
            return Decimal('0')
        
        std_dev = np.std(price_changes, ddof=1)
        return Decimal(str(std_dev)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def _calculate_parkinson_volatility(self, period: int) -> Decimal:
        """Calculate Parkinson volatility estimator.
        
        Parkinson volatility = sqrt(1/n * sum(ln(Hi/Li)^2) / (4*ln(2)))
        """
        if len(self._price_history) < period:
            return Decimal('0')
        
        log_hl_ratios = []
        for i in range(len(self._price_history) - period, len(self._price_history)):
            data_point = self._price_history[i]
            high = float(data_point.high_price)
            low = float(data_point.low_price)
            
            if low > 0:
                log_ratio = np.log(high / low)
                log_hl_ratios.append(log_ratio ** 2)
        
        if not log_hl_ratios:
            return Decimal('0')
        
        mean_log_ratio = np.mean(log_hl_ratios)
        parkinson_vol = np.sqrt(mean_log_ratio / (4 * np.log(2)))
        
        return Decimal(str(parkinson_vol)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def _calculate_garman_klass_volatility(self, period: int) -> Decimal:
        """Calculate Garman-Klass volatility estimator."""
        if len(self._price_history) < period + 1:
            return Decimal('0')
        
        gk_values = []
        for i in range(len(self._price_history) - period, len(self._price_history)):
            if i > 0:
                data_point = self._price_history[i]
                prev_close = float(self._price_history[i-1].close_price)
                open_price = float(data_point.open_price)
                high = float(data_point.high_price)
                low = float(data_point.low_price)
                close = float(data_point.close_price)
                
                if prev_close > 0 and low > 0:
                    # Garman-Klass formula
                    term1 = 0.5 * (np.log(high / low)) ** 2
                    term2 = (2 * np.log(2) - 1) * (np.log(close / open)) ** 2
                    gk_value = term1 - term2
                    gk_values.append(gk_value)
        
        if not gk_values:
            return Decimal('0')
        
        gk_vol = np.sqrt(np.mean(gk_values))
        return Decimal(str(gk_vol)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def _classify_volatility_regime(self, volatility: Decimal) -> VolatilityRegime:
        """Classify current volatility regime."""
        if volatility <= self.config.low_volatility_threshold:
            return VolatilityRegime.LOW
        elif volatility <= self.config.high_volatility_threshold:
            return VolatilityRegime.NORMAL
        elif volatility <= self.config.extreme_volatility_threshold:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    def _calculate_volatility_percentile(self, current_volatility: Decimal) -> Decimal:
        """Calculate percentile of current volatility vs historical."""
        if len(self._volatility_history) < 10:
            return Decimal('50')  # Default to median
        
        historical_vols = [float(vm.realized_volatility) for vm in self._volatility_history[-100:]]
        current_vol = float(current_volatility)
        
        percentile = stats.percentileofscore(historical_vols, current_vol)
        return Decimal(str(percentile)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    
    def _analyze_trend_strength(self) -> Tuple[Decimal, TrendDirection]:
        """Analyze trend strength and direction."""
        if len(self._price_history) < self.config.trend_period:
            return Decimal('0'), TrendDirection.SIDEWAYS
        
        # Get recent prices
        recent_data = self._price_history[-self.config.trend_period:]
        prices = [float(dp.close_price) for dp in recent_data]
        
        # Calculate linear regression
        x = np.arange(len(prices))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)
        
        # Calculate trend strength (R-squared)
        trend_strength = Decimal(str(abs(r_value))).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        
        # Determine trend direction
        if trend_strength < Decimal('0.3'):
            direction = TrendDirection.SIDEWAYS
        elif slope > 0:
            if trend_strength >= Decimal('0.7'):
                direction = TrendDirection.STRONG_UP
            else:
                direction = TrendDirection.WEAK_UP
        else:
            if trend_strength >= Decimal('0.7'):
                direction = TrendDirection.STRONG_DOWN
            else:
                direction = TrendDirection.WEAK_DOWN
        
        return trend_strength, direction
    
    def detect_trend_reversal(self, current_data: ProcessedDataPoint) -> Optional[ReversalSignal]:
        """Detect potential trend reversal signals.
        
        Args:
            current_data: Current market data point
            
        Returns:
            ReversalSignal if reversal detected, None otherwise
        """
        if len(self._price_history) < self.config.reversal_lookback * 2:
            return None
        
        # Get current volatility metrics
        vol_metrics = self.calculate_volatility_metrics(current_data)
        
        # Check for divergence patterns
        price_divergence = self._detect_price_divergence()
        volume_divergence = self._detect_volume_divergence()
        
        # Check for reversal patterns
        reversal_pattern = self._detect_reversal_patterns(current_data)
        
        if not (price_divergence or volume_divergence or reversal_pattern):
            return None
        
        # Calculate confidence score
        confidence = self._calculate_reversal_confidence(
            price_divergence, volume_divergence, reversal_pattern, vol_metrics
        )
        
        if confidence < self.config.min_reversal_confidence:
            return None
        
        # Determine reversal type
        if vol_metrics.trend_direction in [TrendDirection.STRONG_DOWN, TrendDirection.WEAK_DOWN]:
            reversal_type = ReversalType.BULLISH_REVERSAL
        elif vol_metrics.trend_direction in [TrendDirection.STRONG_UP, TrendDirection.WEAK_UP]:
            reversal_type = ReversalType.BEARISH_REVERSAL
        else:
            reversal_type = ReversalType.CONTINUATION
        
        # Calculate support/resistance levels
        support, resistance = self._calculate_support_resistance_levels()
        
        return ReversalSignal(
            timestamp=current_data.timestamp,
            symbol=current_data.symbol,
            reversal_type=reversal_type,
            confidence_score=confidence,
            strength=vol_metrics.trend_strength,
            trigger_price=current_data.close_price,
            support_level=support,
            resistance_level=resistance,
            rsi_value=current_data.rsi_14,
            macd_divergence=price_divergence,
            volume_confirmation=volume_divergence,
            pattern_name=reversal_pattern,
            false_signal_probability=Decimal('1.0') - confidence
        )
    
    def _detect_price_divergence(self) -> bool:
        """Detect price divergence patterns."""
        if len(self._price_history) < self.config.reversal_lookback * 2:
            return False
        
        # Simple divergence detection - compare recent highs/lows with price momentum
        recent_data = self._price_history[-self.config.reversal_lookback:]
        older_data = self._price_history[-self.config.reversal_lookback*2:-self.config.reversal_lookback]
        
        recent_high = max(float(dp.high_price) for dp in recent_data)
        recent_low = min(float(dp.low_price) for dp in recent_data)
        older_high = max(float(dp.high_price) for dp in older_data)
        older_low = min(float(dp.low_price) for dp in older_data)
        
        # Bullish divergence: lower lows in price but higher momentum
        # Bearish divergence: higher highs in price but lower momentum
        
        # Simplified check - would need more sophisticated momentum indicators
        price_trend_up = recent_high > older_high
        price_trend_down = recent_low < older_low
        
        return price_trend_up or price_trend_down
    
    def _detect_volume_divergence(self) -> bool:
        """Detect volume divergence patterns."""
        if len(self._price_history) < self.config.reversal_lookback:
            return False
        
        recent_data = self._price_history[-self.config.reversal_lookback:]
        
        # Calculate average volume for recent periods
        recent_volumes = [float(dp.volume) for dp in recent_data]
        avg_volume = np.mean(recent_volumes)
        
        # Check if recent volume is significantly different from average
        current_volume = float(self._price_history[-1].volume)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Volume divergence if volume is 50% above or below average
        return volume_ratio > 1.5 or volume_ratio < 0.5
    
    def _detect_reversal_patterns(self, current_data: ProcessedDataPoint) -> Optional[str]:
        """Detect chart reversal patterns."""
        if not self.config.enable_pattern_recognition:
            return None
        
        if len(self._price_history) < 10:
            return None
        
        # Simple pattern detection - would be expanded with more sophisticated patterns
        recent_data = self._price_history[-10:]
        
        # Doji pattern detection
        current_open = float(current_data.open_price)
        current_close = float(current_data.close_price)
        current_high = float(current_data.high_price)
        current_low = float(current_data.low_price)
        
        body_size = abs(current_close - current_open)
        total_range = current_high - current_low
        
        if total_range > 0 and body_size / total_range < 0.1:
            return "DOJI"
        
        # Hammer/Hanging Man pattern
        lower_shadow = min(current_open, current_close) - current_low
        upper_shadow = current_high - max(current_open, current_close)
        
        if (lower_shadow > body_size * 2 and upper_shadow < body_size * 0.5):
            return "HAMMER" if current_close > current_open else "HANGING_MAN"
        
        return None
    
    def _calculate_reversal_confidence(self, price_div: bool, volume_div: bool, 
                                     pattern: Optional[str], vol_metrics: VolatilityMetrics) -> Decimal:
        """Calculate confidence score for reversal signal."""
        confidence = Decimal('0.0')
        
        # Base confidence from pattern recognition
        if pattern:
            confidence += Decimal('0.3')
        
        # Add confidence from divergences
        if price_div:
            confidence += Decimal('0.25')
        if volume_div:
            confidence += Decimal('0.25')
        
        # Adjust for trend strength (stronger trends less likely to reverse)
        trend_adjustment = Decimal('0.2') * (Decimal('1.0') - vol_metrics.trend_strength)
        confidence += trend_adjustment
        
        # Adjust for volatility regime
        if vol_metrics.volatility_regime == VolatilityRegime.HIGH:
            confidence += Decimal('0.1')  # High volatility increases reversal probability
        elif vol_metrics.volatility_regime == VolatilityRegime.LOW:
            confidence -= Decimal('0.1')  # Low volatility decreases reversal probability
        
        return min(confidence, Decimal('1.0'))
    
    def _calculate_support_resistance_levels(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Calculate support and resistance levels."""
        if len(self._price_history) < 20:
            return None, None
        
        recent_data = self._price_history[-20:]
        
        # Find recent highs and lows
        highs = [float(dp.high_price) for dp in recent_data]
        lows = [float(dp.low_price) for dp in recent_data]
        
        # Simple support/resistance calculation
        resistance = Decimal(str(max(highs)))
        support = Decimal(str(min(lows)))
        
        return support, resistance
    
    def detect_breakout(self, current_data: ProcessedDataPoint) -> Optional[BreakoutSignal]:
        """Detect price breakout signals.
        
        Args:
            current_data: Current market data point
            
        Returns:
            BreakoutSignal if breakout detected, None otherwise
        """
        if len(self._price_history) < self.config.breakout_lookback:
            return None
        
        # Identify recent trading range
        range_data = self._price_history[-self.config.breakout_lookback:]
        range_high = max(float(dp.high_price) for dp in range_data)
        range_low = min(float(dp.low_price) for dp in range_data)
        range_size = range_high - range_low
        
        current_price = float(current_data.close_price)
        current_volume = float(current_data.volume)
        
        # Calculate average volume
        avg_volume = np.mean([float(dp.volume) for dp in range_data])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Check for breakout
        breakout_type = None
        breakout_level = None
        
        if current_price > range_high:
            breakout_type = BreakoutType.UPWARD_BREAKOUT
            breakout_level = Decimal(str(range_high))
        elif current_price < range_low:
            breakout_type = BreakoutType.DOWNWARD_BREAKOUT
            breakout_level = Decimal(str(range_low))
        
        if not breakout_type:
            return None
        
        # Check volume confirmation
        volume_confirmation = volume_ratio >= float(self.config.min_breakout_volume_ratio)
        
        # Calculate breakout strength
        price_distance = abs(current_price - float(breakout_level))
        breakout_strength = min(price_distance / range_size, 1.0) if range_size > 0 else 0.0
        
        # Calculate momentum
        momentum = self._calculate_price_momentum()
        
        return BreakoutSignal(
            timestamp=current_data.timestamp,
            symbol=current_data.symbol,
            breakout_type=breakout_type,
            breakout_level=breakout_level,
            breakout_strength=Decimal(str(breakout_strength)),
            volume_ratio=Decimal(str(volume_ratio)),
            volume_confirmation=volume_confirmation,
            price_momentum=momentum,
            range_size=Decimal(str(range_size)),
            time_in_range=self.config.breakout_lookback
        )
    
    def _calculate_price_momentum(self) -> Decimal:
        """Calculate price momentum score."""
        if len(self._price_history) < 5:
            return Decimal('0')
        
        # Simple momentum calculation using recent price changes
        recent_prices = [float(dp.close_price) for dp in self._price_history[-5:]]
        
        momentum_sum = 0.0
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            momentum_sum += change
        
        # Normalize momentum to 0-1 scale
        normalized_momentum = max(0.0, min(1.0, (momentum_sum + 0.1) / 0.2))
        
        return Decimal(str(normalized_momentum)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    
    def get_current_analysis(self) -> Dict[str, Any]:
        """Get current volatility and trend analysis.
        
        Returns:
            Dictionary with current analysis results
        """
        if not self._volatility_history:
            return {"status": "insufficient_data"}
        
        latest_metrics = self._volatility_history[-1]
        
        return {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "volatility": {
                "realized": float(latest_metrics.realized_volatility),
                "intraday": float(latest_metrics.intraday_volatility),
                "regime": latest_metrics.volatility_regime.value,
                "percentile": float(latest_metrics.volatility_percentile)
            },
            "trend": {
                "direction": latest_metrics.trend_direction.value,
                "strength": float(latest_metrics.trend_strength)
            },
            "data_points": len(self._price_history),
            "analysis_ready": len(self._price_history) >= self.config.medium_period
        }
    
    def reset(self) -> None:
        """Reset analyzer state."""
        self._volatility_history.clear()
        self._price_history.clear()
        
        logger.info("VolatilityAnalyzer reset")