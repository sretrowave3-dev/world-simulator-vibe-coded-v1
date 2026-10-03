"""
project/entities/bacteria.py

Single-Celled Bacteria Organism Model for the ALife Platform.

Features:
- Chemotactic movement sensing chemical concentration gradients.
- Rapid binary fission asexual reproduction upon reaching energy threshold.
- Elevated genetic mutation rate.
- Microscopic scale and low mass.
"""

from __future__ import annotations

from dataclasses import dataclass
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Bacteria(Entity):
    """Prokaryotic single-celled organism specializing in rapid reproduction and adaptation."""

    chemotaxis_sensitivity: float = 0.8
    flagella_speed_multiplier: float = 1.2
    fission_energy_threshold: float = 60.0
    fission_cost: float = 25.0
    mutation_rate_multiplier: float = 2.5
    nutrient_absorption_efficiency: float = 0.90

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.BACTERIA
        self.radius = 0.5
        self.mass_kg = 0.01
        self.max_health = 30.0
        self.health = 30.0
        self.max_energy = 100.0
        self.energy = 50.0
        self.base_speed = 1.4
        self.max_speed_cap = 3.5
        self.strength = 1.0
        self.max_strength_cap = 5.0
        self.metabolic_rate = 0.015
        self.is_endotherm = False
        self.body_temperature_c = 20.0
        self.max_age_ticks = 2500
        self.maturity_age_ticks = 40

    def can_divide(self) -> bool:
        """Returns True if the bacteria has sufficient energy to undergo binary fission."""
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= self.fission_energy_threshold
            and self.reproduction_cooldown <= 0
        )

    __hash__ = Entity.__hash__
    __eq__ = Entity.__eq__
