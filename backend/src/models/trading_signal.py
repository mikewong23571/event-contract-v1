from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class TradingSignal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    symbol: str
    direction: str
    predicted_probability: float
    confidence_level: str
    expiry_time: datetime
    strategy_version: str
    technical_indicators: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

    @validator('predicted_probability')
    def validate_probability(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('predicted_probability must be between 0.0 and 1.0')
        return v

    @validator('direction')
    def validate_direction(cls, v):
        if v not in ["UP", "DOWN"]:
            raise ValueError('direction must be "UP" or "DOWN"')
        return v

    @validator('confidence_level')
    def validate_confidence_level(cls, v):
        if v not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError('confidence_level must be "LOW", "MEDIUM", or "HIGH"')
        return v

    @validator('expiry_time')
    def validate_expiry_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('expiry_time must be in the future')
        return v

    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('expires_at must be in the future')
        return v