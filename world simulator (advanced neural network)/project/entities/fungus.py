"""
project/entities/fungus.py

Fungus Entity Data Model (Mycelium Networks, Giant Morel, Bioluminescent Fungi).
Saprophytic decomposer organisms consuming detritus and dead matter, enriching soil chunks
with nitrogen and potassium, and fruiting edible mushrooms for herbivores and humans.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Fungus(Entity):
    """Sessile saprophytic decomposer and subterranean mycelium network."""
    mycelial_spread_radius: float = 24.0
    spore_yield_count: int = 0
    decomposition_efficiency: float = 1.5

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.FUNGUS
        self.radius = 3.8
        self.mass_kg = 2.0
        self.max_health = 80.0
        self.health = 80.0
        self.max_energy = 120.0
        self.energy = 100.0
        self.max_hydration = 200.0
        self.hydration = 180.0
        self.base_speed = 0.0
        self.max_speed_cap = 0.0
        self.strength = 3.0
        self.max_strength_cap = 20.0
        self.metabolic_rate = 0.006
        self.is_endotherm = False
        self.body_temperature_c = 18.0
        self.max_age_ticks = 12000
        self.maturity_age_ticks = 70
        self.color_rgb = (190, 120, 220)
