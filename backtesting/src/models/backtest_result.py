from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class BacktestResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_signals: int
    successful_signals: int
    win_rate: Decimal
    total_profit_loss: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    parameters: Dict[str, Any]
    execution_mode: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('win_rate')
    def validate_win_rate(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('win_rate must be between 0.0 and 1.0')
        return v

    @validator('successful_signals')
    def validate_successful_signals(cls, v, values):
        if 'total_signals' in values and v > values['total_signals']:
            raise ValueError('successful_signals must be <= total_signals')
        return v

    @validator('total_signals')
    def validate_total_signals(cls, v):
        if v < 0:
            raise ValueError('total_signals must be non-negative')
        return v

    @validator('execution_mode')
    def validate_execution_mode(cls, v):
        if v not in ["FIRST_SIGNAL", "CONTINUOUS", "ENHANCED"]:
            raise ValueError('execution_mode must be "FIRST_SIGNAL", "CONTINUOUS", or "ENHANCED"')
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v