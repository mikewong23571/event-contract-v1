import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any, Set
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException, BinanceRequestException

from ..processors.market_data_processor import PriceData
from ..config.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class BinanceWebSocketClient:
    """
    Binance WebSocket client for real-time market data streaming.

    Connects to Binance WebSocket API and streams market data for specified symbols.
    Converts Binance data format to internal PriceData format for processing.
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or settings.binance_api_key
        self.api_secret = api_secret or settings.binance_secret_key
        self.testnet = settings.binance_testnet

        self.client: Optional[AsyncClient] = None
        self.socket_manager: Optional[BinanceSocketManager] = None

        # Connection management
        self.is_connected = False
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds

        # Subscribed symbols and streams
        self.subscribed_symbols: Set[str] = set()
        self.active_streams: Dict[str, Any] = {}

        # Data callbacks
        self.data_callbacks: List[Callable[[PriceData], None]] = []
        self.error_callbacks: List[Callable[[Exception], None]] = []
        self.connection_callbacks: List[Callable[[bool], None]] = []

        # Statistics
        self.messages_received = 0
        self.last_message_time: Optional[datetime] = None
        self.connection_start_time: Optional[datetime] = None

    def add_data_callback(self, callback: Callable[[PriceData], None]) -> None:
        """Add a callback function to be called when market data is received."""
        self.data_callbacks.append(callback)

    def remove_data_callback(self, callback: Callable[[PriceData], None]) -> None:
        """Remove a data callback."""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)

    def add_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Add a callback function to be called when an error occurs."""
        self.error_callbacks.append(callback)

    def add_connection_callback(self, callback: Callable[[bool], None]) -> None:
        """Add a callback function to be called when connection status changes."""
        self.connection_callbacks.append(callback)

    async def connect(self) -> bool:
        """
        Establish connection to Binance WebSocket API.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Initialize Binance client
            self.client = await AsyncClient.create(
                api_key=self.api_key, api_secret=self.api_secret, testnet=self.testnet
            )

            # Create socket manager
            self.socket_manager = BinanceSocketManager(self.client)

            self.is_connected = True
            self.connection_start_time = datetime.utcnow()
            self.reconnect_attempts = 0

            logger.info(f"Connected to Binance WebSocket API (testnet: {self.testnet})")

            # Notify connection callbacks
            for callback in self.connection_callbacks:
                try:
                    await self._safe_callback(callback, True)
                except Exception as e:
                    logger.error(f"Error in connection callback: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket API: {e}")
            await self._handle_error(e)
            return False

    async def disconnect(self) -> None:
        """Disconnect from Binance WebSocket API."""
        try:
            self.is_running = False
            self.is_connected = False

            # Close all active streams
            for stream_name, stream in list(self.active_streams.items()):
                try:
                    await stream.__aexit__(None, None, None)
                    logger.info(f"Closed stream: {stream_name}")
                except Exception as e:
                    logger.warning(f"Error closing stream {stream_name}: {e}")

            self.active_streams.clear()

            # Close socket manager and client
            if self.socket_manager:
                # BinanceSocketManager doesn't have close method, just set to None
                self.socket_manager = None

            if self.client:
                await self.client.close_connection()
                self.client = None

            # Notify connection callbacks
            for callback in self.connection_callbacks:
                try:
                    await self._safe_callback(callback, False)
                except Exception as e:
                    logger.error(f"Error in connection callback: {e}")

            logger.info("Disconnected from Binance WebSocket API")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def subscribe_symbol(self, symbol: str) -> bool:
        """
        Subscribe to real-time market data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not self.is_connected or not self.socket_manager:
            logger.error("Not connected to Binance WebSocket API")
            return False

        try:
            symbol = symbol.upper()

            if symbol in self.subscribed_symbols:
                logger.warning(f"Already subscribed to {symbol}")
                return True

            # Create kline (candlestick) stream for 1m interval
            stream = self.socket_manager.kline_socket(symbol=symbol, interval="1m")

            # Start the stream
            await stream.__aenter__()
            self.active_streams[symbol] = stream
            self.subscribed_symbols.add(symbol)

            # Start listening task
            asyncio.create_task(self._listen_to_stream(symbol, stream))

            logger.info(f"Subscribed to {symbol} market data")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol}: {e}")
            await self._handle_error(e)
            return False

    async def unsubscribe_symbol(self, symbol: str) -> bool:
        """
        Unsubscribe from market data for a symbol.

        Args:
            symbol: Trading symbol to unsubscribe from

        Returns:
            bool: True if unsubscription successful, False otherwise
        """
        try:
            symbol = symbol.upper()

            if symbol not in self.subscribed_symbols:
                logger.warning(f"Not subscribed to {symbol}")
                return True

            # Close the stream
            if symbol in self.active_streams:
                stream = self.active_streams[symbol]
                await stream.__aexit__(None, None, None)
                del self.active_streams[symbol]

            self.subscribed_symbols.remove(symbol)

            logger.info(f"Unsubscribed from {symbol} market data")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from {symbol}: {e}")
            await self._handle_error(e)
            return False

    async def subscribe_multiple_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Subscribe to multiple symbols.

        Args:
            symbols: List of trading symbols

        Returns:
            Dict mapping symbol to subscription success status
        """
        results = {}

        for symbol in symbols:
            results[symbol] = await self.subscribe_symbol(symbol)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)

        return results

    async def start_streaming(self, symbols: Optional[List[str]] = None) -> None:
        """
        Start streaming market data.

        Args:
            symbols: Optional list of symbols to subscribe to
        """
        if not await self.connect():
            raise ConnectionError("Failed to connect to Binance WebSocket API")

        self.is_running = True

        # Subscribe to symbols if provided
        if symbols:
            await self.subscribe_multiple_symbols(symbols)

        logger.info("Started Binance WebSocket streaming")

    async def stop_streaming(self) -> None:
        """Stop streaming market data."""
        self.is_running = False
        await self.disconnect()

    async def _listen_to_stream(self, symbol: str, stream) -> None:
        """
        Listen to a specific symbol stream and process messages.

        Args:
            symbol: Symbol being streamed
            stream: WebSocket stream object
        """
        try:
            while self.is_running:
                try:
                    msg = await stream.recv()
                    if msg:
                        await self._process_message(symbol, msg)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message for {symbol}: {e}")
                    break

        except ConnectionClosed:
            logger.warning(f"WebSocket connection closed for {symbol}")
            await self._handle_reconnect(symbol)

        except Exception as e:
            logger.error(f"Error in stream listener for {symbol}: {e}")
            await self._handle_error(e)

    async def _process_message(self, symbol: str, message: Dict[str, Any]) -> None:
        """
        Process incoming WebSocket message and convert to PriceData.

        Args:
            symbol: Symbol the message belongs to
            message: Raw message from Binance WebSocket
        """
        try:
            self.messages_received += 1
            self.last_message_time = datetime.utcnow()

            # Extract kline data from message
            if "k" not in message:
                logger.warning(
                    f"Invalid message format for {symbol}: missing kline data"
                )
                return

            kline = message["k"]

            # Convert Binance kline data to PriceData format
            price_data = PriceData(
                symbol=kline["s"],
                timestamp=datetime.utcfromtimestamp(
                    kline["t"] / 1000
                ),  # Convert from milliseconds
                open_price=Decimal(str(kline["o"])),
                high_price=Decimal(str(kline["h"])),
                low_price=Decimal(str(kline["l"])),
                close_price=Decimal(str(kline["c"])),
                volume=Decimal(str(kline["v"])),
                source="binance_ws",
            )

            # Notify data callbacks
            for callback in self.data_callbacks:
                try:
                    await self._safe_callback(callback, price_data)
                except Exception as e:
                    logger.error(f"Error in data callback: {e}")

        except Exception as e:
            logger.error(f"Error processing message for {symbol}: {e}")
            await self._handle_error(e)

    async def _handle_reconnect(self, symbol: str) -> None:
        """
        Handle reconnection logic for a symbol.

        Args:
            symbol: Symbol to reconnect
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {symbol}")
            return

        self.reconnect_attempts += 1
        logger.info(
            f"Attempting reconnection for {symbol} (attempt {self.reconnect_attempts})"
        )

        try:
            # Wait before reconnecting
            await asyncio.sleep(self.reconnect_delay)

            # Remove from subscribed symbols and try to resubscribe
            if symbol in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol)

            if symbol in self.active_streams:
                del self.active_streams[symbol]

            # Attempt to reconnect and resubscribe
            if await self.connect():
                await self.subscribe_symbol(symbol)

        except Exception as e:
            logger.error(f"Reconnection failed for {symbol}: {e}")

    async def _handle_error(self, error: Exception) -> None:
        """
        Handle errors and notify error callbacks.

        Args:
            error: Exception that occurred
        """
        for callback in self.error_callbacks:
            try:
                await self._safe_callback(callback, error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    async def _safe_callback(self, callback: Callable, *args) -> None:
        """Safely execute callback, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)

    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information from Binance API.

        Returns:
            Dict with account information or None if failed
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        try:
            return await self.client.get_account()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            await self._handle_error(e)
            return None

    async def get_server_time(self) -> Optional[int]:
        """
        Get Binance server time.

        Returns:
            Server time in milliseconds or None if failed
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        try:
            result = await self.client.get_server_time()
            return result["serverTime"]
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            await self._handle_error(e)
            return None

    async def test_connectivity(self) -> bool:
        """
        Test connectivity to Binance API.

        Returns:
            bool: True if connectivity test successful, False otherwise
        """
        try:
            if not self.client:
                await self.connect()

            if not self.client:
                return False

            # Test with ping
            await self.client.ping()

            # Test with server time
            server_time = await self.get_server_time()

            return server_time is not None

        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            await self._handle_error(e)
            return False

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dict with connection statistics
        """
        uptime_seconds = 0
        if self.connection_start_time:
            uptime_seconds = (
                datetime.utcnow() - self.connection_start_time
            ).total_seconds()

        return {
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "subscribed_symbols": list(self.subscribed_symbols),
            "active_streams": len(self.active_streams),
            "messages_received": self.messages_received,
            "last_message_time": self.last_message_time.isoformat()
            if self.last_message_time
            else None,
            "connection_uptime_seconds": uptime_seconds,
            "reconnect_attempts": self.reconnect_attempts,
            "testnet": self.testnet,
        }

    def get_subscribed_symbols(self) -> List[str]:
        """Get list of currently subscribed symbols."""
        return list(self.subscribed_symbols)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the client.

        Returns:
            Dict with health check results
        """
        health_status = {
            "status": "healthy",
            "issues": [],
            "connectivity": False,
            "server_time_sync": False,
        }

        try:
            # Test connectivity
            health_status["connectivity"] = await self.test_connectivity()
            if not health_status["connectivity"]:
                health_status["issues"].append("Failed connectivity test")
                health_status["status"] = "unhealthy"

            # Check server time sync
            server_time = await self.get_server_time()
            if server_time:
                local_time = int(datetime.utcnow().timestamp() * 1000)
                time_diff = abs(server_time - local_time)
                health_status["server_time_sync"] = (
                    time_diff < 5000
                )  # 5 seconds tolerance
                health_status["time_difference_ms"] = time_diff

                if not health_status["server_time_sync"]:
                    health_status["issues"].append(
                        f"Server time out of sync by {time_diff}ms"
                    )
                    health_status["status"] = "degraded"

            # Check if we have recent messages
            if self.is_running and self.subscribed_symbols:
                if not self.last_message_time:
                    health_status["issues"].append("No messages received yet")
                    health_status["status"] = "degraded"
                else:
                    time_since_last_message = (
                        datetime.utcnow() - self.last_message_time
                    ).total_seconds()
                    if time_since_last_message > 120:  # 2 minutes
                        health_status["issues"].append(
                            f"No messages received for {time_since_last_message:.1f} seconds"
                        )
                        health_status["status"] = "degraded"

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["issues"].append(f"Health check failed: {str(e)}")

        health_status.update(self.get_connection_stats())
        return health_status


# Factory function for creating client instances
def create_binance_client(
    api_key: Optional[str] = None, api_secret: Optional[str] = None
) -> BinanceWebSocketClient:
    """Create and return a configured BinanceWebSocketClient instance."""
    return BinanceWebSocketClient(api_key=api_key, api_secret=api_secret)


# CLI entry point
async def main() -> None:
    """CLI entry point for the Binance WebSocket client."""
    import sys
    import signal

    client = create_binance_client()

    def print_market_data(data: PriceData) -> None:
        print(
            f"[{data.timestamp}] {data.symbol}: {data.close_price} (vol: {data.volume})"
        )

    def print_error(error: Exception) -> None:
        print(f"Error: {error}")

    def print_connection_status(connected: bool) -> None:
        status = "Connected" if connected else "Disconnected"
        print(f"Connection status: {status}")

    client.add_data_callback(print_market_data)
    client.add_error_callback(print_error)
    client.add_connection_callback(print_connection_status)

    # Default symbols to monitor
    symbols = ["BTCUSDT", "ETHUSDT"]

    # Handle graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler():
        print("\nShutdown requested...")
        shutdown_event.set()

    # Register signal handlers
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

    try:
        print("Starting Binance WebSocket client...")
        print(f"Monitoring symbols: {', '.join(symbols)}")

        # Start streaming
        await client.start_streaming(symbols)

        # Wait for shutdown signal
        await shutdown_event.wait()

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Stopping client...")
        await client.stop_streaming()
        print("Client stopped")


if __name__ == "__main__":
    asyncio.run(main())
