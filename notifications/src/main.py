"""
Event Contract Trading System - Notifications Service

Main entry point for the notification service that handles alerts and messages
via multiple channels (Telegram, Feishu, Email, etc.).
"""

import asyncio
import logging
import signal
import sys
from typing import NoReturn

import structlog
from celery import Celery

from .config.settings import get_settings

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


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    settings = get_settings()
    
    app = Celery(
        "notifications",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["src.tasks"],
    )
    
    app.config_from_object(settings, namespace="CELERY")
    return app


celery_app = create_celery_app()


class NotificationService:
    """Main notification service for managing alerts and messages."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.running = False
        
    async def start(self) -> None:
        """Start the notification service."""
        logger.info("Starting Event Contract Notifications Service", version="0.1.0")
        self.running = True
        
        # Initialize notification clients
        await self._initialize_clients()
        
        # Start message processing
        await self._run()
        
    async def stop(self) -> None:
        """Stop the notification service gracefully."""
        logger.info("Stopping Event Contract Notifications Service")
        self.running = False
        
    async def _initialize_clients(self) -> None:
        """Initialize notification clients (Telegram, Feishu, etc.)."""
        logger.info("Initializing notification clients")
        # Client initialization will be implemented in later tasks
        
    async def _run(self) -> None:
        """Main message processing loop."""
        logger.info("Notification service processing loop started")
        
        try:
            while self.running:
                # Message processing logic will be implemented in later tasks
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            logger.info("Notification service processing cancelled")
        except Exception as e:
            logger.error("Notification service error", error=str(e))
            raise


def setup_signal_handlers(service: NotificationService) -> None:
    """Set up signal handlers for graceful shutdown."""
    
    def signal_handler(signum: int, frame) -> None:
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(service.stop())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main() -> NoReturn:
    """Main entry point."""
    service = NotificationService()
    setup_signal_handlers(service)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Fatal error in notification service", error=str(e))
        sys.exit(1)
    finally:
        await service.stop()
        
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())