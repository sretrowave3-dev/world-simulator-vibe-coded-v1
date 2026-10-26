"""
project/entities/plant.py

Photosynthetic Plant & Living Forest Organism Model for the ALife Platform.

Features:
- Stationary primary producer utilizing solar radiation, water, and soil nutrients.
- Dynamic Growth Lifecycle: Sprout -> Bush -> Sapling -> Mature Tree -> Ancient Canopy.
- Wood and fruit production: Mature trees yield timber (wood) for human crafting and fruit for foraging.
- Living Forests: Disperses seeds into neighboring soil to organically spawn tree clusters and forests.
- Root absorption competition radius and environmental microclimate moderation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Plant(Entity):
    """Autotrophic stationary organism producing biomass and developing into mature timber trees and forests."""

    photosynthesis_efficiency: float = 0.85
    root_radius: float = 4.0
    seed_spread_radius: float = 25.0
    seed_production_cost: float = 30.0
    biomass_kg: float = 2.0
    max_biomass_kg: float = 300.0  # Allows growth into massive canopy trees
    is_flowering: bool = False
    is_pollinated: bool = False
    pollination_progress: float = 0.0
    growth_stage: str = "sprout"    # "sprout", "bush", "sapling", "tree", "ancient_tree"
    fruit_reserve_kg: float = 0.0
    trunk_wood_kg: float = 0.5

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.PLANT
        self.radius = 2.0
        self.mass_kg = 5.0
        self.max_health = 100.0
        self.health = 100.0
        self.max_energy = 500.0
        self.energy = 120.0
        self.base_speed = 0.0
        self.max_speed_cap = 0.0
        self.strength = 5.0
        self.max_strength_cap = 50.0
        self.metabolic_rate = 0.005
        self.is_endotherm = False
        self.body_temperature_c = 20.0
        self.max_age_ticks = 50000
        self.maturity_age_ticks = 100

        # Initialize growth stage based on initial biomass
        self._update_growth_stage()

    def _update_growth_stage(self) -> None:
        """Transitions plant stage as biomass and wood volume increase."""
        if self.biomass_kg < 8.0:
            self.growth_stage = "sprout"
            self.radius = 2.0
            self.trunk_wood_kg = self.biomass_kg * 0.25
        elif self.biomass_kg < 25.0:
            self.growth_stage = "bush"
            self.radius = 3.2
            self.trunk_wood_kg = self.biomass_kg * 0.35
        elif self.biomass_kg < 60.0:
            self.growth_stage = "sapling"
            self.radius = 4.5
            self.trunk_wood_kg = self.biomass_kg * 0.50
        elif self.biomass_kg < 180.0:
            self.growth_stage = "tree"
            self.radius = 6.5
            self.trunk_wood_kg = self.biomass_kg * 0.65
            self.root_radius = 12.0
        else:
            self.growth_stage = "ancient_tree"
            self.radius = 9.5
            self.trunk_wood_kg = self.biomass_kg * 0.75
            self.root_radius = 20.0

        # Sync custom data for renderer and AI inspectors
        self.custom_data["growth_stage"] = self.growth_stage
        self.custom_data["wood_kg"] = self.trunk_wood_kg
        self.custom_data["is_tree"] = self.is_tree()
        self.custom_data["fruit_kg"] = self.fruit_reserve_kg

    def is_tree(self) -> bool:
        """Returns True if the plant has developed into a mature tree or ancient canopy."""
        return self.growth_stage in ("sapling", "tree", "ancient_tree")

    def grow_biomass(self, delta_kg: float) -> None:
        """Absorbs solar energy and soil nutrients, growing in biomass, wood, and fruit."""
        if not self.is_alive:
            return
        self.biomass_kg = min(self.max_biomass_kg, self.biomass_kg + delta_kg)
        self.mass_kg = self.biomass_kg

        # Produce edible fruit when mature and flourishing
        if self.is_tree() and self.energy > 200.0:
            self.fruit_reserve_kg = min(25.0, self.fruit_reserve_kg + delta_kg * 0.3)

        self._update_growth_stage()

    def harvest_wood(self, requested_kg: float, tool_multiplier: float = 1.0) -> float:
        """
        Allows humans to harvest wood/timber.
        Using a tool (like a Stone Axe) increases harvest speed.
        """
        if not self.is_alive or self.trunk_wood_kg <= 0.1:
            return 0.0

        effective_harvest = min(self.trunk_wood_kg, requested_kg * tool_multiplier)
        self.trunk_wood_kg -= effective_harvest
        self.biomass_kg = max(2.0, self.biomass_kg - effective_harvest)
        self._update_growth_stage()

        # If a tree is completely felled, convert to stump/sprout
        if self.trunk_wood_kg < 1.0 and self.is_tree():
            self.growth_stage = "sprout"
            self.radius = 2.0
            self.health = max(10.0, self.health * 0.5)

        return effective_harvest

    def harvest_fruit(self, requested_kg: float) -> float:
        """Harvests nutritious edible fruit without damaging the tree."""
        if self.fruit_reserve_kg <= 0.0:
            return 0.0
        harvested = min(self.fruit_reserve_kg, requested_kg)
        self.fruit_reserve_kg -= harvested
        return harvested

    def can_reproduce_seed(self) -> bool:
        """Trees and mature plants disperse seeds to form forests."""
        return (
            self.is_alive
            and (self.is_mature or self.is_tree())
            and self.energy >= self.seed_production_cost
            and self.reproduction_cooldown <= 0
        )

    __hash__ = Entity.__hash__
    __eq__ = Entity.__eq__
