"""
project/systems/time_system.py

Time System coordinating planetary time keeper tick progressions.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.time import WorldTimeManager


class TimeSystem:
    """Advances planetary time tracking."""

    def __init__(self, time_manager: WorldTimeManager) -> None:
        self._time_manager = time_manager

    @property
    def name(self) -> str:
        return "TimeSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.PRE_UPDATE

    @property
    def priority(self) -> int:
        return ExecutionPriority.WEATHER - 1  # Runs first in PRE_UPDATE

    @property
    def dependencies(self) -> Set[str]:
        return set()

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        self._time_manager.reset()

    def update(self, context: UpdateContext) -> None:
        self._time_manager.tick(context.delta_time)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
