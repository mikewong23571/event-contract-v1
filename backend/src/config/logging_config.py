"""
Structured logging configuration for the backend using structlog.

Task: T095 Structured logging setup across all components (backend part)
Path: backend/src/config/logging_config.py
"""

from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_structlog(level: int = logging.INFO) -> None:
    """Configure structlog with JSON renderer and stdlib integration."""
    logging.basicConfig(level=level, format="%(message)s")

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

