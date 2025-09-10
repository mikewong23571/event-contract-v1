"""
Contract test for POST /api/v1/market-data/stream endpoint

This test validates the API contract specification for initiating market data streams.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestPostMarketDataStreamContract:
    """Contract tests for POST /api/v1/market-data/stream endpoint"""

    def test_post_market_data_stream_success_response(self):
        """Test successful stream initiation response structure"""
        request_body = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "client_id": "test_client_123"
        }
        
        response = client.post("/api/v1/market-data/stream", json=request_body)
        
        # Contract: Should return 201 Created for successful stream initiation
        assert response.status_code == 201
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response should contain stream session info
        data = response.json()
        assert isinstance(data, dict)
        assert "stream_id" in data
        assert "symbol" in data
        assert "status" in data

    def test_post_market_data_stream_request_validation(self):
        """Test request body validation per contract"""
        # Contract: symbol is required
        response = client.post("/api/v1/market-data/stream", json={})
        assert response.status_code == 400
        
        # Contract: Valid request should work
        response = client.post("/api/v1/market-data/stream", json={
            "symbol": "BTCUSDT", 
            "interval": "1m",
            "client_id": "test"
        })
        assert response.status_code == 201

    def test_post_market_data_stream_interval_validation(self):
        """Test interval parameter validation"""
        valid_intervals = ["1m", "5m", "15m", "1h"]
        for interval in valid_intervals:
            response = client.post("/api/v1/market-data/stream", json={
                "symbol": "BTCUSDT",
                "interval": interval,
                "client_id": "test"
            })
            assert response.status_code == 201