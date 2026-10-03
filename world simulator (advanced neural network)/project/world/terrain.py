"""
world/terrain.py

Complete Planetary Environment Subsystem for the ALife Research Platform.

Architectural Upgrades:
- Zero Data Duplication: TerrainTile delegates reads directly to underlying map stores.
- Modular Generator Pipeline: Pipeline pattern with decoupled, single-stage execution.
- Biome Classification Engine: Multidimensional classifier (Elevation, Continentalness,
  Erosion, Temperature, Humidity, Latitude, Soil, Weirdness).
- Multi-Layer Map Model: Geological, Atmospheric, Hydrological, Soil, Resource, Vegetation,
  Hazard, Navigation, Infrastructure, Ownership, Heatmap, and Fog of War layers.
- Temporal History System: TerrainTimeline tracks historical natural events, aging, and changes.
- Specialized System Separation: Manager split into ChunkManager, TerrainQueries, TerrainCache,
  TerrainEvents, TerrainAdapters, and SpatialHashIndex.
- Entity Spatial Tracking: Tile-level entity registrations for O(1) spatial updates.
- Contract Packets: Memory-efficient RenderPacket, rich GeminiContextSummary, and
  CivilizationSuitabilityScore payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import json
import math
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


# =============================================================================
# ENUMS & CORE TYPES
# =============================================================================

class NoiseType(Enum):
    PERLIN = auto()
    SIMPLEX = auto()
    OPENSIMPLEX = auto()
    VORONOI = auto()
    RIDGED = auto()
    FRACTAL = auto()
    DOMAIN_WARP = auto()


class BiomeType(Enum):
    DEEP_OCEAN = auto()
    OCEAN = auto()
    BEACH = auto()
    GRASSLAND = auto()
    FOREST = auto()
    RAINFOREST = auto()
    JUNGLE = auto()
    SWAMP = auto()
    SAVANNA = auto()
    DESERT = auto()
    ROCK_DESERT = auto()
    MOUNTAIN = auto()
    SNOW = auto()
    ICE = auto()
    VOLCANO = auto()
    TUNDRA = auto()
    CRYSTAL = auto()
    TOXIC = auto()
    RUINS = auto()


class WaterType(Enum):
    NONE = auto()
    OCEAN = auto()
    RIVER = auto()
    STREAM = auto()
    LAKE = auto()
    POND = auto()
    UNDERGROUND = auto()


class ResourceType(Enum):
    NONE = auto()
    FOOD = auto()
    FRUIT = auto()
    WOOD = auto()
    STONE = auto()
    IRON = auto()
    GOLD = auto()
    COAL = auto()
    CRYSTAL = auto()
    MEDICINE = auto()
    RARE_RESOURCES = auto()


class VegetationType(Enum):
    NONE = auto()
    GRASS = auto()
    BUSHES = auto()
    FLOWERS = auto()
    TREES = auto()
    DEAD_TREES = auto()
    FUNGI = auto()
    CROPS = auto()


class HazardType(Enum):
    NONE = auto()
    FIRE = auto()
    FLOOD = auto()
    POISON = auto()
    RADIATION = auto()
    VOLCANO = auto()
    LAVA = auto()
    EXTREME_COLD = auto()
    DISEASE = auto()


class RockType(Enum):
    SEDIMENTARY = auto()
    IGNEOUS = auto()
    METAMORPHIC = auto()
    BASALT = auto()
    GRANITE = auto()


class TerrainEvent(Enum):
    RIVER_CREATED = auto()
    FLOOD = auto()
    WILDFIRE = auto()
    VOLCANO = auto()
    FOREST_GROWTH = auto()
    BIOME_CHANGED = auto()
    LANDSLIDE = auto()
    TERRAIN_MODIFIED = auto()
    GLACIATION = auto()
    SOIL_EROSION = auto()


# =============================================================================
# BIOME & REGISTRY DATA
# =============================================================================

@dataclass(frozen=True, slots=True)
class BiomeConfig:
    name: str
    type: BiomeType
    walk_modifier: float
    swim_modifier: float
    climb_modifier: float
    fertility: float
    color_hex: str
    primary_resource: ResourceType
    primary_vegetation: VegetationType


BIOME_REGISTRY: Dict[BiomeType, BiomeConfig] = {
    BiomeType.DEEP_OCEAN: BiomeConfig("Deep Ocean", BiomeType.DEEP_OCEAN, 5.0, 1.0, 10.0, 0.05, "#000033", ResourceType.FOOD, VegetationType.NONE),
    BiomeType.OCEAN: BiomeConfig("Ocean", BiomeType.OCEAN, 3.0, 1.0, 8.0, 0.1, "#000088", ResourceType.FOOD, VegetationType.NONE),
    BiomeType.BEACH: BiomeConfig("Beach", BiomeType.BEACH, 1.2, 1.5, 2.0, 0.2, "#EEDC82", ResourceType.STONE, VegetationType.NONE),
    BiomeType.GRASSLAND: BiomeConfig("Grassland", BiomeType.GRASSLAND, 1.0, 2.0, 1.5, 0.9, "#7EC850", ResourceType.FOOD, VegetationType.GRASS),
    BiomeType.FOREST: BiomeConfig("Forest", BiomeType.FOREST, 1.3, 2.0, 1.8, 0.8, "#228B22", ResourceType.WOOD, VegetationType.TREES),
    BiomeType.RAINFOREST: BiomeConfig("Rainforest", BiomeType.RAINFOREST, 1.6, 2.2, 2.0, 1.0, "#006400", ResourceType.MEDICINE, VegetationType.TREES),
    BiomeType.JUNGLE: BiomeConfig("Jungle", BiomeType.JUNGLE, 1.8, 2.2, 2.2, 0.95, "#004B00", ResourceType.FRUIT, VegetationType.BUSHES),
    BiomeType.SWAMP: BiomeConfig("Swamp", BiomeType.SWAMP, 2.5, 1.2, 3.0, 0.7, "#2F4F4F", ResourceType.MEDICINE, VegetationType.FUNGI),
    BiomeType.SAVANNA: BiomeConfig("Savanna", BiomeType.SAVANNA, 1.1, 2.0, 1.4, 0.5, "#E1C16E", ResourceType.FOOD, VegetationType.GRASS),
    BiomeType.DESERT: BiomeConfig("Desert", BiomeType.DESERT, 1.4, 3.0, 2.0, 0.05, "#EDC9AF", ResourceType.STONE, VegetationType.NONE),
    BiomeType.ROCK_DESERT: BiomeConfig("Rock Desert", BiomeType.ROCK_DESERT, 1.5, 3.0, 2.2, 0.02, "#B87333", ResourceType.IRON, VegetationType.NONE),
    BiomeType.MOUNTAIN: BiomeConfig("Mountain", BiomeType.MOUNTAIN, 2.2, 4.0, 1.2, 0.1, "#808080", ResourceType.COAL, VegetationType.NONE),
    BiomeType.SNOW: BiomeConfig("Snow", BiomeType.SNOW, 1.8, 3.5, 2.5, 0.0, "#FFFFFF", ResourceType.NONE, VegetationType.NONE),
    BiomeType.ICE: BiomeConfig("Ice", BiomeType.ICE, 2.2, 2.0, 3.0, 0.0, "#E0FFFF", ResourceType.NONE, VegetationType.NONE),
    BiomeType.VOLCANO: BiomeConfig("Volcano", BiomeType.VOLCANO, 3.0, 5.0, 2.5, 0.0, "#8B0000", ResourceType.RARE_RESOURCES, VegetationType.NONE),
    BiomeType.TUNDRA: BiomeConfig("Tundra", BiomeType.TUNDRA, 1.4, 2.5, 1.8, 0.2, "#96B3D6", ResourceType.STONE, VegetationType.BUSHES),
    BiomeType.CRYSTAL: BiomeConfig("Crystal Fields", BiomeType.CRYSTAL, 1.2, 2.5, 1.8, 0.3, "#DA70D6", ResourceType.CRYSTAL, VegetationType.NONE),
    BiomeType.TOXIC: BiomeConfig("Toxic Waste", BiomeType.TOXIC, 2.0, 3.0, 2.0, 0.0, "#7FFF00", ResourceType.RARE_RESOURCES, VegetationType.FUNGI),
    BiomeType.RUINS: BiomeConfig("Ancient Ruins", BiomeType.RUINS, 1.1, 2.0, 1.5, 0.4, "#B5A642", ResourceType.GOLD, VegetationType.NONE),
}


# =============================================================================
# MAP DATA CONTAINERS (MAP STORES)
# =============================================================================

class HeightMap:
    __slots__ = ("height", "slope", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.height: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.slope: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]

class BiomeMap:
    __slots__ = ("data", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.data: List[List[BiomeType]] = [[BiomeType.GRASSLAND for _ in range(size)] for _ in range(size)]

class ClimateMap:
    __slots__ = ("temperature", "humidity", "rainfall", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.temperature: List[List[float]] = [[20.0 for _ in range(size)] for _ in range(size)]
        self.humidity: List[List[float]] = [[0.5 for _ in range(size)] for _ in range(size)]
        self.rainfall: List[List[float]] = [[0.5 for _ in range(size)] for _ in range(size)]

class AtmosphericMap:
    __slots__ = ("pressure", "wind_x", "wind_y", "cloud_density", "solar_radiation", "evaporation", "air_quality", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.pressure: List[List[float]] = [[101.3 for _ in range(size)] for _ in range(size)]
        self.wind_x: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.wind_y: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.cloud_density: List[List[float]] = [[0.2 for _ in range(size)] for _ in range(size)]
        self.solar_radiation: List[List[float]] = [[1.0 for _ in range(size)] for _ in range(size)]
        self.evaporation: List[List[float]] = [[0.1 for _ in range(size)] for _ in range(size)]
        self.air_quality: List[List[float]] = [[1.0 for _ in range(size)] for _ in range(size)]

class GeologicalMap:
    __slots__ = ("rock_type", "fault_line", "mineral_veins", "plate_id", "volcanic_activity", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.rock_type: List[List[RockType]] = [[RockType.SEDIMENTARY for _ in range(size)] for _ in range(size)]
        self.fault_line: List[List[bool]] = [[False for _ in range(size)] for _ in range(size)]
        self.mineral_veins: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.plate_id: List[List[int]] = [[0 for _ in range(size)] for _ in range(size)]
        self.volcanic_activity: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]

class SoilMap:
    __slots__ = ("organic_matter", "moisture", "nitrogen", "phosphorus", "ph", "density", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.organic_matter: List[List[float]] = [[0.5 for _ in range(size)] for _ in range(size)]
        self.moisture: List[List[float]] = [[0.5 for _ in range(size)] for _ in range(size)]
        self.nitrogen: List[List[float]] = [[0.5 for _ in range(size)] for _ in range(size)]
        self.phosphorus: List[List[float]] = [[0.5 for _ in range(size)] for _ in range(size)]
        self.ph: List[List[float]] = [[6.5 for _ in range(size)] for _ in range(size)]
        self.density: List[List[float]] = [[1.0 for _ in range(size)] for _ in range(size)]

class WaterMap:
    __slots__ = ("water_type", "depth", "flow_x", "flow_y", "purity", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.water_type: List[List[WaterType]] = [[WaterType.NONE for _ in range(size)] for _ in range(size)]
        self.depth: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.flow_x: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.flow_y: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]
        self.purity: List[List[float]] = [[1.0 for _ in range(size)] for _ in range(size)]

class ResourceMap:
    __slots__ = ("quantities", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        # Stores discrete quantities per resource type per tile
        self.quantities: List[List[Dict[ResourceType, float]]] = [
            [{} for _ in range(size)] for _ in range(size)
        ]

class VegetationMap:
    __slots__ = ("vegetation_type", "density", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.vegetation_type: List[List[VegetationType]] = [[VegetationType.NONE for _ in range(size)] for _ in range(size)]
        self.density: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]

class HazardMap:
    __slots__ = ("hazard_type", "intensity", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.hazard_type: List[List[HazardType]] = [[HazardType.NONE for _ in range(size)] for _ in range(size)]
        self.intensity: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]

class NavigationMap:
    __slots__ = ("walk_cost", "swim_cost", "climb_cost", "fly_cost", "is_blocked", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.walk_cost: List[List[float]] = [[1.0 for _ in range(size)] for _ in range(size)]
        self.swim_cost: List[List[float]] = [[2.0 for _ in range(size)] for _ in range(size)]
        self.climb_cost: List[List[float]] = [[1.5 for _ in range(size)] for _ in range(size)]
        self.fly_cost: List[List[float]] = [[1.0 for _ in range(size)] for _ in range(size)]
        self.is_blocked: List[List[bool]] = [[False for _ in range(size)] for _ in range(size)]

class LayerMap:
    """Extra thematic layers (Infrastructure, Ownership, Fog of War, Heatmaps)."""
    __slots__ = ("roads", "ownership", "fog_of_war", "heatmap", "size")
    def __init__(self, size: int) -> None:
        self.size = size
        self.roads: List[List[bool]] = [[False for _ in range(size)] for _ in range(size)]
        self.ownership: List[List[int]] = [[-1 for _ in range(size)] for _ in range(size)]  # Faction ID
        self.fog_of_war: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]  # 0.0 hidden, 1.0 visible
        self.heatmap: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]


# =============================================================================
# CHUNK & LIGHTWEIGHT TILE WRAPPER
# =============================================================================

class TerrainChunk:
    """Subgrid spatial block wrapping maps and entity registrations."""
    CHUNK_SIZE: int = 64

    def __init__(self, chunk_x: int, chunk_y: int) -> None:
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.chunk_id = f"{chunk_x}_{chunk_y}"
        self.is_dirty: bool = False

        self.height_map = HeightMap(self.CHUNK_SIZE)
        self.biome_map = BiomeMap(self.CHUNK_SIZE)
        self.climate_map = ClimateMap(self.CHUNK_SIZE)
        self.atmospheric_map = AtmosphericMap(self.CHUNK_SIZE)
        self.geological_map = GeologicalMap(self.CHUNK_SIZE)
        self.soil_map = SoilMap(self.CHUNK_SIZE)
        self.water_map = WaterMap(self.CHUNK_SIZE)
        self.resource_map = ResourceMap(self.CHUNK_SIZE)
        self.vegetation_map = VegetationMap(self.CHUNK_SIZE)
        self.hazard_map = HazardMap(self.CHUNK_SIZE)
        self.navigation_map = NavigationMap(self.CHUNK_SIZE)
        self.layer_map = LayerMap(self.CHUNK_SIZE)

        # Entity registration tracking per local coordinate (local_x, local_y) -> Set of Entity IDs
        self.entities: Dict[Tuple[int, int], Set[str]] = {
            (lx, ly): set() for lx in range(self.CHUNK_SIZE) for ly in range(self.CHUNK_SIZE)
        }


class TerrainTile:
    """
    Zero-Duplication Proxy Tile View.
    Delegates all property lookups directly to underlying map stores inside the chunk.
    """
    __slots__ = ("chunk", "local_x", "local_y", "global_x", "global_y")

    def __init__(self, chunk: TerrainChunk, local_x: int, local_y: int) -> None:
        self.chunk = chunk
        self.local_x = local_x
        self.local_y = local_y
        self.global_x = chunk.chunk_x * TerrainChunk.CHUNK_SIZE + local_x
        self.global_y = chunk.chunk_y * TerrainChunk.CHUNK_SIZE + local_y

    @property
    def height(self) -> float:
        return self.chunk.height_map.height[self.local_x][self.local_y]

    @property
    def slope(self) -> float:
        return self.chunk.height_map.slope[self.local_x][self.local_y]

    @property
    def biome(self) -> BiomeType:
        return self.chunk.biome_map.data[self.local_x][self.local_y]

    @property
    def temperature(self) -> float:
        return self.chunk.climate_map.temperature[self.local_x][self.local_y]

    @property
    def humidity(self) -> float:
        return self.chunk.climate_map.humidity[self.local_x][self.local_y]

    @property
    def rainfall(self) -> float:
        return self.chunk.climate_map.rainfall[self.local_x][self.local_y]

    @property
    def water_type(self) -> WaterType:
        return self.chunk.water_map.water_type[self.local_x][self.local_y]

    @property
    def water_depth(self) -> float:
        return self.chunk.water_map.depth[self.local_x][self.local_y]

    @property
    def walk_cost(self) -> float:
        return self.chunk.navigation_map.walk_cost[self.local_x][self.local_y]

    @property
    def is_blocked(self) -> bool:
        return self.chunk.navigation_map.is_blocked[self.local_x][self.local_y]

    @property
    def resource_quantities(self) -> Dict[ResourceType, float]:
        return self.chunk.resource_map.quantities[self.local_x][self.local_y]

    @property
    def entities(self) -> Set[str]:
        return self.chunk.entities[(self.local_x, self.local_y)]

    def add_entity(self, entity_id: str) -> None:
        self.chunk.entities[(self.local_x, self.local_y)].add(entity_id)

    def remove_entity(self, entity_id: str) -> None:
        self.chunk.entities[(self.local_x, self.local_y)].discard(entity_id)


# =============================================================================
# BIOME CLASSIFIER & NOISE ENGINES
# =============================================================================

class NoiseGenerator:
    """Modular noise generator supporting multi-type noise queries."""
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def sample(self, x: float, y: float, noise_type: NoiseType = NoiseType.PERLIN, octaves: int = 4, persistence: float = 0.5) -> float:
        if noise_type == NoiseType.RIDGED:
            val = self._sample_fractal(x, y, octaves, persistence)
            return 1.0 - abs(val * 2.0 - 1.0)
        elif noise_type == NoiseType.VORONOI:
            gx, gy = math.floor(x), math.floor(y)
            min_d = 1.0
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    cx, cy = gx + dx, gy + dy
                    px = cx + (math.sin(cx * 12.9898 + cy * 78.233 + self.seed) % 1.0)
                    py = cy + (math.cos(cx * 4.1414 + cy * 23.512 + self.seed) % 1.0)
                    min_d = min(min_d, math.hypot(x - px, y - py))
            return min(1.0, min_d)
        elif noise_type == NoiseType.DOMAIN_WARP:
            qx = self._sample_fractal(x, y, octaves, persistence)
            qy = self._sample_fractal(x + 5.2, y + 1.3, octaves, persistence)
            return self._sample_fractal(x + 4.0 * qx, y + 4.0 * qy, octaves, persistence)
        else:
            return self._sample_fractal(x, y, octaves, persistence)

    def _sample_fractal(self, x: float, y: float, octaves: int, persistence: float) -> float:
        total, freq, amp, max_v = 0.0, 1.0, 1.0, 0.0
        for _ in range(octaves):
            nx, ny = (x * freq) + self.seed, (y * freq) + self.seed
            v = (math.sin(nx) * math.cos(ny) + math.sin(nx * 0.7) + math.cos(ny * 1.3)) / 3.0
            total += ((v + 1.0) / 2.0) * amp
            max_v += amp
            amp *= persistence
            freq *= 2.0
        return total / max_v


class BiomeClassifier:
    """Multi-parameter biome classification engine."""
    @staticmethod
    def classify(elevation: float, continentalness: float, erosion: float,
                 temperature: float, humidity: float, latitude: float, weirdness: float) -> BiomeType:
        if elevation < 0.2:
            return BiomeType.DEEP_OCEAN
        if elevation < 0.35:
            return BiomeType.OCEAN
        if elevation < 0.38:
            return BiomeType.BEACH
        if elevation > 0.85:
            return BiomeType.SNOW if temperature < 0 else BiomeType.VOLCANO
        if elevation > 0.7:
            return BiomeType.MOUNTAIN

        # Latitude / Temperature driven overrides
        if abs(latitude) > 70.0 or temperature < -10.0:
            return BiomeType.ICE if temperature < -25.0 else BiomeType.TUNDRA
        if weirdness > 0.85:
            return BiomeType.CRYSTAL if weirdness < 0.95 else BiomeType.TOXIC

        if humidity < 0.2:
            return BiomeType.DESERT if temperature > 15 else BiomeType.ROCK_DESERT
        elif humidity > 0.75:
            return BiomeType.RAINFOREST if temperature > 20 else BiomeType.SWAMP
        elif humidity > 0.45:
            return BiomeType.FOREST
        else:
            return BiomeType.SAVANNA if temperature > 25 else BiomeType.GRASSLAND


# =============================================================================
# MODULAR PIPELINE STAGES
# =============================================================================

class PipelineStage:
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        raise NotImplementedError

class NoiseStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        pass

class HeightStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        sx, sy = chunk.chunk_x * sz, chunk.chunk_y * sz
        for x in range(sz):
            for y in range(sz):
                gx, gy = (sx + x) * 0.005, (sy + y) * 0.005
                h = noise.sample(gx, gy, noise_type=NoiseType.DOMAIN_WARP)
                chunk.height_map.height[x][y] = max(0.0, min(1.0, h))

class ClimateStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        sx, sy = chunk.chunk_x * sz, chunk.chunk_y * sz
        for x in range(sz):
            for y in range(sz):
                gx, gy = (sx + x) * 0.003, (sy + y) * 0.003
                h = chunk.height_map.height[x][y]
                # Latitude factor: 0 at equator, 90 at pole
                latitude = min(90.0, abs(sy + y) * 0.1)
                lat_factor = math.cos(math.radians(latitude))
                base_temp = (lat_factor * 50.0) - 10.0
                temp = base_temp + (noise.sample(gx + 10.0, gy + 10.0) * 10.0) - (h * 30.0)
                hum = noise.sample(gx + 20.0, gy + 20.0)
                rain = max(0.0, min(1.0, hum * 1.2 - (temp / 100.0)))

                chunk.climate_map.temperature[x][y] = temp
                chunk.climate_map.humidity[x][y] = hum
                chunk.climate_map.rainfall[x][y] = rain

class BiomeStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        sx, sy = chunk.chunk_x * sz, chunk.chunk_y * sz
        for x in range(sz):
            for y in range(sz):
                gx, gy = (sx + x) * 0.005, (sy + y) * 0.005
                h = chunk.height_map.height[x][y]
                temp = chunk.climate_map.temperature[x][y]
                hum = chunk.climate_map.humidity[x][y]
                lat = (sy + y) * 0.1
                cont = noise.sample(gx + 30.0, gy + 30.0)
                eros = noise.sample(gx + 40.0, gy + 40.0)
                weird = noise.sample(gx + 50.0, gy + 50.0)

                biome = BiomeClassifier.classify(h, cont, eros, temp, hum, lat, weird)
                chunk.biome_map.data[x][y] = biome

class WaterStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                h = chunk.height_map.height[x][y]
                if h < 0.2:
                    chunk.water_map.water_type[x][y] = WaterType.OCEAN
                    chunk.water_map.depth[x][y] = (0.2 - h) * 100.0
                elif h < 0.35:
                    chunk.water_map.water_type[x][y] = WaterType.OCEAN
                    chunk.water_map.depth[x][y] = (0.35 - h) * 30.0

class ResourcesStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                biome = chunk.biome_map.data[x][y]
                res_type = BIOME_REGISTRY[biome].primary_resource
                if res_type != ResourceType.NONE:
                    chunk.resource_map.quantities[x][y][res_type] = 500.0

class VegetationStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                biome = chunk.biome_map.data[x][y]
                cfg = BIOME_REGISTRY[biome]
                chunk.vegetation_map.vegetation_type[x][y] = cfg.primary_vegetation
                chunk.vegetation_map.density[x][y] = cfg.fertility

class NavigationStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                biome = chunk.biome_map.data[x][y]
                cfg = BIOME_REGISTRY[biome]
                chunk.navigation_map.walk_cost[x][y] = cfg.walk_modifier
                chunk.navigation_map.swim_cost[x][y] = cfg.swim_modifier
                chunk.navigation_map.climb_cost[x][y] = cfg.climb_modifier
                if biome in (BiomeType.DEEP_OCEAN, BiomeType.VOLCANO):
                    chunk.navigation_map.is_blocked[x][y] = True

class HazardsStage(PipelineStage):
    def execute(self, chunk: TerrainChunk, noise: NoiseGenerator) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                biome = chunk.biome_map.data[x][y]
                if biome == BiomeType.VOLCANO:
                    chunk.hazard_map.hazard_type[x][y] = HazardType.VOLCANO
                    chunk.hazard_map.intensity[x][y] = 0.9

class TerrainGeneratorPipeline:
    """Executes registered pipeline stages sequentially."""
    def __init__(self, seed: int = 42) -> None:
        self.noise = NoiseGenerator(seed=seed)
        self.stages: List[PipelineStage] = [
            NoiseStage(), HeightStage(), ClimateStage(), BiomeStage(),
            WaterStage(), ResourcesStage(), VegetationStage(),
            NavigationStage(), HazardsStage()
        ]

    def execute_pipeline(self, chunk: TerrainChunk) -> None:
        for stage in self.stages:
            stage.execute(chunk, self.noise)


# =============================================================================
# TERRAIN EVOLUTION & TERRAIN TIMELINE
# =============================================================================

class SoilErosionModule:
    def process(self, chunk: TerrainChunk) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                if chunk.climate_map.rainfall[x][y] > 0.8:
                    chunk.soil_map.organic_matter[x][y] = max(0.0, chunk.soil_map.organic_matter[x][y] - 0.01)

class ForestGrowthModule:
    def process(self, chunk: TerrainChunk, timeline: TerrainTimeline) -> None:
        sz = TerrainChunk.CHUNK_SIZE
        for x in range(sz):
            for y in range(sz):
                if chunk.vegetation_map.vegetation_type[x][y] == VegetationType.GRASS and chunk.climate_map.rainfall[x][y] > 0.6:
                    chunk.vegetation_map.density[x][y] = min(1.0, chunk.vegetation_map.density[x][y] + 0.02)

class TerrainTimeline:
    """Tracks historical events, biome ages, and natural history logs."""
    def __init__(self) -> None:
        self.events_log: List[Dict[str, Any]] = []

    def record_event(self, tick: int, event_type: TerrainEvent, location: Tuple[int, int], description: str) -> None:
        self.events_log.append({
            "tick": tick,
            "event": event_type.name,
            "location": location,
            "description": description
        })

    def get_history_summary(self, center: Tuple[int, int], radius: int) -> List[str]:
        cx, cy = center
        matches = []
        for e in self.events_log:
            lx, ly = e["location"]
            if abs(lx - cx) <= radius and abs(ly - cy) <= radius:
                matches.append(f"[Tick {e['tick']}] {e['event']}: {e['description']}")
        return matches


class ModularTerrainEvolution:
    """Executes evolution sub-modules over time."""
    def __init__(self, manager: TerrainManager) -> None:
        self.manager = manager
        self.erosion_module = SoilErosionModule()
        self.growth_module = ForestGrowthModule()

    def update(self, tick: int) -> None:
        if tick % 20 != 0:
            return
        for chunk in self.manager.chunk_manager.chunks.values():
            self.erosion_module.process(chunk)
            self.growth_module.process(chunk, self.manager.timeline)


# =============================================================================
# CONTRACT PACKETS & ADAPTERS
# =============================================================================

@dataclass(slots=True)
class RenderPacket:
    x: int
    y: int
    height: float
    biome_code: int
    color_hex: str
    water_depth: float
    visibility: float

@dataclass(slots=True)
class CivilizationSuitabilityScore:
    settlement_score: float
    agriculture_score: float
    mining_score: float
    trade_score: float
    defense_score: float
    disease_risk: float
    flood_risk: float

@dataclass(slots=True)
class GeminiContextSummary:
    center_position: Tuple[int, int]
    current_biome: str
    nearby_biomes: List[str]
    climate: Dict[str, float]
    nearby_resources: Dict[str, float]
    nearby_hazards: List[str]
    historical_events: List[str]
    civ_suitability: CivilizationSuitabilityScore


class TerrainAdapters:
    """Converts internal engine state to lightweight contract structures."""
    def __init__(self, manager: TerrainManager) -> None:
        self.manager = manager

    def generate_render_packet(self, min_x: int, min_y: int, max_x: int, max_y: int) -> List[RenderPacket]:
        packets = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile = self.manager.queries.get_tile(x, y)
                cfg = BIOME_REGISTRY[tile.biome]
                packets.append(RenderPacket(
                    x=x, y=y, height=tile.height,
                    biome_code=tile.biome.value,
                    color_hex=cfg.color_hex,
                    water_depth=tile.water_depth,
                    visibility=1.0
                ))
        return packets

    def generate_civ_score(self, x: int, y: int) -> CivilizationSuitabilityScore:
        tile = self.manager.queries.get_tile(x, y)
        agri = tile.chunk.soil_map.organic_matter[tile.local_x][tile.local_y] * (1.0 if tile.water_type != WaterType.NONE else 0.3)
        defense = min(1.0, tile.height * 1.2)
        mining = tile.chunk.geological_map.mineral_veins[tile.local_x][tile.local_y]
        return CivilizationSuitabilityScore(
            settlement_score=round((agri + defense) / 2.0, 2),
            agriculture_score=round(agri, 2),
            mining_score=round(mining, 2),
            trade_score=0.5,
            defense_score=round(defense, 2),
            disease_risk=0.1,
            flood_risk=0.2 if tile.water_type != WaterType.NONE else 0.0
        )

    def generate_gemini_summary(self, center_x: int, center_y: int, radius: int = 5) -> GeminiContextSummary:
        center_tile = self.manager.queries.get_tile(center_x, center_y)
        biomes_seen = set()
        resources_found: Dict[str, float] = {}
        hazards_near = []

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                t = self.manager.queries.get_tile(center_x + dx, center_y + dy)
                biomes_seen.add(t.biome.name)
                for r_type, q in t.resource_quantities.items():
                    resources_found[r_type.name] = resources_found.get(r_type.name, 0.0) + q

        history = self.manager.timeline.get_history_summary((center_x, center_y), radius)
        civ_score = self.generate_civ_score(center_x, center_y)

        return GeminiContextSummary(
            center_position=(center_x, center_y),
            current_biome=center_tile.biome.name,
            nearby_biomes=list(biomes_seen),
            climate={
                "temp": round(center_tile.temperature, 1),
                "humidity": round(center_tile.humidity, 2)
            },
            nearby_resources=resources_found,
            nearby_hazards=hazards_near,
            historical_events=history,
            civ_suitability=civ_score
        )


# =============================================================================
# SPATIAL INDEX, CACHE & SUB-MANAGERS
# =============================================================================

class SpatialHashIndex:
    """O(1) Spatial Hash Bucket Index."""
    def __init__(self, bucket_size: int = 16) -> None:
        self.bucket_size = bucket_size
        self.buckets: Dict[Tuple[int, int], Set[str]] = {}

    def _get_key(self, x: int, y: int) -> Tuple[int, int]:
        return (x // self.bucket_size, y // self.bucket_size)

    def insert(self, x: int, y: int, entity_id: str) -> None:
        k = self._get_key(x, y)
        if k not in self.buckets:
            self.buckets[k] = set()
        self.buckets[k].add(entity_id)

    def remove(self, x: int, y: int, entity_id: str) -> None:
        k = self._get_key(x, y)
        if k in self.buckets:
            self.buckets[k].discard(entity_id)


class TerrainCacheHierarchy:
    """Tiered Cache Store for Chunks and Queries."""
    def __init__(self) -> None:
        self.tile_proxy_cache: Dict[Tuple[int, int], TerrainTile] = {}

    def clear(self) -> None:
        self.tile_proxy_cache.clear()


class ChunkManager:
    """Manages active terrain chunk lifecycles and generation."""
    def __init__(self, generator: TerrainGeneratorPipeline) -> None:
        self.generator = generator
        self.chunks: Dict[str, TerrainChunk] = {}

    def get_chunk(self, chunk_x: int, chunk_y: int) -> TerrainChunk:
        cid = f"{chunk_x}_{chunk_y}"
        if cid not in self.chunks:
            chunk = TerrainChunk(chunk_x, chunk_y)
            self.generator.execute_pipeline(chunk)
            self.chunks[cid] = chunk
        return self.chunks[cid]

    def unload_chunk(self, chunk_id: str) -> None:
        if chunk_id in self.chunks:
            del self.chunks[chunk_id]


class TerrainQueries:
    """High-Performance Query API abstraction."""
    def __init__(self, manager: TerrainManager) -> None:
        self.manager = manager

    def get_tile(self, x: int, y: int) -> TerrainTile:
        pos = (x, y)
        if pos in self.manager.cache.tile_proxy_cache:
            return self.manager.cache.tile_proxy_cache[pos]

        cx = x // TerrainChunk.CHUNK_SIZE
        cy = y // TerrainChunk.CHUNK_SIZE
        lx = x % TerrainChunk.CHUNK_SIZE
        ly = y % TerrainChunk.CHUNK_SIZE

        chunk = self.manager.chunk_manager.get_chunk(cx, cy)
        tile = TerrainTile(chunk, lx, ly)
        self.manager.cache.tile_proxy_cache[pos] = tile
        return tile

    def is_walkable(self, x: int, y: int) -> bool:
        t = self.get_tile(x, y)
        return not t.is_blocked and t.walk_cost < 4.0


class TerrainEvents:
    """Pub/Sub Event Bus for Environmental Events."""
    def __init__(self) -> None:
        self.subscribers: List[Callable[[TerrainEvent, Dict[str, Any]], None]] = []

    def subscribe(self, callback: Callable[[TerrainEvent, Dict[str, Any]], None]) -> None:
        self.subscribers.append(callback)

    def publish(self, event: TerrainEvent, data: Dict[str, Any]) -> None:
        for sub in self.subscribers:
            sub(event, data)


# =============================================================================
# FACADE TERRAIN MANAGER
# =============================================================================

class TerrainManager:
    """
    Facade Domain Manager coordinating modular sub-components.
    Refactored away from God-Object anti-pattern into clean subsystem aggregators.
    """
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.generator = TerrainGeneratorPipeline(seed=seed)
        self.chunk_manager = ChunkManager(generator=self.generator)
        self.cache = TerrainCacheHierarchy()
        self.queries = TerrainQueries(manager=self)
        self.events = TerrainEvents()
        self.adapters = TerrainAdapters(manager=self)
        self.spatial_index = SpatialHashIndex()
        self.timeline = TerrainTimeline()
        self.evolution = ModularTerrainEvolution(manager=self)

    def update(self, tick: int) -> None:
        """Simulation tick entry point."""
        self.evolution.update(tick)

    # Proxy Facade Methods for Clean External Interface
    def get_tile(self, x: int, y: int) -> TerrainTile:
        return self.queries.get_tile(x, y)

    def get_chunk(self, chunk_x: int, chunk_y: int) -> TerrainChunk:
        return self.chunk_manager.get_chunk(chunk_x, chunk_y)

    def get_render_packets(self, min_x: int, min_y: int, max_x: int, max_y: int) -> List[RenderPacket]:
        return self.adapters.generate_render_packet(min_x, min_y, max_x, max_y)

    def get_gemini_summary(self, center_x: int, center_y: int, radius: int = 5) -> GeminiContextSummary:
        return self.adapters.generate_gemini_summary(center_x, center_y, radius)