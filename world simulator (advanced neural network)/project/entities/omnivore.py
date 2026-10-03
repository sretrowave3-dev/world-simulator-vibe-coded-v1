"""
project/entities/omnivore.py

Flexible Omnivore Organism Model for the ALife Platform.

Features:
- Dual-diet adaptation capable of metabolizing both flora (fruits, seeds, plants) and meat (hunted prey, carrion).
- Opportunistic foraging behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Omnivore(Entity):
    """Generalist consumer organism utilizing diverse food sources."""

    plant_digestion_efficiency: float = 0.80
    meat_digestion_efficiency: float = 0.80
    attack_damage: float = 15.0
    foraging_curiosity: float = 0.85

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.OMNIVORE
        self.radius = 1.9
        self.mass_kg = 50.0
        self.max_health = 130.0
        self.health = 130.0
        self.max_energy = 350.0
        self.energy = 200.0
        self.base_speed = 3.9
        self.max_speed_cap = 10.0
        self.strength = 22.0
        self.max_strength_cap = 65.0
        self.metabolic_rate = 0.040
        self.is_endotherm = True
        self.body_temperature_c = 37.5
        self.max_age_ticks = 17000
        self.maturity_age_ticks = 140
        self._apply_individual_variance()

    def can_mate(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= 180.0
            and self.reproduction_cooldown <= 0
        )
