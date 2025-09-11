"""
Performance metrics collection utilities.

Task: T092 Performance metrics collection
Path: backend/src/monitoring/metrics.py

Provides lightweight, in-memory collectors for:
- Data pipeline metrics (ingestion rate, latency, error rate, quality)
- System performance metrics aggregation (daily summaries)

Notes:
- Intentionally simple and dependency-free; can later be wired to
  Prometheus or a TSDB if needed.
- Thread-safe via internal locks for use across async tasks/threads.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from threading import Lock
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from ..models.performance_metrics import PerformanceMetrics


@dataclass
class _SlidingWindow:
    """Time-based sliding window of float values.

    Maintains values with associated timestamps and supports computation of
    averages over a configurable time window.
    """

    window: timedelta
    samples: Deque[Tuple[datetime, float]] = field(default_factory=deque)
    lock: Lock = field(default_factory=Lock)

    def add(self, value: float, ts: Optional[datetime] = None) -> None:
        ts = ts or datetime.utcnow()
        with self.lock:
            self.samples.append((ts, value))
            self._prune(ts)

    def _prune(self, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        cutoff = now - self.window
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()

    def avg(self) -> float:
        with self.lock:
            self._prune()
            if not self.samples:
                return 0.0
            return sum(v for _t, v in self.samples) / len(self.samples)

    def count(self) -> int:
        with self.lock:
            self._prune()
            return len(self.samples)


class DataPipelineMetricsCollector:
    """Collects basic data pipeline performance metrics.

    Tracks:
    - ingestion_rate: events per minute (rolling 5-minute window)
    - processing_latency: average processing duration (ms) over last 5 minutes
    - error_rate: fraction of failures over last 5 minutes
    - data_quality_score: average 0..1 score over last 5 minutes
    - storage_utilization: placeholder (0..1) if available
    """

    def __init__(self) -> None:
        window = timedelta(minutes=5)
        self._ingestions = _SlidingWindow(window)
        self._latencies_ms = _SlidingWindow(window)
        self._errors = _SlidingWindow(window)
        self._quality = _SlidingWindow(window)
        self._storage_utilization: float = 0.0
        self._lock = Lock()

    def record_ingestion(
        self,
        duration_seconds: float,
        success: bool = True,
        quality_score: Optional[float] = None,
        ts: Optional[datetime] = None,
    ) -> None:
        ts = ts or datetime.utcnow()
        self._ingestions.add(1.0, ts)
        self._latencies_ms.add(duration_seconds * 1000.0, ts)
        if not success:
            self._errors.add(1.0, ts)
        if quality_score is not None:
            # Clamp into [0,1]
            qs = max(0.0, min(1.0, float(quality_score)))
            self._quality.add(qs, ts)

    def set_storage_utilization(self, utilization_0_1: float) -> None:
        with self._lock:
            self._storage_utilization = max(0.0, min(1.0, float(utilization_0_1)))

    def get_metrics(self) -> Dict[str, float]:
        now = datetime.utcnow()
        # Events per minute ≈ count in last 5 minutes / 5
        ingestions_last_5m = self._ingestions.count()
        ingestion_rate_per_min = ingestions_last_5m / 5.0

        avg_latency_ms = self._latencies_ms.avg()
        error_rate = 0.0
        if ingestions_last_5m > 0:
            error_rate = self._errors.count() / float(ingestions_last_5m)

        dq = self._quality.avg()  # [0,1]
        with self._lock:
            storage = self._storage_utilization

        return {
            "ingestion_rate": float(ingestion_rate_per_min),
            "processing_latency": float(avg_latency_ms),
            "error_rate": float(error_rate),
            "data_quality_score": float(dq),
            "storage_utilization": float(storage),
            "timestamp": now.timestamp(),
        }


class PerformanceMetricsCollector:
    """Aggregates high-level performance metrics per-day for reporting.

    This collector is intentionally minimal and computes a daily snapshot that
    can be serialized with the existing PerformanceMetrics Pydantic model.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        # Day → aggregation state
        self._state: Dict[date, Dict[str, float]] = {}
        # uptime estimates (simple heuristic)
        self._start_time = datetime.utcnow()

    def record_signal(
        self,
        latency_ms: float,
        executed: bool,
        won: Optional[bool] = None,
        profit_loss: Optional[float] = None,
        ts: Optional[datetime] = None,
    ) -> None:
        ts = ts or datetime.utcnow()
        d = ts.date()
        with self._lock:
            s = self._state.setdefault(
                d,
                dict(
                    total_generated=0.0,
                    total_executed=0.0,
                    wins=0.0,
                    pnl=0.0,
                    latency_sum_ms=0.0,
                ),
            )
            s["total_generated"] += 1.0
            if executed:
                s["total_executed"] += 1.0
            if won is True:
                s["wins"] += 1.0
            if profit_loss is not None:
                s["pnl"] += float(profit_loss)
            s["latency_sum_ms"] += float(latency_ms)

    def _uptime_ratio(self) -> Decimal:
        # naive uptime estimation: time since start vs 24h
        elapsed = datetime.utcnow() - self._start_time
        ratio = min(1.0, max(0.0, elapsed.total_seconds() / (24 * 3600)))
        return Decimal(str(round(ratio, 6)))

    def get_daily_metrics(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> Tuple[List[PerformanceMetrics], Dict[str, Dict[str, str]]]:
        """Return list of PerformanceMetrics between dates and a summary.

        Summary contains overall win rate and PnL plus best/worst day info.
        """
        with self._lock:
            items = list(self._state.items())

        # Filter by date range
        if start is not None or end is not None:
            def in_range(d: date) -> bool:
                if start is not None and d < start:
                    return False
                if end is not None and d > end:
                    return False
                return True

            items = [(d, s) for d, s in items if in_range(d)]

        metrics: List[PerformanceMetrics] = []
        overall_generated = 0.0
        overall_wins = 0.0
        total_pnl = Decimal("0")
        best: Optional[Tuple[date, Decimal]] = None
        worst: Optional[Tuple[date, Decimal]] = None

        for d, s in sorted(items, key=lambda x: x[0]):
            total_gen = int(s.get("total_generated", 0.0))
            total_exec = int(s.get("total_executed", 0.0))
            wins = int(s.get("wins", 0.0))
            pnl = Decimal(str(round(s.get("pnl", 0.0), 8)))
            avg_latency_ms = int(
                round((s.get("latency_sum_ms", 0.0) / total_gen) if total_gen else 0.0)
            )

            win_rate = Decimal("0")
            if total_gen:
                win_rate = Decimal(str(round(wins / total_gen, 6)))

            pm = PerformanceMetrics(
                date=d,
                total_signals_generated=total_gen,
                total_signals_executed=total_exec,
                daily_win_rate=win_rate,
                daily_profit_loss=pnl,
                avg_signal_latency_ms=avg_latency_ms,
                system_uptime_percentage=self._uptime_ratio(),
            )
            metrics.append(pm)

            # Accumulate summary
            overall_generated += total_gen
            overall_wins += wins
            total_pnl += pnl

            # Update best/worst
            if best is None or pnl > best[1]:
                best = (d, pnl)
            if worst is None or pnl < worst[1]:
                worst = (d, pnl)

        overall_wr = Decimal("0")
        if overall_generated:
            overall_wr = Decimal(str(round(overall_wins / overall_generated, 6)))

        def _fmt_day(entry: Optional[Tuple[date, Decimal]]) -> Dict[str, str]:
            if not entry:
                return {"date": "", "profit_loss": "0"}
            d, v = entry
            return {"date": d.isoformat(), "profit_loss": str(v)}

        summary = {
            "overall_win_rate": str(overall_wr),
            "total_profit_loss": str(total_pnl),
            "best_day": _fmt_day(best),
            "worst_day": _fmt_day(worst),
        }

        return metrics, summary


class MetricsRegistry:
    """Singleton-like registry for metrics collectors used by the backend."""

    def __init__(self) -> None:
        self.data_pipeline = DataPipelineMetricsCollector()
        self.performance = PerformanceMetricsCollector()


# Global registry instance for convenience imports
metrics_registry = MetricsRegistry()


def get_system_metrics() -> Dict[str, float]:
    """Get current system metrics for WebSocket status broadcasts."""
    pipeline_metrics = metrics_registry.data_pipeline.get_metrics()
    
    # Get today's performance metrics 
    daily_metrics, _ = metrics_registry.performance.get_daily_metrics(
        start=datetime.utcnow().date(), 
        end=datetime.utcnow().date()
    )
    
    signals_today = daily_metrics[0].total_signals_generated if daily_metrics else 0
    avg_latency = daily_metrics[0].avg_signal_latency_ms if daily_metrics else 50
    uptime_hours = (datetime.utcnow() - metrics_registry.performance._start_time).total_seconds() / 3600
    
    return {
        "signals_generated_today": signals_today,
        "avg_signal_latency_ms": avg_latency,
        "system_uptime_hours": round(uptime_hours, 2),
        "ingestion_rate": pipeline_metrics.get("ingestion_rate", 0),
        "processing_latency": pipeline_metrics.get("processing_latency", 0),
        "error_rate": pipeline_metrics.get("error_rate", 0),
        "data_quality_score": pipeline_metrics.get("data_quality_score", 1.0),
        "storage_utilization": pipeline_metrics.get("storage_utilization", 0),
    }

