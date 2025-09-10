from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Query


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


router = APIRouter()


@router.get("/signals")
async def get_signals(
    symbol: Optional[str] = Query(None, description="Filter by trading symbol, e.g., BTCUSDT"),
    confidence: Optional[str] = Query(
        None, description="Filter by confidence level: LOW, MEDIUM, HIGH"
    ),
    limit: Optional[int] = Query(
        None, description="Maximum number of signals to return (1-100)"
    ),
    since: Optional[str] = Query(
        None, description="ISO8601 timestamp to filter signals since this time"
    ),
):
    """
    GET /api/v1/signals

    Returns a paginated list of trading signals with optional filters.
    Contract expectations:
    - 200 on success with keys: signals (list), total_count (int), has_more (bool)
    - limit range validation: 1..100 -> 400 on violation
    - confidence enum validation: LOW|MEDIUM|HIGH -> 400 on violation
    """

    # Validate limit parameter (explicit 400 per contract)
    if limit is not None:
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    # Validate confidence parameter explicitly to return 400 (not default 422)
    if confidence is not None:
        allowed = {"LOW", "MEDIUM", "HIGH"}
        if confidence not in allowed:
            raise HTTPException(status_code=400, detail="invalid confidence level")

    # Validate since timestamp if provided (basic ISO8601 parsing)
    if since is not None:
        try:
            # Allow both 'Z' and offset formats, and handle '+' becoming space in query strings
            normalized = since.replace("Z", "+00:00").replace(" ", "+")
            _ = datetime.fromisoformat(normalized)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid since timestamp format")

    # For now, return an empty result set that satisfies the contract.
    # Filtering semantics are placeholders until data persistence is implemented.
    signals = []

    # Apply limit if any signals are present (signals is empty for now)
    if limit is not None:
        signals = signals[:limit]

    return {
        "signals": signals,
        "total_count": len(signals),
        "has_more": False,
    }
