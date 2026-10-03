"""
project/entities/arthropod.py

Arthropod Entity Data Model (Pollinator Bees, Scarabs, Ants).
High-density small organisms facilitating cross-pollination of flowering flora,
producing honey nutrient clusters, and accelerating ecological nutrient turnover.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Arthropod(Entity):
    """Arthropod/Insect organism specializing in pollination and colony swarming."""
    pollen_carried_mg: float = 0.0
    pollination_count: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.ARTHROPOD
        self.radius = 1.2
        self.mass_kg = 0.05
        self.max_health = 25.0
        self.health = 25.0
        self.max_energy = 80.0
        self.energy = 70.0
        self.max_hydration = 60.0
        self.hydration = 55.0
        self.base_speed = 3.5
        self.max_speed_cap = 9.0
        self.strength = 4.0
        self.max_strength_cap = 15.0
        self.metabolic_rate = 0.022
        self.is_endotherm = False
        self.body_temperature_c = 22.0
        self.max_age_ticks = 4500
        self.maturity_age_ticks = 40
        self.color_rgb = (240, 200, 20)
        self._apply_individual_variance()
