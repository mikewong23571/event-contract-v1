from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID
import logging

from ..models.trading_signal import TradingSignal
from ..models.market_data import MarketData
from ..models.risk_parameters import RiskParameters
from ..lib.signal_generation.signal_generator import SignalGenerator
from ..lib.risk_management.risk_manager import RiskManager


class SignalService:
    def __init__(self, strategy_version: str = "v1.0"):
        self.signal_generator = SignalGenerator(strategy_version)
        self.risk_manager = RiskManager()
        self.logger = logging.getLogger(__name__)

    def generate_signal(
        self,
        symbol: str,
        market_data: List[MarketData],
        risk_params: Optional[RiskParameters] = None,
        expiry_minutes: int = 15
    ) -> Optional[TradingSignal]:
        """Generate a single trading signal for a symbol"""
        
        try:
            self.logger.info(f"Generating signal for {symbol} with {len(market_data)} data points")
            
            # Generate raw signal using signal generator
            signal = self.signal_generator.generate_signal(
                market_data=market_data,
                symbol=symbol,
                expiry_minutes=expiry_minutes
            )
            
            if not signal:
                self.logger.info(f"No signal generated for {symbol}")
                return None
            
            # Validate signal quality
            if not self.signal_generator.validate_signal_quality(signal):
                self.logger.warning(f"Generated signal for {symbol} failed quality validation")
                return None
            
            # Apply risk management if risk parameters provided
            if risk_params:
                is_valid, risk_message = self._validate_signal_against_risk(signal, risk_params)
                if not is_valid:
                    self.logger.info(f"Signal for {symbol} rejected by risk management: {risk_message}")
                    return None
            
            self.logger.info(f"Successfully generated signal for {symbol}: {signal.direction} @ {signal.predicted_probability:.3f}")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return None

    def batch_generate_signals(
        self,
        symbols_data: Dict[str, List[MarketData]],
        risk_params: Optional[RiskParameters] = None,
        expiry_minutes: int = 15,
        max_signals: Optional[int] = None
    ) -> List[TradingSignal]:
        """Generate signals for multiple symbols in batch"""
        
        self.logger.info(f"Batch generating signals for {len(symbols_data)} symbols")
        
        signals = []
        processed_count = 0
        
        try:
            for symbol, market_data in symbols_data.items():
                if max_signals and len(signals) >= max_signals:
                    self.logger.info(f"Reached maximum signals limit ({max_signals})")
                    break
                
                signal = self.generate_signal(
                    symbol=symbol,
                    market_data=market_data,
                    risk_params=risk_params,
                    expiry_minutes=expiry_minutes
                )
                
                if signal:
                    signals.append(signal)
                
                processed_count += 1
            
            self.logger.info(f"Batch processing complete: {len(signals)} signals generated from {processed_count} symbols")
            return signals
            
        except Exception as e:
            self.logger.error(f"Error in batch signal generation: {e}")
            return signals

    def get_active_signals(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[TradingSignal]:
        """Get active (non-expired) signals"""
        
        # This would typically query from database
        # For now, return empty list as placeholder
        self.logger.info(f"Retrieving active signals for user: {user_id}, symbol: {symbol}")
        return []

    def get_signal_by_id(self, signal_id: UUID) -> Optional[TradingSignal]:
        """Get a specific signal by ID"""
        
        # This would typically query from database
        # For now, return None as placeholder
        self.logger.info(f"Retrieving signal by ID: {signal_id}")
        return None

    def get_signal_history(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TradingSignal]:
        """Get historical signals with filters"""
        
        # This would typically query from database with filters
        # For now, return empty list as placeholder
        self.logger.info(f"Retrieving signal history for user: {user_id}, symbol: {symbol}")
        return []

    def validate_signal_expiry(self, signal: TradingSignal) -> bool:
        """Check if a signal has expired"""
        
        current_time = datetime.utcnow()
        is_expired = current_time >= signal.expires_at
        
        if is_expired:
            self.logger.debug(f"Signal {signal.id} has expired at {signal.expires_at}")
        
        return not is_expired

    def calculate_signal_performance(
        self,
        signals: List[TradingSignal],
        actual_outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a list of signals"""
        
        if not signals or not actual_outcomes:
            return {
                "total_signals": 0,
                "successful_signals": 0,
                "win_rate": 0.0,
                "average_probability": 0.0,
                "confidence_breakdown": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            }
        
        try:
            total_signals = len(signals)
            successful_signals = 0
            probability_sum = 0.0
            confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            
            # Match signals with outcomes (simplified matching by timestamp/symbol)
            for signal in signals:
                probability_sum += signal.predicted_probability
                confidence_counts[signal.confidence_level] += 1
                
                # Find matching outcome
                matching_outcome = None
                for outcome in actual_outcomes:
                    if (outcome.get("symbol") == signal.symbol and 
                        abs((outcome.get("timestamp", datetime.min) - signal.timestamp).total_seconds()) < 300):
                        matching_outcome = outcome
                        break
                
                if matching_outcome:
                    # Check if signal prediction was correct
                    predicted_direction = signal.direction
                    actual_direction = matching_outcome.get("direction", "UNKNOWN")
                    
                    if predicted_direction == actual_direction:
                        successful_signals += 1
            
            win_rate = successful_signals / total_signals if total_signals > 0 else 0.0
            average_probability = probability_sum / total_signals if total_signals > 0 else 0.0
            
            performance_metrics = {
                "total_signals": total_signals,
                "successful_signals": successful_signals,
                "win_rate": win_rate,
                "average_probability": average_probability,
                "confidence_breakdown": confidence_counts,
                "accuracy_by_confidence": self._calculate_accuracy_by_confidence(signals, actual_outcomes)
            }
            
            self.logger.info(f"Signal performance calculated: {win_rate:.1%} win rate from {total_signals} signals")
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating signal performance: {e}")
            return {
                "total_signals": len(signals),
                "successful_signals": 0,
                "win_rate": 0.0,
                "average_probability": 0.0,
                "confidence_breakdown": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "error": str(e)
            }

    def get_signal_analytics(
        self,
        signals: List[TradingSignal],
        time_period: str = "24h"
    ) -> Dict[str, Any]:
        """Get analytics and insights for signals"""
        
        if not signals:
            return {"error": "No signals provided for analytics"}
        
        try:
            current_time = datetime.utcnow()
            
            # Filter signals by time period
            if time_period == "24h":
                cutoff_time = current_time - timedelta(hours=24)
            elif time_period == "7d":
                cutoff_time = current_time - timedelta(days=7)
            elif time_period == "30d":
                cutoff_time = current_time - timedelta(days=30)
            else:
                cutoff_time = current_time - timedelta(hours=24)
            
            filtered_signals = [s for s in signals if s.timestamp >= cutoff_time]
            
            if not filtered_signals:
                return {"error": f"No signals found in the last {time_period}"}
            
            # Calculate analytics
            total_signals = len(filtered_signals)
            symbol_distribution = {}
            direction_distribution = {"UP": 0, "DOWN": 0}
            confidence_distribution = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            avg_probability = sum(s.predicted_probability for s in filtered_signals) / total_signals
            
            for signal in filtered_signals:
                symbol_distribution[signal.symbol] = symbol_distribution.get(signal.symbol, 0) + 1
                direction_distribution[signal.direction] += 1
                confidence_distribution[signal.confidence_level] += 1
            
            # Signal frequency analysis
            time_range = (max(s.timestamp for s in filtered_signals) - min(s.timestamp for s in filtered_signals)).total_seconds() / 3600
            signals_per_hour = total_signals / max(time_range, 1)
            
            analytics = {
                "time_period": time_period,
                "total_signals": total_signals,
                "average_probability": avg_probability,
                "signals_per_hour": signals_per_hour,
                "symbol_distribution": symbol_distribution,
                "direction_distribution": direction_distribution,
                "confidence_distribution": confidence_distribution,
                "most_active_symbol": max(symbol_distribution.items(), key=lambda x: x[1])[0] if symbol_distribution else None,
                "directional_bias": "UP" if direction_distribution["UP"] > direction_distribution["DOWN"] else "DOWN"
            }
            
            self.logger.info(f"Signal analytics generated for {total_signals} signals in {time_period}")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error generating signal analytics: {e}")
            return {"error": str(e)}

    def cleanup_expired_signals(self) -> int:
        """Remove expired signals from storage"""
        
        # This would typically query and delete expired signals from database
        # For now, return 0 as placeholder
        self.logger.info("Cleaning up expired signals")
        return 0

    def _validate_signal_against_risk(
        self, 
        signal: TradingSignal, 
        risk_params: RiskParameters
    ) -> Tuple[bool, str]:
        """Validate signal against risk parameters"""
        
        try:
            # Get current portfolio state (placeholder data)
            current_positions = []  # Would fetch from database
            daily_stats = {
                "bet_count": 0,
                "total_pnl": Decimal("0"),
                "last_signal_time": None
            }
            
            # Use risk manager to validate
            return self.risk_manager.validate_signal_risk(
                signal=signal,
                risk_params=risk_params,
                current_positions=current_positions,
                daily_stats=daily_stats
            )
            
        except Exception as e:
            self.logger.error(f"Error validating signal against risk: {e}")
            return False, f"Risk validation error: {str(e)}"

    def _calculate_accuracy_by_confidence(
        self,
        signals: List[TradingSignal],
        actual_outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate accuracy metrics broken down by confidence level"""
        
        accuracy_by_confidence = {
            "HIGH": {"total": 0, "correct": 0, "accuracy": 0.0},
            "MEDIUM": {"total": 0, "correct": 0, "accuracy": 0.0},
            "LOW": {"total": 0, "correct": 0, "accuracy": 0.0}
        }
        
        try:
            for signal in signals:
                confidence = signal.confidence_level
                accuracy_by_confidence[confidence]["total"] += 1
                
                # Find matching outcome
                for outcome in actual_outcomes:
                    if (outcome.get("symbol") == signal.symbol and 
                        abs((outcome.get("timestamp", datetime.min) - signal.timestamp).total_seconds()) < 300):
                        if outcome.get("direction") == signal.direction:
                            accuracy_by_confidence[confidence]["correct"] += 1
                        break
            
            # Calculate accuracy percentages
            for confidence in accuracy_by_confidence:
                data = accuracy_by_confidence[confidence]
                if data["total"] > 0:
                    data["accuracy"] = data["correct"] / data["total"]
            
            return accuracy_by_confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating accuracy by confidence: {e}")
            return accuracy_by_confidence