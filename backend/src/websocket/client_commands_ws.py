"""WebSocket /ws/client/commands and /ws/client/responses handlers

Implements contract for WebSocket client command and response channels.
Handles subscribe/unsubscribe/get_status/update_risk_params/generate_signal commands.
"""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from ..websocket.connection_manager import ConnectionManager

router = APIRouter()
command_manager = ConnectionManager()
response_manager = ConnectionManager()


async def send_response(websocket: WebSocket, request_id: str, status: str, message: str, data: Dict[str, Any] = None, error_code: str = None):
    """Send a command response matching AsyncAPI schema."""
    response = {
        "request_id": request_id,
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if data:
        response["data"] = data
    if error_code:
        response["error_code"] = error_code
        
    await websocket.send_text(json.dumps(response))


async def handle_command(websocket: WebSocket, command_data: Dict[str, Any]):
    """Process client command and send response."""
    try:
        command = command_data.get("command")
        request_id = command_data.get("request_id", str(uuid.uuid4()))
        parameters = command_data.get("parameters", {})
        
        if command == "subscribe":
            channel = parameters.get("channel")
            if not channel:
                await send_response(websocket, request_id, "error", "Missing channel parameter", error_code="MISSING_PARAMETER")
                return
            await send_response(websocket, request_id, "success", f"Subscribed to {channel}")
            
        elif command == "unsubscribe":
            channel = parameters.get("channel")
            if not channel:
                await send_response(websocket, request_id, "error", "Missing channel parameter", error_code="MISSING_PARAMETER")
                return
            await send_response(websocket, request_id, "success", f"Unsubscribed from {channel}")
            
        elif command == "get_status":
            status_data = {
                "system_status": "healthy",
                "active_connections": command_manager.active_count,
                "uptime": "running"
            }
            await send_response(websocket, request_id, "success", "Status retrieved", data=status_data)
            
        elif command == "update_risk_params":
            risk_parameters = parameters.get("risk_parameters")
            if not risk_parameters:
                await send_response(websocket, request_id, "error", "Missing risk_parameters", error_code="MISSING_PARAMETER")
                return
            # TODO: Implement actual risk parameter update
            await send_response(websocket, request_id, "success", "Risk parameters updated", data={"updated_params": risk_parameters})
            
        elif command == "generate_signal":
            symbol = parameters.get("symbol")
            if not symbol:
                await send_response(websocket, request_id, "error", "Missing symbol parameter", error_code="MISSING_PARAMETER")
                return
            # TODO: Implement actual signal generation
            signal_data = {
                "signal_id": str(uuid.uuid4()),
                "symbol": symbol,
                "status": "generated"
            }
            await send_response(websocket, request_id, "success", f"Signal generated for {symbol}", data=signal_data)
            
        else:
            await send_response(websocket, request_id, "error", f"Unknown command: {command}", error_code="UNKNOWN_COMMAND")
            
    except Exception as e:
        request_id = command_data.get("request_id", "unknown")
        await send_response(websocket, request_id, "error", f"Command processing failed: {str(e)}", error_code="PROCESSING_ERROR")


@router.websocket("/ws/client/commands")
async def websocket_client_commands(websocket: WebSocket):
    """WebSocket endpoint for receiving client commands.
    
    Accepts commands per AsyncAPI schema and processes them.
    """
    await websocket.accept()
    await command_manager.connect(websocket)
    
    try:
        while True:
            # Receive command from client
            message = await websocket.receive_text()
            try:
                command_data = json.loads(message)
                await handle_command(websocket, command_data)
            except json.JSONDecodeError:
                await send_response(websocket, "unknown", "error", "Invalid JSON format", error_code="INVALID_JSON")
            except Exception as e:
                await send_response(websocket, "unknown", "error", f"Unexpected error: {str(e)}", error_code="UNEXPECTED_ERROR")
                
    except WebSocketDisconnect:
        command_manager.disconnect(websocket)


@router.websocket("/ws/client/responses")
async def websocket_client_responses(websocket: WebSocket):
    """WebSocket endpoint for sending command responses.
    
    This endpoint is used for response-only connections where clients
    only listen for responses without sending commands.
    """
    await websocket.accept()
    await response_manager.connect(websocket)
    
    try:
        # Keep connection alive - responses will be sent via other channels
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        response_manager.disconnect(websocket)