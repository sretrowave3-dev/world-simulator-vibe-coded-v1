"""
project/systems/soil_system.py

Soil System running mineral nutrient updates and organic mineralization cycles.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.soil import SoilManager


class SoilSystem:
    """Manages chemical cycles of nitrogen, phosphorus, and potassium."""

    def __init__(self, soil_manager: SoilManager) -> None:
        self._soil_manager = soil_manager

    @property
    def name(self) -> str:
        return "SoilSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.RESOURCES

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self._soil_manager.reset()

    def update(self, context: UpdateContext) -> None:
        # Tick the soil manager with typical surface temperature
        self._soil_manager.tick(context.delta_time, ambient_temperature_c=20.0)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
