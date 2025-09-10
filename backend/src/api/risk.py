from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError, Field

from ..models.risk_parameters import RiskParameters
from ..services.risk_service import RiskManagementService


router = APIRouter()

# Single service instance for in-memory persistence across requests
_risk_service = RiskManagementService()


class RiskParametersUpdate(BaseModel):
    """Schema for updating risk parameters (partial updates allowed)."""

    user_id: str | None = None
    max_bet_size: Decimal | None = Field(default=None)
    max_daily_bets: int | None = Field(default=None)
    max_parallel_positions: int | None = Field(default=None)
    min_probability_edge: Decimal | None = Field(default=None)
    frequency_limit_minutes: int | None = Field(default=None)
    max_daily_loss: Decimal | None = Field(default=None)


def _ensure_default_params(user_id: str) -> RiskParameters:
    """Ensure a user has risk parameters; create sensible defaults if missing."""
    existing = _risk_service.get_risk_parameters(user_id)
    if existing:
        return existing
    return _risk_service.create_risk_parameters(
        user_id=user_id,
        max_bet_size=Decimal("100.00"),
        max_daily_bets=10,
        max_parallel_positions=3,
        min_probability_edge=Decimal("0.10"),
        frequency_limit_minutes=15,
        max_daily_loss=Decimal("500.00"),
    )


@router.get("/risk-parameters")
async def get_risk_parameters():
    """
    GET /api/v1/risk-parameters

    Returns current risk parameter configuration for the default user.

    Contract expectations:
    - 200 with RiskParameters schema when parameters exist
    - Decimal-like fields are returned as strings per contract
    """

    params = _ensure_default_params("default")
    # Use custom encoders to ensure Decimals are serialized as strings
    encoded = jsonable_encoder(
        params, custom_encoder=RiskParameters.Config.json_encoders
    )
    return encoded


@router.put("/risk-parameters")
async def put_risk_parameters(body: dict):
    """
    PUT /api/v1/risk-parameters

    Updates risk parameter configuration for the default user. Partial updates allowed.

    Contract expectations (from tests):
    - 200 on successful update with RiskParameters schema in response
    - 400 for invalid values or malformed inputs
    - Partial updates supported (only provided fields are updated)
    """

    # Validate request body against update schema, mapping errors to 400
    try:
        update = RiskParametersUpdate(**body)
    except ValidationError:
        raise HTTPException(status_code=400, detail="invalid request body")

    user_id = update.user_id or "default"
    # Ensure there is a baseline to update
    _ensure_default_params(user_id)

    # Build updates dict with only provided fields
    updates: dict = {}
    for field in (
        "max_bet_size",
        "max_daily_bets",
        "max_parallel_positions",
        "min_probability_edge",
        "frequency_limit_minutes",
        "max_daily_loss",
    ):
        value = getattr(update, field)
        if value is not None:
            updates[field] = value

    # Validate business rules using the RiskParameters model by attempting to construct it
    # through the service update (which uses the model's validators).
    updated = _risk_service.update_risk_parameters(user_id=user_id, **updates)
    if updated is None:
        # If update failed (e.g., user not found), treat as bad request per contract
        raise HTTPException(status_code=400, detail="unable to update risk parameters")

    # Encode with custom encoders to match contract (decimals as strings)
    encoded = jsonable_encoder(
        updated, custom_encoder=RiskParameters.Config.json_encoders
    )
    return encoded
