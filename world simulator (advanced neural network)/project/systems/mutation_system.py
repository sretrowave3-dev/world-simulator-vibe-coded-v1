"""
project/systems/mutation_system.py

Mutation System implementing environmental modifiers on genetic genomes.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity
from project.world.disasters import DisasterManager


class MutationSystem:
    """Manages environmental modifications on genomes."""

    def __init__(self, entities_list: List[Entity], disaster_manager: DisasterManager) -> None:
        self._entities_list = entities_list
        self._disaster_manager = disaster_manager
        self._query_buf = [0.0] * 256

    @property
    def name(self) -> str:
        return "MutationSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.MUTATION

    @property
    def dependencies(self) -> Set[str]:
        return {"BirthSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        # Loop through entities. If inside toxic or radiation zones, increase mutation
        for entity in self._entities_list:
            if not entity.is_alive or not entity.genome:
                continue

            cx = int(math.floor(entity.pos_x / 16.0))
            cy = int(math.floor(entity.pos_y / 16.0))
            lx = int(math.floor(entity.pos_x)) % 16
            ly = int(math.floor(entity.pos_y)) % 16
            idx = ly * 16 + lx

            # Query environmental hazards if any
            self._disaster_manager.query_hazards((cx, cy), self._query_buf)
            hazard_type = self._query_buf[idx]

            # High mutation checks
            if hazard_type > 0:
                entity.genome = entity.genome.mutate(mutation_rate=0.20, mutation_magnitude=0.30)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
