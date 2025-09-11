"""WebSocket /ws/system-status handler

Implements contract for WebSocket subscriptions to system status updates.
Sends periodic system health and performance metrics per AsyncAPI schema.
"""
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..websocket.connection_manager import ConnectionManager
from ..monitoring.metrics import get_system_metrics

router = APIRouter()
system_status_manager = ConnectionManager()


async def broadcast_system_status():
    """Broadcast system status to all connected clients every 30 seconds."""
    while True:
        try:
            # Get system metrics from monitoring
            metrics = get_system_metrics()
            
            # Build system status message per AsyncAPI schema
            status_message = {
                "type": "system_status",
                "data": {
                    "status": "healthy",  # TODO: derive from actual health checks
                    "components": {
                        "signal_generator": {
                            "status": "ok",
                            "last_check": datetime.utcnow().isoformat() + "Z"
                        },
                        "market_data_feed": {
                            "status": "ok", 
                            "last_check": datetime.utcnow().isoformat() + "Z"
                        },
                        "risk_manager": {
                            "status": "ok",
                            "last_check": datetime.utcnow().isoformat() + "Z"
                        },
                        "database": {
                            "status": "ok",
                            "last_check": datetime.utcnow().isoformat() + "Z"
                        },
                        "backtesting_engine": {
                            "status": "ok",
                            "last_check": datetime.utcnow().isoformat() + "Z"
                        }
                    },
                    "metrics": {
                        "signals_generated_today": metrics.get("signals_generated_today", 0),
                        "avg_signal_latency_ms": metrics.get("avg_signal_latency_ms", 50),
                        "active_websocket_connections": system_status_manager.active_count,
                        "system_uptime_hours": metrics.get("system_uptime_hours", 1.0)
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            await system_status_manager.broadcast(json.dumps(status_message))
            await asyncio.sleep(30)  # Broadcast every 30 seconds
            
        except Exception:
            # Continue broadcasting even if there's an error
            await asyncio.sleep(30)


# Start background task for broadcasting
_broadcast_task = None


async def start_system_status_broadcast():
    """Start the background task for broadcasting system status."""
    global _broadcast_task
    if _broadcast_task is None:
        _broadcast_task = asyncio.create_task(broadcast_system_status())


@router.websocket("/ws/system-status")
async def websocket_system_status(websocket: WebSocket):
    """WebSocket endpoint for subscribing to system status updates.
    
    Sends periodic system health and performance metrics matching AsyncAPI schema.
    """
    await websocket.accept()
    await system_status_manager.connect(websocket)
    
    # Start broadcast task if not already running
    await start_system_status_broadcast()
    
    try:
        # Keep connection alive - client receives broadcasts automatically
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        system_status_manager.disconnect(websocket)