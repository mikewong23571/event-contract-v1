from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID, uuid4
import logging

from ..models.event_contract import EventContract
from ..models.trading_signal import TradingSignal
from ..models.market_data import MarketData


class EventContractService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In production, these would be stored in a database
        self._contracts: Dict[UUID, EventContract] = {}
        self._symbol_contracts: Dict[str, List[UUID]] = {}
        self._active_contracts: List[UUID] = []

    def create_contract(
        self,
        contract_id: str,
        symbol: str,
        strike_price: Decimal,
        expiry_time: datetime,
        payout_ratio: Decimal,
        implied_probability: Optional[Decimal] = None
    ) -> EventContract:
        """Create a new event contract"""
        
        try:
            # Calculate implied probability if not provided
            if implied_probability is None:
                implied_probability = payout_ratio / (1 + payout_ratio)
            
            # Create contract
            contract = EventContract(
                contract_id=contract_id,
                symbol=symbol,
                strike_price=strike_price,
                expiry_time=expiry_time,
                payout_ratio=payout_ratio,
                implied_probability=implied_probability,
                status="ACTIVE"
            )
            
            # Store in memory (in production, this would be saved to database)
            self._contracts[contract.id] = contract
            if symbol not in self._symbol_contracts:
                self._symbol_contracts[symbol] = []
            self._symbol_contracts[symbol].append(contract.id)
            self._active_contracts.append(contract.id)
            
            self.logger.info(f"Created event contract {contract.id} for {symbol} with expiry {expiry_time}")
            return contract
            
        except Exception as e:
            self.logger.error(f"Error creating event contract for {symbol}: {e}")
            raise

    def get_contract(self, contract_id: UUID) -> Optional[EventContract]:
        """Get a specific contract by ID"""
        
        contract = self._contracts.get(contract_id)
        if not contract:
            self.logger.warning(f"Contract {contract_id} not found")
        return contract

    def get_contracts_by_symbol(self, symbol: str) -> List[EventContract]:
        """Get all contracts for a specific symbol"""
        
        try:
            contract_ids = self._symbol_contracts.get(symbol, [])
            contracts = [self._contracts[cid] for cid in contract_ids if cid in self._contracts]
            self.logger.debug(f"Retrieved {len(contracts)} contracts for symbol {symbol}")
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error retrieving contracts for symbol {symbol}: {e}")
            return []

    def get_active_contracts(self, symbol: Optional[str] = None) -> List[EventContract]:
        """Get all active contracts, optionally filtered by symbol"""
        
        try:
            active_contracts = []
            contract_ids = self._active_contracts if not symbol else self._symbol_contracts.get(symbol, [])
            
            for cid in contract_ids:
                if cid in self._contracts:
                    contract = self._contracts[cid]
                    # Check if still active
                    if contract.status == "ACTIVE":
                        # Check if expired
                        if contract.expiry_time > datetime.utcnow():
                            active_contracts.append(contract)
                        else:
                            # Auto-settle expired contracts
                            self._settle_expired_contract(contract)
            
            self.logger.debug(f"Retrieved {len(active_contracts)} active contracts")
            return active_contracts
            
        except Exception as e:
            self.logger.error(f"Error retrieving active contracts: {e}")
            return []

    def settle_contract(
        self,
        contract_id: UUID,
        settlement_price: Decimal
    ) -> Optional[EventContract]:
        """Settle a contract with actual settlement price"""
        
        try:
            if contract_id not in self._contracts:
                self.logger.warning(f"Contract {contract_id} not found for settlement")
                return None
            
            contract = self._contracts[contract_id]
            
            # Validate contract can be settled
            if contract.status != "ACTIVE":
                self.logger.warning(f"Contract {contract_id} cannot be settled, status is {contract.status}")
                return None
            
            # Update contract with settlement data
            contract.settlement_price = settlement_price
            contract.status = "SETTLED"
            contract.updated_at = datetime.utcnow()
            
            # Remove from active contracts list
            if contract_id in self._active_contracts:
                self._active_contracts.remove(contract_id)
            
            self.logger.info(f"Settled contract {contract_id} for {contract.symbol} at price {settlement_price}")
            return contract
            
        except Exception as e:
            self.logger.error(f"Error settling contract {contract_id}: {e}")
            return None

    def cancel_contract(self, contract_id: UUID) -> Optional[EventContract]:
        """Cancel a contract"""
        
        try:
            if contract_id not in self._contracts:
                self.logger.warning(f"Contract {contract_id} not found for cancellation")
                return None
            
            contract = self._contracts[contract_id]
            
            # Validate contract can be cancelled
            if contract.status != "ACTIVE":
                self.logger.warning(f"Contract {contract_id} cannot be cancelled, status is {contract.status}")
                return None
            
            # Update contract status
            contract.status = "CANCELLED"
            contract.updated_at = datetime.utcnow()
            
            # Remove from active contracts list
            if contract_id in self._active_contracts:
                self._active_contracts.remove(contract_id)
            
            self.logger.info(f"Cancelled contract {contract_id} for {contract.symbol}")
            return contract
            
        except Exception as e:
            self.logger.error(f"Error cancelling contract {contract_id}: {e}")
            return None

    def update_contract(
        self,
        contract_id: UUID,
        **updates
    ) -> Optional[EventContract]:
        """Update an existing contract"""
        
        try:
            if contract_id not in self._contracts:
                self.logger.warning(f"Contract {contract_id} not found for update")
                return None
            
            contract = self._contracts[contract_id]
            
            # Apply updates
            update_data = contract.dict()
            update_data.update(updates)
            update_data['updated_at'] = datetime.utcnow()
            
            # Validate updated contract
            updated_contract = EventContract(**update_data)
            self._contracts[contract_id] = updated_contract
            
            self.logger.info(f"Updated contract {contract_id} for {contract.symbol}")
            return updated_contract
            
        except Exception as e:
            self.logger.error(f"Error updating contract {contract_id}: {e}")
            return None

    def get_contracts_by_status(self, status: str) -> List[EventContract]:
        """Get all contracts with a specific status"""
        
        try:
            contracts = [contract for contract in self._contracts.values() if contract.status == status]
            self.logger.debug(f"Retrieved {len(contracts)} contracts with status {status}")
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error retrieving contracts with status {status}: {e}")
            return []

    def get_contracts_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None
    ) -> List[EventContract]:
        """Get contracts created within a date range"""
        
        try:
            contracts = []
            for contract in self._contracts.values():
                if start_date <= contract.created_at <= end_date:
                    if symbol is None or contract.symbol == symbol:
                        contracts.append(contract)
            
            self.logger.debug(f"Retrieved {len(contracts)} contracts in date range {start_date} to {end_date}")
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error retrieving contracts by date range: {e}")
            return []

    def validate_contract_pricing(
        self,
        contract: EventContract
    ) -> Tuple[bool, str]:
        """Validate contract pricing relationships"""
        
        try:
            # Check payout ratio validity
            if contract.payout_ratio <= 0:
                return False, "Invalid payout ratio - must be positive"
            
            # Check implied probability calculation
            expected_probability = contract.payout_ratio / (1 + contract.payout_ratio)
            if abs(contract.implied_probability - expected_probability) > Decimal('0.0001'):
                return False, f"Implied probability mismatch - expected {expected_probability}, got {contract.implied_probability}"
            
            # Check expiry time for active contracts
            if contract.status == "ACTIVE" and contract.expiry_time <= datetime.utcnow():
                return False, "Expiry time must be in the future for active contracts"
            
            # Check strike price
            if contract.strike_price <= 0:
                return False, "Invalid strike price - must be positive"
            
            return True, "Contract pricing is valid"
            
        except Exception as e:
            self.logger.error(f"Error validating contract pricing: {e}")
            return False, f"Validation error: {str(e)}"

    def get_contract_analytics(
        self,
        symbol: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for contracts"""
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            # Filter contracts by time range and symbol
            contracts = []
            for contract in self._contracts.values():
                if start_time <= contract.created_at <= end_time:
                    if symbol is None or contract.symbol == symbol:
                        contracts.append(contract)
            
            if not contracts:
                return {"error": "No contracts found for analytics"}
            
            # Calculate analytics
            total_contracts = len(contracts)
            active_contracts = len([c for c in contracts if c.status == "ACTIVE"])
            settled_contracts = len([c for c in contracts if c.status == "SETTLED"])
            cancelled_contracts = len([c for c in contracts if c.status == "CANCELLED"])
            
            # Calculate average payout ratio and implied probability
            total_payout = sum(c.payout_ratio for c in contracts)
            total_probability = sum(c.implied_probability for c in contracts)
            
            # Calculate settlement statistics
            settled_with_price = [c for c in contracts if c.status == "SETTLED" and c.settlement_price is not None]
            avg_settlement_price = sum(c.settlement_price for c in settled_with_price) / len(settled_with_price) if settled_with_price else Decimal('0')
            
            # Distribution by symbol
            symbol_distribution = {}
            for contract in contracts:
                symbol_distribution[contract.symbol] = symbol_distribution.get(contract.symbol, 0) + 1
            
            analytics = {
                "period_start": start_time,
                "period_end": end_time,
                "total_contracts": total_contracts,
                "active_contracts": active_contracts,
                "settled_contracts": settled_contracts,
                "cancelled_contracts": cancelled_contracts,
                "average_payout_ratio": float(total_payout / total_contracts) if total_contracts > 0 else 0,
                "average_implied_probability": float(total_probability / total_contracts) if total_contracts > 0 else 0,
                "average_settlement_price": float(avg_settlement_price),
                "symbol_distribution": symbol_distribution,
                "settlement_rate": settled_contracts / max(total_contracts, 1)
            }
            
            self.logger.info(f"Generated analytics for {total_contracts} contracts")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error generating contract analytics: {e}")
            return {"error": str(e)}

    def get_contract_performance(
        self,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for contracts"""
        
        try:
            # Filter settled contracts
            settled_contracts = [c for c in self._contracts.values() if c.status == "SETTLED" and c.settlement_price is not None]
            
            if symbol:
                settled_contracts = [c for c in settled_contracts if c.symbol == symbol]
            
            if not settled_contracts:
                return {"error": "No settled contracts found for performance analysis"}
            
            # Calculate performance metrics
            total_settled = len(settled_contracts)
            profitable_contracts = 0
            total_payout_value = Decimal('0')
            total_implied_value = Decimal('0')
            
            for contract in settled_contracts:
                # Determine if contract was profitable (simplified logic)
                # In a real implementation, this would depend on the specific contract terms
                if contract.settlement_price and contract.settlement_price > contract.strike_price:
                    profitable_contracts += 1
                    total_payout_value += contract.payout_ratio
                total_implied_value += contract.implied_probability
            
            performance_metrics = {
                "total_settled_contracts": total_settled,
                "profitable_contracts": profitable_contracts,
                "win_rate": profitable_contracts / max(total_settled, 1),
                "average_payout_value": float(total_payout_value / max(total_settled, 1)),
                "average_implied_value": float(total_implied_value / max(total_settled, 1)),
                "total_value_generated": float(total_payout_value),
                "value_realization_rate": float(total_payout_value / max(total_implied_value, Decimal('1')))
            }
            
            self.logger.info(f"Generated performance metrics for {total_settled} settled contracts")
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating contract performance: {e}")
            return {"error": str(e)}

    def link_signal_to_contract(
        self,
        signal_id: UUID,
        contract_id: UUID
    ) -> bool:
        """Link a trading signal to a contract (placeholder for future implementation)"""
        
        try:
            # In a full implementation, this would create a relationship between
            # a trading signal and an event contract in the database
            self.logger.info(f"Linked signal {signal_id} to contract {contract_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error linking signal {signal_id} to contract {contract_id}: {e}")
            return False

    def get_system_contract_metrics(self) -> Dict[str, Any]:
        """Get system-wide contract metrics"""
        
        try:
            total_contracts = len(self._contracts)
            active_contracts = len(self.get_active_contracts())
            settled_contracts = len(self.get_contracts_by_status("SETTLED"))
            cancelled_contracts = len(self.get_contracts_by_status("CANCELLED"))
            
            # Calculate contracts by symbol
            symbol_metrics = {}
            for symbol, contract_ids in self._symbol_contracts.items():
                symbol_metrics[symbol] = {
                    "total": len(contract_ids),
                    "active": len([cid for cid in contract_ids if cid in self._contracts and self._contracts[cid].status == "ACTIVE"]),
                    "settled": len([cid for cid in contract_ids if cid in self._contracts and self._contracts[cid].status == "SETTLED"]),
                    "cancelled": len([cid for cid in contract_ids if cid in self._contracts and self._contracts[cid].status == "CANCELLED"])
                }
            
            system_metrics = {
                "total_contracts": total_contracts,
                "active_contracts": active_contracts,
                "settled_contracts": settled_contracts,
                "cancelled_contracts": cancelled_contracts,
                "contracts_by_status": {
                    "ACTIVE": active_contracts,
                    "SETTLED": settled_contracts,
                    "CANCELLED": cancelled_contracts
                },
                "contracts_by_symbol": symbol_metrics,
                "timestamp": datetime.utcnow()
            }
            
            self.logger.info(f"System contract metrics: {total_contracts} total contracts")
            return system_metrics
            
        except Exception as e:
            self.logger.error(f"Error getting system contract metrics: {e}")
            return {"error": str(e)}

    def cleanup_expired_contracts(self) -> int:
        """Clean up expired contracts that haven't been settled"""
        
        try:
            current_time = datetime.utcnow()
            expired_count = 0
            
            for contract_id in self._active_contracts[:]:  # Copy list to avoid modification during iteration
                if contract_id in self._contracts:
                    contract = self._contracts[contract_id]
                    if contract.status == "ACTIVE" and contract.expiry_time <= current_time:
                        self._settle_expired_contract(contract)
                        expired_count += 1
            
            self.logger.info(f"Cleaned up {expired_count} expired contracts")
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired contracts: {e}")
            return 0

    def _settle_expired_contract(self, contract: EventContract) -> None:
        """Internal method to settle an expired contract"""
        
        try:
            contract.status = "SETTLED"
            contract.updated_at = datetime.utcnow()
            
            # Remove from active contracts list
            if contract.id in self._active_contracts:
                self._active_contracts.remove(contract.id)
            
            self.logger.info(f"Auto-settled expired contract {contract.id} for {contract.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error auto-settling expired contract {contract.id}: {e}")