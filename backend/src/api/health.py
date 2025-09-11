"""
Health check endpoints.

Task: T093 Health check endpoints
Path: backend/src/api/health.py

Implements a basic health endpoint consistent with the API contract:
- GET /api/v1/health → {status, checks, timestamp}

Checks are lightweight and do not perform real I/O yet. They are designed
to be extended later to verify database/cache/message-broker availability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, object]:
    """Return overall health status and component checks.

    Response structure aligns with the OpenAPI contract in specs:
    {
      "status": "healthy|degraded|unhealthy",
      "checks": {"database": "ok|error", ...},
      "timestamp": "ISO-8601"
    }
    """
    # Placeholder checks – upgrade to real checks when integrations are wired
    checks = {
        "database": "ok",
        "market_data_feed": "ok",
        "signal_generation": "ok",
    }

    # Aggregate status from checks (simple policy: any error → degraded)
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }

