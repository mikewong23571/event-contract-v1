"""
Contract test for POST /api/v1/signals/generate endpoint

This test validates the API contract specification for generating trading signals manually.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
import json
from src.main import app

client = TestClient(app)


class TestPostSignalsGenerateContract:
    """Contract tests for POST /api/v1/signals/generate endpoint"""

    def test_post_signals_generate_success_response(self):
        """Test successful signal generation response structure matches contract"""
        request_body = {"symbol": "BTCUSDT"}
        
        response = client.post("/api/v1/signals/generate", json=request_body)
        
        # Contract: Should return 201 Created for successful generation
        assert response.status_code == 201
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response should be a TradingSignal object
        data = response.json()
        assert isinstance(data, dict)
        
        # Contract: TradingSignal schema validation
        required_fields = [
            "id", "timestamp", "symbol", "direction", 
            "predicted_probability", "confidence_level", "expiry_time"
        ]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing"

    def test_post_signals_generate_request_body_validation(self):
        """Test request body validation per contract"""
        # Contract: symbol is required
        response = client.post("/api/v1/signals/generate", json={})
        assert response.status_code == 400
        
        # Contract: Valid symbol should work
        response = client.post("/api/v1/signals/generate", json={"symbol": "BTCUSDT"})
        assert response.status_code == 201
        
        # Contract: Invalid JSON should return 400
        response = client.post("/api/v1/signals/generate", data="invalid json")
        assert response.status_code == 400

    def test_post_signals_generate_with_force_calculation(self):
        """Test force_calculation parameter per contract"""
        # Contract: force_calculation is optional boolean, defaults to false
        request_body = {
            "symbol": "BTCUSDT",
            "force_calculation": True
        }
        
        response = client.post("/api/v1/signals/generate", json=request_body)
        assert response.status_code == 201
        
        # Test with false value
        request_body["force_calculation"] = False
        response = client.post("/api/v1/signals/generate", json=request_body)
        assert response.status_code == 201
        
        # Test without force_calculation (should default to false)
        request_body = {"symbol": "BTCUSDT"}
        response = client.post("/api/v1/signals/generate", json=request_body)
        assert response.status_code == 201

    def test_post_signals_generate_trading_signal_response_schema(self):
        """Test response TradingSignal object matches contract schema"""
        request_body = {"symbol": "BTCUSDT"}
        
        response = client.post("/api/v1/signals/generate", json=request_body)
        assert response.status_code == 201
        
        signal = response.json()
        
        # Contract: Required fields validation
        assert isinstance(signal["id"], str)
        uuid.UUID(signal["id"])  # Should not raise exception
        
        assert isinstance(signal["timestamp"], str)
        datetime.fromisoformat(signal["timestamp"].replace('Z', '+00:00'))
        
        assert isinstance(signal["symbol"], str)
        assert signal["symbol"] == "BTCUSDT"  # Should match request
        
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

    def test_post_signals_generate_symbol_parameter_validation(self):
        """Test symbol parameter validation"""
        # Valid symbols
        valid_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        for symbol in valid_symbols:
            response = client.post("/api/v1/signals/generate", json={"symbol": symbol})
            assert response.status_code == 201
            
            # Verify symbol in response matches request
            data = response.json()
            assert data["symbol"] == symbol

    def test_post_signals_generate_error_responses(self):
        """Test error response formats match contract"""
        # Contract: 400 for bad request (missing symbol)
        response = client.post("/api/v1/signals/generate", json={})
        assert response.status_code == 400
        
        # Contract: 400 for invalid JSON structure
        response = client.post(
            "/api/v1/signals/generate", 
            headers={"content-type": "application/json"},
            data="invalid json"
        )
        assert response.status_code == 400
        
        # Contract: Should handle invalid symbols appropriately
        response = client.post("/api/v1/signals/generate", json={"symbol": ""})
        assert response.status_code == 400

    def test_post_signals_generate_conflict_response(self):
        """Test 409 Conflict response per contract"""
        # Contract: Should return 409 if signal already exists for current time period
        # This test will validate the response structure when we get 409
        request_body = {"symbol": "BTCUSDT"}
        
        # First request should succeed
        response = client.post("/api/v1/signals/generate", json=request_body)
        assert response.status_code == 201
        
        # Second request within same time period might return 409
        # (depending on implementation logic)
        response2 = client.post("/api/v1/signals/generate", json=request_body)
        # Could be 201 (new signal) or 409 (conflict) depending on time window
        assert response2.status_code in [201, 409]

    def test_post_signals_generate_content_type_validation(self):
        """Test content type validation"""
        request_body = {"symbol": "BTCUSDT"}
        
        # Contract: Should accept application/json
        response = client.post(
            "/api/v1/signals/generate",
            json=request_body
        )
        assert response.status_code == 201
        
        # Should reject other content types
        response = client.post(
            "/api/v1/signals/generate",
            data="symbol=BTCUSDT",
            headers={"content-type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    def test_post_signals_generate_multiple_symbols(self, symbol):
        """Test signal generation for different trading symbols"""
        request_body = {"symbol": symbol}
        
        response = client.post("/api/v1/signals/generate", json=request_body)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == symbol

    def test_post_signals_generate_response_headers(self):
        """Test response headers match expectations"""
        request_body = {"symbol": "BTCUSDT"}
        
        response = client.post("/api/v1/signals/generate", json=request_body)
        
        # Contract: Content-Type should be application/json
        assert response.headers["content-type"].startswith("application/json")
        
        # Should have standard HTTP headers
        assert "content-length" in response.headers or "transfer-encoding" in response.headers