"""
Contract test for GET /api/v1/market-data/{symbol} endpoint

This test validates the API contract specification for retrieving market data.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from src.main import app

client = TestClient(app)


class TestGetMarketDataContract:
    """Contract tests for GET /api/v1/market-data/{symbol} endpoint"""

    def test_get_market_data_basic_success_response(self):
        """Test basic successful response structure matches contract"""
        response = client.get("/api/v1/market-data/BTCUSDT")
        
        # Contract: Should return 200 OK
        assert response.status_code == 200
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response structure should match schema
        data = response.json()
        assert isinstance(data, dict)
        assert "symbol" in data
        assert "interval" in data
        assert "data" in data
        
        # Contract: symbol should match request
        assert data["symbol"] == "BTCUSDT"
        
        # Contract: interval should be string
        assert isinstance(data["interval"], str)
        
        # Contract: data should be an array
        assert isinstance(data["data"], list)

    def test_get_market_data_with_query_parameters(self):
        """Test query parameters are handled according to contract"""
        # Test with interval parameter
        for interval in ['1m', '5m', '15m', '1h']:
            response = client.get(f"/api/v1/market-data/BTCUSDT?interval={interval}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["interval"] == interval
        
        # Test with limit parameter
        response = client.get("/api/v1/market-data/BTCUSDT?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["data"]) <= 50
        
        # Test with both parameters
        response = client.get("/api/v1/market-data/BTCUSDT?interval=5m&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["interval"] == "5m"
        assert len(data["data"]) <= 10

    def test_get_market_data_interval_validation(self):
        """Test interval parameter enum validation per contract"""
        # Valid intervals
        valid_intervals = ['1m', '5m', '15m', '1h']
        for interval in valid_intervals:
            response = client.get(f"/api/v1/market-data/BTCUSDT?interval={interval}")
            assert response.status_code == 200
        
        # Invalid interval should return 400
        response = client.get("/api/v1/market-data/BTCUSDT?interval=invalid")
        assert response.status_code == 400

    def test_get_market_data_limit_validation(self):
        """Test limit parameter validation per contract"""
        # Contract: limit minimum is 1
        response = client.get("/api/v1/market-data/BTCUSDT?limit=0")
        assert response.status_code == 400
        
        # Contract: limit maximum is 1000
        response = client.get("/api/v1/market-data/BTCUSDT?limit=1001")
        assert response.status_code == 400
        
        # Contract: valid limit should work
        response = client.get("/api/v1/market-data/BTCUSDT?limit=500")
        assert response.status_code == 200

    def test_get_market_data_default_parameters(self):
        """Test default parameter values per contract"""
        response = client.get("/api/v1/market-data/BTCUSDT")
        assert response.status_code == 200
        
        data = response.json()
        # Contract: default interval should be '1m'
        assert data["interval"] == "1m"
        # Contract: default limit should be 100 (or less if not enough data)
        assert len(data["data"]) <= 100

    def test_get_market_data_market_data_schema(self):
        """Test individual MarketData objects match contract schema"""
        response = client.get("/api/v1/market-data/BTCUSDT?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["data"]) > 0:
            market_data = data["data"][0]
            
            # Contract: Required fields must be present
            required_fields = [
                "symbol", "timestamp", "open_price", "high_price", 
                "low_price", "close_price", "volume"
            ]
            for field in required_fields:
                assert field in market_data, f"Required field '{field}' missing"
            
            # Contract: Field type and format validation
            assert isinstance(market_data["symbol"], str)
            assert market_data["symbol"] == "BTCUSDT"
            
            assert isinstance(market_data["timestamp"], str)
            # ISO datetime format validation
            datetime.fromisoformat(market_data["timestamp"].replace('Z', '+00:00'))
            
            # Price fields should be strings (as per contract)
            price_fields = ["open_price", "high_price", "low_price", "close_price"]
            for field in price_fields:
                assert isinstance(market_data[field], str)
                # Should be valid decimal number
                float(market_data[field])  # Should not raise exception
            
            assert isinstance(market_data["volume"], str)
            float(market_data["volume"])  # Should be valid decimal
            
            # Contract: Optional fields validation if present
            optional_fields = {
                "quote_volume": str,
                "trade_count": int
            }
            
            for field, expected_type in optional_fields.items():
                if field in market_data:
                    assert isinstance(market_data[field], expected_type)

    def test_get_market_data_symbol_path_parameter(self):
        """Test symbol path parameter validation"""
        # Contract: symbol is required in path
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 404  # Path not found without symbol
        
        # Valid symbols should work
        valid_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        for symbol in valid_symbols:
            response = client.get(f"/api/v1/market-data/{symbol}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["symbol"] == symbol

    def test_get_market_data_not_found_response(self):
        """Test 404 response for invalid symbols per contract"""
        # Contract: Should return 404 for unknown symbols
        response = client.get("/api/v1/market-data/INVALIDSYMBOL")
        assert response.status_code == 404

    def test_get_market_data_response_headers(self):
        """Test response headers match expectations"""
        response = client.get("/api/v1/market-data/BTCUSDT")
        
        # Contract: Content-Type should be application/json
        assert response.headers["content-type"].startswith("application/json")
        
        # Should have standard HTTP headers
        assert "content-length" in response.headers or "transfer-encoding" in response.headers

    def test_get_market_data_price_ordering(self):
        """Test price data logical ordering (high >= low, etc.)"""
        response = client.get("/api/v1/market-data/BTCUSDT?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for market_data in data["data"]:
            # Convert string prices to float for comparison
            open_price = float(market_data["open_price"])
            high_price = float(market_data["high_price"])
            low_price = float(market_data["low_price"])
            close_price = float(market_data["close_price"])
            
            # Basic price validation
            assert high_price >= low_price, "High price should be >= low price"
            assert high_price >= max(open_price, close_price), "High should be >= open and close"
            assert low_price <= min(open_price, close_price), "Low should be <= open and close"

    @pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    @pytest.mark.parametrize("interval", ["1m", "5m", "15m", "1h"])
    def test_get_market_data_multiple_combinations(self, symbol, interval):
        """Test different symbol and interval combinations"""
        response = client.get(f"/api/v1/market-data/{symbol}?interval={interval}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == symbol
        assert data["interval"] == interval