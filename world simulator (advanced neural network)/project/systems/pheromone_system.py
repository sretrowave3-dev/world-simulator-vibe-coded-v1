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

        # 2. Let entities deposit pheromone trails based on biology and actions
        dt = context.delta_time
        for entity in self._entities_list:
            if not entity.is_alive:
                continue

            action = getattr(entity, "current_action", "") or ""
            action_upper = action.upper()
            ex = entity.pos_x
            ey = entity.pos_y

            # A. Food Sources: Plants, crops, fruits, and food nodes emit appetizing ambient scent
            is_food_source = (
                entity.entity_type in (EntityType.PLANT, EntityType.FUNGUS)
                or entity.custom_data.get("is_food", False)
                or "food" in entity.species_id.lower()
                or "fruit" in entity.species_id.lower()
            )
            if is_food_source:
                self._pheromone_grid.deposit(
                    ex, ey,
                    PheromoneType.FOOD_TRAIL,
                    intensity=25.0 * dt
                )

            # B. Foraging Organisms: Entities eating, seeking, or carrying food deposit path scent
            if (
                "EAT" in action_upper
                or "FORAGE" in action_upper
                or "FEAST" in action_upper
                or "GRAZE" in action_upper
                or "FOOD" in action_upper
                or action_upper == "FORAGE_FOOD"
            ):
                self._pheromone_grid.deposit(
                    ex, ey,
                    PheromoneType.FOOD_TRAIL,
                    intensity=30.0 * dt
                )

            # C. Threat & Alarm: Fleeing, terrified, or combat-engaged organisms deposit danger scent
            fear = getattr(entity, "fear", 0.0)
            stress = getattr(entity, "stress", 0.0)
            in_combat = getattr(entity, "in_combat", False) or "COMBAT" in action_upper or "ATTACK" in action_upper
            is_fleeing = "FLEE" in action_upper or "ESCAPE" in action_upper

            if is_fleeing or in_combat or fear > 0.35 or stress > 0.6:
                self._pheromone_grid.deposit(
                    ex, ey,
                    PheromoneType.DANGER_ALARM,
                    intensity=45.0 * dt
                )

            # D. Predator Trail: Apex carnivores emit an ominous localized threat scent
            if entity.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE):
                self._pheromone_grid.deposit(
                    ex, ey,
                    PheromoneType.DANGER_ALARM,
                    intensity=15.0 * dt
                )

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
