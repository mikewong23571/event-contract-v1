from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class BacktestTrade(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    backtest_result_id: UUID
    signal_timestamp: datetime
    direction: str
    entry_price: Decimal
    exit_price: Decimal
    bet_amount: Decimal
    profit_loss: Decimal
    was_successful: bool
    contract_duration_minutes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('direction')
    def validate_direction(cls, v):
        if v not in ["UP", "DOWN"]:
            raise ValueError('direction must be "UP" or "DOWN"')
        return v

    @validator('entry_price', 'exit_price', 'bet_amount')
    def validate_positive_values(cls, v):
        if v <= 0:
            raise ValueError('entry_price, exit_price, and bet_amount must be positive')
        return v

    @validator('contract_duration_minutes')
    def validate_contract_duration(cls, v):
        if v <= 0:
            raise ValueError('contract_duration_minutes must be positive')
        return v