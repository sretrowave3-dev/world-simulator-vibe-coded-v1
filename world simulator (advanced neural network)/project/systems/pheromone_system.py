"""
project/systems/pheromone_system.py

Pheromone System executing diffusion equations and evaporation decay loops.
"""

from __future__ import annotations

from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.ai.pheromone import PheromoneGrid, PheromoneType
from project.entities.entity import Entity, EntityType


class PheromoneSystem:
    """Manages chemical diffusion grid updates."""

    def __init__(self, pheromone_grid: PheromoneGrid, entities_list: List[Entity]) -> None:
        self._pheromone_grid = pheromone_grid
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "PheromoneSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.AI

    @property
    def priority(self) -> int:
        return ExecutionPriority.PHEROMONES

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self._pheromone_grid.clear()

    def update(self, context: UpdateContext) -> None:
        # 1. Diffuse and evaporate pheromones
        self._pheromone_grid.tick(context.delta_time)

        # 2. Let entities deposit pheromone trails based on actions
        for entity in self._entities_list:
            if not entity.is_alive:
                continue

            if entity.current_action == "FORAGE_FOOD":
                # Deposit food trail scent
                self._pheromone_grid.deposit(
                    entity.pos_x,
                    entity.pos_y,
                    PheromoneType.FOOD_TRAIL,
                    intensity=10.0 * context.delta_time
                )
            elif entity.current_action == "FLEE":
                # Deposit danger alarm scent
                self._pheromone_grid.deposit(
                    entity.pos_x,
                    entity.pos_y,
                    PheromoneType.DANGER_ALARM,
                    intensity=25.0 * context.delta_time
                )

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
