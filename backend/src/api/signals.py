from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Request
from json import JSONDecodeError

from ..models.trading_signal import TradingSignal


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


@router.post("/signals/generate", status_code=201)
async def post_signals_generate(request: Request) -> Dict[str, Any]:
    """
    POST /api/v1/signals/generate

    Manually trigger generation of a trading signal for a given symbol.
    Contract expectations:
    - Accepts JSON body with required field: symbol (str)
    - Optional field: force_calculation (bool), defaults to false
    - Content-Type must be application/json; other types -> 400
    - Returns 201 with TradingSignal-like JSON object on success
    - Returns 400 for bad request or invalid JSON
    """

    # Enforce JSON content type explicitly per contract
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        raise HTTPException(status_code=400, detail="content-type must be application/json")

    # Parse JSON body with explicit error handling to map to 400
    try:
        body = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid json body")
    except Exception:
        raise HTTPException(status_code=400, detail="invalid request body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")

    symbol = body.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise HTTPException(status_code=400, detail="symbol is required")

    # Optional flag with default
    force_calculation = body.get("force_calculation", False)
    if isinstance(force_calculation, str):
        # Normalize common string booleans
        force_calculation = force_calculation.lower() in {"1", "true", "yes"}
    elif not isinstance(force_calculation, bool):
        force_calculation = False

    # Minimal signal generation consistent with contract schema
    now = datetime.utcnow()
    expiry = now + timedelta(minutes=15)

    # Use model to maintain schema consistency
    signal = TradingSignal(
        timestamp=now,
        symbol=symbol.strip(),
        direction="UP",
        predicted_probability=0.6,
        confidence_level="MEDIUM",
        expiry_time=expiry,
        strategy_version="v1.0",
        technical_indicators={},
        expires_at=expiry,
    )

    # Convert to serializable dict using model config encoders
    payload = signal.dict()
    return payload
