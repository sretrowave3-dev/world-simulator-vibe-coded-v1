"""
project/world/biomes.py

Comprehensive Biome System & Ecological Classification Engine for the ALife Platform.

Features:
- Complete definitions for 19 planetary biomes with ecological carrying capacities.
- Multidimensional Whittaker classification based on thermal, moisture, elevation, and terrain parameters.
- Movement cost modifiers (walk, swim, climb, fly) for spatial pathfinding.
- Agricultural, mining, and settlement suitability scores.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class BiomeType(enum.IntEnum):
    DEEP_OCEAN = 0
    OCEAN = 1
    BEACH = 2
    GRASSLAND = 3
    FOREST = 4
    RAINFOREST = 5
    JUNGLE = 6
    SWAMP = 7
    SAVANNA = 8
    DESERT = 9
    ROCK_DESERT = 10
    MOUNTAIN = 11
    SNOW = 12
    ICE = 13
    VOLCANO = 14
    TUNDRA = 15
    CRYSTAL = 16
    TOXIC = 17
    RUINS = 18


@dataclass(frozen=True, slots=True)
class BiomeParameters:
    biome_id: BiomeType
    name: str
    optimal_temp_c: float
    optimal_moisture: float
    fertility: float
    max_plant_biomass_kg: float
    max_animal_carrying_capacity: int
    walk_cost: float
    swim_cost: float
    climb_cost: float
    fly_cost: float
    is_habitable: bool
    color_rgb: Tuple[int, int, int]
    primary_resource: str
    primary_vegetation: str


BIOME_CATALOG: Dict[BiomeType, BiomeParameters] = {
    BiomeType.DEEP_OCEAN: BiomeParameters(
        biome_id=BiomeType.DEEP_OCEAN,
        name="Deep Ocean",
        optimal_temp_c=4.0,
        optimal_moisture=1.0,
        fertility=0.05,
        max_plant_biomass_kg=50.0,
        max_animal_carrying_capacity=50,
        walk_cost=99.0,
        swim_cost=1.0,
        climb_cost=99.0,
        fly_cost=1.0,
        is_habitable=False,
        color_rgb=(10, 30, 80),
        primary_resource="FISH",
        primary_vegetation="NONE",
    ),
    BiomeType.OCEAN: BiomeParameters(
        biome_id=BiomeType.OCEAN,
        name="Ocean",
        optimal_temp_c=14.0,
        optimal_moisture=1.0,
        fertility=0.15,
        max_plant_biomass_kg=150.0,
        max_animal_carrying_capacity=150,
        walk_cost=10.0,
        swim_cost=1.0,
        climb_cost=99.0,
        fly_cost=1.0,
        is_habitable=False,
        color_rgb=(30, 80, 160),
        primary_resource="FISH",
        primary_vegetation="ALGAE",
    ),
    BiomeType.BEACH: BiomeParameters(
        biome_id=BiomeType.BEACH,
        name="Beach",
        optimal_temp_c=22.0,
        optimal_moisture=0.7,
        fertility=0.25,
        max_plant_biomass_kg=200.0,
        max_animal_carrying_capacity=100,
        walk_cost=1.2,
        swim_cost=1.5,
        climb_cost=2.0,
        fly_cost=1.0,
        is_habitable=True,
        color_rgb=(238, 220, 130),
        primary_resource="SAND",
        primary_vegetation="PALM",
    ),
    BiomeType.GRASSLAND: BiomeParameters(
        biome_id=BiomeType.GRASSLAND,
        name="Grassland",
        optimal_temp_c=18.0,
        optimal_moisture=0.5,
        fertility=0.90,
        max_plant_biomass_kg=1200.0,
        max_animal_carrying_capacity=500,
        walk_cost=1.0,
        swim_cost=2.0,
        climb_cost=1.2,
        fly_cost=1.0,
        is_habitable=True,
        color_rgb=(126, 200, 80),
        primary_resource="FOOD",
        primary_vegetation="GRASS",
    ),
    BiomeType.FOREST: BiomeParameters(
        biome_id=BiomeType.FOREST,
        name="Temperate Forest",
        optimal_temp_c=16.0,
        optimal_moisture=0.65,
        fertility=0.85,
        max_plant_biomass_kg=2500.0,
        max_animal_carrying_capacity=450,
        walk_cost=1.3,
        swim_cost=2.0,
        climb_cost=1.5,
        fly_cost=1.2,
        is_habitable=True,
        color_rgb=(34, 139, 34),
        primary_resource="WOOD",
        primary_vegetation="OAK",
    ),
    BiomeType.RAINFOREST: BiomeParameters(
        biome_id=BiomeType.RAINFOREST,
        name="Rainforest",
        optimal_temp_c=26.0,
        optimal_moisture=0.95,
        fertility=1.00,
        max_plant_biomass_kg=4000.0,
        max_animal_carrying_capacity=600,
        walk_cost=1.6,
        swim_cost=2.2,
        climb_cost=1.8,
        fly_cost=1.4,
        is_habitable=True,
        color_rgb=(0, 100, 0),
        primary_resource="MEDICINE",
        primary_vegetation="CANOPY_TREE",
    ),
    BiomeType.JUNGLE: BiomeParameters(
        biome_id=BiomeType.JUNGLE,
        name="Dense Jungle",
        optimal_temp_c=28.0,
        optimal_moisture=0.85,
        fertility=0.95,
        max_plant_biomass_kg=3500.0,
        max_animal_carrying_capacity=550,
        walk_cost=1.8,
        swim_cost=2.2,
        climb_cost=2.0,
        fly_cost=1.5,
        is_habitable=True,
        color_rgb=(0, 75, 0),
        primary_resource="FRUIT",
        primary_vegetation="VINES",
    ),
    BiomeType.SWAMP: BiomeParameters(
        biome_id=BiomeType.SWAMP,
        name="Swamp",
        optimal_temp_c=22.0,
        optimal_moisture=0.90,
        fertility=0.70,
        max_plant_biomass_kg=1800.0,
        max_animal_carrying_capacity=300,
        walk_cost=2.5,
        swim_cost=1.2,
        climb_cost=2.5,
        fly_cost=1.0,
        is_habitable=True,
        color_rgb=(47, 79, 79),
        primary_resource="PEAT",
        primary_vegetation="MOSS",
    ),
    BiomeType.SAVANNA: BiomeParameters(
        biome_id=BiomeType.SAVANNA,
        name="Savanna",
        optimal_temp_c=28.0,
        optimal_moisture=0.35,
        fertility=0.55,
        max_plant_biomass_kg=800.0,
        max_animal_carrying_capacity=400,
        walk_cost=1.1,
        swim_cost=2.0,
        climb_cost=1.2,
        fly_cost=1.0,
        is_habitable=True,
        color_rgb=(225, 193, 110),
        primary_resource="FOOD",
        primary_vegetation="ACACIA",
    ),
    BiomeType.DESERT: BiomeParameters(
        biome_id=BiomeType.DESERT,
        name="Arid Desert",
        optimal_temp_c=36.0,
        optimal_moisture=0.10,
        fertility=0.08,
        max_plant_biomass_kg=100.0,
        max_animal_carrying_capacity=60,
        walk_cost=1.4,
        swim_cost=3.0,
        climb_cost=1.8,
        fly_cost=1.0,
        is_habitable=False,
        color_rgb=(237, 201, 175),
        primary_resource="STONE",
        primary_vegetation="CACTUS",
    ),
    BiomeType.ROCK_DESERT: BiomeParameters(
        biome_id=BiomeType.ROCK_DESERT,
        name="Rocky Badlands",
        optimal_temp_c=32.0,
        optimal_moisture=0.12,
        fertility=0.05,
        max_plant_biomass_kg=80.0,
        max_animal_carrying_capacity=50,
        walk_cost=1.5,
        swim_cost=3.0,
        climb_cost=2.0,
        fly_cost=1.0,
        is_habitable=False,
        color_rgb=(184, 115, 51),
        primary_resource="IRON",
        primary_vegetation="SHRUB",
    ),
    BiomeType.MOUNTAIN: BiomeParameters(
        biome_id=BiomeType.MOUNTAIN,
        name="Mountain Range",
        optimal_temp_c=5.0,
        optimal_moisture=0.40,
        fertility=0.15,
        max_plant_biomass_kg=300.0,
        max_animal_carrying_capacity=100,
        walk_cost=2.2,
        swim_cost=4.0,
        climb_cost=1.2,
        fly_cost=1.2,
        is_habitable=True,
        color_rgb=(128, 128, 128),
        primary_resource="COAL",
        primary_vegetation="PINE",
    ),
    BiomeType.SNOW: BiomeParameters(
        biome_id=BiomeType.SNOW,
        name="Snow Peak",
        optimal_temp_c=-5.0,
        optimal_moisture=0.50,
        fertility=0.02,
        max_plant_biomass_kg=30.0,
        max_animal_carrying_capacity=30,
        walk_cost=1.8,
        swim_cost=3.5,
        climb_cost=2.2,
        fly_cost=1.2,
        is_habitable=False,
        color_rgb=(250, 250, 250),
        primary_resource="ICE",
        primary_vegetation="NONE",
    ),
    BiomeType.ICE: BiomeParameters(
        biome_id=BiomeType.ICE,
        name="Glacier Ice Sheet",
        optimal_temp_c=-20.0,
        optimal_moisture=0.30,
        fertility=0.00,
        max_plant_biomass_kg=0.0,
        max_animal_carrying_capacity=10,
        walk_cost=2.2,
        swim_cost=2.0,
        climb_cost=3.0,
        fly_cost=1.0,
        is_habitable=False,
        color_rgb=(224, 255, 255),
        primary_resource="ICE",
        primary_vegetation="NONE",
    ),
    BiomeType.VOLCANO: BiomeParameters(
        biome_id=BiomeType.VOLCANO,
        name="Volcanic Caldera",
        optimal_temp_c=55.0,
        optimal_moisture=0.05,
        fertility=0.00,
        max_plant_biomass_kg=0.0,
        max_animal_carrying_capacity=5,
        walk_cost=3.5,
        swim_cost=99.0,
        climb_cost=2.5,
        fly_cost=1.5,
        is_habitable=False,
        color_rgb=(139, 0, 0),
        primary_resource="OBSIDIAN",
        primary_vegetation="NONE",
    ),
    BiomeType.TUNDRA: BiomeParameters(
        biome_id=BiomeType.TUNDRA,
        name="Arctic Tundra",
        optimal_temp_c=-2.0,
        optimal_moisture=0.45,
        fertility=0.20,
        max_plant_biomass_kg=400.0,
        max_animal_carrying_capacity=150,
        walk_cost=1.4,
        swim_cost=2.5,
        climb_cost=1.8,
        fly_cost=1.0,
        is_habitable=True,
        color_rgb=(150, 179, 214),
        primary_resource="FUR",
        primary_vegetation="LICHEN",
    ),
    BiomeType.CRYSTAL: BiomeParameters(
        biome_id=BiomeType.CRYSTAL,
        name="Crystal Expanse",
        optimal_temp_c=15.0,
        optimal_moisture=0.50,
        fertility=0.25,
        max_plant_biomass_kg=200.0,
        max_animal_carrying_capacity=80,
        walk_cost=1.3,
        swim_cost=2.5,
        climb_cost=1.6,
        fly_cost=1.0,
        is_habitable=False,
        color_rgb=(218, 112, 214),
        primary_resource="CRYSTAL",
        primary_vegetation="CRYSTAL_FLORA",
    ),
    BiomeType.TOXIC: BiomeParameters(
        biome_id=BiomeType.TOXIC,
        name="Toxic Mire",
        optimal_temp_c=30.0,
        optimal_moisture=0.80,
        fertility=0.02,
        max_plant_biomass_kg=50.0,
        max_animal_carrying_capacity=20,
        walk_cost=2.0,
        swim_cost=3.0,
        climb_cost=2.0,
        fly_cost=1.2,
        is_habitable=False,
        color_rgb=(127, 255, 0),
        primary_resource="SULFUR",
        primary_vegetation="MUTANT_FUNGI",
    ),
    BiomeType.RUINS: BiomeParameters(
        biome_id=BiomeType.RUINS,
        name="Ancient Ruins",
        optimal_temp_c=20.0,
        optimal_moisture=0.40,
        fertility=0.30,
        max_plant_biomass_kg=300.0,
        max_animal_carrying_capacity=100,
        walk_cost=1.1,
        swim_cost=2.0,
        climb_cost=1.4,
        fly_cost=1.0,
        is_habitable=True,
        color_rgb=(181, 166, 66),
        primary_resource="RELIC",
        primary_vegetation="OVERGROWTH",
    ),
}


class BiomeClassifier:
    """Classifies environmental conditions into matching BiomeTypes."""

    @staticmethod
    def classify(
        elevation: float,
        temperature_c: float,
        moisture: float,
        latitude: float = 0.0,
        weirdness: float = 0.0,
    ) -> BiomeType:
        # 1. Marine & Water Elevations
        if elevation < 0.20:
            return BiomeType.DEEP_OCEAN
        if elevation < 0.35:
            return BiomeType.OCEAN
        if elevation < 0.38:
            return BiomeType.BEACH

        # 2. High Altitudes & Volcanic Activity
        if elevation > 0.85:
            return BiomeType.SNOW if temperature_c < 0.0 else BiomeType.VOLCANO
        if elevation > 0.70:
            return BiomeType.MOUNTAIN

        # 3. Extreme Latitudes & Polar Caps
        abs_lat = abs(latitude)
        if abs_lat > 75.0 or temperature_c < -15.0:
            return BiomeType.ICE if temperature_c < -25.0 else BiomeType.TUNDRA

        # 4. Anomalous "Weirdness" Biomes
        if weirdness > 0.88:
            return BiomeType.CRYSTAL if weirdness < 0.95 else BiomeType.TOXIC

        # 5. Terrestrial Moisture / Temperature Matrix
        if moisture < 0.20:
            return BiomeType.DESERT if temperature_c > 20.0 else BiomeType.ROCK_DESERT
        elif moisture > 0.75:
            return BiomeType.RAINFOREST if temperature_c > 22.0 else BiomeType.SWAMP
        elif moisture > 0.45:
            return BiomeType.FOREST if temperature_c < 24.0 else BiomeType.JUNGLE
        else:
            return BiomeType.SAVANNA if temperature_c > 25.0 else BiomeType.GRASSLAND

    @staticmethod
    def get_parameters(biome: BiomeType) -> BiomeParameters:
        return BIOME_CATALOG[biome]
