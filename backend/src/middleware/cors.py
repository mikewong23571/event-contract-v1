"""
CORS configuration helper for the FastAPI app.

Task: T085 CORS configuration
Path: backend/src/middleware/cors.py
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import get_settings


def setup_cors(app: FastAPI, origins: Optional[Iterable[str]] = None) -> None:
    """Attach CORSMiddleware to `app` configured from settings or provided origins."""
    settings = get_settings()
    allowed_origins: List[str] = list(origins) if origins is not None else list(settings.cors_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

