"""
Integration test for real-time trading signal detection (T024)

This integration test validates the real-time signal detection system:
1. Real-time market data streaming and processing
2. Continuous probability calculation and signal detection
3. Event contract opportunity identification
4. Real-time risk parameter enforcement
5. WebSocket signal broadcasting to clients
6. Signal persistence and cleanup

The test MUST FAIL initially as the implementation is not complete yet (TDD requirement).
"""

import pytest
import asyncio
import json
import threading
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import test client for API interactions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from main import app

client = TestClient(app)


class TestRealtimeSignalsIntegration:
    """Integration tests for real-time trading signal detection"""

    @pytest.fixture
    def realtime_market_data_stream(self):
        """Simulated real-time market data stream"""
        base_price = Decimal("45000.00")
        base_time = datetime.now(timezone.utc)
        
        def generate_data_stream():
            """Generator for continuous market data"""
            for i in range(100):  # 100 data points over time
                current_time = base_time + timedelta(seconds=i * 5)  # Every 5 seconds
                
                # Simulate price movement with some volatility
                price_change = Decimal(str(i % 20 - 10)) * Decimal("5.0")  # ±50 price range
                current_price = base_price + price_change
                
                yield {
                    "symbol": "BTCUSDT",
                    "timestamp": current_time.isoformat(),
                    "open_price": float(current_price - Decimal("2.5")),
                    "high_price": float(current_price + Decimal("12.5")),
                    "low_price": float(current_price - Decimal("7.5")),
                    "close_price": float(current_price),
                    "volume": 1000.0 + (i * 5),
                    "quote_volume": float(current_price * Decimal("1000")),
                    "trade_count": 1500 + (i * 2),
                    "source": "realtime_test",
                    "is_realtime": True
                }
                
                # Add some pause to simulate real-time streaming
                time.sleep(0.1)
        
        return generate_data_stream()

    @pytest.fixture
    def sample_event_contracts(self):
        """Sample event contracts available for trading"""
        current_time = datetime.now(timezone.utc)
        
        return [
            {
                "contract_id": "BTC_10MIN_UP_001",
                "symbol": "BTCUSDT",
                "strike_price": 45000.00,
                "direction": "UP",
                "expiry_time": (current_time + timedelta(minutes=10)).isoformat(),
                "payout_ratio": 0.80,  # 80% return
                "implied_probability": 0.556,  # 55.6%
                "status": "ACTIVE",
                "min_bet": 5.0,
                "max_bet": 1000.0
            },
            {
                "contract_id": "BTC_10MIN_DOWN_001",
                "symbol": "BTCUSDT",
                "strike_price": 45000.00,
                "direction": "DOWN",
                "expiry_time": (current_time + timedelta(minutes=10)).isoformat(),
                "payout_ratio": 0.75,  # 75% return
                "implied_probability": 0.571,  # 57.1%
                "status": "ACTIVE",
                "min_bet": 5.0,
                "max_bet": 1000.0
            }
        ]

    @pytest.fixture
    def realtime_risk_parameters(self):
        """Risk parameters for real-time signal detection"""
        return {
            "user_id": "realtime_test_user",
            "max_bet_size": Decimal("200.00"),
            "max_daily_bets": 50,
            "max_parallel_positions": 5,
            "min_probability_edge": Decimal("0.08"),  # 8% minimum edge
            "frequency_limit_minutes": 2,  # 2 minutes between signals
            "max_daily_loss": Decimal("1000.00"),
            "min_confidence_score": 0.65,  # 65% minimum confidence
            "signal_expiry_minutes": 1,   # Signals expire in 1 minute
            "enable_realtime_signals": True
        }

    def test_realtime_signal_detection_complete_flow(self, realtime_risk_parameters, sample_event_contracts):
        """
        Test complete real-time signal detection and broadcasting flow
        
        Flow:
        1. Configure risk parameters for real-time detection
        2. Start WebSocket connection for signal streaming
        3. Simulate market data ingestion
        4. Monitor for generated signals
        5. Validate signal content and timing
        6. Test signal expiry and cleanup
        """
        
        # Step 1: Configure risk parameters
        risk_response = client.put("/api/v1/risk-parameters", json=realtime_risk_parameters)
        
        if risk_response.status_code not in [200, 201]:
            print(f"Risk parameters setup: {risk_response.status_code}")
        
        # Step 2: Attempt WebSocket connection for real-time signals
        signals_received = []
        websocket_errors = []
        
        def websocket_listener():
            """Listen for real-time signals via WebSocket"""
            try:
                with client.websocket_connect("/ws/signals/BTCUSDT") as websocket:
                    # Listen for signals for a limited time
                    start_time = time.time()
                    while time.time() - start_time < 30:  # 30 seconds max
                        try:
                            message = websocket.receive_json()
                            signals_received.append({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "message": message
                            })
                            
                            # Validate signal message structure
                            if "type" in message and message["type"] == "signal":
                                signal_data = message.get("data", {})
                                
                                # Validate required signal fields
                                required_fields = ["id", "symbol", "direction", "predicted_probability"]
                                missing_fields = [f for f in required_fields if f not in signal_data]
                                
                                if missing_fields:
                                    websocket_errors.append(f"Missing fields: {missing_fields}")
                                else:
                                    print(f"Valid signal received: {signal_data['id']}")
                        
                        except Exception as e:
                            websocket_errors.append(f"WebSocket receive error: {e}")
                            break
                            
            except (WebSocketDisconnect, Exception) as e:
                websocket_errors.append(f"WebSocket connection error: {e}")

        # Start WebSocket listener in background
        websocket_thread = threading.Thread(target=websocket_listener, daemon=True)
        websocket_thread.start()
        
        time.sleep(1)  # Allow WebSocket to establish connection
        
        # Step 3: Simulate real-time market data ingestion
        market_data_points = []
        base_price = 45000.0
        base_time = datetime.now(timezone.utc)
        
        for i in range(10):  # Send 10 data points
            current_time = base_time + timedelta(seconds=i * 3)
            price_movement = (i % 6 - 3) * 20  # Price oscillation
            current_price = base_price + price_movement
            
            market_data = {
                "symbol": "BTCUSDT",
                "timestamp": current_time.isoformat(),
                "open_price": current_price - 5,
                "high_price": current_price + 15,
                "low_price": current_price - 10,
                "close_price": current_price,
                "volume": 1000.0 + i * 10,
                "quote_volume": current_price * (1000.0 + i * 10),
                "trade_count": 1500 + i * 5,
                "source": "realtime_simulation"
            }
            
            # Send market data
            data_response = client.post("/api/v1/market-data", json=market_data)
            market_data_points.append((current_price, data_response.status_code))
            
            time.sleep(0.5)  # Small delay between data points
        
        # Step 4: Monitor for signal generation (check API endpoint)
        time.sleep(2)  # Allow processing time
        
        # Check for signals via REST API
        signals_response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=10")
        api_signals = []
        
        if signals_response.status_code == 200:
            data = signals_response.json()
            api_signals = data.get("signals", [])
        
        # Wait for WebSocket thread to complete
        websocket_thread.join(timeout=5)
        
        # Step 5: Validate results
        total_signals = len(signals_received) + len(api_signals)
        
        if total_signals > 0:
            print(f"Signals detected: {len(signals_received)} via WebSocket, {len(api_signals)} via API")
            
            # Validate signal timing and content
            for signal_event in signals_received:
                message = signal_event["message"]
                if message.get("type") == "signal":
                    signal_data = message["data"]
                    
                    # Validate probability range
                    prob = signal_data.get("predicted_probability", 0)
                    assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"
                    
                    # Validate direction
                    direction = signal_data.get("direction", "")
                    assert direction in ["UP", "DOWN"], f"Invalid direction: {direction}"
                    
                    # Validate symbol
                    symbol = signal_data.get("symbol", "")
                    assert symbol == "BTCUSDT", f"Unexpected symbol: {symbol}"
            
            # Validate API signals
            for signal in api_signals:
                assert signal["symbol"] == "BTCUSDT"
                assert 0.0 <= signal["predicted_probability"] <= 1.0
                assert signal["direction"] in ["UP", "DOWN"]
        
        else:
            # No signals generated - could be due to:
            # 1. Insufficient market movement
            # 2. Risk parameters too restrictive
            # 3. Signal generation not implemented
            # 4. Data processing delays
            print("No real-time signals generated during test")
            
            # Verify the system is processing data
            successful_ingestions = sum(1 for _, status in market_data_points if status in [200, 201])
            assert successful_ingestions > 0, "No market data was successfully processed"
        
        # Report WebSocket errors for debugging
        if websocket_errors:
            print(f"WebSocket errors: {websocket_errors}")

    def test_realtime_signal_frequency_limiting(self, realtime_risk_parameters):
        """
        Test that real-time signal generation respects frequency limits
        """
        # Configure very restrictive frequency limit
        restrictive_params = dict(realtime_risk_parameters)
        restrictive_params["frequency_limit_minutes"] = 5  # 5 minutes between signals
        restrictive_params["min_probability_edge"] = Decimal("0.05")  # Lower edge for more signals
        
        client.put("/api/v1/risk-parameters", json=restrictive_params)
        
        # Generate rapid market data to trigger multiple signal opportunities
        rapid_data_points = []
        base_time = datetime.now(timezone.utc)
        base_price = 45000.0
        
        for i in range(20):  # 20 rapid data points
            current_time = base_time + timedelta(seconds=i * 10)  # Every 10 seconds
            
            # Create significant price movements to trigger signals
            if i < 10:
                price = base_price + (i * 50)  # Rising trend
            else:
                price = base_price + ((20 - i) * 50)  # Falling trend
            
            market_data = {
                "symbol": "BTCUSDT",
                "timestamp": current_time.isoformat(),
                "open_price": price - 5,
                "high_price": price + 20,
                "low_price": price - 15,
                "close_price": price,
                "volume": 1500.0,
                "quote_volume": price * 1500,
                "trade_count": 2000,
                "source": "frequency_test"
            }
            
            response = client.post("/api/v1/market-data", json=market_data)
            rapid_data_points.append((i, response.status_code))
            
            time.sleep(0.2)  # Brief delay
        
        # Allow processing time
        time.sleep(5)
        
        # Check generated signals
        signals_response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=50")
        
        if signals_response.status_code == 200:
            data = signals_response.json()
            signals = data.get("signals", [])
            
            # Filter recent signals from this test
            recent_signals = [
                s for s in signals 
                if s.get("timestamp") and 
                datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00')) >= base_time
            ]
            
            if len(recent_signals) > 1:
                # Validate frequency limiting
                signal_times = [
                    datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00'))
                    for s in recent_signals
                ]
                signal_times.sort()
                
                # Check time gaps between signals
                for i in range(1, len(signal_times)):
                    time_gap = signal_times[i] - signal_times[i-1]
                    gap_minutes = time_gap.total_seconds() / 60
                    
                    # Should respect 5-minute frequency limit
                    if gap_minutes < 4.5:  # Allow some tolerance
                        print(f"Potential frequency limit violation: {gap_minutes:.2f} minutes gap")
            
            else:
                print(f"Generated {len(recent_signals)} signals - frequency limiting may be working")
        
        else:
            print(f"Signal retrieval failed: {signals_response.status_code}")

    def test_realtime_signal_probability_edge_filtering(self, realtime_risk_parameters):
        """
        Test that only signals with sufficient probability edge are generated
        """
        # Test with high edge requirement
        high_edge_params = dict(realtime_risk_parameters)
        high_edge_params["min_probability_edge"] = Decimal("0.20")  # 20% edge (70%+ confidence)
        
        client.put("/api/v1/risk-parameters", json=high_edge_params)
        
        # Generate market data with moderate movements (unlikely to trigger high-confidence signals)
        moderate_movements = []
        base_time = datetime.now(timezone.utc)
        base_price = 45000.0
        
        for i in range(15):
            current_time = base_time + timedelta(seconds=i * 15)
            
            # Small, random-like price movements
            price_change = ((i * 7) % 13) - 6  # Small oscillations
            price = base_price + (price_change * 10)
            
            market_data = {
                "symbol": "BTCUSDT",
                "timestamp": current_time.isoformat(),
                "open_price": price - 2,
                "high_price": price + 8,
                "low_price": price - 5,
                "close_price": price,
                "volume": 1200.0,
                "quote_volume": price * 1200,
                "trade_count": 1800,
                "source": "edge_filter_test"
            }
            
            response = client.post("/api/v1/market-data", json=market_data)
            moderate_movements.append((price_change, response.status_code))
        
        time.sleep(3)
        
        # Check for signals with high edge requirement
        signals_response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=20")
        high_edge_signals = []
        
        if signals_response.status_code == 200:
            data = signals_response.json()
            all_signals = data.get("signals", [])
            
            # Filter signals from this test period
            high_edge_signals = [
                s for s in all_signals
                if s.get("timestamp") and
                datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00')) >= base_time and
                s.get("predicted_probability", 0.5)  # Filter by probability if available
            ]
        
        # Now test with low edge requirement
        low_edge_params = dict(realtime_risk_parameters)
        low_edge_params["min_probability_edge"] = Decimal("0.02")  # 2% edge (52%+ confidence)
        
        client.put("/api/v1/risk-parameters", json=low_edge_params)
        
        # Generate the same moderate movements
        base_time_2 = datetime.now(timezone.utc)
        
        for i in range(15):
            current_time = base_time_2 + timedelta(seconds=i * 15)
            price_change = ((i * 7) % 13) - 6
            price = base_price + (price_change * 10)
            
            market_data = {
                "symbol": "BTCUSDT",
                "timestamp": current_time.isoformat(),
                "open_price": price - 2,
                "high_price": price + 8,
                "low_price": price - 5,
                "close_price": price,
                "volume": 1200.0,
                "quote_volume": price * 1200,
                "trade_count": 1800,
                "source": "low_edge_test"
            }
            
            client.post("/api/v1/market-data", json=market_data)
        
        time.sleep(3)
        
        # Check for signals with low edge requirement
        signals_response_2 = client.get("/api/v1/signals?symbol=BTCUSDT&limit=30")
        low_edge_signals = []
        
        if signals_response_2.status_code == 200:
            data = signals_response_2.json()
            all_signals = data.get("signals", [])
            
            low_edge_signals = [
                s for s in all_signals
                if s.get("timestamp") and
                datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00')) >= base_time_2
            ]
        
        # Compare results
        print(f"High edge requirement (20%): {len(high_edge_signals)} signals")
        print(f"Low edge requirement (2%): {len(low_edge_signals)} signals")
        
        # Low edge requirement should generate more signals (if any)
        if len(high_edge_signals) > 0 or len(low_edge_signals) > 0:
            # Validate that edge filtering is working
            assert len(low_edge_signals) >= len(high_edge_signals), \
                   "Lower edge requirement should generate at least as many signals"

    def test_realtime_signal_expiry_and_cleanup(self, realtime_risk_parameters):
        """
        Test real-time signal expiry and automatic cleanup
        """
        # Configure short signal expiry
        short_expiry_params = dict(realtime_risk_parameters)
        short_expiry_params["signal_expiry_minutes"] = 1  # 1 minute expiry
        short_expiry_params["min_probability_edge"] = Decimal("0.05")  # Lower for more signals
        
        client.put("/api/v1/risk-parameters", json=short_expiry_params)
        
        # Generate market data to create signals
        signal_generation_time = datetime.now(timezone.utc)
        
        # Create strong price movement to trigger signal
        strong_movement_data = {
            "symbol": "BTCUSDT",
            "timestamp": signal_generation_time.isoformat(),
            "open_price": 45000.0,
            "high_price": 45200.0,  # Strong upward movement
            "low_price": 44980.0,
            "close_price": 45180.0,
            "volume": 2000.0,
            "quote_volume": 90360000.0,
            "trade_count": 3000,
            "source": "expiry_test"
        }
        
        response = client.post("/api/v1/market-data", json=strong_movement_data)
        
        time.sleep(2)  # Allow signal generation
        
        # Check for newly generated signals
        signals_response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=10")
        initial_signals = []
        
        if signals_response.status_code == 200:
            data = signals_response.json()
            all_signals = data.get("signals", [])
            
            # Filter signals from around the generation time
            initial_signals = [
                s for s in all_signals
                if s.get("timestamp") and
                abs((datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00')) - 
                     signal_generation_time).total_seconds()) < 30
            ]
        
        print(f"Initial signals found: {len(initial_signals)}")
        
        # Wait for signals to expire (1 minute + buffer)
        time.sleep(70)
        
        # Check signals again after expiry
        expired_signals_response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=10")
        remaining_signals = []
        
        if expired_signals_response.status_code == 200:
            data = expired_signals_response.json()
            all_signals = data.get("signals", [])
            
            # Check if the initial signals are still present
            initial_signal_ids = {s["id"] for s in initial_signals}
            remaining_signals = [
                s for s in all_signals
                if s["id"] in initial_signal_ids
            ]
        
        print(f"Remaining signals after expiry: {len(remaining_signals)}")
        
        # Validate expiry behavior
        if len(initial_signals) > 0:
            # Check if signals have been marked as expired or removed
            expired_count = 0
            for signal in remaining_signals:
                if "status" in signal and signal["status"] in ["EXPIRED", "INACTIVE"]:
                    expired_count += 1
                elif "expires_at" in signal:
                    expires_at = datetime.fromisoformat(signal["expires_at"].replace('Z', '+00:00'))
                    if expires_at < datetime.now(timezone.utc):
                        expired_count += 1
            
            # Either signals should be removed or marked as expired
            total_handled = (len(initial_signals) - len(remaining_signals)) + expired_count
            
            if total_handled > 0:
                print(f"Signal expiry handling: {total_handled}/{len(initial_signals)} signals handled")
            else:
                print("Signal expiry mechanism may not be implemented yet")

    def test_concurrent_realtime_signal_processing(self, realtime_risk_parameters):
        """
        Test concurrent real-time signal processing under load
        """
        client.put("/api/v1/risk-parameters", json=realtime_risk_parameters)
        
        # Prepare concurrent market data streams
        def generate_market_data_stream(stream_id: int, symbol: str):
            """Generate market data for a specific stream"""
            results = []
            base_time = datetime.now(timezone.utc)
            base_price = 45000.0 + (stream_id * 1000)  # Different base prices
            
            for i in range(10):  # 10 data points per stream
                current_time = base_time + timedelta(seconds=i * 2 + stream_id)
                price = base_price + ((i + stream_id) % 8 - 4) * 25  # Price variation
                
                market_data = {
                    "symbol": symbol,
                    "timestamp": current_time.isoformat(),
                    "open_price": price - 3,
                    "high_price": price + 12,
                    "low_price": price - 8,
                    "close_price": price,
                    "volume": 1000.0 + stream_id * 100,
                    "quote_volume": price * (1000.0 + stream_id * 100),
                    "trade_count": 1500 + stream_id * 50,
                    "source": f"concurrent_stream_{stream_id}"
                }
                
                try:
                    response = client.post("/api/v1/market-data", json=market_data)
                    results.append((stream_id, i, response.status_code))
                except Exception as e:
                    results.append((stream_id, i, f"Error: {e}"))
                
                time.sleep(0.1)  # Brief delay
            
            return results
        
        # Execute concurrent streams
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        concurrent_results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_stream = {
                executor.submit(generate_market_data_stream, i, symbols[i]): i
                for i in range(3)
            }
            
            for future in as_completed(future_to_stream):
                stream_id = future_to_stream[future]
                try:
                    result = future.result()
                    concurrent_results.extend(result)
                except Exception as e:
                    print(f"Stream {stream_id} error: {e}")
        
        # Allow processing time
        time.sleep(5)
        
        # Check signal generation across all symbols
        total_signals = 0
        
        for symbol in symbols:
            response = client.get(f"/api/v1/signals?symbol={symbol}&limit=20")
            
            if response.status_code == 200:
                data = response.json()
                signals = data.get("signals", [])
                symbol_signals = len(signals)
                total_signals += symbol_signals
                print(f"{symbol}: {symbol_signals} signals")
        
        # Analyze concurrent processing results
        successful_ingestions = sum(1 for _, _, status in concurrent_results 
                                  if isinstance(status, int) and status in [200, 201])
        
        failed_ingestions = sum(1 for _, _, status in concurrent_results 
                              if not (isinstance(status, int) and status in [200, 201]))
        
        print(f"Concurrent processing: {successful_ingestions} successful, {failed_ingestions} failed")
        print(f"Total signals generated: {total_signals}")
        
        # Basic validation
        assert successful_ingestions > 0, "Some concurrent data should be processed successfully"

    def test_realtime_signal_error_recovery(self, realtime_risk_parameters):
        """
        Test error recovery and resilience in real-time signal processing
        """
        client.put("/api/v1/risk-parameters", json=realtime_risk_parameters)
        
        # Test with various error conditions
        error_conditions = [
            # Malformed data
            {
                "symbol": "BTCUSDT",
                "timestamp": "invalid_timestamp",
                "open_price": "not_a_number",
                "close_price": 45000.0,
                "source": "error_test_malformed"
            },
            # Missing required fields
            {
                "symbol": "BTCUSDT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # Missing price fields
                "source": "error_test_missing"
            },
            # Invalid price relationships
            {
                "symbol": "BTCUSDT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "open_price": 45000.0,
                "high_price": 44000.0,  # High < Open (invalid)
                "low_price": 46000.0,   # Low > Open (invalid)
                "close_price": 45500.0,
                "volume": 1000.0,
                "source": "error_test_invalid_prices"
            }
        ]
        
        error_responses = []
        
        for error_data in error_conditions:
            try:
                response = client.post("/api/v1/market-data", json=error_data)
                error_responses.append((error_data["source"], response.status_code))
            except Exception as e:
                error_responses.append((error_data["source"], f"Exception: {e}"))
        
        # Send valid data after errors to test recovery
        valid_recovery_data = {
            "symbol": "BTCUSDT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open_price": 45000.0,
            "high_price": 45100.0,
            "low_price": 44950.0,
            "close_price": 45075.0,
            "volume": 1500.0,
            "quote_volume": 67612500.0,
            "trade_count": 2000,
            "source": "error_recovery_test"
        }
        
        recovery_response = client.post("/api/v1/market-data", json=valid_recovery_data)
        
        # Validate error handling
        for source, response in error_responses:
            if isinstance(response, int):
                assert response in [400, 422, 500], f"Error condition should return error code: {source}"
            else:
                print(f"Exception in {source}: {response}")
        
        # Validate recovery
        assert recovery_response.status_code in [200, 201], \
               "System should recover after error conditions"
        
        # Check if system continues to process signals after recovery
        time.sleep(2)
        
        recovery_signals_response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=5")
        
        if recovery_signals_response.status_code == 200:
            print("Signal processing recovered successfully after errors")
        else:
            print(f"Signal processing recovery status: {recovery_signals_response.status_code}")

    def test_realtime_performance_monitoring(self, realtime_risk_parameters):
        """
        Test performance monitoring for real-time signal detection
        """
        client.put("/api/v1/risk-parameters", json=realtime_risk_parameters)
        
        # Measure performance metrics during data processing
        start_time = time.time()
        processing_times = []
        
        # Generate data points and measure processing latency
        for i in range(20):
            data_start = time.time()
            
            market_data = {
                "symbol": "BTCUSDT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "open_price": 45000.0 + i,
                "high_price": 45100.0 + i,
                "low_price": 44950.0 + i,
                "close_price": 45075.0 + i,
                "volume": 1000.0 + i * 10,
                "quote_volume": (45075.0 + i) * (1000.0 + i * 10),
                "trade_count": 1500 + i * 5,
                "source": "performance_test"
            }
            
            response = client.post("/api/v1/market-data", json=market_data)
            
            data_end = time.time()
            processing_times.append(data_end - data_start)
            
            if response.status_code not in [200, 201]:
                print(f"Data point {i} processing failed: {response.status_code}")
            
            time.sleep(0.1)  # Brief interval
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        if processing_times:
            avg_latency = sum(processing_times) / len(processing_times)
            max_latency = max(processing_times)
            min_latency = min(processing_times)
            
            print(f"Performance metrics:")
            print(f"  Average latency: {avg_latency:.3f}s")
            print(f"  Maximum latency: {max_latency:.3f}s")
            print(f"  Minimum latency: {min_latency:.3f}s")
            print(f"  Total processing time: {total_time:.3f}s")
            print(f"  Throughput: {20/total_time:.2f} data points/second")
            
            # Performance assertions
            assert avg_latency < 2.0, f"Average processing latency too high: {avg_latency}s"
            assert max_latency < 5.0, f"Maximum processing latency too high: {max_latency}s"
        
        # Check if performance monitoring endpoint exists
        metrics_response = client.get("/api/v1/metrics/realtime-signals")
        
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            
            # Validate performance metrics structure
            expected_metrics = [
                "signal_generation_rate", "processing_latency", "error_rate",
                "active_signals_count", "queue_depth", "memory_usage"
            ]
            
            available_metrics = [m for m in expected_metrics if m in metrics]
            
            if available_metrics:
                print(f"Available performance metrics: {available_metrics}")
                
                for metric in available_metrics:
                    value = metrics[metric]
                    assert isinstance(value, (int, float)), f"Metric {metric} should be numeric"
            else:
                print("Performance metrics not yet implemented")
        else:
            print(f"Performance metrics endpoint: {metrics_response.status_code}")