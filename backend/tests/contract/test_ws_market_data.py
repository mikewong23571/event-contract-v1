"""
Contract test for WebSocket /ws/market-data/{symbol}

This test validates the WebSocket contract for subscribing to market data.
The test MUST FAIL initially as the WebSocket endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from src.main import app

client = TestClient(app)


class TestWebSocketMarketDataContract:
    """Contract tests for WebSocket /ws/market-data/{symbol}"""

    def test_websocket_market_data_connection_success(self):
        """Connection to valid market-data channel should succeed (per contract)."""
        symbol = "BTCUSDT"
        with client.websocket_connect(f"/ws/market-data/{symbol}") as ws:
            assert ws is not None

    def test_websocket_market_data_symbol_validation(self):
        """Invalid symbol pattern should be rejected per contract pattern ^[A-Z]{3,}USDT$."""
        invalid_symbols = [
            "eth",        # lowercase
            "ETH",        # missing USDT suffix
            "ETH-USD",    # wrong format
            "E",          # too short
            "ETHUSDT_",   # extra chars
        ]

        for sym in invalid_symbols:
            with pytest.raises((WebSocketDisconnect, AssertionError)):
                with client.websocket_connect(f"/ws/market-data/{sym}"):
                    assert False, "Invalid symbol should not connect"

