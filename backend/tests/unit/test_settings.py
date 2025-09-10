import os

from src.config.settings import Settings, get_public_settings


def test_settings_load_defaults():
    s = Settings(_env_file=None)  # do not read .env in this test
    assert s.environment in {"development", "production", "test"}
    assert isinstance(s.backend_port, int)
    # DSNs are formed
    assert "postgresql" in s.database_dsn_sync()
    assert "+asyncpg" in s.database_dsn_async()


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "db")
    monkeypatch.setenv("POSTGRES_DB", "ec")
    s = Settings(_env_file=None)
    assert s.postgres_host == "db"
    assert s.postgres_db == "ec"


def test_get_public_settings_safe():
    info = get_public_settings()
    assert isinstance(info.cors_origins, list)
    assert info.backend_port > 0

