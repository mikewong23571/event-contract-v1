"""Strategy simulator for backtesting engine.

This module simulates trading strategies against historical market data to evaluate
their performance and generate backtest results.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, AsyncIterator
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from ..models.backtest_result import BacktestResult
from ..models.backtest_trade import BacktestTrade
from ..loaders.data_loader import HistoricalDataPoint, HistoricalDataLoader


class StrategyConfig(BaseModel):
    """Configuration for strategy simulation."""
    strategy_name: str
    initial_capital: Decimal
    bet_amount: Decimal
    max_concurrent_contracts: int = 5
    execution_mode: str = "FIRST_SIGNAL"  # FIRST_SIGNAL, CONTINUOUS, ENHANCED
    contract_duration_minutes: int = 60
    minimum_probability_threshold: float = 0.6
    minimum_confidence_level: str = "MEDIUM"
    risk_parameters: Dict[str, Any] = Field(default_factory=dict)

    @validator('initial_capital', 'bet_amount')
    def validate_positive_amounts(cls, v):
        if v <= 0:
            raise ValueError('initial_capital and bet_amount must be positive')
        return v

    @validator('minimum_probability_threshold')
    def validate_probability_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('minimum_probability_threshold must be between 0.0 and 1.0')
        return v

    @validator('execution_mode')
    def validate_execution_mode(cls, v):
        if v not in ["FIRST_SIGNAL", "CONTINUOUS", "ENHANCED"]:
            raise ValueError('execution_mode must be "FIRST_SIGNAL", "CONTINUOUS", or "ENHANCED"')
        return v

    @validator('minimum_confidence_level')
    def validate_confidence_level(cls, v):
        if v not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError('minimum_confidence_level must be "LOW", "MEDIUM", or "HIGH"')
        return v


class SimulatedSignal(BaseModel):
    """Simulated trading signal for backtesting."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    symbol: str
    direction: str
    predicted_probability: float
    confidence_level: str
    expiry_time: datetime
    strategy_version: str
    technical_indicators: Dict[str, Any] = Field(default_factory=dict)

    @validator('direction')
    def validate_direction(cls, v):
        if v not in ["UP", "DOWN"]:
            raise ValueError('direction must be "UP" or "DOWN"')
        return v

    @validator('predicted_probability')
    def validate_probability(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('predicted_probability must be between 0.0 and 1.0')
        return v


class TradeExecution(BaseModel):
    """Details of a trade execution during simulation."""
    signal: SimulatedSignal
    entry_data: HistoricalDataPoint
    exit_data: HistoricalDataPoint
    bet_amount: Decimal
    was_successful: bool
    profit_loss: Decimal
    execution_timestamp: datetime


class SimulationState(BaseModel):
    """Current state of the simulation."""
    current_balance: Decimal
    active_contracts: List[TradeExecution]
    completed_trades: List[BacktestTrade]
    current_timestamp: datetime
    total_signals_generated: int
    signals_executed: int


class StrategySimulator:
    """Simulates trading strategies for backtesting."""

    def __init__(self, config: StrategyConfig, data_loader: HistoricalDataLoader):
        self.config = config
        self.data_loader = data_loader
        self._simulation_state: Optional[SimulationState] = None

    async def run_simulation(self, symbols: List[str], 
                           start_date: datetime, 
                           end_date: datetime) -> BacktestResult:
        """Run complete strategy simulation.
        
        Args:
            symbols: List of trading symbols to simulate
            start_date: Simulation start date
            end_date: Simulation end date
            
        Returns:
            BacktestResult with simulation results
        """
        # Initialize simulation state
        self._simulation_state = SimulationState(
            current_balance=self.config.initial_capital,
            active_contracts=[],
            completed_trades=[],
            current_timestamp=start_date,
            total_signals_generated=0,
            signals_executed=0
        )

        all_completed_trades = []
        
        # Process each symbol
        for symbol in symbols:
            symbol_trades = await self._simulate_symbol(symbol, start_date, end_date)
            all_completed_trades.extend(symbol_trades)

        # Calculate final results
        result = await self._generate_backtest_result(
            all_completed_trades, start_date, end_date
        )
        
        return result

    async def _simulate_symbol(self, symbol: str, 
                              start_date: datetime, 
                              end_date: datetime) -> List[BacktestTrade]:
        """Simulate trading for a single symbol."""
        completed_trades = []
        
        # Get historical data stream for the symbol
        async for data_point in self.data_loader.get_data_stream(
            symbol, start_date, end_date
        ):
            self._simulation_state.current_timestamp = data_point.timestamp
            
            # Check for contract expirations
            await self._process_contract_expirations(data_point)
            
            # Generate trading signal for current data point
            signal = await self._generate_signal(data_point)
            
            if signal:
                self._simulation_state.total_signals_generated += 1
                
                # Check if signal meets criteria for execution
                if self._should_execute_signal(signal):
                    trade_execution = await self._execute_trade(signal, data_point)
                    if trade_execution:
                        self._simulation_state.active_contracts.append(trade_execution)
                        self._simulation_state.signals_executed += 1

        # Close any remaining active contracts
        await self._close_remaining_contracts()
        
        # Add completed trades to result
        completed_trades.extend(self._simulation_state.completed_trades)
        self._simulation_state.completed_trades.clear()
        
        return completed_trades

    async def _generate_signal(self, data_point: HistoricalDataPoint) -> Optional[SimulatedSignal]:
        """Generate trading signal based on market data.
        
        This is a simplified signal generation logic for demonstration.
        In a real implementation, this would use complex technical analysis.
        """
        # Simple strategy: Generate signal based on price momentum
        # This is placeholder logic - replace with actual strategy
        
        # Calculate some basic technical indicators
        close_price = float(data_point.close_price)
        high_price = float(data_point.high_price)
        low_price = float(data_point.low_price)
        
        # Simple volatility-based signal
        price_range = (high_price - low_price) / close_price
        
        if price_range < 0.01:  # Low volatility - no signal
            return None
            
        # Determine direction based on close vs midpoint
        midpoint = (high_price + low_price) / 2
        direction = "UP" if close_price > midpoint else "DOWN"
        
        # Calculate probability based on price range (simplified)
        probability = min(0.5 + (price_range * 10), 0.95)
        
        # Determine confidence level
        if probability >= 0.8:
            confidence = "HIGH"
        elif probability >= 0.65:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        expiry_time = data_point.timestamp + timedelta(
            minutes=self.config.contract_duration_minutes
        )

        return SimulatedSignal(
            timestamp=data_point.timestamp,
            symbol=data_point.symbol,
            direction=direction,
            predicted_probability=probability,
            confidence_level=confidence,
            expiry_time=expiry_time,
            strategy_version=self.config.strategy_name,
            technical_indicators={
                "price_range": price_range,
                "close_price": close_price,
                "midpoint": midpoint
            }
        )

    def _should_execute_signal(self, signal: SimulatedSignal) -> bool:
        """Determine if a signal should be executed based on strategy config."""
        # Check probability threshold
        if signal.predicted_probability < self.config.minimum_probability_threshold:
            return False
        
        # Check confidence level
        confidence_levels = ["LOW", "MEDIUM", "HIGH"]
        min_level_index = confidence_levels.index(self.config.minimum_confidence_level)
        signal_level_index = confidence_levels.index(signal.confidence_level)
        
        if signal_level_index < min_level_index:
            return False
        
        # Check available balance
        if self._simulation_state.current_balance < self.config.bet_amount:
            return False
        
        # Check maximum concurrent contracts
        if len(self._simulation_state.active_contracts) >= self.config.max_concurrent_contracts:
            return False
        
        # Check execution mode constraints
        if self.config.execution_mode == "FIRST_SIGNAL":
            # Only execute if no active contracts for this symbol
            active_symbols = [contract.signal.symbol for contract in self._simulation_state.active_contracts]
            if signal.symbol in active_symbols:
                return False
        
        return True

    async def _execute_trade(self, signal: SimulatedSignal, 
                           entry_data: HistoricalDataPoint) -> Optional[TradeExecution]:
        """Execute a trade based on signal."""
        # Deduct bet amount from balance
        self._simulation_state.current_balance -= self.config.bet_amount
        
        trade_execution = TradeExecution(
            signal=signal,
            entry_data=entry_data,
            exit_data=entry_data,  # Will be updated at expiry
            bet_amount=self.config.bet_amount,
            was_successful=False,  # Will be determined at expiry
            profit_loss=Decimal('0'),  # Will be calculated at expiry
            execution_timestamp=signal.timestamp
        )
        
        return trade_execution

    async def _process_contract_expirations(self, current_data: HistoricalDataPoint) -> None:
        """Process expired contracts and calculate results."""
        expired_contracts = []
        
        for contract in self._simulation_state.active_contracts:
            if (contract.signal.expiry_time <= current_data.timestamp and 
                contract.signal.symbol == current_data.symbol):
                
                # Update exit data
                contract.exit_data = current_data
                
                # Determine if trade was successful
                entry_price = contract.entry_data.close_price
                exit_price = current_data.close_price
                
                if contract.signal.direction == "UP":
                    contract.was_successful = exit_price > entry_price
                else:  # DOWN
                    contract.was_successful = exit_price < entry_price
                
                # Calculate profit/loss
                if contract.was_successful:
                    # Win: get back bet + profit (assuming 80% payout)
                    payout_rate = Decimal('0.8')
                    contract.profit_loss = contract.bet_amount * payout_rate
                    self._simulation_state.current_balance += contract.bet_amount + contract.profit_loss
                else:
                    # Loss: lose the bet amount
                    contract.profit_loss = -contract.bet_amount
                
                # Create backtest trade record
                backtest_trade = BacktestTrade(
                    backtest_result_id=uuid4(),  # Will be updated later
                    signal_timestamp=contract.signal.timestamp,
                    direction=contract.signal.direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    bet_amount=contract.bet_amount,
                    profit_loss=contract.profit_loss,
                    was_successful=contract.was_successful,
                    contract_duration_minutes=self.config.contract_duration_minutes
                )
                
                self._simulation_state.completed_trades.append(backtest_trade)
                expired_contracts.append(contract)
        
        # Remove expired contracts from active list
        for contract in expired_contracts:
            self._simulation_state.active_contracts.remove(contract)

    async def _close_remaining_contracts(self) -> None:
        """Close any remaining active contracts at the end of simulation."""
        # In a real implementation, we would need the final data point
        # For now, we'll assume all remaining contracts are losses
        for contract in self._simulation_state.active_contracts:
            contract.was_successful = False
            contract.profit_loss = -contract.bet_amount
            
            backtest_trade = BacktestTrade(
                backtest_result_id=uuid4(),
                signal_timestamp=contract.signal.timestamp,
                direction=contract.signal.direction,
                entry_price=contract.entry_data.close_price,
                exit_price=contract.entry_data.close_price,  # No change assumed
                bet_amount=contract.bet_amount,
                profit_loss=contract.profit_loss,
                was_successful=contract.was_successful,
                contract_duration_minutes=self.config.contract_duration_minutes
            )
            
            self._simulation_state.completed_trades.append(backtest_trade)
        
        self._simulation_state.active_contracts.clear()

    async def _generate_backtest_result(self, completed_trades: List[BacktestTrade],
                                      start_date: datetime, 
                                      end_date: datetime) -> BacktestResult:
        """Generate final backtest result from completed trades."""
        if not completed_trades:
            return BacktestResult(
                strategy_name=self.config.strategy_name,
                start_date=start_date,
                end_date=end_date,
                total_signals=0,
                successful_signals=0,
                win_rate=Decimal('0.0'),
                total_profit_loss=Decimal('0.0'),
                max_drawdown=Decimal('0.0'),
                sharpe_ratio=Decimal('0.0'),
                parameters=self.config.dict(),
                execution_mode=self.config.execution_mode
            )
        
        # Calculate metrics
        total_signals = len(completed_trades)
        successful_signals = sum(1 for trade in completed_trades if trade.was_successful)
        win_rate = Decimal(successful_signals) / Decimal(total_signals)
        
        total_profit_loss = sum(trade.profit_loss for trade in completed_trades)
        
        # Calculate max drawdown
        max_drawdown = await self._calculate_max_drawdown(completed_trades)
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = await self._calculate_sharpe_ratio(completed_trades)
        
        # Update backtest result ID in trades
        result_id = uuid4()
        for trade in completed_trades:
            trade.backtest_result_id = result_id

        return BacktestResult(
            id=result_id,
            strategy_name=self.config.strategy_name,
            start_date=start_date,
            end_date=end_date,
            total_signals=total_signals,
            successful_signals=successful_signals,
            win_rate=win_rate,
            total_profit_loss=total_profit_loss,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            parameters=self.config.dict(),
            execution_mode=self.config.execution_mode
        )

    async def _calculate_max_drawdown(self, completed_trades: List[BacktestTrade]) -> Decimal:
        """Calculate maximum drawdown during the simulation."""
        if not completed_trades:
            return Decimal('0.0')
        
        running_balance = self.config.initial_capital
        peak_balance = running_balance
        max_drawdown = Decimal('0.0')
        
        for trade in completed_trades:
            running_balance += trade.profit_loss
            
            if running_balance > peak_balance:
                peak_balance = running_balance
            
            current_drawdown = peak_balance - running_balance
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
        
        return max_drawdown

    async def _calculate_sharpe_ratio(self, completed_trades: List[BacktestTrade]) -> Decimal:
        """Calculate Sharpe ratio (simplified version)."""
        if not completed_trades:
            return Decimal('0.0')
        
        # Calculate returns
        returns = [float(trade.profit_loss) / float(trade.bet_amount) for trade in completed_trades]
        
        if len(returns) < 2:
            return Decimal('0.0')
        
        # Calculate mean and standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return Decimal('0.0')
        
        # Sharpe ratio (assuming risk-free rate of 0)
        sharpe_ratio = mean_return / std_dev
        
        return Decimal(str(round(sharpe_ratio, 4)))

    def get_simulation_state(self) -> Optional[SimulationState]:
        """Get current simulation state."""
        return self._simulation_state

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the simulation."""
        if not self._simulation_state:
            return {"error": "No simulation has been run"}
        
        total_trades = len(self._simulation_state.completed_trades)
        if total_trades == 0:
            return {"message": "No trades executed"}
        
        successful_trades = sum(
            1 for trade in self._simulation_state.completed_trades 
            if trade.was_successful
        )
        
        total_pnl = sum(
            trade.profit_loss for trade in self._simulation_state.completed_trades
        )
        
        return {
            "strategy_name": self.config.strategy_name,
            "execution_mode": self.config.execution_mode,
            "initial_capital": float(self.config.initial_capital),
            "final_balance": float(self._simulation_state.current_balance),
            "total_signals_generated": self._simulation_state.total_signals_generated,
            "signals_executed": self._simulation_state.signals_executed,
            "execution_rate": (
                self._simulation_state.signals_executed / 
                self._simulation_state.total_signals_generated
                if self._simulation_state.total_signals_generated > 0 else 0
            ),
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "win_rate": successful_trades / total_trades if total_trades > 0 else 0,
            "total_pnl": float(total_pnl),
            "roi": float(total_pnl / self.config.initial_capital) if self.config.initial_capital > 0 else 0
        }