"""Event Contract Binary Settlement Simulator.

This module implements the binary settlement mechanism specific to event contracts,
including the 55.6% implied probability calculation model and precise simulation
of binary outcomes with fixed payout ratios.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
import structlog

from ..models.backtest_result import BacktestResult
from ..models.backtest_trade import BacktestTrade
from ..loaders.data_loader import HistoricalDataPoint


logger = structlog.get_logger(__name__)


class ContractDirection(str, Enum):
    """Event contract direction."""
    UP = "UP"
    DOWN = "DOWN"


class ContractStatus(str, Enum):
    """Event contract status."""
    ACTIVE = "ACTIVE"
    EXPIRED_WIN = "EXPIRED_WIN"
    EXPIRED_LOSS = "EXPIRED_LOSS"
    CANCELLED = "CANCELLED"


class EventContractConfig(BaseModel):
    """Configuration for event contract simulation."""
    
    # Payout configuration
    payout_percentage: Decimal = Decimal('0.80')  # 80% payout on win
    implied_probability_threshold: Decimal = Decimal('0.556')  # 55.6% breakeven
    
    # Contract duration settings
    default_duration_minutes: int = 60
    min_duration_minutes: int = 10
    max_duration_minutes: int = 1440  # 24 hours
    
    # Risk management
    max_bet_amount: Decimal = Decimal('1000.0')
    min_bet_amount: Decimal = Decimal('1.0')
    max_concurrent_contracts: int = 10
    
    # Execution parameters
    execution_delay_seconds: float = 0.1  # Simulated execution delay
    slippage_tolerance: Decimal = Decimal('0.001')  # 0.1% slippage
    
    @validator('payout_percentage')
    def validate_payout_percentage(cls, v):
        if not Decimal('0.1') <= v <= Decimal('2.0'):
            raise ValueError('payout_percentage must be between 0.1 and 2.0')
        return v
    
    @validator('implied_probability_threshold')
    def validate_implied_probability(cls, v):
        if not Decimal('0.1') <= v <= Decimal('0.9'):
            raise ValueError('implied_probability_threshold must be between 0.1 and 0.9')
        return v


class EventContract(BaseModel):
    """Represents an active event contract."""
    
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    direction: ContractDirection
    entry_price: Decimal
    bet_amount: Decimal
    entry_timestamp: datetime
    expiry_timestamp: datetime
    status: ContractStatus = ContractStatus.ACTIVE
    
    # Settlement data (populated on expiry)
    exit_price: Optional[Decimal] = None
    settlement_timestamp: Optional[datetime] = None
    profit_loss: Optional[Decimal] = None
    
    # Metadata
    strategy_name: str
    confidence_score: Optional[Decimal] = None
    predicted_probability: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }
    
    @validator('bet_amount')
    def validate_bet_amount(cls, v):
        if v <= 0:
            raise ValueError('bet_amount must be positive')
        return v
    
    @validator('expiry_timestamp')
    def validate_expiry_timestamp(cls, v, values):
        if 'entry_timestamp' in values and v <= values['entry_timestamp']:
            raise ValueError('expiry_timestamp must be after entry_timestamp')
        return v


class ContractSettlement(BaseModel):
    """Result of contract settlement."""
    
    contract_id: UUID
    was_successful: bool
    entry_price: Decimal
    exit_price: Decimal
    price_change: Decimal
    price_change_percentage: Decimal
    profit_loss: Decimal
    settlement_timestamp: datetime
    duration_minutes: int
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }


class EventContractSimulator:
    """Simulates event contract trading with binary settlement mechanism."""
    
    def __init__(self, config: EventContractConfig):
        self.config = config
        self.active_contracts: Dict[UUID, EventContract] = {}
        self.settled_contracts: List[ContractSettlement] = []
        
        # Performance tracking
        self.total_contracts_created = 0
        self.total_contracts_settled = 0
        self.total_profit_loss = Decimal('0.0')
        
        logger.info(
            "EventContractSimulator initialized",
            payout_percentage=float(config.payout_percentage),
            implied_probability=float(config.implied_probability_threshold)
        )
    
    def calculate_implied_probability(self, payout_percentage: Optional[Decimal] = None) -> Decimal:
        """Calculate the implied probability for breakeven.
        
        For event contracts with fixed payout:
        Implied Probability = 1 / (1 + Payout Percentage)
        
        Args:
            payout_percentage: Custom payout percentage, uses config default if None
            
        Returns:
            Implied probability as decimal (e.g., 0.556 for 55.6%)
        """
        payout = payout_percentage or self.config.payout_percentage
        implied_prob = Decimal('1.0') / (Decimal('1.0') + payout)
        
        logger.debug(
            "Calculated implied probability",
            payout_percentage=float(payout),
            implied_probability=float(implied_prob)
        )
        
        return implied_prob.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    
    def calculate_expected_value(self, win_probability: Decimal, 
                               bet_amount: Decimal,
                               payout_percentage: Optional[Decimal] = None) -> Decimal:
        """Calculate expected value of a contract.
        
        EV = (Win Probability × Payout) - (Loss Probability × Bet Amount)
        
        Args:
            win_probability: Probability of winning (0.0 to 1.0)
            bet_amount: Amount being bet
            payout_percentage: Custom payout percentage
            
        Returns:
            Expected value (positive = profitable, negative = unprofitable)
        """
        payout = payout_percentage or self.config.payout_percentage
        loss_probability = Decimal('1.0') - win_probability
        
        expected_win = win_probability * (bet_amount * payout)
        expected_loss = loss_probability * bet_amount
        
        expected_value = expected_win - expected_loss
        
        logger.debug(
            "Calculated expected value",
            win_probability=float(win_probability),
            bet_amount=float(bet_amount),
            expected_value=float(expected_value)
        )
        
        return expected_value
    
    def validate_contract_parameters(self, bet_amount: Decimal, 
                                   duration_minutes: int,
                                   predicted_probability: Optional[Decimal] = None) -> Tuple[bool, str]:
        """Validate contract parameters before creation.
        
        Args:
            bet_amount: Amount to bet
            duration_minutes: Contract duration
            predicted_probability: Predicted win probability
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check bet amount limits
        if bet_amount < self.config.min_bet_amount:
            return False, f"Bet amount {bet_amount} below minimum {self.config.min_bet_amount}"
        
        if bet_amount > self.config.max_bet_amount:
            return False, f"Bet amount {bet_amount} exceeds maximum {self.config.max_bet_amount}"
        
        # Check duration limits
        if duration_minutes < self.config.min_duration_minutes:
            return False, f"Duration {duration_minutes}m below minimum {self.config.min_duration_minutes}m"
        
        if duration_minutes > self.config.max_duration_minutes:
            return False, f"Duration {duration_minutes}m exceeds maximum {self.config.max_duration_minutes}m"
        
        # Check concurrent contracts limit
        if len(self.active_contracts) >= self.config.max_concurrent_contracts:
            return False, f"Maximum concurrent contracts ({self.config.max_concurrent_contracts}) reached"
        
        # Check probability threshold if provided
        if predicted_probability is not None:
            implied_prob = self.calculate_implied_probability()
            if predicted_probability <= implied_prob:
                return False, f"Predicted probability {predicted_probability} below breakeven threshold {implied_prob}"
        
        return True, ""
    
    async def create_contract(self, symbol: str,
                            direction: ContractDirection,
                            entry_price: Decimal,
                            bet_amount: Decimal,
                            entry_timestamp: datetime,
                            duration_minutes: Optional[int] = None,
                            strategy_name: str = "default",
                            confidence_score: Optional[Decimal] = None,
                            predicted_probability: Optional[Decimal] = None) -> EventContract:
        """Create a new event contract.
        
        Args:
            symbol: Trading symbol
            direction: UP or DOWN prediction
            entry_price: Price at contract creation
            bet_amount: Amount being bet
            entry_timestamp: When contract was created
            duration_minutes: Contract duration (uses default if None)
            strategy_name: Name of strategy creating contract
            confidence_score: Strategy confidence (0.0 to 1.0)
            predicted_probability: Predicted win probability
            
        Returns:
            Created EventContract
            
        Raises:
            ValueError: If contract parameters are invalid
        """
        duration = duration_minutes or self.config.default_duration_minutes
        
        # Validate parameters
        is_valid, error_msg = self.validate_contract_parameters(
            bet_amount, duration, predicted_probability
        )
        if not is_valid:
            raise ValueError(f"Invalid contract parameters: {error_msg}")
        
        # Calculate expiry time
        expiry_timestamp = entry_timestamp + timedelta(minutes=duration)
        
        # Create contract
        contract = EventContract(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            bet_amount=bet_amount,
            entry_timestamp=entry_timestamp,
            expiry_timestamp=expiry_timestamp,
            strategy_name=strategy_name,
            confidence_score=confidence_score,
            predicted_probability=predicted_probability
        )
        
        # Add to active contracts
        self.active_contracts[contract.id] = contract
        self.total_contracts_created += 1
        
        # Simulate execution delay
        if self.config.execution_delay_seconds > 0:
            await asyncio.sleep(self.config.execution_delay_seconds)
        
        logger.info(
            "Event contract created",
            contract_id=str(contract.id),
            symbol=symbol,
            direction=direction.value,
            bet_amount=float(bet_amount),
            duration_minutes=duration,
            entry_price=float(entry_price)
        )
        
        return contract
    
    def settle_contract(self, contract_id: UUID, 
                      exit_price: Decimal,
                      settlement_timestamp: datetime) -> ContractSettlement:
        """Settle an event contract based on exit price.
        
        Args:
            contract_id: ID of contract to settle
            exit_price: Final price at expiry
            settlement_timestamp: When settlement occurred
            
        Returns:
            ContractSettlement with results
            
        Raises:
            ValueError: If contract not found or already settled
        """
        if contract_id not in self.active_contracts:
            raise ValueError(f"Contract {contract_id} not found in active contracts")
        
        contract = self.active_contracts[contract_id]
        
        if contract.status != ContractStatus.ACTIVE:
            raise ValueError(f"Contract {contract_id} is not active (status: {contract.status})")
        
        # Calculate price change
        price_change = exit_price - contract.entry_price
        price_change_pct = (price_change / contract.entry_price) * Decimal('100')
        
        # Determine if contract won
        if contract.direction == ContractDirection.UP:
            was_successful = exit_price > contract.entry_price
        else:  # DOWN
            was_successful = exit_price < contract.entry_price
        
        # Calculate profit/loss
        if was_successful:
            profit_loss = contract.bet_amount * self.config.payout_percentage
            contract.status = ContractStatus.EXPIRED_WIN
        else:
            profit_loss = -contract.bet_amount
            contract.status = ContractStatus.EXPIRED_LOSS
        
        # Update contract
        contract.exit_price = exit_price
        contract.settlement_timestamp = settlement_timestamp
        contract.profit_loss = profit_loss
        
        # Calculate duration
        duration_minutes = int(
            (settlement_timestamp - contract.entry_timestamp).total_seconds() / 60
        )
        
        # Create settlement record
        settlement = ContractSettlement(
            contract_id=contract_id,
            was_successful=was_successful,
            entry_price=contract.entry_price,
            exit_price=exit_price,
            price_change=price_change,
            price_change_percentage=price_change_pct,
            profit_loss=profit_loss,
            settlement_timestamp=settlement_timestamp,
            duration_minutes=duration_minutes
        )
        
        # Move to settled contracts
        del self.active_contracts[contract_id]
        self.settled_contracts.append(settlement)
        self.total_contracts_settled += 1
        self.total_profit_loss += profit_loss
        
        logger.info(
            "Event contract settled",
            contract_id=str(contract_id),
            was_successful=was_successful,
            entry_price=float(contract.entry_price),
            exit_price=float(exit_price),
            profit_loss=float(profit_loss),
            duration_minutes=duration_minutes
        )
        
        return settlement
    
    async def process_expired_contracts(self, current_data: HistoricalDataPoint) -> List[ContractSettlement]:
        """Process contracts that have expired based on current market data.
        
        Args:
            current_data: Current market data point
            
        Returns:
            List of settlements for expired contracts
        """
        settlements = []
        expired_contract_ids = []
        
        # Find expired contracts for this symbol
        for contract_id, contract in self.active_contracts.items():
            if (contract.symbol == current_data.symbol and 
                contract.expiry_timestamp <= current_data.timestamp):
                expired_contract_ids.append(contract_id)
        
        # Settle expired contracts
        for contract_id in expired_contract_ids:
            try:
                settlement = self.settle_contract(
                    contract_id=contract_id,
                    exit_price=current_data.close_price,
                    settlement_timestamp=current_data.timestamp
                )
                settlements.append(settlement)
            except Exception as e:
                logger.error(
                    "Failed to settle expired contract",
                    contract_id=str(contract_id),
                    error=str(e)
                )
        
        return settlements
    
    def get_active_contracts_for_symbol(self, symbol: str) -> List[EventContract]:
        """Get all active contracts for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of active contracts for the symbol
        """
        return [
            contract for contract in self.active_contracts.values()
            if contract.symbol == symbol
        ]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics.
        
        Returns:
            Dictionary with performance statistics
        """
        if self.total_contracts_settled == 0:
            return {
                "total_contracts_created": self.total_contracts_created,
                "total_contracts_settled": 0,
                "active_contracts": len(self.active_contracts),
                "win_rate": 0.0,
                "total_profit_loss": 0.0,
                "average_profit_per_contract": 0.0,
                "implied_probability_threshold": float(self.config.implied_probability_threshold)
            }
        
        # Calculate win rate
        winning_contracts = sum(
            1 for settlement in self.settled_contracts
            if settlement.was_successful
        )
        win_rate = winning_contracts / self.total_contracts_settled
        
        # Calculate average profit per contract
        avg_profit = self.total_profit_loss / self.total_contracts_settled
        
        return {
            "total_contracts_created": self.total_contracts_created,
            "total_contracts_settled": self.total_contracts_settled,
            "active_contracts": len(self.active_contracts),
            "winning_contracts": winning_contracts,
            "losing_contracts": self.total_contracts_settled - winning_contracts,
            "win_rate": float(win_rate),
            "total_profit_loss": float(self.total_profit_loss),
            "average_profit_per_contract": float(avg_profit),
            "implied_probability_threshold": float(self.config.implied_probability_threshold),
            "payout_percentage": float(self.config.payout_percentage),
            "breakeven_win_rate_required": float(self.calculate_implied_probability())
        }
    
    def reset(self) -> None:
        """Reset simulator state for new simulation."""
        self.active_contracts.clear()
        self.settled_contracts.clear()
        self.total_contracts_created = 0
        self.total_contracts_settled = 0
        self.total_profit_loss = Decimal('0.0')
        
        logger.info("EventContractSimulator reset")