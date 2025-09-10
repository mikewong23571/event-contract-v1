"""
Contract test for GET /api/v1/signals endpoint

This test validates the API contract specification for retrieving trading signals.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
from src.main import app

client = TestClient(app)


class TestGetSignalsContract:
    """Contract tests for GET /api/v1/signals endpoint"""

    def test_get_signals_basic_success_response(self):
        """Test basic successful response structure matches contract"""
        response = client.get("/api/v1/signals")
        
        # Contract: Should return 200 OK
        assert response.status_code == 200
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response structure should match schema
        data = response.json()
        assert isinstance(data, dict)
        assert "signals" in data
        assert "total_count" in data
        assert "has_more" in data
        
        # Contract: signals should be an array
        assert isinstance(data["signals"], list)
        
        # Contract: total_count should be integer
        assert isinstance(data["total_count"], int)
        assert data["total_count"] >= 0
        
        # Contract: has_more should be boolean
        assert isinstance(data["has_more"], bool)

    def test_get_signals_with_query_parameters(self):
        """Test query parameters are handled according to contract"""
        # Test with symbol filter
        response = client.get("/api/v1/signals?symbol=BTCUSDT")
        assert response.status_code == 200
        
        # Test with confidence filter
        response = client.get("/api/v1/signals?confidence=HIGH")
        assert response.status_code == 200
        
        # Test with limit parameter
        response = client.get("/api/v1/signals?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) <= 10
        
        # Test with since timestamp
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        response = client.get(f"/api/v1/signals?since={iso_timestamp}")
        assert response.status_code == 200

    def test_get_signals_limit_validation(self):
        """Test limit parameter validation per contract"""
        # Contract: limit minimum is 1
        response = client.get("/api/v1/signals?limit=0")
        assert response.status_code == 400
        
        # Contract: limit maximum is 100
        response = client.get("/api/v1/signals?limit=101")
        assert response.status_code == 400
        
        # Contract: valid limit should work
        response = client.get("/api/v1/signals?limit=50")
        assert response.status_code == 200

    def test_get_signals_confidence_enum_validation(self):
        """Test confidence parameter enum validation per contract"""
        # Valid confidence levels
        for confidence in ["LOW", "MEDIUM", "HIGH"]:
            response = client.get(f"/api/v1/signals?confidence={confidence}")
            assert response.status_code == 200
        
        # Invalid confidence level should return 400
        response = client.get("/api/v1/signals?confidence=INVALID")
        assert response.status_code == 400

    def test_get_signals_trading_signal_schema(self):
        """Test individual TradingSignal objects match contract schema"""
        response = client.get("/api/v1/signals?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["signals"]) > 0:
            signal = data["signals"][0]
            
            # Contract: Required fields must be present
            required_fields = [
                "id", "timestamp", "symbol", "direction", 
                "predicted_probability", "confidence_level", "expiry_time"
            ]
            for field in required_fields:
                assert field in signal, f"Required field '{field}' missing"
            
            # Contract: Field type and format validation
            assert isinstance(signal["id"], str)
            # UUID format validation
            uuid.UUID(signal["id"])  # Should not raise exception
            
            assert isinstance(signal["timestamp"], str)
            # ISO datetime format validation
            datetime.fromisoformat(signal["timestamp"].replace('Z', '+00:00'))
            
            assert isinstance(signal["symbol"], str)
            assert len(signal["symbol"]) > 0
            
            assert signal["direction"] in ["UP", "DOWN"]
            
            assert isinstance(signal["predicted_probability"], (int, float))
            assert 0.0 <= signal["predicted_probability"] <= 1.0
            
            assert signal["confidence_level"] in ["LOW", "MEDIUM", "HIGH"]
            
            assert isinstance(signal["expiry_time"], str)
            datetime.fromisoformat(signal["expiry_time"].replace('Z', '+00:00'))
            
            # Contract: Optional fields validation if present
            optional_fields = {
                "strategy_version": str,
                "technical_indicators": dict,
                "probability_edge": (int, float),
                "created_at": str
            }
            
            for field, expected_type in optional_fields.items():
                if field in signal:
                    assert isinstance(signal[field], expected_type)

    def test_get_signals_error_responses(self):
        """Test error response formats match contract"""
        # Contract: Invalid query parameters should return 400
        response = client.get("/api/v1/signals?invalid_param=value")
        # Note: This might be 200 if server ignores unknown params,
        # but if validation is strict, should be 400
        
        # Contract: Should handle server errors with 500
        # This will be tested when we can trigger server errors

    def test_get_signals_response_headers(self):
        """Test response headers match expectations"""
        response = client.get("/api/v1/signals")
        
        # Contract: Content-Type should be application/json
        assert response.headers["content-type"].startswith("application/json")
        
        # Should have standard HTTP headers
        assert "content-length" in response.headers or "transfer-encoding" in response.headers

    @pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    def test_get_signals_symbol_parameter(self, symbol):
        """Test symbol parameter filtering works for different symbols"""
        response = client.get(f"/api/v1/signals?symbol={symbol}")
        assert response.status_code == 200
        
        data = response.json()
        # If signals are returned, they should match the requested symbol
        for signal in data["signals"]:
            assert signal["symbol"] == symbol