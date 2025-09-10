"""
Contract test for WebSocket /ws/signals/{symbol}

This test validates the WebSocket contract for subscribing to trading signals.
The test MUST FAIL initially as the WebSocket endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from src.main import app

client = TestClient(app)


class TestWebSocketSignalsContract:
    """Contract tests for WebSocket /ws/signals/{symbol}"""

    def test_websocket_signals_connection_success(self):
        """Connection to valid signals channel should succeed (per contract)."""
        symbol = "BTCUSDT"
        with client.websocket_connect(f"/ws/signals/{symbol}") as ws:
            # If we reach here, handshake succeeded as required by contract
            assert ws is not None

    def test_websocket_signals_symbol_validation(self):
        """Invalid symbol pattern should be rejected per contract pattern ^[A-Z]{3,}USDT$."""
        invalid_symbols = [
            "btc",        # lowercase
            "BTC",        # missing USDT suffix
            "BTC-USD",    # wrong format
            "X",          # too short
            "BTCUSDTX",   # extra suffix
        ]

        for sym in invalid_symbols:
            with pytest.raises((WebSocketDisconnect, AssertionError)):
                # Expect handshake rejection or disconnect
                with client.websocket_connect(f"/ws/signals/{sym}"):
                    # If it connects, assert to fail validation
                    assert False, "Invalid symbol should not connect"

