"""
project/systems/civilization_system.py

Civilization System managing technological advancements, cultural drifts, and settlements.
"""

from __future__ import annotations

from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human


class CivilizationSystem:
    """Manages technology progression across human factions."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "CivilizationSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.CIVILIZATION

    @property
    def priority(self) -> int:
        return ExecutionPriority.CIVILIZATION

    @property
    def dependencies(self) -> Set[str]:
        return {"SocialSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        humans = [e for e in self._entities_list if e.is_alive and e.entity_type == EntityType.HUMAN]

        # Faction level updates
        for h in humans:
            if h.energy > 300.0 and h.social_rank == 2:  # Elders with high energy study tech
                if context.tick % 1000 == 0:
                    h.technology_level += 1

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
