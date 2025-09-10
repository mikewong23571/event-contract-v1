from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class MarketData(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    trade_count: int
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('open_price', 'high_price', 'low_price', 'close_price')
    def validate_positive_prices(cls, v):
        if v <= 0:
            raise ValueError('All prices must be positive')
        return v

    @validator('high_price')
    def validate_high_price(cls, v, values):
        if 'open_price' in values and 'close_price' in values:
            max_price = max(values['open_price'], values['close_price'])
            if v < max_price:
                raise ValueError('high_price must be >= max(open_price, close_price)')
        return v

    @validator('low_price')
    def validate_low_price(cls, v, values):
        if 'open_price' in values and 'close_price' in values:
            min_price = min(values['open_price'], values['close_price'])
            if v > min_price:
                raise ValueError('low_price must be <= min(open_price, close_price)')
        return v

    @validator('volume', 'quote_volume')
    def validate_non_negative_volumes(cls, v):
        if v < 0:
            raise ValueError('volume and quote_volume must be non-negative')
        return v

    @validator('trade_count')
    def validate_trade_count(cls, v):
        if v < 0:
            raise ValueError('trade_count must be non-negative')
        return v