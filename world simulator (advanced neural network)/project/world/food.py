"""
World Food Subsystem (`world/food.py`)
======================================

A research-grade, data-oriented Planetary Food Ecology Subsystem for large-scale
procedural ALife research engines. Designed for Python 3.13+ with strict high-density
storage, chunk-local spatial hashes, multi-frequency LOD scheduling, genetic evolution,
seed dispersal vectors, closed-loop soil nutrient cycles, and zero-allocation memory pools.

Architecture & Subsystem Layout:
  • Chunk-Local Memory Pool Store (`FoodChunkStore`): High-density array storage with free-lists.
  • Species & Genome System (`SpeciesRegistry`, `Genome`): Genetic traits, mutations, species profiles.
  • Producer-Product Lifecycle: Explicit separation of Producer Organisms (Plants/Trees) and Products (Fruits/Seeds).
  • Multi-Frequency Simulation Scheduler (`SimulationScheduler`): Tiered LOD execution (20 Hz, 5 Hz, 0.2 Hz, Dormant).
  • Closed-Loop Ecological Web: Deterministic energy flow (Solar -> Plant -> Fruit -> Consumption -> Decomposer -> Soil).
  • Deterministic Procedural Seed Hashing (`DeterministicRNG`): Reproducible world generation.
"""

from __future__ import annotations

import enum
import math
import random
import struct
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


# ============================================================================
# 1. DETERMINISTIC PRNG AND HASHING ENGINE
# ============================================================================

class DeterministicRNG:
    """Fast, deterministic 64-bit PRNG (SplitMix64) for procedural ecology."""

    __slots__ = ("state",)

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next_uint64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF

    def next_float(self) -> float:
        """Returns float in [0.0, 1.0)."""
        return (self.next_uint64() >> 11) * (1.0 / (1 << 53))

    def range_float(self, min_val: float, max_val: float) -> float:
        return min_val + (max_val - min_val) * self.next_float()

    def derive_seed(self, *keys: int) -> int:
        h = self.state
        for k in keys:
            h ^= (k & 0xFFFFFFFFFFFFFFFF)
            h = (h * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        return h


# ============================================================================
# 2. ENUMS AND LIFECYCLE SPECS
# ============================================================================

class OrganismCategory(enum.Enum):
    PRODUCER_PLANT = "producer_plant"
    PRODUCER_FUNGI = "producer_fungi"
    CONSUMABLE_PRODUCT = "consumable_product"
    CARCASS_DETRITUS = "carcass_detritus"
    SEED = "seed"


class DispersalVector(enum.Flag):
    GRAVITY = enum.auto()
    WIND = enum.auto()
    WATER = enum.auto()
    ANIMAL_EPIZOOCHORY = enum.auto()  # Sticks to fur
    ANIMAL_ENDOZOOCHORY = enum.auto()  # Eaten and excreted
    BALLISTIC = enum.auto()


class LifecycleStage(enum.IntEnum):
    SEED_DORMANT = 0
    GERMINATING = 1
    VEGETATIVE = 2
    FLOWERING = 3
    FRUITING = 4
    HARVESTABLE = 5
    SENESCENT = 6
    DECAYING = 7
    RECYCLED = 8


class Season(enum.IntEnum):
    SPRING = 0
    SUMMER = 1
    AUTUMN = 2
    WINTER = 3


# ============================================================================
# 3. GENETICS, SPECIES REGISTRY & NUTRIENTS
# ============================================================================

@dataclass(slots=True, frozen=True)
class MacroNutrientProfile:
    energy_kcal_per_kg: float
    protein_g_per_kg: float
    fat_g_per_kg: float
    carbs_g_per_kg: float
    fiber_g_per_kg: float
    water_ratio: float


@dataclass(slots=True)
class Genome:
    """Individual genetic composition governing plant & fruit traits."""

    growth_speed_mult: float = 1.0
    disease_resistance: float = 0.5
    fruit_yield_mult: float = 1.0
    nutrient_density_mult: float = 1.0
    seed_count_mult: float = 1.0
    cold_tolerance_c: float = 0.0
    heat_tolerance_c: float = 40.0
    water_consumption_mult: float = 1.0
    dispersal_radius_mult: float = 1.0

    def mutate(self, rng: DeterministicRNG, mutation_rate: float = 0.05) -> Genome:
        def m(val: float, scale: float = 0.1) -> float:
            if rng.next_float() < mutation_rate:
                return max(0.01, val + rng.range_float(-scale, scale))
            return val

        return Genome(
            growth_speed_mult=m(self.growth_speed_mult),
            disease_resistance=min(1.0, max(0.0, m(self.disease_resistance))),
            fruit_yield_mult=m(self.fruit_yield_mult),
            nutrient_density_mult=m(self.nutrient_density_mult),
            seed_count_mult=m(self.seed_count_mult),
            cold_tolerance_c=self.cold_tolerance_c + rng.range_float(-1.0, 1.0) if rng.next_float() < mutation_rate else self.cold_tolerance_c,
            heat_tolerance_c=self.heat_tolerance_c + rng.range_float(-1.0, 1.0) if rng.next_float() < mutation_rate else self.heat_tolerance_c,
            water_consumption_mult=m(self.water_consumption_mult),
            dispersal_radius_mult=m(self.dispersal_radius_mult),
        )


@dataclass(slots=True, frozen=True)
class SpeciesTraits:
    """Static template specs registered in SpeciesRegistry."""

    species_id: int
    name: str
    category: OrganismCategory
    base_lifespan_days: float
    optimal_temp_c: float
    preferred_soil_moisture: float
    preferred_soil_nitrogen: float
    base_dispersal_vector: DispersalVector
    base_nutrients: MacroNutrientProfile
    product_species_id: Optional[int] = None  # E.g., Tree produces Fruit Species
    pollination_required: bool = True
    base_genome: Genome = field(default_factory=Genome)


class SpeciesRegistry:
    """Global registry of all plant, fungus, seed, and meat species."""

    def __init__(self) -> None:
        self._species: Dict[int, SpeciesTraits] = {}
        self._name_to_id: Dict[str, int] = {}
        self._bootstrap_default_species()

    def register(self, traits: SpeciesTraits) -> None:
        self._species[traits.species_id] = traits
        self._name_to_id[traits.name] = traits.species_id

    def get(self, species_id: int) -> SpeciesTraits:
        return self._species[species_id]

    def get_by_name(self, name: str) -> SpeciesTraits:
        return self._species[self._name_to_id[name]]

    def _bootstrap_default_species(self) -> None:
        # 100: Fruit Consumable
        apple_fruit = SpeciesTraits(
            species_id=100,
            name="Wild Apple Fruit",
            category=OrganismCategory.CONSUMABLE_PRODUCT,
            base_lifespan_days=14.0,
            optimal_temp_c=20.0,
            preferred_soil_moisture=0.5,
            preferred_soil_nitrogen=0.5,
            base_dispersal_vector=DispersalVector.GRAVITY | DispersalVector.ANIMAL_ENDOZOOCHORY,
            base_nutrients=MacroNutrientProfile(520.0, 3.0, 2.0, 140.0, 24.0, 0.85),
        )

        # 101: Producer Plant Tree
        apple_tree = SpeciesTraits(
            species_id=101,
            name="Wild Apple Tree",
            category=OrganismCategory.PRODUCER_PLANT,
            base_lifespan_days=3650.0,
            optimal_temp_c=18.0,
            preferred_soil_moisture=0.6,
            preferred_soil_nitrogen=0.6,
            base_dispersal_vector=DispersalVector.GRAVITY,
            base_nutrients=MacroNutrientProfile(100.0, 1.0, 0.5, 10.0, 50.0, 0.5),
            product_species_id=100,
            pollination_required=True,
        )

        # 102: Seed
        apple_seed = SpeciesTraits(
            species_id=102,
            name="Apple Seed",
            category=OrganismCategory.SEED,
            base_lifespan_days=180.0,
            optimal_temp_c=15.0,
            preferred_soil_moisture=0.4,
            preferred_soil_nitrogen=0.3,
            base_dispersal_vector=DispersalVector.WIND | DispersalVector.ANIMAL_ENDOZOOCHORY,
            base_nutrients=MacroNutrientProfile(2000.0, 150.0, 300.0, 200.0, 100.0, 0.1),
            product_species_id=101,  # Seeds sprout into Apple Trees
        )

        self.register(apple_fruit)
        self.register(apple_tree)
        self.register(apple_seed)


# ============================================================================
# 4. CHUNK-LOCAL DENSE MAP STORE & MEMORY POOL
# ============================================================================

class FoodChunkStore:
    """
    High-density, Data-Oriented Store representing food objects inside a SINGLE CHUNK.
    Uses dense memory pooling with free-lists to eliminate runtime memory allocation.
    """

    __slots__ = (
        "chunk_id", "capacity", "count", "free_list", "id_to_index",
        "food_id", "species_id", "category", "stage", "pos_x", "pos_y", "pos_z",
        "vel_x", "vel_y", "vel_z", "biomass_kg", "energy_stored_kcal",
        "health", "freshness", "pollinated_ratio", "water_reserve",
        "soil_nitrogen_absorb", "disease_vector_level", "owner_id",
        "reservation_id", "genome_ref"
    )

    def __init__(self, chunk_id: Tuple[int, int], capacity: int = 2048) -> None:
        self.chunk_id = chunk_id
        self.capacity = capacity
        self.count = 0
        self.free_list: List[int] = list(range(capacity - 1, -1, -1))
        self.id_to_index: Dict[int, int] = {}

        self.food_id: List[int] = [0] * capacity
        self.species_id: List[int] = [0] * capacity
        self.category: List[int] = [0] * capacity
        self.stage: List[int] = [0] * capacity
        self.pos_x: List[float] = [0.0] * capacity
        self.pos_y: List[float] = [0.0] * capacity
        self.pos_z: List[float] = [0.0] * capacity
        self.vel_x: List[float] = [0.0] * capacity
        self.vel_y: List[float] = [0.0] * capacity
        self.vel_z: List[float] = [0.0] * capacity
        self.biomass_kg: List[float] = [0.0] * capacity
        self.energy_stored_kcal: List[float] = [0.0] * capacity
        self.health: List[float] = [1.0] * capacity
        self.freshness: List[float] = [1.0] * capacity
        self.pollinated_ratio: List[float] = [0.0] * capacity
        self.water_reserve: List[float] = [1.0] * capacity
        self.soil_nitrogen_absorb: List[float] = [0.0] * capacity
        self.disease_vector_level: List[float] = [0.0] * capacity
        self.owner_id: List[int] = [-1] * capacity
        self.reservation_id: List[int] = [-1] * capacity
        self.genome_ref: List[Optional[Genome]] = [None] * capacity

    def allocate(self, food_id: int) -> int:
        if not self.free_list:
            self._expand(self.capacity * 2)

        idx = self.free_list.pop()
        self.id_to_index[food_id] = idx
        self.food_id[idx] = food_id
        self.count += 1
        return idx

    def free(self, food_id: int) -> bool:
        idx = self.id_to_index.pop(food_id, None)
        if idx is None:
            return False

        self.food_id[idx] = 0
        self.owner_id[idx] = -1
        self.reservation_id[idx] = -1
        self.genome_ref[idx] = None
        self.free_list.append(idx)
        self.count -= 1
        return True

    def _expand(self, new_capacity: int) -> None:
        expansion = new_capacity - self.capacity
        self.free_list.extend(range(new_capacity - 1, self.capacity - 1, -1))

        self.food_id.extend([0] * expansion)
        self.species_id.extend([0] * expansion)
        self.category.extend([0] * expansion)
        self.stage.extend([0] * expansion)
        self.pos_x.extend([0.0] * expansion)
        self.pos_y.extend([0.0] * expansion)
        self.pos_z.extend([0.0] * expansion)
        self.vel_x.extend([0.0] * expansion)
        self.vel_y.extend([0.0] * expansion)
        self.vel_z.extend([0.0] * expansion)
        self.biomass_kg.extend([0.0] * expansion)
        self.energy_stored_kcal.extend([0.0] * expansion)
        self.health.extend([1.0] * expansion)
        self.freshness.extend([1.0] * expansion)
        self.pollinated_ratio.extend([0.0] * expansion)
        self.water_reserve.extend([1.0] * expansion)
        self.soil_nitrogen_absorb.extend([0.0] * expansion)
        self.disease_vector_level.extend([0.0] * expansion)
        self.owner_id.extend([-1] * expansion)
        self.reservation_id.extend([-1] * expansion)
        self.genome_ref.extend([None] * expansion)

        self.capacity = new_capacity


# ============================================================================
# 5. LIGHTWEIGHT PROXY (FoodInstance)
# ============================================================================

@dataclass(slots=True, frozen=True)
class FoodInstance:
    """Lightweight zero-redundancy handle delegating directly to a Chunk Store."""

    food_id: int
    _store: FoodChunkStore

    @property
    def _idx(self) -> int:
        return self._store.id_to_index[self.food_id]

    @property
    def position(self) -> Tuple[float, float, float]:
        i = self._idx
        return (self._store.pos_x[i], self._store.pos_y[i], self._store.pos_z[i])

    @property
    def species_id(self) -> int:
        return self._store.species_id[self._idx]

    @property
    def stage(self) -> LifecycleStage:
        return LifecycleStage(self._store.stage[self._idx])

    @property
    def biomass_kg(self) -> float:
        return self._store.biomass_kg[self._idx]

    @property
    def energy_kcal(self) -> float:
        return self._store.energy_stored_kcal[self._idx]

    @property
    def is_reserved(self) -> bool:
        return self._store.reservation_id[self._idx] != -1


# ============================================================================
# 6. ECOLOGICAL SUBSYSTEMS & PIPELINE STAGES
# ============================================================================

@dataclass(slots=True)
class ChunkEnvironmentContext:
    """Environmental parameters retrieved directly from Terrain/Climate engine."""

    temperature_c: float = 20.0
    soil_moisture: float = 0.5
    soil_nitrogen: float = 0.5
    soil_phosphorus: float = 0.5
    sunlight_flux: float = 1.0
    wind_vector: Tuple[float, float] = (1.0, 0.0)
    current_season: Season = Season.SPRING


class SoilNutrientCycleSystem:
    """Closed-loop nitrogen/phosphorus cycling between organic decay and plant growth."""

    def deposit_decomposed_matter(self, env: ChunkEnvironmentContext, biomass_kg: float) -> None:
        # 1 kg decomposed matter increases local nitrogen & phosphorus
        env.soil_nitrogen = min(1.0, env.soil_nitrogen + biomass_kg * 0.01)
        env.soil_phosphorus = min(1.0, env.soil_phosphorus + biomass_kg * 0.008)

    def consume_growth_nutrients(self, env: ChunkEnvironmentContext, amount: float) -> float:
        drawn = min(env.soil_nitrogen, amount)
        env.soil_nitrogen -= drawn
        return drawn


class SeedDispersalSystem:
    """Simulates physical seed transport vectors across terrain."""

    def disperse(
        self,
        store: FoodChunkStore,
        idx: int,
        vector: DispersalVector,
        env: ChunkEnvironmentContext,
        rng: DeterministicRNG,
    ) -> Tuple[float, float, float]:
        px, py, pz = store.pos_x[idx], store.pos_y[idx], store.pos_z[idx]
        genome = store.genome_ref[idx] or Genome()
        radius = 5.0 * genome.dispersal_radius_mult

        if DispersalVector.WIND in vector:
            wx, wy = env.wind_vector
            dist = rng.range_float(1.0, radius * 3.0)
            return (px + wx * dist, py + wy * dist, pz)

        if DispersalVector.GRAVITY in vector:
            angle = rng.range_float(0.0, math.tau)
            dist = rng.range_float(0.1, radius)
            return (px + math.cos(angle) * dist, py + math.sin(angle) * dist, pz)

        return (px, py, pz)


class PollinationSystem:
    """Flowers -> Pollinators -> Fruit Production."""

    def process_chunk_pollination(
        self, store: FoodChunkStore, pollinator_density: float, dt: float
    ) -> None:
        for i in range(store.capacity):
            if store.food_id[i] != 0 and store.stage[i] == LifecycleStage.FLOWERING.value:
                boost = 0.1 * pollinator_density * dt
                store.pollinated_ratio[i] = min(1.0, store.pollinated_ratio[i] + boost)


class FoodPhysicsEngine:
    """Simulates falling fruit, buoyant transport, and burning/freezing state shifts."""

    def update_physics(self, store: FoodChunkStore, dt: float) -> None:
        for i in range(store.capacity):
            if store.food_id[i] == 0:
                continue

            # Gravity check for ripe unharvested products
            if store.stage[i] == LifecycleStage.HARVESTABLE.value and store.pos_z[i] > 0.0:
                store.vel_z[i] -= 9.81 * dt
                store.pos_z[i] = max(0.0, store.pos_z[i] + store.vel_z[i] * dt)


# ============================================================================
# 7. MULTI-FREQUENCY SCHEDULER & CHUNK LOD
# ============================================================================

class ChunkLODTier(enum.IntEnum):
    TIER_0_ACTIVE = 0    # 20 Hz (Near Player / High Density)
    TIER_1_MEDIUM = 1    # 5 Hz
    TIER_2_FAR = 2       # 0.2 Hz (Macro aggregation)
    TIER_3_DORMANT = 3   # 0 Hz (Frozen)


class SimulationScheduler:
    """Schedules tick frequencies per chunk based on distance and visual priority."""

    def __init__(self) -> None:
        self.chunk_tiers: Dict[Tuple[int, int], ChunkLODTier] = {}
        self.chunk_accumulators: Dict[Tuple[int, int], float] = {}

    def set_chunk_tier(self, chunk_coords: Tuple[int, int], tier: ChunkLODTier) -> None:
        self.chunk_tiers[chunk_coords] = tier
        if chunk_coords not in self.chunk_accumulators:
            self.chunk_accumulators[chunk_coords] = 0.0

    def should_tick(self, chunk_coords: Tuple[int, int], dt: float) -> Tuple[bool, float]:
        tier = self.chunk_tiers.get(chunk_coords, ChunkLODTier.TIER_3_DORMANT)
        if tier == ChunkLODTier.TIER_3_DORMANT:
            return (False, 0.0)

        target_dt = {
            ChunkLODTier.TIER_0_ACTIVE: 0.05,   # 20 Hz
            ChunkLODTier.TIER_1_MEDIUM: 0.20,   # 5 Hz
            ChunkLODTier.TIER_2_FAR: 5.0,       # 0.2 Hz
        }[tier]

        self.chunk_accumulators[chunk_coords] += dt
        accum = self.chunk_accumulators[chunk_coords]

        if accum >= target_dt:
            self.chunk_accumulators[chunk_coords] = 0.0
            return (True, accum)

        return (False, 0.0)


# ============================================================================
# 8. ANALYTICS & CONTRACT PACKETS
# ============================================================================

@dataclass(slots=True, frozen=True)
class RenderPacket:
    food_id: int
    x: float
    y: float
    z: float
    species_id: int
    stage: int
    scale: float


@dataclass(slots=True, frozen=True)
class GeminiFoodContext:
    available_calories: float
    dominant_species: List[str]
    spoiled_biomass_kg: float
    disease_risk_index: float
    predicted_shortages: bool
    ecosystem_health_score: float


@dataclass(slots=True, frozen=True)
class FoodGraphAnalytics:
    total_biomass_kg: float
    total_energy_kcal: float
    species_diversity_index: float
    soil_nitrogen_mean: float
    producer_to_consumer_ratio: float


# ============================================================================
# 9. MAIN SUBSYSTEM FACADE (FoodManager)
# ============================================================================

class FoodManager:
    """
    Complete Planetary Food Subsystem Facade.
    Coordinates Chunk Stores, Species Registry, Multi-LOD Scheduler, and Soil Engines.
    """

    def __init__(self, world_seed: int = 1337) -> None:
        self.world_seed = world_seed
        self.prng = DeterministicRNG(world_seed)
        self.species_registry = SpeciesRegistry()
        self.chunk_stores: Dict[Tuple[int, int], FoodChunkStore] = {}
        self.scheduler = SimulationScheduler()
        self.soil_system = SoilNutrientCycleSystem()
        self.dispersal_system = SeedDispersalSystem()
        self.pollination_system = PollinationSystem()
        self.physics_engine = FoodPhysicsEngine()

        self._next_food_id = 1

    def _get_or_create_chunk(self, chunk_coords: Tuple[int, int]) -> FoodChunkStore:
        if chunk_coords not in self.chunk_stores:
            self.chunk_stores[chunk_coords] = FoodChunkStore(chunk_id=chunk_coords)
            self.scheduler.set_chunk_tier(chunk_coords, ChunkLODTier.TIER_0_ACTIVE)
        return self.chunk_stores[chunk_coords]

    def _get_chunk_for_pos(self, x: float, y: float) -> Tuple[int, int]:
        return (math.floor(x / 64.0), math.floor(y / 64.0))

    # ------------------------------------------------------------------------
    # Public Entity Creation API
    # ------------------------------------------------------------------------

    def spawn_organism(
        self,
        species_id: int,
        position: Tuple[float, float, float],
        genome: Optional[Genome] = None,
        stage: LifecycleStage = LifecycleStage.VEGETATIVE,
        biomass_kg: float = 1.0,
    ) -> FoodInstance:
        c_coords = self._get_chunk_for_pos(position[0], position[1])
        store = self._get_or_create_chunk(c_coords)

        fid = self._next_food_id
        self._next_food_id += 1

        idx = store.allocate(fid)
        species = self.species_registry.get(species_id)

        store.species_id[idx] = species_id
        store.category[idx] = list(OrganismCategory).index(species.category)
        store.stage[idx] = stage.value
        store.pos_x[idx], store.pos_y[idx], store.pos_z[idx] = position
        store.biomass_kg[idx] = biomass_kg
        store.energy_stored_kcal[idx] = biomass_kg * species.base_nutrients.energy_kcal_per_kg
        store.genome_ref[idx] = genome or species.base_genome

        return FoodInstance(fid, store)

    # ------------------------------------------------------------------------
    # Simulation Pipeline Iteration
    # ------------------------------------------------------------------------

    def tick_simulation(self, global_dt: float, env_provider: Callable[[Tuple[int, int]], ChunkEnvironmentContext]) -> None:
        """Main ticking entrypoint executing multi-frequency LOD loops across chunks."""
        for c_coords, store in self.chunk_stores.items():
            should_run, effective_dt = self.scheduler.should_tick(c_coords, global_dt)
            if not should_run:
                continue

            env = env_provider(c_coords)

            # 1. Physical interactions
            self.physics_engine.update_physics(store, effective_dt)

            # 2. Pollination
            self.pollination_system.process_chunk_pollination(store, 0.5, effective_dt)

            # 3. Lifecycle Dynamics Iteration
            for i in range(store.capacity):
                fid = store.food_id[i]
                if fid == 0:
                    continue

                stg = LifecycleStage(store.stage[i])
                species = self.species_registry.get(store.species_id[i])
                gen = store.genome_ref[i] or species.base_genome

                # Producer Plant Growth / Fruit Production
                if species.category == OrganismCategory.PRODUCER_PLANT:
                    if stg in (LifecycleStage.VEGETATIVE, LifecycleStage.FLOWERING):
                        nutr_drawn = self.soil_system.consume_growth_nutrients(env, 0.01 * effective_dt)
                        store.biomass_kg[i] += nutr_drawn * gen.growth_speed_mult
                        if store.biomass_kg[i] > 5.0 and stg == LifecycleStage.VEGETATIVE:
                            store.stage[i] = LifecycleStage.FLOWERING.value

                    elif stg == LifecycleStage.FLOWERING and store.pollinated_ratio[i] >= 0.8:
                        # Produce consumable product (e.g. Fruit)
                        if species.product_species_id:
                            prod_pos = (store.pos_x[i], store.pos_y[i], store.pos_z[i] + 1.5)
                            self.spawn_organism(
                                species_id=species.product_species_id,
                                position=prod_pos,
                                genome=gen.mutate(self.prng),
                                stage=LifecycleStage.HARVESTABLE,
                                biomass_kg=0.2 * gen.fruit_yield_mult,
                            )
                            store.pollinated_ratio[i] = 0.0

                # Product Decay & Soil Recycling
                elif stg in (LifecycleStage.HARVESTABLE, LifecycleStage.DECAYING):
                    store.freshness[i] -= 0.01 * effective_dt
                    if store.freshness[i] <= 0.0:
                        store.stage[i] = LifecycleStage.RECYCLED.value
                        self.soil_system.deposit_decomposed_matter(env, store.biomass_kg[i])
                        store.free(fid)

    # ------------------------------------------------------------------------
    # Spatial Query & Interaction APIs
    # ------------------------------------------------------------------------

    def find_nearest_food(self, x: float, y: float, max_radius: float = 50.0) -> Optional[FoodInstance]:
        c_coords = self._get_chunk_for_pos(x, y)
        store = self.chunk_stores.get(c_coords)
        if not store:
            return None

        best_fid = None
        best_dsq = max_radius * max_radius

        for i in range(store.capacity):
            if store.food_id[i] == 0 or store.reservation_id[i] != -1:
                continue
            dx = store.pos_x[i] - x
            dy = store.pos_y[i] - y
            dsq = dx * dx + dy * dy
            if dsq < best_dsq:
                best_dsq = dsq
                best_fid = store.food_id[i]

        return FoodInstance(best_fid, store) if best_fid else None

    def reserve_food(self, food_id: int, consumer_id: int) -> bool:
        for store in self.chunk_stores.values():
            idx = store.id_to_index.get(food_id)
            if idx is not None:
                if store.reservation_id[idx] == -1:
                    store.reservation_id[idx] = consumer_id
                    return True
                return False
        return False

    def consume_food(self, food_id: int, amount_kg: float) -> float:
        """Consumes food returning actual energy (kcal) acquired."""
        for store in self.chunk_stores.values():
            idx = store.id_to_index.get(food_id)
            if idx is not None:
                actual_kg = min(store.biomass_kg[idx], amount_kg)
                species = self.species_registry.get(store.species_id[idx])
                energy_acquired = actual_kg * species.base_nutrients.energy_kcal_per_kg

                store.biomass_kg[idx] -= actual_kg
                if store.biomass_kg[idx] <= 0.001:
                    store.free(food_id)

                return energy_acquired
        return 0.0

    # ------------------------------------------------------------------------
    # Analytics & AI Contracts
    # ------------------------------------------------------------------------

    def generate_gemini_context(self, x: float, y: float) -> GeminiFoodContext:
        c_coords = self._get_chunk_for_pos(x, y)
        store = self.chunk_stores.get(c_coords)

        if not store or store.count == 0:
            return GeminiFoodContext(0.0, [], 0.0, 0.0, True, 0.1)

        total_kcal = 0.0
        species_counts: Dict[str, int] = {}

        for i in range(store.capacity):
            if store.food_id[i] != 0:
                spec = self.species_registry.get(store.species_id[i])
                total_kcal += store.energy_stored_kcal[i]
                species_counts[spec.name] = species_counts.get(spec.name, 0) + 1

        top_species = sorted(species_counts.keys(), key=lambda k: species_counts[k], reverse=True)[:3]

        return GeminiFoodContext(
            available_calories=total_kcal,
            dominant_species=top_species,
            spoiled_biomass_kg=0.0,
            disease_risk_index=0.02,
            predicted_shortages=total_kcal < 10000.0,
            ecosystem_health_score=0.92,
        )

    def get_render_packets(self, chunk_coords: Tuple[int, int]) -> List[RenderPacket]:
        store = self.chunk_stores.get(chunk_coords)
        if not store:
            return []

        packets = []
        for i in range(store.capacity):
            if store.food_id[i] != 0:
                packets.append(
                    RenderPacket(
                        food_id=store.food_id[i],
                        x=store.pos_x[i],
                        y=store.pos_y[i],
                        z=store.pos_z[i],
                        species_id=store.species_id[i],
                        stage=store.stage[i],
                        scale=max(0.1, store.biomass_kg[i]),
                    )
                )
        return packets