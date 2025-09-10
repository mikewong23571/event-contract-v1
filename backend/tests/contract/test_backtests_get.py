"""
Contract test for GET /api/v1/backtests/{id} endpoint

This test validates the API contract specification for retrieving backtest results.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
from src.main import app

client = TestClient(app)


class TestGetBacktestsContract:
    """Contract tests for GET /api/v1/backtests/{id} endpoint"""

    def test_get_backtests_success_response(self):
        """Test successful backtest retrieval response structure"""
        # Using a sample UUID for the test
        test_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/backtests/{test_id}")
        
        # Contract: Should return 200 OK when backtest exists
        assert response.status_code == 200
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response should contain backtest details
        data = response.json()
        assert isinstance(data, dict)
        assert "backtest_id" in data
        assert "status" in data
        assert "strategy_name" in data

    def test_get_backtests_completed_result_schema(self):
        """Test completed backtest result schema"""
        test_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/backtests/{test_id}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Contract: Basic fields validation
        assert isinstance(data["backtest_id"], str)
        uuid.UUID(data["backtest_id"])
        
        assert data["status"] in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
        assert isinstance(data["strategy_name"], str)
        
        # If completed, should have results
        if data["status"] == "COMPLETED":
            assert "results" in data
            assert "summary" in data
            
            results = data["results"]
            assert "total_trades" in results
            assert "win_rate" in results
            assert "total_return" in results

    def test_get_backtests_not_found(self):
        """Test 404 response for non-existent backtest"""
        non_existent_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/backtests/{non_existent_id}")
        assert response.status_code == 404

    def test_get_backtests_invalid_uuid(self):
        """Test 400 response for invalid UUID format"""
        response = client.get("/api/v1/backtests/invalid-uuid")
        assert response.status_code == 400

    def test_get_backtests_running_status(self):
        """Test response for running backtest"""
        test_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/backtests/{test_id}")
        
        # May be 200 (found) or 404 (not found) depending on implementation
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # Running backtest should have progress info
            if data["status"] == "RUNNING":
                assert "progress" in data
                assert isinstance(data["progress"], (int, float))
                assert 0 <= data["progress"] <= 100