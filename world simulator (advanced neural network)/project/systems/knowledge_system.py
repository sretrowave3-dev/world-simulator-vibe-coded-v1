"""
project/systems/knowledge_system.py

Knowledge System coordinating learning transfers and tech tree node discoveries.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human


class KnowledgeSystem:
    """Orchestrates knowledge inheritance transfers between entities."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "KnowledgeSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.CIVILIZATION

    @property
    def priority(self) -> int:
        return ExecutionPriority.KNOWLEDGE

    @property
    def dependencies(self) -> Set[str]:
        return {"CivilizationSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        humans = [e for e in self._entities_list if e.is_alive and e.entity_type == EntityType.HUMAN]

        # Fittest/Elder teaches neighbors
        for teacher in humans:
            if teacher.social_rank == 2:  # Elder
                for student in humans:
                    if student.entity_id != teacher.entity_id and student.technology_level < teacher.technology_level:
                        dx = student.pos_x - teacher.pos_x
                        dy = student.pos_y - teacher.pos_y
                        dist = math.hypot(dx, dy)
                        if dist < 50.0:  # Transfer within range
                            student.technology_level = teacher.technology_level

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
