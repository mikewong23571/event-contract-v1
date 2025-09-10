from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class EventContract(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    contract_id: str
    symbol: str
    strike_price: Decimal
    expiry_time: datetime
    payout_ratio: Decimal
    implied_probability: Decimal
    status: str
    settlement_price: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('payout_ratio')
    def validate_payout_ratio(cls, v):
        if v <= 0:
            raise ValueError('payout_ratio must be positive')
        return v

    @validator('implied_probability')
    def validate_implied_probability(cls, v, values):
        if 'payout_ratio' in values:
            expected_probability = values['payout_ratio'] / (1 + values['payout_ratio'])
            # Allow small floating point differences
            if abs(v - expected_probability) > 0.0001:
                raise ValueError('implied_probability must equal payout_ratio / (1 + payout_ratio)')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v not in ["ACTIVE", "SETTLED", "CANCELLED"]:
            raise ValueError('status must be "ACTIVE", "SETTLED", or "CANCELLED"')
        return v

    @validator('expiry_time')
    def validate_expiry_time(cls, v, values):
        if 'status' in values and values['status'] == "ACTIVE":
            if v <= datetime.utcnow():
                raise ValueError('expiry_time must be future when status is "ACTIVE"')
        return v

    @validator('strike_price')
    def validate_strike_price(cls, v):
        if v <= 0:
            raise ValueError('strike_price must be positive')
        return v