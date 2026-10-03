"""
project/entities/carnivore.py

Carnivore Organism Model for the ALife Platform.

Features:
- Pure carnivorous meat diet.
- Tracking prey via vision cones and blood/meat scent trails.
- Bite force attack damage and carcass meat consumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Carnivore(Entity):
    """Secondary consumer organism hunting herbivores and scavenging carcasses."""

    bite_damage: float = 25.0
    attack_cooldown_ticks: int = 0
    scent_tracking_radius: float = 80.0
    meat_digestion_efficiency: float = 0.85
    hunger_aggression_threshold: float = 0.50

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.CARNIVORE
        self.radius = 2.0
        self.mass_kg = 60.0
        self.max_health = 150.0
        self.health = 150.0
        self.max_energy = 400.0
        self.energy = 220.0
        self.base_speed = 4.0
        self.max_speed_cap = 10.5
        self.strength = 28.0
        self.max_strength_cap = 75.0
        self.metabolic_rate = 0.052
        self.is_endotherm = True
        self.body_temperature_c = 38.0
        self.max_age_ticks = 20000
        self.maturity_age_ticks = 150
        self._apply_individual_variance()

    def can_mate(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= 200.0
            and self.reproduction_cooldown <= 0
        )
