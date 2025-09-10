"""
InfluxDB client setup using influxdb-client.

Task: T078 InfluxDB connection setup
Path: backend/src/database/influxdb.py
"""

from __future__ import annotations

from typing import Optional

try:
    from influxdb_client import InfluxDBClient
except Exception:  # pragma: no cover - optional import for environments without the package
    InfluxDBClient = object  # type: ignore

from ..config.settings import get_settings


_client: Optional[InfluxDBClient] = None  # type: ignore[assignment]


def get_influx_client() -> InfluxDBClient:  # type: ignore[override]
    """Return a singleton InfluxDB client configured from settings.

    Raises ValueError if required settings are missing.
    """
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.influxdb_url or not settings.influxdb_token:
            raise ValueError("InfluxDB configuration is incomplete: URL and TOKEN are required")
        _client = InfluxDBClient(
            url=str(settings.influxdb_url),
            token=settings.influxdb_token,
            org=settings.influxdb_org,
        )
    return _client

