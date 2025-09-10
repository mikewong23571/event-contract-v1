from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query

from ..lib.data_ingestion.data_ingester import DataIngester
from ..services.market_data_service import MarketDataService
from ..models.market_data import MarketData


router = APIRouter()


@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    interval: str = Query(
        default="1m",
        description="Data interval (allowed: 1m, 5m, 15m, 1h)",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of data points to return (1-1000)",
    ),
) -> Dict[str, Any]:
    """
    GET /api/v1/market-data/{symbol}

    Contract expectations:
    - Path parameter `symbol` is required and must be supported → 404 if unknown
    - Query `interval` allowed values: 1m, 5m, 15m, 1h → 400 if invalid
    - Query `limit` integer range: 1..1000 → 400 if invalid
    - Response JSON: { symbol, interval, data: [MarketData...] }
      where MarketData fields include: symbol, timestamp (ISO),
      open_price, high_price, low_price, close_price, volume (as strings),
      and may include quote_volume (string) and trade_count (int).
    """

    # Validate interval explicitly (return 400 instead of 422)
    allowed_intervals = {"1m", "5m", "15m", "1h"}
    if interval not in allowed_intervals:
        raise HTTPException(status_code=400, detail="invalid interval")

    # Validate limit bounds explicitly (return 400 instead of 422)
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

    # Validate symbol against supported list
    service = MarketDataService()
    if symbol not in service.get_supported_symbols():
        raise HTTPException(status_code=404, detail="symbol not found")

    # Ingest market data for the requested symbol
    ingester = DataIngester()
    records: List[MarketData] = ingester.ingest_market_data([symbol], timeframe=interval, limit=limit)

    # Transform records into contract-compliant JSON objects
    data: List[Dict[str, Any]] = []
    for md in records[:limit]:
        item: Dict[str, Any] = {
            "symbol": md.symbol,
            "timestamp": md.timestamp.isoformat(),
            "open_price": str(md.open_price),
            "high_price": str(md.high_price),
            "low_price": str(md.low_price),
            "close_price": str(md.close_price),
            "volume": str(md.volume),
        }

        # Optional fields if present
        if hasattr(md, "quote_volume") and md.quote_volume is not None:
            item["quote_volume"] = str(md.quote_volume)
        if hasattr(md, "trade_count") and md.trade_count is not None:
            item["trade_count"] = int(md.trade_count)

        data.append(item)

    return {
        "symbol": symbol,
        "interval": interval,
        "data": data,
    }

