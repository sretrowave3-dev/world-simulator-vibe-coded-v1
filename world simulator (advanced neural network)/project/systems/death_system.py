"""
project/systems/death_system.py

Death System managing carcasses, registry deletions, and resource depositation.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.world.soil import SoilManager


class DeathSystem:
    """Manages biological death processes and nutrient recycling."""

    def __init__(self, entities_list: List[Entity], soil_manager: SoilManager) -> None:
        self._entities_list = entities_list
        self._soil_manager = soil_manager

    @property
    def name(self) -> str:
        return "DeathSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.MUTATION - 1

    @property
    def dependencies(self) -> Set[str]:
        return {"AgingSystem", "CombatSystem", "DigestionSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        dead_entities: List[Entity] = []

        # Find dead entities to recycle
        for entity in self._entities_list:
            if not entity.is_alive:
                dead_entities.append(entity)

        for entity in dead_entities:
            # Recycle biomass into soil nutrients at their final position
            cx = int(math.floor(entity.pos_x / 16.0))
            cy = int(math.floor(entity.pos_y / 16.0))
            lx = int(math.floor(entity.pos_x)) % 16
            ly = int(math.floor(entity.pos_y)) % 16

            soil_chunk = self._soil_manager.get_or_create_chunk((cx, cy))
            soil_chunk.deposit_organic_matter(lx, ly, mass_kg=entity.mass_kg)

            # Remove from active list
            if entity in self._entities_list:
                self._entities_list.remove(entity)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
