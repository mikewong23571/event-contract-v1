"""
Signal Publisher - Bridge between runtime detection and backend
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

import websockets
import aiohttp

from ..engines.signal_detector import DetectedSignal
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SignalPublisher:
    """
    Publishes detected signals to the backend API and WebSocket endpoints.
    Acts as a bridge between the runtime signal detection and the backend.
    """

    def __init__(self, backend_url: str = "http://localhost:8000", websocket_url: str = "ws://localhost:8000"):
        self.backend_url = backend_url.rstrip('/')
        self.websocket_url = websocket_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the signal publisher."""
        self.session = aiohttp.ClientSession()
        self.running = True
        logger.info("Signal publisher started")
        
    async def stop(self) -> None:
        """Stop the signal publisher."""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("Signal publisher stopped")
        
    async def publish_signal(self, signal: DetectedSignal) -> bool:
        """
        Publish a detected signal to the backend.
        
        This method:
        1. Persists the signal via POST /api/v1/signals/generate
        2. Broadcasts to WebSocket subscribers
        
        Args:
            signal: The detected signal to publish
            
        Returns:
            True if successful, False otherwise
        """
        if not self.running or not self.session:
            logger.warning("Publisher not running, skipping signal publication")
            return False
            
        try:
            # 1. Persist signal to backend API
            success = await self._persist_signal_to_api(signal)
            
            # 2. Broadcast to WebSocket (optional - signals channel might be handled by backend)
            if success:
                await self._broadcast_to_websocket(signal)
                
            return success
            
        except Exception as e:
            logger.error(f"Error publishing signal {signal.id}: {e}")
            return False
            
    async def _persist_signal_to_api(self, signal: DetectedSignal) -> bool:
        """Persist signal to backend API via POST /signals/generate."""
        try:
            # Transform DetectedSignal to the format expected by backend
            payload = {
                "symbol": signal.symbol,
                "force_calculation": False,
                # Add any additional data that can be passed to the backend signal generation
            }
            
            url = f"{self.backend_url}/api/v1/signals/generate"
            headers = {"Content-Type": "application/json"}
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(f"Signal persisted: {signal.symbol} -> {result.get('id', 'unknown')}")
                    return True
                else:
                    logger.error(f"Failed to persist signal: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error persisting signal to API: {e}")
            return False
            
    async def _broadcast_to_websocket(self, signal: DetectedSignal) -> None:
        """Broadcast signal to WebSocket subscribers (if needed)."""
        try:
            # Transform signal to WebSocket message format per AsyncAPI schema
            message = {
                "type": "signal",
                "data": {
                    "id": signal.id,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "predicted_probability": signal.predicted_probability,
                    "confidence_level": signal.confidence_level,
                    "expiry_time": signal.expiry_time.isoformat() + "Z",
                    "probability_edge": signal.predicted_probability - 0.5,  # Simple edge calculation
                    "strategy_version": signal.strategy_name,
                    "technical_indicators": {
                        "rsi": signal.technical_indicators.get("rsi", 0),
                        "macd": signal.technical_indicators.get("macd", 0),
                        "bb_position": 0.5,  # Placeholder
                        "volume_profile": "neutral"  # Placeholder
                    }
                },
                "timestamp": signal.detected_at.isoformat() + "Z"
            }
            
            # Connect to WebSocket and send message
            ws_url = f"{self.websocket_url}/ws/signals/{signal.symbol}"
            
            try:
                async with websockets.connect(ws_url) as websocket:
                    await websocket.send(json.dumps(message))
                    logger.debug(f"Signal broadcasted to WebSocket: {signal.symbol}")
            except Exception as e:
                logger.debug(f"WebSocket broadcast failed (normal if no subscribers): {e}")
                
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")
            
    async def update_metrics(self, signal: DetectedSignal) -> None:
        """Update backend metrics with signal generation data."""
        try:
            from ...backend.src.monitoring.metrics import metrics_registry
            
            # Record signal generation metrics
            metrics_registry.performance.record_signal(
                latency_ms=50.0,  # Placeholder latency
                executed=False,   # Not executed yet
                ts=signal.detected_at
            )
            
            # Record data pipeline metrics
            metrics_registry.data_pipeline.record_ingestion(
                duration_seconds=0.1,  # Placeholder processing time
                success=True,
                quality_score=float(signal.predicted_probability),
                ts=signal.detected_at
            )
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            
    async def send_notification(self, signal: DetectedSignal) -> None:
        """Send notification about the detected signal."""
        try:
            # Use the notifications system to alert about high-confidence signals
            if signal.confidence_level == "HIGH":
                # This would integrate with the notification manager
                notification_data = {
                    "type": "signal_detected",
                    "signal_id": signal.id,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "confidence": signal.confidence_level,
                    "probability": signal.predicted_probability
                }
                
                # For now, just log the notification
                logger.info(f"HIGH confidence signal notification: {json.dumps(notification_data)}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")


# Signal callback function that can be registered with SignalDetector
async def publish_detected_signal(signal: DetectedSignal, publisher: SignalPublisher) -> None:
    """Callback function to publish detected signals."""
    success = await publisher.publish_signal(signal)
    
    if success:
        # Update metrics and send notifications
        await publisher.update_metrics(signal)
        await publisher.send_notification(signal)
        
        logger.info(f"Published signal: {signal.symbol} {signal.direction} (confidence: {signal.confidence_level})")
    else:
        logger.warning(f"Failed to publish signal: {signal.symbol} {signal.direction}")


# Factory function
def create_signal_publisher(backend_url: Optional[str] = None, websocket_url: Optional[str] = None) -> SignalPublisher:
    """Create and return a configured SignalPublisher instance."""
    backend_url = backend_url or settings.BACKEND_URL if hasattr(settings, 'BACKEND_URL') else "http://localhost:8000"
    websocket_url = websocket_url or settings.WEBSOCKET_URL if hasattr(settings, 'WEBSOCKET_URL') else "ws://localhost:8000"
    
    return SignalPublisher(backend_url=backend_url, websocket_url=websocket_url)