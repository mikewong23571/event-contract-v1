"""
Contract test for POST /api/v1/backtests endpoint

This test validates the API contract specification for creating backtest jobs.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
from src.main import app

client = TestClient(app)


class TestPostBacktestsContract:
    """Contract tests for POST /api/v1/backtests endpoint"""

    def test_post_backtests_success_response(self):
        """Test successful backtest creation response structure"""
        request_body = {
            "strategy_name": "ensemble_v1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31", 
            "symbol": "BTCUSDT",
            "initial_balance": "1000.00"
        }
        
        response = client.post("/api/v1/backtests", json=request_body)
        
        # Contract: Should return 202 Accepted for async job creation
        assert response.status_code == 202
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response should contain job info
        data = response.json()
        assert isinstance(data, dict)
        assert "backtest_id" in data
        assert "status" in data
        assert "created_at" in data

    def test_post_backtests_request_validation(self):
        """Test BacktestRequest schema validation"""
        # Contract: All required fields must be present
        required_fields = ["strategy_name", "start_date", "end_date", "symbol"]
        
        for field in required_fields:
            incomplete_request = {
                "strategy_name": "test",
                "start_date": "2024-01-01", 
                "end_date": "2024-01-31",
                "symbol": "BTCUSDT"
            }
            del incomplete_request[field]
            
            response = client.post("/api/v1/backtests", json=incomplete_request)
            assert response.status_code == 400

    def test_post_backtests_date_validation(self):
        """Test date format and logic validation"""
        base_request = {
            "strategy_name": "ensemble_v1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "symbol": "BTCUSDT"
        }
        
        # Valid request should work
        response = client.post("/api/v1/backtests", json=base_request)
        assert response.status_code == 202
        
        # Invalid date formats should fail
        invalid_date_request = base_request.copy()
        invalid_date_request["start_date"] = "invalid-date"
        response = client.post("/api/v1/backtests", json=invalid_date_request)
        assert response.status_code == 400

    def test_post_backtests_response_schema(self):
        """Test backtest creation response schema"""
        request_body = {
            "strategy_name": "ensemble_v1", 
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "symbol": "BTCUSDT"
        }
        
        response = client.post("/api/v1/backtests", json=request_body)
        assert response.status_code == 202
        
        data = response.json()
        
        # Validate response fields
        assert isinstance(data["backtest_id"], str)
        uuid.UUID(data["backtest_id"])  # Should be valid UUID
        
        assert data["status"] in ["PENDING", "RUNNING", "QUEUED"]
        
        assert isinstance(data["created_at"], str)
        datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))