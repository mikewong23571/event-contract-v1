from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID
import logging

from ..models.risk_parameters import RiskParameters
from ..models.trading_signal import TradingSignal
from ..models.performance_metrics import PerformanceMetrics
from ..lib.risk_management.risk_manager import RiskManager


class RiskManagementService:
    def __init__(self):
        self.risk_manager = RiskManager()
        self.logger = logging.getLogger(__name__)
        self._user_risk_params: Dict[str, RiskParameters] = {}
        self._position_tracking: Dict[str, List[Dict]] = {}
        self._daily_stats: Dict[str, Dict] = {}

    def create_risk_parameters(
        self,
        user_id: str,
        max_bet_size: Decimal,
        max_daily_bets: int,
        max_parallel_positions: int,
        min_probability_edge: Decimal,
        frequency_limit_minutes: int,
        max_daily_loss: Decimal
    ) -> RiskParameters:
        """Create new risk parameters for a user"""
        
        try:
            risk_params = RiskParameters(
                user_id=user_id,
                max_bet_size=max_bet_size,
                max_daily_bets=max_daily_bets,
                max_parallel_positions=max_parallel_positions,
                min_probability_edge=min_probability_edge,
                frequency_limit_minutes=frequency_limit_minutes,
                max_daily_loss=max_daily_loss
            )
            
            # Store in memory cache (in production, this would be saved to database)
            self._user_risk_params[user_id] = risk_params
            
            self.logger.info(f"Created risk parameters for user {user_id}")
            return risk_params
            
        except Exception as e:
            self.logger.error(f"Error creating risk parameters for user {user_id}: {e}")
            raise

    def update_risk_parameters(
        self,
        user_id: str,
        **updates
    ) -> Optional[RiskParameters]:
        """Update existing risk parameters for a user"""
        
        try:
            if user_id not in self._user_risk_params:
                self.logger.warning(f"Risk parameters not found for user {user_id}")
                return None
            
            current_params = self._user_risk_params[user_id]
            
            # Create updated parameters
            updated_data = current_params.dict()
            updated_data.update(updates)
            updated_data['updated_at'] = datetime.utcnow()
            
            new_params = RiskParameters(**updated_data)
            self._user_risk_params[user_id] = new_params
            
            self.logger.info(f"Updated risk parameters for user {user_id}")
            return new_params
            
        except Exception as e:
            self.logger.error(f"Error updating risk parameters for user {user_id}: {e}")
            return None

    def get_risk_parameters(self, user_id: str) -> Optional[RiskParameters]:
        """Get risk parameters for a user"""
        
        risk_params = self._user_risk_params.get(user_id)
        
        if not risk_params:
            self.logger.warning(f"Risk parameters not found for user {user_id}")
        
        return risk_params

    def validate_signal_risk(
        self,
        user_id: str,
        signal: TradingSignal
    ) -> Tuple[bool, str]:
        """Validate if a signal meets user's risk requirements"""
        
        try:
            # Get user's risk parameters
            risk_params = self.get_risk_parameters(user_id)
            if not risk_params:
                return False, "Risk parameters not found for user"
            
            # Get current user positions and daily stats
            current_positions = self._position_tracking.get(user_id, [])
            daily_stats = self._get_daily_stats(user_id)
            
            # Use risk manager to validate
            is_valid, message = self.risk_manager.validate_signal_risk(
                signal=signal,
                risk_params=risk_params,
                current_positions=current_positions,
                daily_stats=daily_stats
            )
            
            self.logger.info(f"Risk validation for user {user_id}, signal {signal.id}: {message}")
            return is_valid, message
            
        except Exception as e:
            self.logger.error(f"Error validating signal risk for user {user_id}: {e}")
            return False, f"Risk validation error: {str(e)}"

    def calculate_position_size(
        self,
        user_id: str,
        signal: TradingSignal,
        account_balance: Decimal
    ) -> Decimal:
        """Calculate appropriate position size for a signal"""
        
        try:
            risk_params = self.get_risk_parameters(user_id)
            if not risk_params:
                self.logger.warning(f"Risk parameters not found for user {user_id}, using default position size")
                return Decimal("10.0")  # Default minimum
            
            position_size = self.risk_manager.calculate_position_size(
                signal=signal,
                risk_params=risk_params,
                account_balance=account_balance
            )
            
            self.logger.info(f"Calculated position size for user {user_id}: ${position_size}")
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for user {user_id}: {e}")
            return Decimal("10.0")  # Fallback to minimum

    def assess_portfolio_risk(self, user_id: str) -> Dict[str, Any]:
        """Assess overall portfolio risk for a user"""
        
        try:
            risk_params = self.get_risk_parameters(user_id)
            if not risk_params:
                return {"error": "Risk parameters not found for user"}
            
            current_positions = self._position_tracking.get(user_id, [])
            
            risk_assessment = self.risk_manager.assess_portfolio_risk(
                current_positions=current_positions,
                risk_params=risk_params
            )
            
            # Add user-specific context
            risk_assessment["user_id"] = user_id
            risk_assessment["assessment_time"] = datetime.utcnow()
            
            self.logger.info(f"Portfolio risk assessment for user {user_id}: {risk_assessment['overall_risk_score']:.1f}/100")
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk for user {user_id}: {e}")
            return {"error": str(e)}

    def get_risk_suggestions(self, user_id: str) -> List[str]:
        """Get risk management suggestions for a user"""
        
        try:
            risk_assessment = self.assess_portfolio_risk(user_id)
            
            if "error" in risk_assessment:
                return ["Unable to generate suggestions due to missing risk data"]
            
            risk_params = self.get_risk_parameters(user_id)
            if not risk_params:
                return ["Set up risk parameters first"]
            
            suggestions = self.risk_manager.suggest_risk_adjustments(
                risk_assessment=risk_assessment,
                risk_params=risk_params
            )
            
            # Add time-based suggestions
            daily_stats = self._get_daily_stats(user_id)
            current_time = datetime.utcnow()
            
            # Check trading frequency
            if daily_stats.get("bet_count", 0) > risk_params.max_daily_bets * 0.8:
                suggestions.append("Approaching daily bet limit - consider selective trading")
            
            # Check time-based patterns
            if current_time.hour < 9 or current_time.hour > 21:
                suggestions.append("Trading outside market hours - consider increased caution")
            
            self.logger.info(f"Generated {len(suggestions)} risk suggestions for user {user_id}")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating risk suggestions for user {user_id}: {e}")
            return [f"Error generating suggestions: {str(e)}"]

    def perform_emergency_risk_check(
        self,
        user_id: str,
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """Perform emergency risk check for extreme conditions"""
        
        try:
            risk_params = self.get_risk_parameters(user_id)
            if not risk_params:
                return True, ["Emergency check failed - no risk parameters"]
            
            current_positions = self._position_tracking.get(user_id, [])
            
            # Use default market conditions if not provided
            if not market_conditions:
                market_conditions = {
                    "volatility": 0.05,  # 5% default volatility
                    "market_trend": "NEUTRAL"
                }
            
            emergency_triggered, emergency_actions = self.risk_manager.emergency_risk_check(
                current_positions=current_positions,
                risk_params=risk_params,
                market_conditions=market_conditions
            )
            
            if emergency_triggered:
                self.logger.warning(f"Emergency risk triggered for user {user_id}: {emergency_actions}")
                # In production, this would trigger notifications, automatic position closures, etc.
                self._handle_emergency_response(user_id, emergency_actions)
            
            return emergency_triggered, emergency_actions
            
        except Exception as e:
            self.logger.error(f"Error in emergency risk check for user {user_id}: {e}")
            return True, [f"Emergency check error: {str(e)}"]

    def add_position(
        self,
        user_id: str,
        position_data: Dict[str, Any]
    ) -> bool:
        """Add a new position to tracking"""
        
        try:
            if user_id not in self._position_tracking:
                self._position_tracking[user_id] = []
            
            # Add position with tracking metadata
            position_data["created_at"] = datetime.utcnow()
            position_data["status"] = "active"
            
            self._position_tracking[user_id].append(position_data)
            
            # Update daily stats
            self._update_daily_stats(user_id, "position_opened", position_data)
            
            self.logger.info(f"Added position for user {user_id}: {position_data.get('symbol', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding position for user {user_id}: {e}")
            return False

    def close_position(
        self,
        user_id: str,
        position_id: str,
        exit_price: Decimal,
        reason: str = "MANUAL_CLOSE"
    ) -> bool:
        """Close an existing position"""
        
        try:
            positions = self._position_tracking.get(user_id, [])
            
            for position in positions:
                if position.get("id") == position_id:
                    position["status"] = "closed"
                    position["closed_at"] = datetime.utcnow()
                    position["exit_price"] = exit_price
                    position["close_reason"] = reason
                    
                    # Calculate P&L
                    entry_price = position.get("entry_price", Decimal("0"))
                    position_size = position.get("size", Decimal("0"))
                    direction = position.get("direction", "UP")
                    
                    if direction == "UP":
                        pnl = (exit_price - entry_price) * position_size
                    else:
                        pnl = (entry_price - exit_price) * position_size
                    
                    position["realized_pnl"] = pnl
                    
                    # Update daily stats
                    self._update_daily_stats(user_id, "position_closed", position)
                    
                    self.logger.info(f"Closed position {position_id} for user {user_id}: P&L ${pnl}")
                    return True
            
            self.logger.warning(f"Position {position_id} not found for user {user_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing position for user {user_id}: {e}")
            return False

    def get_user_positions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get user's positions"""
        
        positions = self._position_tracking.get(user_id, [])
        
        if active_only:
            positions = [p for p in positions if p.get("status") == "active"]
        
        self.logger.debug(f"Retrieved {len(positions)} positions for user {user_id}")
        return positions

    def get_daily_risk_summary(self, user_id: str) -> Dict[str, Any]:
        """Get daily risk summary for a user"""
        
        try:
            daily_stats = self._get_daily_stats(user_id)
            risk_params = self.get_risk_parameters(user_id)
            
            if not risk_params:
                return {"error": "Risk parameters not configured"}
            
            active_positions = self.get_user_positions(user_id, active_only=True)
            
            summary = {
                "user_id": user_id,
                "date": datetime.utcnow().date(),
                "daily_bets": daily_stats.get("bet_count", 0),
                "max_daily_bets": risk_params.max_daily_bets,
                "bets_remaining": max(0, risk_params.max_daily_bets - daily_stats.get("bet_count", 0)),
                "active_positions": len(active_positions),
                "max_parallel_positions": risk_params.max_parallel_positions,
                "daily_pnl": daily_stats.get("total_pnl", Decimal("0")),
                "max_daily_loss": risk_params.max_daily_loss,
                "loss_limit_remaining": risk_params.max_daily_loss + daily_stats.get("total_pnl", Decimal("0")),
                "last_signal_time": daily_stats.get("last_signal_time"),
                "frequency_limit_minutes": risk_params.frequency_limit_minutes,
                "risk_status": "HEALTHY"
            }
            
            # Determine risk status
            if summary["daily_pnl"] <= -risk_params.max_daily_loss:
                summary["risk_status"] = "DAILY_LOSS_LIMIT_EXCEEDED"
            elif summary["daily_bets"] >= risk_params.max_daily_bets:
                summary["risk_status"] = "DAILY_BET_LIMIT_REACHED"
            elif len(active_positions) >= risk_params.max_parallel_positions:
                summary["risk_status"] = "MAX_POSITIONS_REACHED"
            elif summary["daily_pnl"] <= -risk_params.max_daily_loss * 0.8:
                summary["risk_status"] = "WARNING_HIGH_LOSS"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating daily risk summary for user {user_id}: {e}")
            return {"error": str(e)}

    def reset_daily_limits(self, user_id: str) -> bool:
        """Reset daily limits for a user (typically called at midnight)"""
        
        try:
            self._daily_stats[user_id] = {
                "bet_count": 0,
                "total_pnl": Decimal("0"),
                "last_signal_time": None,
                "positions_opened": 0,
                "positions_closed": 0,
                "reset_time": datetime.utcnow()
            }
            
            self.logger.info(f"Reset daily limits for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting daily limits for user {user_id}: {e}")
            return False

    def _get_daily_stats(self, user_id: str) -> Dict[str, Any]:
        """Get or initialize daily stats for a user"""
        
        if user_id not in self._daily_stats:
            self._daily_stats[user_id] = {
                "bet_count": 0,
                "total_pnl": Decimal("0"),
                "last_signal_time": None,
                "positions_opened": 0,
                "positions_closed": 0
            }
        
        return self._daily_stats[user_id]

    def _update_daily_stats(self, user_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Update daily statistics based on events"""
        
        try:
            stats = self._get_daily_stats(user_id)
            
            if event_type == "position_opened":
                stats["bet_count"] += 1
                stats["positions_opened"] += 1
                stats["last_signal_time"] = datetime.utcnow()
                
            elif event_type == "position_closed":
                stats["positions_closed"] += 1
                pnl = data.get("realized_pnl", Decimal("0"))
                stats["total_pnl"] += pnl
            
            self._daily_stats[user_id] = stats
            
        except Exception as e:
            self.logger.error(f"Error updating daily stats for user {user_id}: {e}")

    def _handle_emergency_response(self, user_id: str, emergency_actions: List[str]) -> None:
        """Handle emergency response actions"""
        
        try:
            self.logger.critical(f"Emergency response triggered for user {user_id}")
            
            # In production, this would:
            # 1. Send immediate notifications
            # 2. Automatically close risky positions
            # 3. Temporarily disable trading
            # 4. Alert risk management team
            # 5. Log to emergency response system
            
            # For now, just log the actions
            for action in emergency_actions:
                self.logger.critical(f"Emergency action for user {user_id}: {action}")
            
        except Exception as e:
            self.logger.error(f"Error handling emergency response for user {user_id}: {e}")

    def get_system_risk_metrics(self) -> Dict[str, Any]:
        """Get system-wide risk metrics"""
        
        try:
            total_users = len(self._user_risk_params)
            total_positions = sum(len(positions) for positions in self._position_tracking.values())
            active_positions = sum(
                len([p for p in positions if p.get("status") == "active"])
                for positions in self._position_tracking.values()
            )
            
            # Calculate system-wide P&L
            total_daily_pnl = sum(
                stats.get("total_pnl", Decimal("0"))
                for stats in self._daily_stats.values()
            )
            
            system_metrics = {
                "total_users_with_risk_params": total_users,
                "total_positions": total_positions,
                "active_positions": active_positions,
                "system_daily_pnl": float(total_daily_pnl),
                "average_positions_per_user": total_positions / max(total_users, 1),
                "timestamp": datetime.utcnow()
            }
            
            self.logger.info(f"System risk metrics: {total_users} users, {active_positions} active positions")
            return system_metrics
            
        except Exception as e:
            self.logger.error(f"Error getting system risk metrics: {e}")
            return {"error": str(e)}