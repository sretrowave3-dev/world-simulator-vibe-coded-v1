"""
project/systems/aging_system.py

Aging System incrementing organism age ticks and scaling metabolic profiles over time.
"""

from __future__ import annotations

from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity


class AgingSystem:
    """Manages progression of age and triggers natural death."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "AgingSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.MUTATION - 2

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        from project.core.biology import calculate_gompertz_senescence_hazard

        for entity in self._entities_list:
            if not entity.is_alive:
                continue

            entity.age_ticks += 1

            # -------------------------------------------------------------
            # Stochastic Gompertz-Makeham Cellular Senescence
            # -------------------------------------------------------------
            hazard = calculate_gompertz_senescence_hazard(
                age_ticks=entity.age_ticks,
                max_age_ticks=entity.max_age_ticks,
                health_ratio=getattr(entity, "health_ratio", 1.0),
                constitution=getattr(entity, "constitution", 1.0),
            )

            if hazard > 0.0:
                # Deterministic pseudo-random roll per entity tick
                seed_val = (hash(entity.entity_id) + (context.tick * 31337)) & 0x7FFFFFFF
                roll = (seed_val % 1000000) / 1000000.0
                if roll < hazard:
                    entity.die(reason="OLD_AGE", tick=context.tick)
            elif entity.age_ticks >= (entity.max_age_ticks * 2.5):
                # Hard evolutionary extreme ceiling
                entity.die(reason="OLD_AGE", tick=context.tick)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
