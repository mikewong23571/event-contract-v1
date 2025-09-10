"""
Authentication middleware (non-enforcing by default).

Extracts a bearer token if present and attaches it to `request.state.auth`.
Does not block requests when token is missing or invalid to avoid impacting
existing endpoints. Validation logic can be extended later.

Task: T083 Authentication middleware
Path: backend/src/middleware/auth.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuthState(Dict[str, Any]):
    token: Optional[str]
    authenticated: bool


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        auth_header = request.headers.get("Authorization", "")
        token: Optional[str] = None
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip() or None

        # Attach auth info to request state for downstream handlers
        request.state.auth = AuthState(token=token, authenticated=bool(token))  # type: ignore[arg-type]

        response = await call_next(request)
        return response

