"""
project/entities/herbivore.py

Herbivore Primary Consumer Organism Model for the ALife Platform.

Features:
- Grazing on vegetation chunks and plant biomass.
- Alertness and herd flocking dynamics.
- Flight steering mechanics upon sensing predator threats.
"""

from __future__ import annotations

from dataclasses import dataclass
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Herbivore(Entity):
    """Primary consumer organism grazing on vegetation and fruits."""

    graze_efficiency: float = 0.90
    foraging_vision_radius: float = 60.0
    herd_affinity: float = 0.70
    flight_speed_multiplier: float = 1.5
    sprint_stamina: float = 100.0
    max_sprint_stamina: float = 100.0
    alert_level: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.HERBIVORE
        self.radius = 1.8
        self.mass_kg = 45.0
        self.max_health = 120.0
        self.health = 120.0
        self.max_energy = 300.0
        self.energy = 180.0
        self.base_speed = 3.6
        self.max_speed_cap = 9.2
        self.strength = 14.0
        self.max_strength_cap = 45.0
        self.metabolic_rate = 0.042
        self.is_endotherm = True
        self.body_temperature_c = 38.5
        self.max_age_ticks = 15000
        self.maturity_age_ticks = 120
        self._apply_individual_variance()

    def can_mate(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= 120.0
            and self.hydration >= 40.0
            and self.reproduction_cooldown <= 0
        )

    __hash__ = Entity.__hash__
    __eq__ = Entity.__eq__
