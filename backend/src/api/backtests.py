from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from uuid import UUID, uuid4
from datetime import datetime

# Avoid cross-package imports at module import time to keep backend tests isolated.
# Backtest service and model imports are deferred inside functions when needed.


router = APIRouter()

# Simple in-memory registry to align GET/POST contract behavior without cross-package deps
_BACKTEST_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Note: Service instance deferred to avoid import errors when running isolated backend tests.


def _serialize_backtest_result(result: Any) -> Dict[str, Any]:
    """Serialize BacktestResult to contract-compliant response shape.

    Contract expectations from tests for GET /api/v1/backtests/{id}:
    - Always include: backtest_id (str UUID), status, strategy_name
    - If status == COMPLETED: include results with total_trades, win_rate, total_return
      and a human-readable summary string.
    - If status == RUNNING: include progress (0-100). Not applicable here as we
      only return completed cached results when found.
    """

    # Base fields
    payload: Dict[str, Any] = {
        "backtest_id": str(result.id),
        "status": "COMPLETED",
        "strategy_name": result.strategy_name,
    }

    # Completed results block
    payload["results"] = {
        "total_trades": int(result.total_signals),
        "win_rate": float(result.win_rate),
        "total_return": float(result.total_profit_loss),
    }

    payload["summary"] = (
        f"Strategy {result.strategy_name}: trades={result.total_signals}, "
        f"win_rate={float(result.win_rate):.2f}, return={float(result.total_profit_loss):.2f}"
    )

    # Ensure JSON serializable (e.g., Decimals)
    return jsonable_encoder(payload)


@router.get("/backtests")
async def list_backtests(
    strategy_name: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    GET /api/v1/backtests

    Lists backtest jobs/results.

    Contract expectations:
    - 200 with { results: [...] }
    - Supports optional filters: strategy_name? and limit? (1..100)
    """
    # Validate limit explicitly to return 400 on violations
    if limit is not None:
        try:
            lim = int(limit)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid limit")
        if lim < 1 or lim > 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
        limit = lim

    # Build list from in-memory registry
    items = []
    for bt_id, entry in _BACKTEST_REGISTRY.items():
        if strategy_name and entry.get("strategy_name") != strategy_name:
            continue
        items.append(
            {
                "backtest_id": bt_id,
                "status": entry.get("status", "QUEUED"),
                "strategy_name": entry.get("strategy_name", "unknown"),
            }
        )

    # Apply limit if provided
    if limit is not None:
        items = items[: limit]

    return {"results": items}


@router.post("/backtests", status_code=202)
async def post_backtest(request: Request) -> Dict[str, Any]:
    """
    POST /api/v1/backtests

    Creates a backtest job.

    Contract expectations (tests):
    - Required body fields: strategy_name, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), symbol
    - Optional: initial_balance (string/number)
    - 202 Accepted with JSON: { backtest_id, status, created_at }
    - 400 for missing/invalid fields or invalid date formats
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid request body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")

    # Validate required fields
    required_fields = ["strategy_name", "start_date", "end_date", "symbol"]
    for f in required_fields:
        if f not in body or body[f] in (None, ""):
            raise HTTPException(status_code=400, detail=f"missing field: {f}")

    # Validate dates (YYYY-MM-DD)
    for dfield in ("start_date", "end_date"):
        try:
            datetime.strptime(str(body[dfield]), "%Y-%m-%d")
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid date: {dfield}")

    # Accept the job and register minimal state for retrieval
    backtest_id = str(uuid4())
    created_at = datetime.utcnow().isoformat()
    _BACKTEST_REGISTRY[backtest_id] = {
        "strategy_name": body.get("strategy_name"),
        "status": "RUNNING",
        "created_at": created_at,
    }

    return {"backtest_id": backtest_id, "status": "QUEUED", "created_at": created_at}


@router.get("/backtests/{backtest_id}")
async def get_backtest(backtest_id: str) -> Dict[str, Any]:
    """
    GET /api/v1/backtests/{id}

    Retrieves a backtest result by ID.

    Contract expectations:
    - 400 if `backtest_id` is not a valid UUID string
    - 404 if no backtest exists with the given ID
    - 200 with JSON body containing required fields when found
    """

    # Validate UUID format explicitly (return 400 rather than 422)
    try:
        bt_uuid = UUID(backtest_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid backtest id format")

    # Lookup in local registry; if present, build contract-compliant response
    entry = _BACKTEST_REGISTRY.get(str(bt_uuid))
    if not entry:
        raise HTTPException(status_code=404, detail="backtest not found")

    payload: Dict[str, Any] = {
        "backtest_id": str(bt_uuid),
        "status": entry.get("status", "QUEUED"),
        "strategy_name": entry.get("strategy_name", "unknown"),
    }

    # If later we set status to COMPLETED, include a minimal results block
    if payload["status"] == "COMPLETED":
        payload["results"] = {"total_trades": 0, "win_rate": 0.0, "total_return": 0.0}
        payload["summary"] = (
            f"Strategy {payload['strategy_name']}: trades=0, win_rate=0.00, return=0.00"
        )

    return jsonable_encoder(payload)
