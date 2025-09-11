"""
System alerts configuration and evaluation helpers.

Task: T094 System alerts configuration
Path: backend/src/monitoring/alerts.py

Defines alert rules and simple evaluators for key operational conditions.
Rules are kept intentionally simple and can be expanded with more complex
policies or moved to an external configuration store later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence


Severity = str  # "INFO" | "WARN" | "CRITICAL"


@dataclass(frozen=True)
class AlertRule:
    """Alert rule definition.

    Attributes:
        key: Stable identifier for the rule
        description: Human-readable description
        severity: Severity level (e.g., INFO, WARN, CRITICAL)
        condition: Function that returns True when the rule is violated
    """

    key: str
    description: str
    severity: Severity
    condition: Callable[[Dict[str, float]], bool]


def default_rules() -> List[AlertRule]:
    """Return a set of default alert rules for the system."""

    def error_rate_high(m: Dict[str, float]) -> bool:
        return m.get("error_rate", 0.0) >= 0.05  # 5%+

    def latency_slow(m: Dict[str, float]) -> bool:
        return m.get("processing_latency", 0.0) > 2000.0  # > 2s

    def ingestion_stalled(m: Dict[str, float]) -> bool:
        return m.get("ingestion_rate", 0.0) < 0.1  # < 0.1 ev/min over 5m

    return [
        AlertRule(
            key="high_error_rate",
            description="Data pipeline error rate is high",
            severity="WARN",
            condition=error_rate_high,
        ),
        AlertRule(
            key="slow_processing",
            description="Data pipeline processing latency is slow",
            severity="WARN",
            condition=latency_slow,
        ),
        AlertRule(
            key="ingestion_stalled",
            description="Data ingestion appears stalled",
            severity="CRITICAL",
            condition=ingestion_stalled,
        ),
    ]


def evaluate_alerts(metrics: Dict[str, float], rules: Sequence[AlertRule] | None = None) -> List[Dict[str, str]]:
    """Evaluate metrics against alert rules and return triggered alerts.

    Returns a list of {key, severity, description} for each triggered alert.
    """
    ruleset = list(rules) if rules is not None else default_rules()
    alerts: List[Dict[str, str]] = []
    for r in ruleset:
        try:
            if r.condition(metrics):
                alerts.append({
                    "key": r.key,
                    "severity": r.severity,
                    "description": r.description,
                })
        except Exception:
            # Defensive: rule evaluation should never crash the system
            continue
    return alerts

