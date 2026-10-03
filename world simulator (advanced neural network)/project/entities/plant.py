"""
project/entities/plant.py

Photosynthetic Plant & Flora Organism Model for the ALife Platform.

Features:
- Stationary primary producer utilizing solar radiation and soil nutrients.
- Root absorption competition radius.
- Seed dispersal vector and flowering/fruiting lifecycles.
"""

from __future__ import annotations

from dataclasses import dataclass
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Plant(Entity):
    """Autotrophic stationary organism producing biomass via photosynthesis."""

    photosynthesis_efficiency: float = 0.85
    root_radius: float = 4.0
    seed_spread_radius: float = 15.0
    seed_production_cost: float = 35.0
    biomass_kg: float = 2.0
    max_biomass_kg: float = 50.0
    is_flowering: bool = False
    is_pollinated: bool = False
    pollination_progress: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.PLANT
        self.radius = 2.0
        self.mass_kg = 5.0
        self.max_health = 100.0
        self.health = 100.0
        self.max_energy = 250.0
        self.energy = 80.0
        self.base_speed = 0.0
        self.max_speed_cap = 0.0
        self.strength = 5.0
        self.max_strength_cap = 30.0
        self.metabolic_rate = 0.008
        self.is_endotherm = False
        self.body_temperature_c = 20.0
        self.max_age_ticks = 10000
        self.maturity_age_ticks = 60

    def can_reproduce_seed(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= self.seed_production_cost
            and self.reproduction_cooldown <= 0
        )

    __hash__ = Entity.__hash__
    __eq__ = Entity.__eq__
