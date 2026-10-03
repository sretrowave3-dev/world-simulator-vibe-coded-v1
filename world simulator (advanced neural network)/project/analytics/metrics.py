"""
project/analytics/metrics.py

Telemetry Tracker recording simulation time-series metrics and exporting to CSV.
"""

from __future__ import annotations

import os
import csv
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class TelemetryPoint:
    tick: int
    timestamp_sec: float
    populations: Dict[str, int]
    avg_vitals: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, float] = field(default_factory=dict)


class TelemetryTracker:
    """Buffers and records time-series demographic variables."""

    def __init__(self, flush_interval_ticks: int = 600) -> None:
        self.flush_interval_ticks = flush_interval_ticks
        self.history: List[TelemetryPoint] = []
        self._buffered_points: List[TelemetryPoint] = []

    def record(
        self,
        tick: int,
        timestamp_sec: float,
        populations: Dict[str, int],
        avg_vitals: Dict[str, float],
        custom_metrics: Optional[Dict[str, float]] = None,
    ) -> None:
        """Buffers a single time-series metric point."""
        point = TelemetryPoint(
            tick=tick,
            timestamp_sec=timestamp_sec,
            populations=dict(populations),
            avg_vitals=dict(avg_vitals),
            custom_metrics=dict(custom_metrics or {}),
        )
        self.history.append(point)
        self._buffered_points.append(point)

    def flush_to_csv(self, filepath: str) -> None:
        """Appends all buffered metrics to a CSV file and clears the buffer."""
        if not self._buffered_points:
            return

        file_exists = os.path.exists(filepath)
        
        # Collect headers from the first point
        ref = self._buffered_points[0]
        headers = ["tick", "timestamp_sec"]
        
        # Dynamic headers based on dictionary keys
        pop_keys = sorted(f"pop_{k}" for k in ref.populations.keys())
        vital_keys = sorted(f"vital_{k}" for k in ref.avg_vitals.keys())
        custom_keys = sorted(f"metric_{k}" for k in ref.custom_metrics.keys())
        
        headers.extend(pop_keys)
        headers.extend(vital_keys)
        headers.extend(custom_keys)

        # Open in append mode
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)

            for p in self._buffered_points:
                row = [p.tick, p.timestamp_sec]
                # Populate columns dynamically
                for pk in pop_keys:
                    key = pk[4:]  # strip 'pop_'
                    row.append(p.populations.get(key, 0))
                for vk in vital_keys:
                    key = vk[6:]  # strip 'vital_'
                    row.append(p.avg_vitals.get(key, 0.0))
                for ck in custom_keys:
                    key = ck[7:]  # strip 'metric_'
                    row.append(p.custom_metrics.get(key, 0.0))
                writer.writerow(row)

        self._buffered_points.clear()

    def clear(self) -> None:
        self.history.clear()
        self._buffered_points.clear()
