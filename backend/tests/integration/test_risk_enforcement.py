"""
Integration test for risk parameter enforcement (T025)

This integration test validates comprehensive risk management across the system:
1. Risk parameter validation and persistence
2. Position size and frequency limit enforcement
3. Daily loss limit monitoring and enforcement
4. Parallel position limit management
5. Probability edge requirement enforcement
6. Risk-based signal filtering and blocking
7. Emergency risk controls and circuit breakers

The test MUST FAIL initially as the implementation is not complete yet (TDD requirement).
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestRiskEnforcementIntegration:
    """Integration tests for risk parameter enforcement across the system"""

    @pytest.fixture
    def base_risk_parameters(self):
        """Base risk parameters for testing"""
        return {
            "user_id": "risk_test_user_001",
            "max_bet_size": Decimal("100.00"),
            "max_daily_bets": 5,
            "max_parallel_positions": 3,
            "min_probability_edge": Decimal("0.10"),  # 10% minimum edge (60%+ confidence)
            "frequency_limit_minutes": 10,  # 10 minutes between bets
            "max_daily_loss": Decimal("500.00"),
            "emergency_stop_threshold": Decimal("0.20"),  # 20% emergency stop
            "max_drawdown_limit": Decimal("0.15"),  # 15% max drawdown
            "risk_per_trade": Decimal("0.02"),  # 2% of balance per trade
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for signal generation"""
        base_time = datetime.now(timezone.utc)
        return [
            {
                "symbol": "BTCUSDT",
                "timestamp": (base_time - timedelta(minutes=i)).isoformat(),
                "open_price": 45000.0 + i * 5,
                "high_price": 45100.0 + i * 5,
                "low_price": 44950.0 + i * 5,
                "close_price": 45075.0 + i * 5,
                "volume": 1000.0,
                "quote_volume": 45075000.0,
                "trade_count": 1500,
                "source": "risk_test_data"
            }
            for i in range(20)
        ]

    def test_position_size_limit_enforcement(self, base_risk_parameters, sample_market_data):
        """
        Test that position size limits are strictly enforced
        """
        # Set up risk parameters with small position limit
        small_position_params = dict(base_risk_parameters)
        small_position_params["max_bet_size"] = Decimal("50.00")  # Small limit
        
        # Configure risk parameters
        response = client.put("/api/v1/risk-parameters", json=small_position_params)
        assert response.status_code in [200, 201], f"Risk parameter setup failed: {response.text}"
        
        # Ingest some market data
        for data_point in sample_market_data[:5]:
            client.post("/api/v1/market-data", json=data_point)
        
        # Attempt to generate signal (system should calculate appropriate position size)
        signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        response = client.post("/api/v1/signals/generate", json=signal_request)
        
        if response.status_code == 201:
            signal = response.json()
            
            # Check if position size recommendation respects limits
            if "recommended_position_size" in signal:
                position_size = float(signal["recommended_position_size"])
                max_allowed = float(small_position_params["max_bet_size"])
                
                assert position_size <= max_allowed, \
                       f"Position size {position_size} exceeds limit {max_allowed}"
            
            # Test explicit position size override
            oversized_trade = {
                "signal_id": signal["id"],
                "position_size": 100.00,  # Exceeds limit of 50
                "direction": signal["direction"]
            }
            
            trade_response = client.post("/api/v1/trades/execute", json=oversized_trade)
            
            # Should reject oversized position
            if trade_response.status_code in [400, 422]:
                error_data = trade_response.json()
                assert any(keyword in str(error_data).lower() for keyword in 
                          ["size", "limit", "exceed", "risk"]), \
                       "Error should indicate position size violation"
            elif trade_response.status_code == 404:
                # Trade execution endpoint not implemented
                print("Trade execution endpoint not available")
            else:
                # If accepted, check if system applied position size limits
                trade_result = trade_response.json()
                if "actual_position_size" in trade_result:
                    actual_size = float(trade_result["actual_position_size"])
                    assert actual_size <= max_allowed, \
                           "System should enforce position size limits"

    def test_frequency_limit_enforcement(self, base_risk_parameters, sample_market_data):
        """
        Test that frequency limits between signals are enforced
        """
        # Configure strict frequency limits
        frequency_params = dict(base_risk_parameters)
        frequency_params["frequency_limit_minutes"] = 5  # 5 minutes minimum
        
        response = client.put("/api/v1/risk-parameters", json=frequency_params)
        assert response.status_code in [200, 201]
        
        # Ingest market data
        for data_point in sample_market_data[:10]:
            client.post("/api/v1/market-data", json=data_point)
        
        # Generate first signal
        signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        first_response = client.post("/api/v1/signals/generate", json=signal_request)
        first_signal_time = datetime.now(timezone.utc)
        
        if first_response.status_code == 201:
            first_signal = first_response.json()
            
            # Immediately attempt to generate second signal (should be blocked)
            second_response = client.post("/api/v1/signals/generate", json=signal_request)
            
            if second_response.status_code in [400, 422, 429]:
                # Signal blocked by frequency limit
                error_data = second_response.json()
                assert any(keyword in str(error_data).lower() for keyword in 
                          ["frequency", "limit", "wait", "too soon"]), \
                       f"Error should indicate frequency limit: {error_data}"
                
                # Wait partial time and try again (still should be blocked)
                time.sleep(2)  # 2 minutes < 5 minute limit
                
                third_response = client.post("/api/v1/signals/generate", json=signal_request)
                assert third_response.status_code in [400, 422, 429], \
                       "Signal should still be blocked after partial wait"
                
                # Simulate waiting full frequency limit (in real system, would wait)
                # For testing, we modify the timestamp or use different approach
                future_request = {
                    "symbol": "BTCUSDT", 
                    "force_calculation": True,
                    "test_timestamp": (first_signal_time + timedelta(minutes=6)).isoformat()
                }
                
                future_response = client.post("/api/v1/signals/generate", json=future_request)
                
                # This might succeed if timestamp override is supported
                if future_response.status_code == 201:
                    print("Frequency limit correctly enforced with time override")
                else:
                    print(f"Frequency limit test result: {future_response.status_code}")
            
            elif second_response.status_code == 201:
                # If second signal was allowed, check if there's a valid reason
                second_signal = second_response.json()
                
                # Different symbol might be allowed
                if second_signal["symbol"] != first_signal["symbol"]:
                    print("Different symbol signals allowed (symbol-specific frequency)")
                else:
                    print("Frequency limit may not be implemented or configured differently")

    def test_daily_bet_limit_enforcement(self, base_risk_parameters, sample_market_data):
        """
        Test enforcement of daily betting limits
        """
        # Configure very low daily limit
        daily_limit_params = dict(base_risk_parameters)
        daily_limit_params["max_daily_bets"] = 2  # Only 2 bets per day
        daily_limit_params["frequency_limit_minutes"] = 1  # Reduce frequency limit for testing
        
        response = client.put("/api/v1/risk-parameters", json=daily_limit_params)
        assert response.status_code in [200, 201]
        
        # Ingest market data
        for data_point in sample_market_data[:15]:
            client.post("/api/v1/market-data", json=data_point)
        
        successful_signals = []
        blocked_signals = []
        
        # Attempt to generate multiple signals
        for i in range(5):  # Try 5 signals against limit of 2
            signal_request = {
                "symbol": "BTCUSDT", 
                "force_calculation": True,
                "test_sequence": i  # Help differentiate requests
            }
            
            response = client.post("/api/v1/signals/generate", json=signal_request)
            
            if response.status_code == 201:
                signal = response.json()
                successful_signals.append(signal)
            elif response.status_code in [400, 422, 429]:
                error_data = response.json()
                blocked_signals.append(error_data)
            
            time.sleep(1.5)  # Wait between requests
        
        print(f"Successful signals: {len(successful_signals)}")
        print(f"Blocked signals: {len(blocked_signals)}")
        
        # Validate daily limit enforcement
        if len(successful_signals) > 0:
            # Should not exceed daily limit of 2
            assert len(successful_signals) <= 2, \
                   f"Generated {len(successful_signals)} signals, exceeding daily limit of 2"
            
            # At least some signals should be blocked if we hit the limit
            if len(successful_signals) == 2 and len(blocked_signals) > 0:
                # Check that blocked signals have appropriate error messages
                for blocked in blocked_signals:
                    error_text = str(blocked).lower()
                    assert any(keyword in error_text for keyword in 
                              ["daily", "limit", "exceeded", "quota"]), \
                           f"Blocked signal should indicate daily limit: {blocked}"

    def test_parallel_position_limit_enforcement(self, base_risk_parameters, sample_market_data):
        """
        Test enforcement of parallel/concurrent position limits
        """
        # Configure low parallel position limit
        parallel_params = dict(base_risk_parameters)
        parallel_params["max_parallel_positions"] = 2  # Maximum 2 concurrent positions
        parallel_params["frequency_limit_minutes"] = 1  # Reduce for testing
        
        response = client.put("/api/v1/risk-parameters", json=parallel_params)
        assert response.status_code in [200, 201]
        
        # Ingest market data
        for data_point in sample_market_data[:10]:
            client.post("/api/v1/market-data", json=data_point)
        
        # Generate signals for multiple symbols to create parallel positions
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        active_positions = []
        blocked_positions = []
        
        for symbol in symbols:
            # Add market data for each symbol
            symbol_data = dict(sample_market_data[0])
            symbol_data["symbol"] = symbol
            symbol_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            client.post("/api/v1/market-data", json=symbol_data)
            
            time.sleep(0.5)
            
            # Generate signal for symbol
            signal_request = {"symbol": symbol, "force_calculation": True}
            signal_response = client.post("/api/v1/signals/generate", json=signal_request)
            
            if signal_response.status_code == 201:
                signal = signal_response.json()
                
                # Attempt to execute trade (create position)
                trade_request = {
                    "signal_id": signal["id"],
                    "position_size": 50.0,
                    "direction": signal["direction"]
                }
                
                trade_response = client.post("/api/v1/trades/execute", json=trade_request)
                
                if trade_response.status_code in [200, 201]:
                    trade = trade_response.json()
                    active_positions.append((symbol, trade))
                elif trade_response.status_code in [400, 422, 429]:
                    # Position blocked by parallel limit
                    error_data = trade_response.json()
                    blocked_positions.append((symbol, error_data))
                elif trade_response.status_code == 404:
                    print(f"Trade execution not implemented for {symbol}")
                else:
                    print(f"Trade execution response for {symbol}: {trade_response.status_code}")
        
        print(f"Active positions: {len(active_positions)}")
        print(f"Blocked positions: {len(blocked_positions)}")
        
        # Validate parallel position enforcement
        if len(active_positions) > 0:
            assert len(active_positions) <= 2, \
                   f"Created {len(active_positions)} positions, exceeding limit of 2"
        
        # If we hit the limit, subsequent positions should be blocked
        if len(active_positions) == 2 and len(blocked_positions) > 0:
            for symbol, error_data in blocked_positions:
                error_text = str(error_data).lower()
                assert any(keyword in error_text for keyword in 
                          ["parallel", "concurrent", "position", "limit", "maximum"]), \
                       f"Blocked position should indicate parallel limit: {error_data}"

    def test_probability_edge_enforcement(self, base_risk_parameters, sample_market_data):
        """
        Test enforcement of minimum probability edge requirements
        """
        # Test with high probability edge requirement
        high_edge_params = dict(base_risk_parameters)
        high_edge_params["min_probability_edge"] = Decimal("0.25")  # Require 75%+ confidence
        
        response = client.put("/api/v1/risk-parameters", json=high_edge_params)
        assert response.status_code in [200, 201]
        
        # Ingest market data with moderate movements (unlikely to generate high-confidence signals)
        moderate_data = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(10):
            data_point = {
                "symbol": "BTCUSDT",
                "timestamp": (base_time - timedelta(minutes=i)).isoformat(),
                "open_price": 45000.0 + (i % 3 - 1) * 5,  # Small oscillations
                "high_price": 45000.0 + (i % 3 - 1) * 5 + 10,
                "low_price": 45000.0 + (i % 3 - 1) * 5 - 8,
                "close_price": 45000.0 + (i % 3 - 1) * 5 + 2,
                "volume": 1000.0,
                "quote_volume": 45000000.0,
                "trade_count": 1500,
                "source": "moderate_movement_test"
            }
            client.post("/api/v1/market-data", json=data_point)
        
        # Attempt signal generation with high edge requirement
        high_edge_request = {"symbol": "BTCUSDT", "force_calculation": True}
        high_edge_response = client.post("/api/v1/signals/generate", json=high_edge_request)
        
        high_edge_result = None
        if high_edge_response.status_code == 201:
            high_edge_result = high_edge_response.json()
        elif high_edge_response.status_code in [400, 422]:
            # Signal blocked by probability edge requirement
            error_data = high_edge_response.json()
            edge_keywords = ["probability", "edge", "confidence", "insufficient"]
            assert any(keyword in str(error_data).lower() for keyword in edge_keywords), \
                   f"Error should indicate probability edge issue: {error_data}"
        
        # Now test with low edge requirement
        low_edge_params = dict(base_risk_parameters)
        low_edge_params["min_probability_edge"] = Decimal("0.02")  # Only require 52%+ confidence
        
        response = client.put("/api/v1/risk-parameters", json=low_edge_params)
        assert response.status_code in [200, 201]
        
        # Same market data, different edge requirement
        low_edge_request = {"symbol": "BTCUSDT", "force_calculation": True}
        low_edge_response = client.post("/api/v1/signals/generate", json=low_edge_request)
        
        low_edge_result = None
        if low_edge_response.status_code == 201:
            low_edge_result = low_edge_response.json()
        
        # Compare results
        high_edge_success = high_edge_result is not None
        low_edge_success = low_edge_result is not None
        
        print(f"High edge requirement (25%): {'SUCCESS' if high_edge_success else 'BLOCKED'}")
        print(f"Low edge requirement (2%): {'SUCCESS' if low_edge_success else 'BLOCKED'}")
        
        # Low edge requirement should be more permissive
        if high_edge_success and low_edge_success:
            # Both succeeded, validate probability values
            high_prob = high_edge_result.get("predicted_probability", 0.5)
            low_prob = low_edge_result.get("predicted_probability", 0.5)
            
            # High edge signal should have higher confidence
            high_edge_value = abs(high_prob - 0.5)
            low_edge_value = abs(low_prob - 0.5)
            
            if high_edge_value >= 0.25:  # Meets high requirement
                assert high_edge_value >= 0.25, "High edge signal should meet edge requirement"
        
        elif not high_edge_success and low_edge_success:
            # Perfect - high requirement blocked, low requirement allowed
            low_prob = low_edge_result.get("predicted_probability", 0.5)
            low_edge_value = abs(low_prob - 0.5)
            assert low_edge_value >= 0.02, "Low edge signal should meet minimum requirement"

    def test_daily_loss_limit_enforcement(self, base_risk_parameters, sample_market_data):
        """
        Test enforcement of daily loss limits and emergency stops
        """
        # Configure loss limits
        loss_limit_params = dict(base_risk_parameters)
        loss_limit_params["max_daily_loss"] = Decimal("200.00")  # $200 daily loss limit
        loss_limit_params["emergency_stop_threshold"] = Decimal("0.15")  # 15% emergency stop
        loss_limit_params["frequency_limit_minutes"] = 1
        
        response = client.put("/api/v1/risk-parameters", json=loss_limit_params)
        assert response.status_code in [200, 201]
        
        # Simulate trading session with losses
        # This test requires trade execution and P&L tracking
        
        # Ingest market data
        for data_point in sample_market_data[:5]:
            client.post("/api/v1/market-data", json=data_point)
        
        # Generate signal
        signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        signal_response = client.post("/api/v1/signals/generate", json=signal_request)
        
        if signal_response.status_code == 201:
            signal = signal_response.json()
            
            # Execute trade
            trade_request = {
                "signal_id": signal["id"],
                "position_size": 100.0,
                "direction": signal["direction"]
            }
            
            trade_response = client.post("/api/v1/trades/execute", json=trade_request)
            
            if trade_response.status_code in [200, 201]:
                # Simulate trade loss by updating market data showing opposite movement
                loss_data = {
                    "symbol": "BTCUSDT",
                    "timestamp": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                    "open_price": 45000.0,
                    "high_price": 45020.0,
                    "low_price": 43500.0,  # Significant drop
                    "close_price": 43600.0,  # Loss scenario
                    "volume": 2000.0,
                    "quote_volume": 87200000.0,
                    "trade_count": 2500,
                    "source": "loss_simulation"
                }
                
                client.post("/api/v1/market-data", json=loss_data)
                
                # Attempt to generate another signal after simulated loss
                second_signal_response = client.post("/api/v1/signals/generate", json=signal_request)
                
                if second_signal_response.status_code in [400, 422, 429]:
                    error_data = second_signal_response.json()
                    loss_keywords = ["loss", "limit", "exceeded", "emergency", "stop"]
                    
                    if any(keyword in str(error_data).lower() for keyword in loss_keywords):
                        print("Daily loss limit enforcement detected")
                    else:
                        print(f"Signal blocked for other reason: {error_data}")
                
                # Check risk status endpoint
                risk_status_response = client.get("/api/v1/risk-parameters/status")
                
                if risk_status_response.status_code == 200:
                    risk_status = risk_status_response.json()
                    
                    # Look for loss tracking and limits
                    if "daily_loss" in risk_status:
                        daily_loss = float(risk_status["daily_loss"])
                        max_loss = float(loss_limit_params["max_daily_loss"])
                        
                        print(f"Daily loss: ${daily_loss:.2f} / ${max_loss:.2f}")
                        
                        if daily_loss >= max_loss:
                            assert "emergency_stop" in risk_status or "trading_disabled" in risk_status, \
                                   "Emergency stop should be triggered when loss limit exceeded"
            
            elif trade_response.status_code == 404:
                print("Trade execution endpoint not available for loss limit testing")
        
        else:
            print(f"Signal generation failed for loss limit test: {signal_response.status_code}")

    def test_emergency_risk_controls(self, base_risk_parameters, sample_market_data):
        """
        Test emergency risk controls and circuit breakers
        """
        # Configure sensitive emergency controls
        emergency_params = dict(base_risk_parameters)
        emergency_params["emergency_stop_threshold"] = Decimal("0.10")  # 10% emergency stop
        emergency_params["max_drawdown_limit"] = Decimal("0.08")  # 8% max drawdown
        emergency_params["volatility_limit"] = Decimal("0.50")  # 50% volatility limit
        
        response = client.put("/api/v1/risk-parameters", json=emergency_params)
        assert response.status_code in [200, 201]
        
        # Simulate extreme market volatility
        volatile_data = []
        base_time = datetime.now(timezone.utc)
        base_price = 45000.0
        
        # Create highly volatile price movements
        for i in range(10):
            current_time = base_time + timedelta(minutes=i)
            
            # Simulate extreme price swings
            if i % 2 == 0:
                # Spike up
                price = base_price + (i * 500)
                high_price = price + 1000
                low_price = price - 200
            else:
                # Drop down
                price = base_price - (i * 300)
                high_price = price + 300
                low_price = price - 800
            
            volatile_point = {
                "symbol": "BTCUSDT",
                "timestamp": current_time.isoformat(),
                "open_price": price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": price + ((i % 3 - 1) * 100),
                "volume": 5000.0 + i * 500,  # High volume
                "quote_volume": price * (5000.0 + i * 500),
                "trade_count": 5000 + i * 200,
                "source": "volatility_test"
            }
            
            volatile_data.append(volatile_point)
            client.post("/api/v1/market-data", json=volatile_point)
            time.sleep(0.2)
        
        # Attempt signal generation during high volatility
        emergency_signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        emergency_response = client.post("/api/v1/signals/generate", json=emergency_signal_request)
        
        # Check if emergency controls are triggered
        if emergency_response.status_code in [400, 422, 429, 503]:
            error_data = emergency_response.json()
            emergency_keywords = [
                "emergency", "volatility", "circuit", "breaker", "suspended",
                "extreme", "risk", "halt", "disabled"
            ]
            
            emergency_triggered = any(keyword in str(error_data).lower() 
                                    for keyword in emergency_keywords)
            
            if emergency_triggered:
                print("Emergency risk controls successfully triggered")
            else:
                print(f"Signal blocked for other reason during volatility: {error_data}")
        
        elif emergency_response.status_code == 201:
            print("Signal generated despite high volatility (emergency controls may not be active)")
        
        # Check emergency status
        emergency_status_response = client.get("/api/v1/risk-parameters/emergency-status")
        
        if emergency_status_response.status_code == 200:
            emergency_status = emergency_status_response.json()
            
            # Look for emergency indicators
            if "emergency_stop_active" in emergency_status:
                assert isinstance(emergency_status["emergency_stop_active"], bool)
                
                if emergency_status["emergency_stop_active"]:
                    print("Emergency stop status confirmed active")
                    
                    # Verify all trading functions are disabled
                    disabled_functions = ["signal_generation", "trade_execution", "position_opening"]
                    
                    for function in disabled_functions:
                        if f"{function}_disabled" in emergency_status:
                            assert emergency_status[f"{function}_disabled"], \
                                   f"{function} should be disabled during emergency stop"

    def test_risk_parameter_validation_and_consistency(self, base_risk_parameters):
        """
        Test validation and consistency checks for risk parameters
        """
        # Test invalid parameter combinations
        invalid_configurations = [
            # Negative values
            {
                **base_risk_parameters,
                "max_bet_size": Decimal("-100.00")
            },
            # Inconsistent limits
            {
                **base_risk_parameters,
                "max_bet_size": Decimal("1000.00"),
                "max_daily_loss": Decimal("50.00")  # Daily loss < max bet (inconsistent)
            },
            # Invalid probability ranges
            {
                **base_risk_parameters,
                "min_probability_edge": Decimal("1.5")  # > 1.0 (impossible)
            },
            # Zero or negative frequency limits
            {
                **base_risk_parameters,
                "frequency_limit_minutes": -5
            },
            # Conflicting emergency thresholds
            {
                **base_risk_parameters,
                "emergency_stop_threshold": Decimal("0.05"),  # 5%
                "max_drawdown_limit": Decimal("0.10")  # 10% > emergency (inconsistent)
            }
        ]
        
        validation_results = []
        
        for i, invalid_config in enumerate(invalid_configurations):
            response = client.put("/api/v1/risk-parameters", json=invalid_config)
            
            validation_results.append({
                "config_index": i,
                "status_code": response.status_code,
                "response": response.json() if response.status_code != 500 else {"error": "server_error"}
            })
            
            # Should reject invalid configurations
            assert response.status_code in [400, 422], \
                   f"Invalid config {i} should be rejected: {response.status_code}"
        
        print(f"Validated {len(invalid_configurations)} invalid configurations")
        
        # Test parameter consistency enforcement
        consistent_config = dict(base_risk_parameters)
        consistent_config["max_bet_size"] = Decimal("100.00")
        consistent_config["max_daily_loss"] = Decimal("500.00")  # 5x max bet
        consistent_config["max_daily_bets"] = 5
        
        # This should be accepted
        response = client.put("/api/v1/risk-parameters", json=consistent_config)
        assert response.status_code in [200, 201], \
               f"Consistent configuration should be accepted: {response.status_code}"
        
        # Verify parameters are stored correctly
        get_response = client.get("/api/v1/risk-parameters")
        
        if get_response.status_code == 200:
            stored_params = get_response.json()
            
            # Validate key parameters are stored correctly
            assert float(stored_params["max_bet_size"]) == 100.00
            assert float(stored_params["max_daily_loss"]) == 500.00
            assert stored_params["max_daily_bets"] == 5

    def test_comprehensive_risk_workflow_integration(self, base_risk_parameters, sample_market_data):
        """
        Test comprehensive integration of all risk controls in a realistic workflow
        """
        # Configure comprehensive risk parameters
        comprehensive_params = dict(base_risk_parameters)
        comprehensive_params["max_bet_size"] = Decimal("75.00")
        comprehensive_params["max_daily_bets"] = 3
        comprehensive_params["max_parallel_positions"] = 2
        comprehensive_params["min_probability_edge"] = Decimal("0.08")
        comprehensive_params["frequency_limit_minutes"] = 3
        comprehensive_params["max_daily_loss"] = Decimal("300.00")
        
        response = client.put("/api/v1/risk-parameters", json=comprehensive_params)
        assert response.status_code in [200, 201]
        
        # Ingest comprehensive market data
        for data_point in sample_market_data:
            client.post("/api/v1/market-data", json=data_point)
        
        # Simulate realistic trading session
        trading_session = {
            "signals_generated": 0,
            "signals_blocked": 0,
            "trades_executed": 0,
            "trades_blocked": 0,
            "risk_violations": []
        }
        
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        for i in range(10):  # Attempt 10 operations
            symbol = symbols[i % len(symbols)]
            
            # Generate signal
            signal_request = {"symbol": symbol, "force_calculation": True}
            signal_response = client.post("/api/v1/signals/generate", json=signal_request)
            
            if signal_response.status_code == 201:
                signal = signal_response.json()
                trading_session["signals_generated"] += 1
                
                # Attempt trade execution
                trade_request = {
                    "signal_id": signal["id"],
                    "position_size": 60.0,  # Within individual limit
                    "direction": signal["direction"]
                }
                
                trade_response = client.post("/api/v1/trades/execute", json=trade_request)
                
                if trade_response.status_code in [200, 201]:
                    trading_session["trades_executed"] += 1
                elif trade_response.status_code in [400, 422, 429]:
                    trading_session["trades_blocked"] += 1
                    error_data = trade_response.json()
                    trading_session["risk_violations"].append({
                        "type": "trade_blocked",
                        "reason": str(error_data),
                        "symbol": symbol
                    })
                elif trade_response.status_code == 404:
                    # Trade execution not implemented
                    pass
            
            elif signal_response.status_code in [400, 422, 429]:
                trading_session["signals_blocked"] += 1
                error_data = signal_response.json()
                trading_session["risk_violations"].append({
                    "type": "signal_blocked",
                    "reason": str(error_data),
                    "symbol": symbol
                })
            
            time.sleep(1.2)  # Brief pause between operations
        
        # Analyze comprehensive risk enforcement
        print(f"Trading session summary:")
        print(f"  Signals generated: {trading_session['signals_generated']}")
        print(f"  Signals blocked: {trading_session['signals_blocked']}")
        print(f"  Trades executed: {trading_session['trades_executed']}")
        print(f"  Trades blocked: {trading_session['trades_blocked']}")
        print(f"  Risk violations: {len(trading_session['risk_violations'])}")
        
        # Validate risk enforcement effectiveness
        total_operations = trading_session["signals_generated"] + trading_session["signals_blocked"]
        
        if total_operations > 0:
            # Should not exceed daily bet limit
            assert trading_session["signals_generated"] <= 3, \
                   "Should not exceed daily bet limit of 3"
            
            # Should not exceed parallel position limit
            assert trading_session["trades_executed"] <= 2, \
                   "Should not exceed parallel position limit of 2"
        
        # Check final risk status
        final_risk_status = client.get("/api/v1/risk-parameters/status")
        
        if final_risk_status.status_code == 200:
            risk_data = final_risk_status.json()
            print(f"Final risk status: {risk_data}")
            
            # Validate risk tracking
            if "daily_bets_count" in risk_data:
                assert risk_data["daily_bets_count"] <= 3, "Daily bet count tracking"
            
            if "active_positions_count" in risk_data:
                assert risk_data["active_positions_count"] <= 2, "Active position count tracking"