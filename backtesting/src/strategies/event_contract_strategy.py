"""Event Contract Strategy Interface.

This module defines the standardized interface for event contract trading strategies,
including initialization, signal generation, position management, and risk control
specifically designed for binary outcome prediction.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
import structlog

from ..loaders.binance_event_data_processor import ProcessedDataPoint, TimeFrame
from ..simulators.event_contract_simulator import ContractDirection, EventContract


logger = structlog.get_logger(__name__)


class SignalStrength(str, Enum):
    """Signal strength levels."""
    WEAK = "WEAK"        # Low confidence, avoid trading
    MODERATE = "MODERATE"  # Medium confidence, small position
    STRONG = "STRONG"     # High confidence, normal position
    VERY_STRONG = "VERY_STRONG"  # Very high confidence, large position


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "LOW"          # Conservative trading
    MEDIUM = "MEDIUM"    # Balanced risk/reward
    HIGH = "HIGH"        # Aggressive trading
    EXTREME = "EXTREME"  # Maximum risk tolerance


class MarketCondition(str, Enum):
    """Market condition assessment."""
    TRENDING_UP = "TRENDING_UP"      # Strong upward trend
    TRENDING_DOWN = "TRENDING_DOWN"  # Strong downward trend
    SIDEWAYS = "SIDEWAYS"            # Range-bound market
    VOLATILE = "VOLATILE"            # High volatility, no clear trend
    BREAKOUT = "BREAKOUT"            # Breaking key levels
    REVERSAL = "REVERSAL"            # Trend reversal signals


class EventContractSignal(BaseModel):
    """Event contract trading signal."""
    
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    symbol: str
    
    # Signal details
    direction: ContractDirection
    strength: SignalStrength
    confidence_score: Decimal  # 0.0 to 1.0
    predicted_probability: Decimal  # 0.0 to 1.0 (probability of winning)
    
    # Contract parameters
    suggested_duration_minutes: int
    suggested_bet_amount: Decimal
    max_bet_amount: Decimal
    
    # Risk assessment
    risk_level: RiskLevel
    market_condition: MarketCondition
    volatility_score: Decimal  # 0.0 to 1.0
    
    # Technical analysis
    entry_price: Decimal
    support_level: Optional[Decimal] = None
    resistance_level: Optional[Decimal] = None
    stop_loss_level: Optional[Decimal] = None  # Not applicable for event contracts
    
    # Signal reasoning
    primary_indicator: str
    secondary_indicators: List[str] = Field(default_factory=list)
    signal_reason: str
    conditions_met: List[str] = Field(default_factory=list)
    
    # Metadata
    strategy_name: str
    strategy_version: str = "1.0"
    timeframe_analyzed: TimeFrame
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }
    
    @validator('confidence_score', 'predicted_probability', 'volatility_score')
    def validate_scores(cls, v):
        if not Decimal('0.0') <= v <= Decimal('1.0'):
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v
    
    @validator('suggested_bet_amount', 'max_bet_amount')
    def validate_bet_amounts(cls, v):
        if v <= 0:
            raise ValueError('Bet amounts must be positive')
        return v
    
    @validator('max_bet_amount')
    def validate_max_bet_amount(cls, v, values):
        if 'suggested_bet_amount' in values and v < values['suggested_bet_amount']:
            raise ValueError('max_bet_amount must be >= suggested_bet_amount')
        return v


class PositionSizingConfig(BaseModel):
    """Configuration for position sizing."""
    
    # Base sizing parameters
    base_bet_percentage: Decimal = Decimal('0.02')  # 2% of capital per trade
    max_bet_percentage: Decimal = Decimal('0.05')   # 5% maximum per trade
    min_bet_amount: Decimal = Decimal('10.0')       # Minimum bet amount
    max_bet_amount: Decimal = Decimal('1000.0')     # Maximum bet amount
    
    # Risk-based adjustments
    confidence_multiplier: Decimal = Decimal('2.0')  # Multiply by confidence score
    volatility_adjustment: bool = True               # Adjust for market volatility
    
    # Kelly Criterion settings
    use_kelly_criterion: bool = False
    kelly_fraction: Decimal = Decimal('0.25')  # Fractional Kelly (25%)
    
    # Risk management
    max_concurrent_contracts: int = 5
    max_daily_risk: Decimal = Decimal('0.10')  # 10% of capital per day
    
    @validator('base_bet_percentage', 'max_bet_percentage', 'kelly_fraction', 'max_daily_risk')
    def validate_percentages(cls, v):
        if not Decimal('0.001') <= v <= Decimal('1.0'):
            raise ValueError('Percentages must be between 0.1% and 100%')
        return v


class RiskManagementConfig(BaseModel):
    """Configuration for risk management."""
    
    # Probability thresholds
    min_probability_threshold: Decimal = Decimal('0.60')  # Minimum win probability
    high_confidence_threshold: Decimal = Decimal('0.75')  # High confidence threshold
    
    # Market condition filters
    avoid_high_volatility: bool = True
    volatility_threshold: Decimal = Decimal('0.05')  # 5% volatility threshold
    
    # Time-based restrictions
    avoid_news_events: bool = True
    news_buffer_minutes: int = 30  # Avoid trading 30min before/after news
    
    # Drawdown protection
    max_drawdown_percentage: Decimal = Decimal('0.15')  # 15% max drawdown
    stop_trading_on_drawdown: bool = True
    
    # Consecutive loss protection
    max_consecutive_losses: int = 5
    reduce_size_after_losses: bool = True
    
    @validator('min_probability_threshold', 'high_confidence_threshold')
    def validate_probability_thresholds(cls, v):
        if not Decimal('0.5') <= v <= Decimal('0.95'):
            raise ValueError('Probability thresholds must be between 50% and 95%')
        return v


class StrategyPerformanceMetrics(BaseModel):
    """Strategy performance tracking."""
    
    # Basic metrics
    total_signals_generated: int = 0
    signals_executed: int = 0
    successful_contracts: int = 0
    failed_contracts: int = 0
    
    # Financial metrics
    total_profit_loss: Decimal = Decimal('0.0')
    total_fees_paid: Decimal = Decimal('0.0')
    largest_win: Decimal = Decimal('0.0')
    largest_loss: Decimal = Decimal('0.0')
    
    # Risk metrics
    current_drawdown: Decimal = Decimal('0.0')
    max_drawdown: Decimal = Decimal('0.0')
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    
    # Efficiency metrics
    win_rate: Decimal = Decimal('0.0')
    average_win: Decimal = Decimal('0.0')
    average_loss: Decimal = Decimal('0.0')
    profit_factor: Decimal = Decimal('0.0')
    expectancy: Decimal = Decimal('0.0')
    
    # Time-based metrics
    strategy_start_time: Optional[datetime] = None
    last_signal_time: Optional[datetime] = None
    total_active_time_hours: Decimal = Decimal('0.0')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: str
        }
    
    def calculate_derived_metrics(self) -> None:
        """Calculate derived performance metrics."""
        total_contracts = self.successful_contracts + self.failed_contracts
        
        if total_contracts > 0:
            self.win_rate = Decimal(self.successful_contracts) / Decimal(total_contracts)
        
        if self.successful_contracts > 0:
            total_wins = sum([self.largest_win])  # Simplified - would track all wins
            self.average_win = total_wins / Decimal(self.successful_contracts)
        
        if self.failed_contracts > 0:
            total_losses = abs(sum([self.largest_loss]))  # Simplified - would track all losses
            self.average_loss = total_losses / Decimal(self.failed_contracts)
        
        # Profit factor = Total Wins / Total Losses
        if self.average_loss > 0 and self.failed_contracts > 0:
            total_wins = self.average_win * self.successful_contracts
            total_losses = self.average_loss * self.failed_contracts
            self.profit_factor = total_wins / total_losses
        
        # Expectancy = (Win Rate × Average Win) - (Loss Rate × Average Loss)
        if total_contracts > 0:
            loss_rate = Decimal(self.failed_contracts) / Decimal(total_contracts)
            self.expectancy = (self.win_rate * self.average_win) - (loss_rate * self.average_loss)


class EventContractStrategyConfig(BaseModel):
    """Base configuration for event contract strategies."""
    
    # Strategy identification
    name: str
    version: str = "1.0"
    description: str = ""
    
    # Analysis parameters
    primary_timeframe: TimeFrame = TimeFrame.M15
    secondary_timeframes: List[TimeFrame] = Field(default_factory=lambda: [TimeFrame.M5, TimeFrame.H1])
    lookback_periods: int = 100
    
    # Signal generation
    signal_cooldown_minutes: int = 5  # Minimum time between signals
    require_confirmation: bool = True  # Require multiple indicator confirmation
    
    # Position sizing and risk management
    position_sizing: PositionSizingConfig = Field(default_factory=PositionSizingConfig)
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig)
    
    # Strategy-specific parameters
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('lookback_periods')
    def validate_lookback_periods(cls, v):
        if not 10 <= v <= 1000:
            raise ValueError('lookback_periods must be between 10 and 1000')
        return v


class BaseEventContractStrategy(ABC):
    """Abstract base class for event contract trading strategies.
    
    All event contract strategies must inherit from this class and implement
    the required methods for signal generation, risk management, and position sizing.
    """
    
    def __init__(self, config: EventContractStrategyConfig):
        """Initialize the strategy with configuration.
        
        Args:
            config: Strategy configuration parameters
        """
        self.config = config
        self.name = config.name
        self.version = config.version
        
        # Performance tracking
        self.metrics = StrategyPerformanceMetrics()
        self.metrics.strategy_start_time = datetime.utcnow()
        
        # Data storage
        self._market_data: Dict[TimeFrame, List[ProcessedDataPoint]] = {}
        self._active_contracts: List[EventContract] = []
        
        # State management
        self._is_initialized = False
        self._last_signal_time: Optional[datetime] = None
        self._daily_risk_used = Decimal('0.0')
        self._current_day = datetime.utcnow().date()
        
        logger.info(
            "EventContractStrategy initialized",
            strategy_name=self.name,
            version=self.version,
            primary_timeframe=config.primary_timeframe.value
        )
    
    @abstractmethod
    async def analyze_market_conditions(self, data: Dict[TimeFrame, List[ProcessedDataPoint]]) -> MarketCondition:
        """Analyze current market conditions.
        
        Args:
            data: Multi-timeframe market data
            
        Returns:
            Current market condition assessment
        """
        pass
    
    @abstractmethod
    async def generate_signal(self, current_data: ProcessedDataPoint, 
                            historical_data: Dict[TimeFrame, List[ProcessedDataPoint]]) -> Optional[EventContractSignal]:
        """Generate trading signal based on market analysis.
        
        This is the core method that each strategy must implement. It should analyze
        the current market data and historical context to determine if a trading
        opportunity exists.
        
        Args:
            current_data: Current market data point
            historical_data: Historical data across multiple timeframes
            
        Returns:
            EventContractSignal if opportunity identified, None otherwise
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: EventContractSignal, 
                              available_capital: Decimal,
                              current_risk_exposure: Decimal) -> Decimal:
        """Calculate appropriate position size for a signal.
        
        Args:
            signal: Trading signal
            available_capital: Available capital for trading
            current_risk_exposure: Current risk exposure from active positions
            
        Returns:
            Suggested position size (bet amount)
        """
        pass
    
    @abstractmethod
    def assess_risk_level(self, signal: EventContractSignal, 
                         market_condition: MarketCondition) -> RiskLevel:
        """Assess risk level for a given signal and market condition.
        
        Args:
            signal: Trading signal to assess
            market_condition: Current market condition
            
        Returns:
            Risk level assessment
        """
        pass
    
    def update_market_data(self, timeframe: TimeFrame, data_point: ProcessedDataPoint) -> None:
        """Update strategy with new market data.
        
        Args:
            timeframe: Timeframe of the data
            data_point: New market data point
        """
        if timeframe not in self._market_data:
            self._market_data[timeframe] = []
        
        self._market_data[timeframe].append(data_point)
        
        # Keep only required lookback periods
        max_history = self.config.lookback_periods * 2
        if len(self._market_data[timeframe]) > max_history:
            self._market_data[timeframe] = self._market_data[timeframe][-max_history:]
    
    def get_historical_data(self, timeframe: TimeFrame, periods: Optional[int] = None) -> List[ProcessedDataPoint]:
        """Get historical market data for specified timeframe.
        
        Args:
            timeframe: Timeframe to retrieve
            periods: Number of recent periods (None for all available)
            
        Returns:
            List of historical data points
        """
        if timeframe not in self._market_data:
            return []
        
        data = self._market_data[timeframe]
        if periods is None:
            return data.copy()
        return data[-periods:] if periods > 0 else []
    
    def validate_signal_conditions(self, signal: EventContractSignal) -> Tuple[bool, str]:
        """Validate that a signal meets strategy requirements.
        
        Args:
            signal: Signal to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check minimum probability threshold
        if signal.predicted_probability < self.config.risk_management.min_probability_threshold:
            return False, f"Probability {signal.predicted_probability} below threshold {self.config.risk_management.min_probability_threshold}"
        
        # Check signal cooldown
        if self._last_signal_time is not None:
            time_since_last = signal.timestamp - self._last_signal_time
            cooldown = timedelta(minutes=self.config.signal_cooldown_minutes)
            if time_since_last < cooldown:
                return False, f"Signal cooldown active (last signal {time_since_last.total_seconds():.0f}s ago)"
        
        # Check daily risk limits
        current_day = signal.timestamp.date()
        if current_day != self._current_day:
            self._daily_risk_used = Decimal('0.0')
            self._current_day = current_day
        
        # Check concurrent contracts limit
        if len(self._active_contracts) >= self.config.position_sizing.max_concurrent_contracts:
            return False, f"Maximum concurrent contracts ({self.config.position_sizing.max_concurrent_contracts}) reached"
        
        # Check volatility conditions
        if (self.config.risk_management.avoid_high_volatility and 
            signal.volatility_score > self.config.risk_management.volatility_threshold):
            return False, f"Volatility {signal.volatility_score} exceeds threshold {self.config.risk_management.volatility_threshold}"
        
        return True, ""
    
    def calculate_kelly_position_size(self, win_probability: Decimal, 
                                    payout_ratio: Decimal,
                                    available_capital: Decimal) -> Decimal:
        """Calculate position size using Kelly Criterion.
        
        Kelly % = (bp - q) / b
        where:
        b = payout ratio (e.g., 0.8 for 80% payout)
        p = probability of winning
        q = probability of losing (1 - p)
        
        Args:
            win_probability: Probability of winning (0.0 to 1.0)
            payout_ratio: Payout ratio (e.g., 0.8 for 80%)
            available_capital: Available capital
            
        Returns:
            Suggested position size
        """
        if not self.config.position_sizing.use_kelly_criterion:
            return Decimal('0.0')
        
        p = win_probability
        q = Decimal('1.0') - p
        b = payout_ratio
        
        # Kelly percentage
        kelly_pct = (b * p - q) / b
        
        # Apply fractional Kelly
        kelly_pct *= self.config.position_sizing.kelly_fraction
        
        # Ensure positive and within limits
        kelly_pct = max(kelly_pct, Decimal('0.0'))
        kelly_pct = min(kelly_pct, self.config.position_sizing.max_bet_percentage)
        
        return available_capital * kelly_pct
    
    def update_performance_metrics(self, contract: EventContract, profit_loss: Decimal) -> None:
        """Update strategy performance metrics.
        
        Args:
            contract: Completed contract
            profit_loss: Profit or loss from the contract
        """
        self.metrics.total_profit_loss += profit_loss
        
        if profit_loss > 0:
            self.metrics.successful_contracts += 1
            self.metrics.largest_win = max(self.metrics.largest_win, profit_loss)
            self.metrics.consecutive_losses = 0
        else:
            self.metrics.failed_contracts += 1
            self.metrics.largest_loss = min(self.metrics.largest_loss, profit_loss)
            self.metrics.consecutive_losses += 1
            self.metrics.max_consecutive_losses = max(
                self.metrics.max_consecutive_losses, 
                self.metrics.consecutive_losses
            )
        
        # Update drawdown
        if profit_loss < 0:
            self.metrics.current_drawdown += abs(profit_loss)
            self.metrics.max_drawdown = max(self.metrics.max_drawdown, self.metrics.current_drawdown)
        else:
            self.metrics.current_drawdown = max(Decimal('0.0'), self.metrics.current_drawdown - profit_loss)
        
        # Recalculate derived metrics
        self.metrics.calculate_derived_metrics()
        
        logger.info(
            "Performance metrics updated",
            strategy_name=self.name,
            total_pnl=float(self.metrics.total_profit_loss),
            win_rate=float(self.metrics.win_rate),
            consecutive_losses=self.metrics.consecutive_losses
        )
    
    def should_stop_trading(self) -> Tuple[bool, str]:
        """Check if strategy should stop trading due to risk limits.
        
        Returns:
            Tuple of (should_stop, reason)
        """
        # Check drawdown limits
        if (self.config.risk_management.stop_trading_on_drawdown and 
            self.metrics.current_drawdown > self.config.risk_management.max_drawdown_percentage):
            return True, f"Maximum drawdown exceeded: {self.metrics.current_drawdown}"
        
        # Check consecutive losses
        if self.metrics.consecutive_losses >= self.config.risk_management.max_consecutive_losses:
            return True, f"Maximum consecutive losses reached: {self.metrics.consecutive_losses}"
        
        return False, ""
    
    def get_strategy_state(self) -> Dict[str, Any]:
        """Get current strategy state and performance.
        
        Returns:
            Dictionary with strategy state information
        """
        should_stop, stop_reason = self.should_stop_trading()
        
        return {
            "name": self.name,
            "version": self.version,
            "is_initialized": self._is_initialized,
            "active_contracts": len(self._active_contracts),
            "last_signal_time": self._last_signal_time.isoformat() if self._last_signal_time else None,
            "daily_risk_used": float(self._daily_risk_used),
            "should_stop_trading": should_stop,
            "stop_reason": stop_reason,
            "performance_metrics": {
                "total_signals": self.metrics.total_signals_generated,
                "signals_executed": self.metrics.signals_executed,
                "win_rate": float(self.metrics.win_rate),
                "total_pnl": float(self.metrics.total_profit_loss),
                "current_drawdown": float(self.metrics.current_drawdown),
                "consecutive_losses": self.metrics.consecutive_losses
            },
            "config": {
                "primary_timeframe": self.config.primary_timeframe.value,
                "min_probability_threshold": float(self.config.risk_management.min_probability_threshold),
                "max_concurrent_contracts": self.config.position_sizing.max_concurrent_contracts
            }
        }
    
    def reset(self) -> None:
        """Reset strategy state for new simulation."""
        self._market_data.clear()
        self._active_contracts.clear()
        self._is_initialized = False
        self._last_signal_time = None
        self._daily_risk_used = Decimal('0.0')
        self._current_day = datetime.utcnow().date()
        
        # Reset performance metrics
        self.metrics = StrategyPerformanceMetrics()
        self.metrics.strategy_start_time = datetime.utcnow()
        
        logger.info("Strategy reset", strategy_name=self.name)