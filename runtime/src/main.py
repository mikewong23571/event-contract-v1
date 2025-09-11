"""
Event Contract Trading System - Runtime Engine

Main entry point for the real-time trading signal detection engine.
"""

import asyncio
import logging
import signal
import sys
from typing import NoReturn

import structlog

from .config.settings import get_settings
from .engines.signal_detector import create_signal_detector
from .processors.market_data_processor import create_market_data_processor
from .publishers.signal_publisher import create_signal_publisher, publish_detected_signal

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class RuntimeEngine:
    """Main runtime engine for real-time trading signal detection."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.running = False
        
        # Initialize components
        self.signal_detector = create_signal_detector()
        self.market_data_processor = create_market_data_processor()
        self.signal_publisher = create_signal_publisher()

    async def start(self) -> None:
        """Start the runtime engine."""
        logger.info("Starting Event Contract Runtime Engine", version="0.1.0")
        self.running = True

        # Initialize components
        await self._initialize_components()

        # Start main processing loop
        await self._run()

    async def stop(self) -> None:
        """Stop the runtime engine gracefully."""
        logger.info("Stopping Event Contract Runtime Engine")
        self.running = False
        
        # Stop components
        if hasattr(self, 'signal_detector'):
            await self.signal_detector.stop_detection()
        if hasattr(self, 'signal_publisher'):
            await self.signal_publisher.stop()

    async def _initialize_components(self) -> None:
        """Initialize runtime engine components."""
        logger.info("Initializing runtime components")
        
        # Start signal publisher
        await self.signal_publisher.start()
        
        # Register signal callback to publish detected signals
        async def signal_callback(signal):
            await publish_detected_signal(signal, self.signal_publisher)
            
        self.signal_detector.add_signal_callback(signal_callback)
        
        # Start signal detection engine
        await self.signal_detector.start_detection()
        
        logger.info("Runtime components initialized successfully")

    async def _run(self) -> None:
        """Main processing loop."""
        logger.info("Runtime engine processing loop started")

        try:
            while self.running:
                # Main processing logic will be implemented in later tasks
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("Runtime engine processing cancelled")
        except Exception as e:
            logger.error("Runtime engine error", error=str(e))
            raise


def setup_signal_handlers(engine: RuntimeEngine) -> None:
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum: int, frame) -> None:
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(engine.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main() -> NoReturn:
    """Main entry point."""
    engine = RuntimeEngine()
    setup_signal_handlers(engine)

    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Fatal error in runtime engine", error=str(e))
        sys.exit(1)
    finally:
        await engine.stop()

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
