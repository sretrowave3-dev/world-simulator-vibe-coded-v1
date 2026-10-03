"""
project/analytics/__init__.py

Data analytics, metrics collection, and session reporting modules for the Echo Evolution Simulator.
"""

from project.analytics.metrics import TelemetryTracker, TelemetryPoint
from project.analytics.reports import SessionSummary, SessionReporter

try:
    from project.analytics.graphs import PopulationGraphRenderer
except ImportError:
    PopulationGraphRenderer = None  # type: ignore

__all__ = [
    "TelemetryTracker",
    "TelemetryPoint",
    "SessionSummary",
    "SessionReporter",
    "PopulationGraphRenderer",
]
