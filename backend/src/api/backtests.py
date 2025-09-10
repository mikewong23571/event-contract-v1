from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from uuid import UUID

from ..services.backtest_service import BacktestService
from ...backtesting.src.models.backtest_result import BacktestResult


router = APIRouter()

# In-memory service instance (placeholder until persistence is added)
_backtest_service = BacktestService()


def _serialize_backtest_result(result: BacktestResult) -> Dict[str, Any]:
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
    return jsonable_encoder(payload, custom_encoder=BacktestResult.Config.json_encoders)


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

    # Look up result via service (currently searches in-memory cache)
    result: Optional[BacktestResult] = _backtest_service.get_backtest_by_id(bt_uuid)
    if result is None:
        raise HTTPException(status_code=404, detail="backtest not found")

    return _serialize_backtest_result(result)

