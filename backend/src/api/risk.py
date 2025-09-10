from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter


router = APIRouter()


@router.get("/risk-parameters")
async def get_risk_parameters():
    """
    GET /api/v1/risk-parameters

    Returns current risk parameter configuration.

    Contract expectations:
    - 200 with RiskParameters schema when parameters exist
    - 404 if no parameters configured (not used here; default provided)

    Notes:
    - Decimal-like fields are returned as strings per contract
    - T049 requires only the GET endpoint implementation
    """

    # Provide a minimal, static configuration satisfying the contract schema.
    # Future implementations may fetch per-user settings from persistence.
    now = datetime.utcnow().isoformat()
    return {
        "id": str(uuid4()),
        "user_id": "default",
        "max_bet_size": "100.00",
        "max_daily_bets": 10,
        "max_parallel_positions": 3,
        "min_probability_edge": "0.10",
        "frequency_limit_minutes": 15,
        "max_daily_loss": "500.00",
        "created_at": now,
        "updated_at": now,
    }

