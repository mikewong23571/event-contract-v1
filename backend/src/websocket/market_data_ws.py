"""WebSocket /ws/market-data handler (T054)

Implements contract for WebSocket subscriptions to market data by symbol.
Contract expectations from tests:
- URL pattern: /ws/market-data/{symbol}
- Accepts symbols matching ^[A-Z]{3,}USDT$
- Invalid symbols must result in handshake rejection or immediate disconnect
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import re

router = APIRouter()

SYMBOL_PATTERN = re.compile(r"^[A-Z]{3,}USDT$")


@router.websocket("/ws/market-data/{symbol}")
async def websocket_market_data(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for subscribing to market data for a given symbol.

    Contract rules:
    - Accept connection only if symbol matches ^[A-Z]{3,}USDT$
    - Otherwise, reject by closing the connection during handshake/accept
    """
    # Validate symbol before accepting
    if not SYMBOL_PATTERN.match(symbol):
        # Close without accepting to signal handshake failure to client tests
        # Using code 1008 (Policy Violation) aligns with validation failure semantics
        await websocket.close(code=1008)
        return

    # Accept valid connection
    await websocket.accept()

    try:
        # Minimal contract-compliant behavior: keep connection open
        # until client disconnects; no message protocol specified in T054
        while True:
            # Await for client pings or optional messages to keep loop alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Client disconnected; graceful exit
        return