"""Compatibility wrapper for report generator (T072)

Exposes ReportGenerator under the expected path:
backtesting/src/generators/report_generator.py

Delegates to the library implementation at
backtesting/src/lib/backtesting_engine/report_generator.py.
"""

from __future__ import annotations

from ..lib.backtesting_engine.report_generator import (
    ReportGenerator,  # re-export
)

__all__ = ["ReportGenerator"]

