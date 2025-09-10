from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class PerformanceMetrics(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    date: date
    total_signals_generated: int
    total_signals_executed: int
    daily_win_rate: Decimal
    daily_profit_loss: Decimal
    avg_signal_latency_ms: int
    system_uptime_percentage: Decimal
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('total_signals_generated', 'total_signals_executed', 'avg_signal_latency_ms')
    def validate_non_negative_integers(cls, v):
        if v < 0:
            raise ValueError('Integer values must be non-negative')
        return v

    @validator('total_signals_executed')
    def validate_signals_executed(cls, v, values):
        if 'total_signals_generated' in values and v > values['total_signals_generated']:
            raise ValueError('total_signals_executed must be <= total_signals_generated')
        return v

    @validator('daily_win_rate', 'system_uptime_percentage')
    def validate_percentage_values(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('Percentage values must be between 0.0 and 1.0')
        return v