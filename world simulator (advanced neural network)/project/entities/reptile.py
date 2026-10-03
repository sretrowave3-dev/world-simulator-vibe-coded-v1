"""
project/entities/reptile.py

Reptile Entity Data Model (Vipers, Monitor Lizards, Geckos).
Ectothermic cold-blooded predators utilizing solar basking for kinetic bursts,
stealth camouflage against terrain, and venomous strike attacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Reptile(Entity):
    """Cold-blooded reptile with solar thermoregulation and venomous bite."""
    internal_body_temp_c: float = 24.0
    is_basking: bool = False
    venom_potency: float = 18.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.REPTILE
        self.radius = 2.4
        self.mass_kg = 15.0
        self.max_health = 85.0
        self.health = 85.0
        self.max_energy = 160.0
        self.energy = 140.0
        self.max_hydration = 100.0
        self.hydration = 90.0
        self.base_speed = 3.8
        self.max_speed_cap = 11.0
        self.strength = 32.0
        self.max_strength_cap = 80.0
        self.metabolic_rate = 0.020
        self.is_endotherm = False
        self.body_temperature_c = 25.0
        self.max_age_ticks = 22000
        self.maturity_age_ticks = 180
        self.color_rgb = (160, 190, 40)
        self._apply_individual_variance()
