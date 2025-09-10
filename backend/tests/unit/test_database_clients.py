import os
import types
import pytest

from src.database.postgres import get_engine, get_session_factory
from src.database.redis import get_redis, get_redis_async


def test_postgres_engine_dsn_builds(monkeypatch):
    # Ensure no DATABASE_URL to test build from parts
    monkeypatch.delenv("DATABASE_URL", raising=False)
    engine = get_engine()
    # SQLAlchemy async engine has attribute driver
    assert hasattr(engine, "driver")


@pytest.mark.asyncio
async def test_postgres_session_factory_close():
    session_factory = get_session_factory()
    async with session_factory() as session:
        assert session.bind is not None


def test_redis_client_builds(monkeypatch):
    monkeypatch.setenv("REDIS_HOST", "localhost")
    client = get_redis()
    assert client is not None


def test_redis_async_optional():
    client = get_redis_async()
    # May be None if asyncio extra not installed, but callable shouldn't error
    assert client is None or hasattr(client, "connection_pool")

