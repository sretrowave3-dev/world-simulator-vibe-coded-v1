"""
project/systems/resource_system.py

Resource System to process natural mineral and wood resource node regenerations.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.resources import ResourceManager


class ResourceSystem:
    """Manages natural mineral node regenerations."""

    def __init__(self, resource_manager: ResourceManager) -> None:
        self._resource_manager = resource_manager

    @property
    def name(self) -> str:
        return "ResourceSystem"

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
        self._resource_manager.reset()

    def update(self, context: UpdateContext) -> None:
        self._resource_manager.tick(context.delta_time)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
