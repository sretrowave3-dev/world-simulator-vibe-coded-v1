"""
project/entities/avian.py

Avian Entity Data Model (Falcons, Hawks, Ravens).
High-mobility aerial organism with wide peripheral vision, soaring flight kinematics,
scouting telemetry, and aerial alarm calling instincts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Avian(Entity):
    """Aerial avian organism with flight elevation, high speed, and sharp vision."""
    flight_altitude: float = 25.0
    vision_range: float = 160.0
    diving_attack_cooldown: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.AVIAN
        self.radius = 2.2
        self.mass_kg = 3.5
        self.max_health = 75.0
        self.health = 75.0
        self.max_energy = 180.0
        self.energy = 160.0
        self.max_hydration = 120.0
        self.hydration = 110.0
        self.base_speed = 6.2
        self.max_speed_cap = 16.0
        self.strength = 12.0
        self.max_strength_cap = 35.0
        self.metabolic_rate = 0.075
        self.is_endotherm = True
        self.body_temperature_c = 41.0
        self.max_age_ticks = 14000
        self.maturity_age_ticks = 100
        self.color_rgb = (90, 180, 255)
        self._apply_individual_variance()
