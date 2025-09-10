"""WebSocket /ws/alerts handler (T055)

Implements contract for WebSocket alerts channel.
Contract expectations from tests:
- URL pattern: /ws/alerts
- Connection should succeed
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for subscribing to trading alerts.

    Contract rules:
    - Accept connection to /ws/alerts successfully
    - Keep the connection open until the client disconnects
    """
    # Accept the connection immediately per contract
    await websocket.accept()

    try:
        # Minimal contract-compliant behavior: keep the connection alive
        # until the client disconnects; no specific message protocol required
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Client disconnected; return gracefully
        return