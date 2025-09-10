from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request


router = APIRouter()


@router.post("/backtests", status_code=202)
async def post_backtests(request: Request) -> Dict[str, Any]:
    """
    POST /api/v1/backtests

    Creates a backtest job and returns job metadata.

    Contract expectations (from tests):
    - JSON body with required fields: strategy_name, start_date, end_date, symbol
    - Optional: initial_balance (stringified decimal)
    - Returns 202 with JSON: backtest_id (UUID str), status (PENDING/RUNNING/QUEUED), created_at (ISO8601)
    - Returns 400 on missing fields or invalid date format
    """

    # Enforce JSON content type explicitly
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        raise HTTPException(status_code=400, detail="content-type must be application/json")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid request body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")

    # Required fields validation
    required_fields = ["strategy_name", "start_date", "end_date", "symbol"]
    for field in required_fields:
        if field not in body or body.get(field) in (None, ""):
            raise HTTPException(status_code=400, detail=f"{field} is required")

    # Date validation (expecting YYYY-MM-DD)
    start_date = body.get("start_date")
    end_date = body.get("end_date")
    try:
        # Basic ISO date without time; invalid formats should raise
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid date format")

    # At this stage we acknowledge job creation; actual execution is out of scope here
    backtest_id = str(uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"

    # Allowed statuses by contract: PENDING, RUNNING, QUEUED
    return {
        "backtest_id": backtest_id,
        "status": "QUEUED",
        "created_at": created_at,
    }

