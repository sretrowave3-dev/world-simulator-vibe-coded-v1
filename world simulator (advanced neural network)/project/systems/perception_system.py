"""
project/systems/perception_system.py

Perception System rebuilding spatial hash indices and updating entity local observations.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.utils.spatial_hash import SpatialHashGrid
from project.entities.entity import Entity


class PerceptionSystem:
    """Rebuilds spatial partition hash grids and updates agent visual/sensory tables."""

    def __init__(
        self,
        spatial_grid: SpatialHashGrid[Entity],
        entities_list: List[Entity],
        vision_radius: float = 80.0,
    ) -> None:
        self._spatial_grid = spatial_grid
        self._entities_list = entities_list
        self._vision_radius = vision_radius

    @property
    def name(self) -> str:
        return "PerceptionSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.AI

    @property
    def priority(self) -> int:
        return ExecutionPriority.PERCEPTION

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        self._spatial_grid.clear()

    def update(self, context: UpdateContext) -> None:
        # 1. Clear and rebuild spatial partition index
        self._spatial_grid.clear()
        for entity in self._entities_list:
            if entity.is_alive:
                self._spatial_grid.insert(entity, entity.pos_x, entity.pos_y)

        # 2. Populate perceived local neighbor lists per entity
        # Stagger updates: each entity updates its perception once every 5 ticks (80% CPU reduction)
        tick_mod = context.tick % 5
        
        for i, entity in enumerate(self._entities_list):
            if not entity.is_alive:
                continue
                
            # Throttle spatial hash queries (O(N^2) killer)
            if i % 5 != tick_mod:
                # Keep old perceived list for this tick
                continue

            # Query nearby candidates in grid with direct distance calculation
            nearby = self._spatial_grid.query_radius(
                entity.pos_x,
                entity.pos_y,
                self._vision_radius,
            )

            # Filter out self
            perceived = [e for e in nearby if e.entity_id != entity.entity_id]
            
            # Store perceived list inside entity custom data buffer
            entity.custom_data["perceived_entities"] = perceived

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
