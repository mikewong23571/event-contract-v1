"""
Request logging middleware with correlation ID support.

Adds/propagates `X-Request-ID`, logs method, path, status, and duration.

Task: T084 Request logging middleware
Path: backend/src/middleware/logging.py
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Expose request ID to handlers
        request.state.request_id = request_id

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Add header for tracing across services
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
            },
        )
        return response

