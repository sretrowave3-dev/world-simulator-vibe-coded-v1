"""
project/systems/food_system.py

Food System managing crop cycles, pollination, fruit decays, and environmental nutrient cycle bindings.
"""

from __future__ import annotations

from typing import Set
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.food import FoodManager, ChunkEnvironmentContext


class FoodSystem:
    """Manages plant agricultural lifecycles and fruit drops."""

    def __init__(self, food_manager: FoodManager) -> None:
        self._food_manager = food_manager

    @property
    def name(self) -> str:
        return "FoodSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.FOOD

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        # Mock environment provider mapping chunk coordinates
        def mock_env_provider(c_coords) -> ChunkEnvironmentContext:
            return ChunkEnvironmentContext()

        # Run food simulation ticks
        self._food_manager.tick_simulation(context.delta_time, mock_env_provider)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
