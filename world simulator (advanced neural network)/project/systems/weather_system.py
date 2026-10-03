"""
project/systems/weather_system.py

Weather System executing climate and atmospheric calculations on environmental grids.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.weather import WeatherManager


class WeatherSystem:
    """Executes planetary climate calculations."""

    def __init__(self, weather_manager: WeatherManager) -> None:
        self._weather_manager = weather_manager

    @property
    def name(self) -> str:
        return "WeatherSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.WEATHER

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        # Advance weather simulation
        self._weather_manager.update(context.delta_time)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
