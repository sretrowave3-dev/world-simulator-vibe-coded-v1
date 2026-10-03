"""
project/systems/disaster_system.py

Disaster System executing geophysical hazards and applying damage to organisms.
"""

from __future__ import annotations

import math
from typing import Set, List, Dict, Any
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.disasters import DisasterManager, HazardType
from project.entities.entity import Entity


class DisasterSystem:
    """Simulates natural disasters and inflicts environmental hazard damage."""

    def __init__(
        self,
        disaster_manager: DisasterManager,
        entities_list: List[Entity],
    ) -> None:
        self._disaster_manager = disaster_manager
        self._entities_list = entities_list
        self._query_buf = [0.0] * 256

    @property
    def name(self) -> str:
        return "DisasterSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.WEATHER + 2

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        self._disaster_manager.reset()

    def update(self, context: UpdateContext) -> None:
        # Tick the disaster pipeline
        self._disaster_manager.tick(context.delta_time)

        # Check hazards for all entities and apply damage
        for entity in self._entities_list:
            if not entity.is_alive:
                continue

            cx = int(math.floor(entity.pos_x / 16.0))
            cy = int(math.floor(entity.pos_y / 16.0))
            lx = int(math.floor(entity.pos_x)) % 16
            ly = int(math.floor(entity.pos_y)) % 16
            idx = ly * 16 + lx

            # 1. Fire damage check
            self._disaster_manager.query_fire((cx, cy), self._query_buf)
            fire_int = self._query_buf[idx]
            if fire_int > 0.1:
                entity.take_damage(fire_int * 20.0 * context.delta_time, reason="BURNING", tick=context.tick)

            # 2. Flood damage check
            self._disaster_manager.query_flood((cx, cy), self._query_buf)
            flood_depth = self._query_buf[idx]
            if flood_depth > 0.5:
                entity.take_damage(flood_depth * 5.0 * context.delta_time, reason="DROWNING", tick=context.tick)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
