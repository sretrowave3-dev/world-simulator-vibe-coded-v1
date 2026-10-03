"""
project/systems/statistics_system.py

Statistics System compiling population counts, age distributions, and performance timing statistics.
"""

from __future__ import annotations

from typing import Set, List, Dict
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType


class StatisticsSystem:
    """Manages population telemetry records."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list
        self.history: List[Dict[str, int]] = []

    @property
    def name(self) -> str:
        return "StatisticsSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.ANALYTICS

    @property
    def priority(self) -> int:
        return ExecutionPriority.STATISTICS

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self.history.clear()

    def update(self, context: UpdateContext) -> None:
        if context.tick % 60 == 0:  # Every 60 ticks
            counts = {
                "ticks": context.tick,
                "total": 0,
                "bacteria": 0,
                "plant": 0,
                "herbivore": 0,
                "carnivore": 0,
                "predator": 0,
                "human": 0,
            }

            for entity in self._entities_list:
                if entity.is_alive:
                    counts["total"] += 1
                    t = entity.entity_type
                    if t == EntityType.BACTERIA:
                        counts["bacteria"] += 1
                    elif t == EntityType.PLANT:
                        counts["plant"] += 1
                    elif t == EntityType.HERBIVORE:
                        counts["herbivore"] += 1
                    elif t == EntityType.CARNIVORE:
                        counts["carnivore"] += 1
                    elif t == EntityType.PREDATOR:
                        counts["predator"] += 1
                    elif t == EntityType.HUMAN:
                        counts["human"] += 1

            self.history.append(counts)
            if len(self.history) > 1000:
                self.history.pop(0)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
