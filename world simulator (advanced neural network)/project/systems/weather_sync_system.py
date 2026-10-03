"""
project/systems/weather_sync_system.py

Synchronizes weather grid properties with physical terrain and soil moisture columns.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.weather import WeatherManager


class WeatherSyncSystem:
    """Synchronizes atmospheric weather variables."""

    def __init__(self, weather_manager: WeatherManager) -> None:
        self._weather_manager = weather_manager

    @property
    def name(self) -> str:
        return "WeatherSyncSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.WEATHER + 1

    @property
    def dependencies(self) -> Set[str]:
        return {"WeatherSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        pass

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
