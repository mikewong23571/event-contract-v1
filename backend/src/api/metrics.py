from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from ..monitoring.metrics import metrics_registry
from ..models.performance_metrics import PerformanceMetrics


router = APIRouter()


@router.get("/metrics/performance")
async def get_performance_metrics(
    start_date: Optional[str] = Query(None, description="Filter start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter end date YYYY-MM-DD"),
) -> Dict[str, Any]:
    """
    GET /api/v1/metrics/performance

    Returns aggregated performance metrics and summary.
    Response shape: { metrics: PerformanceMetrics[], summary: {...} }
    """
    from datetime import date

    start: Optional[date] = None
    end: Optional[date] = None

    # Optional date parsing with explicit 400 on bad format
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="invalid start_date")
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="invalid end_date")

    metrics, summary = metrics_registry.performance.get_daily_metrics(start=start, end=end)
    # Serialize using PerformanceMetrics encoders for Decimal/date/UUID
    encoded_metrics = [
        jsonable_encoder(m, custom_encoder=PerformanceMetrics.Config.json_encoders)
        for m in metrics
    ]

    return {"metrics": encoded_metrics, "summary": summary}

