"""
project/world/__init__.py

Master World & Environmental Subsystems for the Echo Evolution Simulator.
"""

from project.world.biomes import BiomeType, BiomeParameters, BIOME_CATALOG, BiomeClassifier
from project.world.terrain import (
    TerrainManager,
    TerrainChunk,
    TerrainTile,
    NoiseType,
    TerrainEvent,
    RenderPacket as TerrainRenderPacket,
    GeminiContextSummary,
    CivilizationSuitabilityScore,
)
from project.world.weather import (
    WeatherManager,
    AtmosphericGrid,
    ChunkData as WeatherChunkData,
    SeasonState,
    ClimateType,
)
from project.world.food import (
    FoodManager,
    FoodChunkStore,
    FoodInstance,
    SpeciesRegistry as FoodSpeciesRegistry,
    Genome as FoodGenome,
    LifecycleStage,
    OrganismCategory,
    DispersalVector,
)
from project.world.disasters import (
    DisasterManager,
    DisasterConfig,
    HazardType,
    HazardEvent,
    HazardSnapshot,
)
from project.world.resources import ResourceManager, ResourceNode, ResourceType
from project.world.soil import SoilManager, SoilChunk, SoilProfile
from project.world.vegetation import VegetationManager, VegetationChunk, VegetationPatch, VegetationType
from project.world.water import WaterManager, WaterChunk, WaterState, WaterType
from project.world.time import WorldTimeManager, Season, TimeSnapshot

__all__ = [
    "BiomeType",
    "BiomeParameters",
    "BIOME_CATALOG",
    "BiomeClassifier",
    "TerrainManager",
    "TerrainChunk",
    "TerrainTile",
    "NoiseType",
    "TerrainEvent",
    "TerrainRenderPacket",
    "GeminiContextSummary",
    "CivilizationSuitabilityScore",
    "WeatherManager",
    "AtmosphericGrid",
    "WeatherChunkData",
    "SeasonState",
    "ClimateType",
    "FoodManager",
    "FoodChunkStore",
    "FoodInstance",
    "FoodSpeciesRegistry",
    "FoodGenome",
    "LifecycleStage",
    "OrganismCategory",
    "DispersalVector",
    "DisasterManager",
    "DisasterConfig",
    "HazardType",
    "HazardEvent",
    "HazardSnapshot",
    "ResourceManager",
    "ResourceNode",
    "ResourceType",
    "SoilManager",
    "SoilChunk",
    "SoilProfile",
    "VegetationManager",
    "VegetationChunk",
    "VegetationPatch",
    "VegetationType",
    "WaterManager",
    "WaterChunk",
    "WaterState",
    "WaterType",
    "WorldTimeManager",
    "Season",
    "TimeSnapshot",
]
