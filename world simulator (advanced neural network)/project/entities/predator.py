"""
project/entities/predator.py

Apex Predator Organism Model for the ALife Platform.

Features:
- High-damage apex hunter with stalking, ambush burst velocity, and pack dynamics.
- Territorial marking and intimidation mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from project.entities.carnivore import Carnivore
from project.entities.entity import EntityType


@dataclass(eq=False)
class Predator(Carnivore):
    """Apex predator specializing in stalking, ambush bursts, and territory defense."""

    stealth_rating: float = 0.80
    ambush_speed_multiplier: float = 2.0
    pack_id: Optional[str] = None
    territory_radius: float = 120.0
    intimidation_factor: float = 0.85

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.PREDATOR
        self.radius = 2.5
        self.mass_kg = 120.0
        self.max_health = 250.0
        self.health = 250.0
        self.max_energy = 600.0
        self.energy = 350.0
        self.bite_damage = 45.0
        self.base_speed = 4.6
        self.max_speed_cap = 12.0
        self.strength = 45.0
        self.max_strength_cap = 110.0
        self.metabolic_rate = 0.062
        self.is_endotherm = True
        self.body_temperature_c = 38.5
        self.max_age_ticks = 18000
        self.maturity_age_ticks = 160
        self._apply_individual_variance()

    __hash__ = Carnivore.__hash__
    __eq__ = Carnivore.__eq__
