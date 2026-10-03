"""
project/systems/water_system.py

Water System running evaporation, precipitation absorption, and lake dynamics.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.water import WaterManager


class WaterSystem:
    """Manages planetary hydrology systems."""

    def __init__(self, water_manager: WaterManager) -> None:
        self._water_manager = water_manager

    @property
    def name(self) -> str:
        return "WaterSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.RESOURCES + 1

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self._water_manager.reset()

    def update(self, context: UpdateContext) -> None:
        self._water_manager.tick(context.delta_time, ambient_temp=20.0, rainfall=0.01)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
