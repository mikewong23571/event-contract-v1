"""
Integration test for complete signal generation workflow (T021)

This integration test validates the end-to-end signal generation process:
1. Market data ingestion and storage
2. Technical indicator calculation
3. Signal generation with probability prediction
4. Risk parameter validation
5. Signal persistence and retrieval

The test MUST FAIL initially as the implementation is not complete yet (TDD requirement).
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestSignalWorkflowIntegration:
    """Integration tests for complete signal generation workflow"""

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing"""
        base_time = datetime.now(timezone.utc)
        return [
            {
                "symbol": "BTCUSDT",
                "timestamp": base_time - timedelta(minutes=i),
                "open_price": Decimal("45000.00") + Decimal(str(i * 10)),
                "high_price": Decimal("45100.00") + Decimal(str(i * 10)),
                "low_price": Decimal("44900.00") + Decimal(str(i * 10)),
                "close_price": Decimal("45050.00") + Decimal(str(i * 10)),
                "volume": Decimal("1000.0"),
                "quote_volume": Decimal("45000000.0"),
                "trade_count": 1500,
                "source": "test_data"
            }
            for i in range(20)  # 20 minutes of historical data
        ]

    @pytest.fixture
    def sample_risk_parameters(self):
        """Sample risk parameters for testing"""
        return {
            "user_id": "test_user_001",
            "max_bet_size": Decimal("100.00"),
            "max_daily_bets": 10,
            "max_parallel_positions": 3,
            "min_probability_edge": Decimal("0.10"),  # 10% minimum edge
            "frequency_limit_minutes": 5,
            "max_daily_loss": Decimal("500.00")
        }

    def test_complete_signal_generation_workflow_success(self, sample_market_data, sample_risk_parameters):
        """
        Test complete end-to-end signal generation workflow
        
        Flow:
        1. Ingest market data via REST API
        2. Configure risk parameters
        3. Generate signal via POST /api/v1/signals/generate
        4. Validate signal meets risk criteria
        5. Retrieve signal via GET /api/v1/signals
        """
        # Step 1: Ingest market data
        # This should eventually call the market data ingestion service
        # For now, we expect this endpoint to exist and accept data
        for data_point in sample_market_data[:10]:  # Use first 10 data points
            response = client.post("/api/v1/market-data", json={
                "symbol": data_point["symbol"],
                "timestamp": data_point["timestamp"].isoformat(),
                "open_price": float(data_point["open_price"]),
                "high_price": float(data_point["high_price"]),
                "low_price": float(data_point["low_price"]),
                "close_price": float(data_point["close_price"]),
                "volume": float(data_point["volume"]),
                "quote_volume": float(data_point["quote_volume"]),
                "trade_count": data_point["trade_count"],
                "source": data_point["source"]
            })
            # Market data ingestion should succeed
            assert response.status_code in [200, 201], f"Market data ingestion failed: {response.text}"

        # Step 2: Configure risk parameters
        response = client.put("/api/v1/risk-parameters", json=sample_risk_parameters)
        assert response.status_code in [200, 201], f"Risk parameter configuration failed: {response.text}"

        # Step 3: Generate signal
        signal_request = {
            "symbol": "BTCUSDT",
            "force_calculation": True
        }
        
        response = client.post("/api/v1/signals/generate", json=signal_request)
        assert response.status_code == 201, f"Signal generation failed: {response.text}"
        
        generated_signal = response.json()
        
        # Step 4: Validate generated signal structure and content
        # Signal should contain all required fields per contract
        required_fields = [
            "id", "timestamp", "symbol", "direction", 
            "predicted_probability", "confidence_level", "expiry_time"
        ]
        for field in required_fields:
            assert field in generated_signal, f"Required field '{field}' missing from signal"

        # Validate signal data types and ranges
        assert isinstance(generated_signal["predicted_probability"], (int, float))
        assert 0.0 <= generated_signal["predicted_probability"] <= 1.0
        assert generated_signal["direction"] in ["UP", "DOWN"]
        assert generated_signal["confidence_level"] in ["LOW", "MEDIUM", "HIGH"]
        assert generated_signal["symbol"] == "BTCUSDT"

        # Step 5: Validate signal meets risk criteria
        probability_edge = abs(generated_signal["predicted_probability"] - 0.5)
        min_edge = float(sample_risk_parameters["min_probability_edge"])
        
        # Signal should only be generated if it meets minimum edge requirement
        # OR this should be validated during retrieval
        
        # Step 6: Retrieve and verify signal persistence
        response = client.get("/api/v1/signals?symbol=BTCUSDT&limit=1")
        assert response.status_code == 200, f"Signal retrieval failed: {response.text}"
        
        signals_data = response.json()
        assert "signals" in signals_data
        assert len(signals_data["signals"]) >= 1, "Generated signal not found in database"
        
        retrieved_signal = signals_data["signals"][0]
        assert retrieved_signal["id"] == generated_signal["id"], "Signal ID mismatch"
        assert retrieved_signal["symbol"] == "BTCUSDT", "Signal symbol mismatch"

    def test_signal_generation_with_insufficient_data(self, sample_risk_parameters):
        """
        Test signal generation fails appropriately with insufficient market data
        """
        # Configure risk parameters
        response = client.put("/api/v1/risk-parameters", json=sample_risk_parameters)
        assert response.status_code in [200, 201]

        # Attempt to generate signal without sufficient historical data
        signal_request = {
            "symbol": "ETHUSDT",  # Different symbol with no data
            "force_calculation": True
        }
        
        response = client.post("/api/v1/signals/generate", json=signal_request)
        
        # Should fail with appropriate error message
        # Either 400 (insufficient data) or 500 (calculation error)
        assert response.status_code in [400, 422, 500], f"Expected error but got: {response.status_code}"
        
        # Error response should be informative
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_signal_generation_respects_risk_parameters(self, sample_market_data):
        """
        Test that signal generation respects configured risk parameters
        """
        # Configure very strict risk parameters
        strict_risk_params = {
            "user_id": "test_user_strict",
            "max_bet_size": Decimal("10.00"),
            "max_daily_bets": 1,
            "max_parallel_positions": 1,
            "min_probability_edge": Decimal("0.25"),  # Require 75%+ confidence
            "frequency_limit_minutes": 60,  # 1 hour between signals
            "max_daily_loss": Decimal("20.00")
        }

        # Ingest some market data
        for data_point in sample_market_data[:10]:
            response = client.post("/api/v1/market-data", json={
                "symbol": data_point["symbol"],
                "timestamp": data_point["timestamp"].isoformat(),
                "open_price": float(data_point["open_price"]),
                "high_price": float(data_point["high_price"]),
                "low_price": float(data_point["low_price"]),
                "close_price": float(data_point["close_price"]),
                "volume": float(data_point["volume"]),
                "quote_volume": float(data_point["quote_volume"]),
                "trade_count": data_point["trade_count"],
                "source": data_point["source"]
            })

        # Configure strict risk parameters
        response = client.put("/api/v1/risk-parameters", json=strict_risk_params)
        assert response.status_code in [200, 201]

        # Generate first signal
        signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        response = client.post("/api/v1/signals/generate", json=signal_request)
        
        # First signal might succeed or fail based on probability calculations
        first_signal_status = response.status_code

        if first_signal_status == 201:
            # If first signal succeeded, second signal should be blocked by frequency limit
            response = client.post("/api/v1/signals/generate", json=signal_request)
            # Should be blocked by frequency limit (too soon)
            assert response.status_code in [400, 429], "Frequency limit not enforced"
            
            error_data = response.json()
            assert any(keyword in str(error_data).lower() 
                      for keyword in ["frequency", "limit", "too soon", "wait"]), \
                   "Error should indicate frequency limit violation"
        else:
            # Signal was blocked by strict probability edge requirement
            assert first_signal_status in [400, 422], "Signal should be blocked by risk parameters"

    def test_signal_workflow_with_multiple_symbols(self, sample_market_data, sample_risk_parameters):
        """
        Test signal generation workflow handles multiple trading symbols
        """
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        # Configure risk parameters
        response = client.put("/api/v1/risk-parameters", json=sample_risk_parameters)
        assert response.status_code in [200, 201]

        # Ingest market data for multiple symbols
        for symbol in symbols:
            for data_point in sample_market_data[:5]:  # 5 data points per symbol
                market_data = dict(data_point)
                market_data["symbol"] = symbol
                market_data["timestamp"] = market_data["timestamp"].isoformat()
                
                # Convert Decimal to float for JSON serialization
                for price_field in ["open_price", "high_price", "low_price", "close_price"]:
                    market_data[price_field] = float(market_data[price_field])
                market_data["volume"] = float(market_data["volume"])
                market_data["quote_volume"] = float(market_data["quote_volume"])

                response = client.post("/api/v1/market-data", json=market_data)
                assert response.status_code in [200, 201]

        # Generate signals for each symbol
        generated_signals = []
        for symbol in symbols:
            signal_request = {"symbol": symbol, "force_calculation": True}
            response = client.post("/api/v1/signals/generate", json=signal_request)
            
            if response.status_code == 201:
                signal_data = response.json()
                generated_signals.append(signal_data)
                assert signal_data["symbol"] == symbol, f"Signal symbol mismatch: expected {symbol}"

        # Verify we can retrieve all signals
        response = client.get("/api/v1/signals?limit=10")
        assert response.status_code == 200
        
        signals_data = response.json()
        retrieved_symbols = {signal["symbol"] for signal in signals_data["signals"]}
        generated_symbols = {signal["symbol"] for signal in generated_signals}
        
        # All generated signals should be retrievable
        assert generated_symbols.issubset(retrieved_symbols), \
               "Not all generated signals are retrievable"

    def test_signal_expiry_and_cleanup(self, sample_market_data, sample_risk_parameters):
        """
        Test that signals expire correctly and can be cleaned up
        """
        # Configure risk parameters
        response = client.put("/api/v1/risk-parameters", json=sample_risk_parameters)
        assert response.status_code in [200, 201]

        # Ingest market data
        for data_point in sample_market_data[:10]:
            market_data = dict(data_point)
            market_data["timestamp"] = market_data["timestamp"].isoformat()
            for price_field in ["open_price", "high_price", "low_price", "close_price"]:
                market_data[price_field] = float(market_data[price_field])
            market_data["volume"] = float(market_data["volume"])
            market_data["quote_volume"] = float(market_data["quote_volume"])

            response = client.post("/api/v1/market-data", json=market_data)
            assert response.status_code in [200, 201]

        # Generate signal
        signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        response = client.post("/api/v1/signals/generate", json=signal_request)
        
        if response.status_code == 201:
            signal_data = response.json()
            
            # Verify signal has expiry time
            assert "expiry_time" in signal_data
            expiry_time = datetime.fromisoformat(signal_data["expiry_time"].replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            
            # Expiry time should be in the future
            assert expiry_time > current_time, "Signal expiry time should be in the future"
            
            # Expiry time should be reasonable (within next hour for event contracts)
            max_expiry = current_time + timedelta(hours=1)
            assert expiry_time <= max_expiry, "Signal expiry time too far in future"

        # Note: Actual expiry cleanup would be tested with time manipulation
        # or background task testing in a more comprehensive integration test

    def test_error_handling_and_recovery(self, sample_risk_parameters):
        """
        Test error handling and recovery in signal generation workflow
        """
        # Test with malformed risk parameters
        invalid_risk_params = dict(sample_risk_parameters)
        invalid_risk_params["min_probability_edge"] = "invalid"  # Should be decimal
        
        response = client.put("/api/v1/risk-parameters", json=invalid_risk_params)
        assert response.status_code == 400, "Should reject invalid risk parameters"

        # Test signal generation without risk parameters configured
        signal_request = {"symbol": "BTCUSDT", "force_calculation": True}
        response = client.post("/api/v1/signals/generate", json=signal_request)
        
        # Should handle missing risk parameters gracefully
        # Either use defaults or return appropriate error
        assert response.status_code in [200, 201, 400, 422], \
               f"Unexpected error handling: {response.status_code}"

        # Test recovery after fixing configuration
        response = client.put("/api/v1/risk-parameters", json=sample_risk_parameters)
        assert response.status_code in [200, 201]

        # Signal generation should now work (if sufficient data available)
        response = client.post("/api/v1/signals/generate", json=signal_request)
        # Result depends on data availability, but should not crash
        assert response.status_code in [200, 201, 400, 422, 500]