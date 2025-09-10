from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class RiskParameters(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    max_bet_size: Decimal
    max_daily_bets: int
    max_parallel_positions: int
    min_probability_edge: Decimal
    frequency_limit_minutes: int
    max_daily_loss: Decimal
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('max_bet_size', 'max_daily_loss')
    def validate_positive_decimal_values(cls, v):
        if v <= 0:
            raise ValueError('All numeric values must be positive')
        return v

    @validator('max_daily_bets', 'max_parallel_positions', 'frequency_limit_minutes')
    def validate_positive_integer_values(cls, v):
        if v <= 0:
            raise ValueError('All numeric values must be positive')
        return v

    @validator('min_probability_edge')
    def validate_min_probability_edge(cls, v):
        if not (0.01 <= v <= 0.20):
            raise ValueError('min_probability_edge typically should be between 0.01 and 0.20')
        return v