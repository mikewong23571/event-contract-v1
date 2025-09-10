"""
Redis client setup.

Task: T079 Redis connection setup
Path: backend/src/database/redis.py
"""

from __future__ import annotations

from typing import Optional

import redis

try:
    from redis import asyncio as aioredis
except Exception:  # pragma: no cover - fallback if asyncio extra not available
    aioredis = None  # type: ignore

from ..config.settings import get_settings


_redis_sync: Optional[redis.Redis] = None
_redis_async = None


def get_redis() -> redis.Redis:
    """Return a singleton synchronous Redis client configured from settings."""
    global _redis_sync
    if _redis_sync is None:
        settings = get_settings()
        _redis_sync = redis.from_url(settings.redis_dsn())
    return _redis_sync


def get_redis_async():
    """Return a singleton asyncio Redis client configured from settings.

    Returns None if asyncio client is unavailable in the environment.
    """
    global _redis_async
    if _redis_async is None and aioredis is not None:
        settings = get_settings()
        _redis_async = aioredis.from_url(settings.redis_dsn())
    return _redis_async

