"""
project/entities/amphibian.py

Amphibian Entity Data Model (Frogs, Salamanders, Axolotls).
Semi-aquatic ectothermic organisms transitioning between freshwater basins and riparian shores,
breathing through cutaneous skin and hunting insects/arthropods.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Amphibian(Entity):
    """Semi-aquatic amphibious organism requiring high environmental humidity."""
    skin_moisture_level: float = 1.0
    is_swimming: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.AMPHIBIAN
        self.radius = 1.6
        self.mass_kg = 0.8
        self.max_health = 60.0
        self.health = 60.0
        self.max_energy = 140.0
        self.energy = 120.0
        self.max_hydration = 200.0
        self.hydration = 190.0
        self.base_speed = 3.2
        self.max_speed_cap = 8.5
        self.strength = 8.0
        self.max_strength_cap = 25.0
        self.metabolic_rate = 0.028
        self.is_endotherm = False
        self.body_temperature_c = 22.0
        self.max_age_ticks = 9000
        self.maturity_age_ticks = 80
        self.color_rgb = (40, 210, 120)
        self._apply_individual_variance()
