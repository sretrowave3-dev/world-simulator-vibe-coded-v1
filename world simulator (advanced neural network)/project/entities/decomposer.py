"""
project/entities/decomposer.py

Decomposer & Detritivore Organism Model for the ALife Platform.

Features:
- Specializes in consuming dead organic matter, carcasses, and biological waste.
- Converts decaying biomass into bioavailable soil nitrogen and phosphorus.
"""

from __future__ import annotations

from dataclasses import dataclass
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Decomposer(Entity):
    """Detritivore organism breaking down organic matter and recycling nutrients."""

    decomposition_speed: float = 1.5
    spore_spread_radius: float = 10.0
    spore_energy_cost: float = 35.0
    organic_to_soil_conversion_rate: float = 0.85

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.DECOMPOSER
        self.radius = 0.8
        self.mass_kg = 0.5
        self.max_health = 40.0
        self.health = 40.0
        self.max_energy = 150.0
        self.energy = 80.0
        self.base_speed = 1.8
        self.max_speed_cap = 4.5
        self.strength = 5.0
        self.max_strength_cap = 20.0
        self.metabolic_rate = 0.018
        self.is_endotherm = False
        self.body_temperature_c = 20.0
        self.max_age_ticks = 8000
        self.maturity_age_ticks = 80

    def can_mate(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= 80.0
            and self.reproduction_cooldown <= 0
        )
