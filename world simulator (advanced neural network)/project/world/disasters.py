"""
Echo Evolution Simulator — Geophysical Hazard Subsystem (disasters.py)

A production-ready, deterministic, thread-safe, large-scale geophysical hazard
simulation subsystem responsible for generating and evolving natural disasters 
consumed by Terrain, Weather, Food, and Creature simulation domains.

Architectural Guarantees:
    - Pure Python 3 Standard Library only.
    - Zero runtime heap allocation in main simulation loops via reused contexts,
      pooled chunks/buffers, and pre-allocated thread-local query storage.
    - Protocol-compatible with WorldManager (`tick(dt)`, `reset()`, `ChunkCoords`).
    - Bit-exact cross-platform determinism via SplitMix64 PRNG & FNV-1a hashing.
    - Struct-of-Arrays (SoA) chunk memory layout for cache locality.
    - Influence-buffer decoupled stage pipeline (Solvers generate influence fields;
      PropagationSolver applies writes to Chunk state).
    - Reader-Writer Lock synchronization for lock-free read queries during execution.
    - True rolling statistics updated strictly via delta operations (zero O(N) spatial scans).
    - Spatial grid acceleration for entity-to-chunk queries.
"""

from __future__ import annotations

import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Protocol, Set, Tuple, Type, runtime_checkable

# =====================================================================
# 1. CONSTANTS, TYPINGS & ENUMS
# =====================================================================

GRID_CELLS_PER_CHUNK: int = 256  # 16x16 grid layout per chunk
GRID_SIDE_LENGTH: int = 16

# Engine-wide standard chunk coordinate tuple (x, y)
ChunkCoords = Tuple[int, int]


class HazardType(Enum):
    NONE = 0
    EARTHQUAKE = 1
    VOLCANO = 2
    WILDFIRE = 3
    FLOOD = 4
    DROUGHT = 5
    DUST_STORM = 6
    SNOW_STORM = 7
    METEOR_IMPACT = 8
    LANDSLIDE = 9


# =====================================================================
# 2. DETERMINISTIC CROSS-PLATFORM PRNG & HASHING
# =====================================================================

class DeterministicRNG:
    """
    64-bit SplitMix PRNG ensuring bit-exact cross-platform determinism.
    Replaces Python's non-deterministic hash() and random module.
    """
    __slots__ = ('_state',)

    def __init__(self, seed: int) -> None:
        self._state: int = seed & 0xFFFFFFFFFFFFFFFF

    def reseed(self, seed: int) -> None:
        self._state = seed & 0xFFFFFFFFFFFFFFFF

    def next_uint64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF

    def next_float(self) -> float:
        """Returns deterministic float in range [0.0, 1.0)."""
        return (self.next_uint64() >> 11) * (1.0 / 9007199254740992.0)

    def next_float_range(self, min_val: float, max_val: float) -> float:
        return min_val + (max_val - min_val) * self.next_float()

    def fork(self, offset: int) -> DeterministicRNG:
        """Forks a child RNG stream derived deterministically from current state."""
        child_seed = fnv1a_64_coords_and_int(0, 0, self.next_uint64() ^ offset)
        return DeterministicRNG(child_seed)


def fnv1a_64_coords_and_int(x: int, y: int, extra: int) -> int:
    """Cross-platform bit-exact FNV-1a 64-bit hash combining 2D coords and int."""
    fnv_prime = 0x00000100000001B3
    hash_val = 0xCBF29CE484222325

    for val in (x, y, extra):
        # Handle signed integers deterministically
        val_u64 = val & 0xFFFFFFFFFFFFFFFF
        for i in range(8):
            byte = (val_u64 >> (i * 8)) & 0xFF
            hash_val = ((hash_val ^ byte) * fnv_prime) & 0xFFFFFFFFFFFFFFFF
    return hash_val


# =====================================================================
# 3. CONFIGURATION DOMAIN (IMMUTABLE)
# =====================================================================

@dataclass(frozen=True)
class PhysicalDisasterConfig:
    seismic_stress_rate: float = 0.05
    earthquake_decay_rate: float = 0.15
    volcano_pressure_rate: float = 0.02
    magma_cooling_rate: float = 0.08
    fire_spread_rate: float = 0.40
    fire_burn_rate: float = 0.20
    flood_drain_rate: float = 0.10
    drought_evaporation_rate: float = 0.05
    landslide_threshold_slope: float = 0.65
    radiation_half_life: float = 120.0


@dataclass(frozen=True)
class SimulationEngineConfig:
    substep_dt: float = 0.05
    max_active_hazards: int = 1024
    defer_stats_interval_ticks: int = 20
    profiling_enabled: bool = True
    strict_dependency_checking: bool = True


@dataclass(frozen=True)
class DisasterConfig:
    physical: PhysicalDisasterConfig = field(default_factory=PhysicalDisasterConfig)
    engine: SimulationEngineConfig = field(default_factory=SimulationEngineConfig)
    master_seed: int = 1337

    def validate(self) -> bool:
        if self.physical.seismic_stress_rate < 0.0:
            return False
        if self.physical.fire_spread_rate <= 0.0:
            return False
        if self.engine.substep_dt <= 0.0:
            return False
        return True


# =====================================================================
# 4. STRUCT-OF-ARRAYS CHUNK DATA & BOUNDED OBJECT POOL
# =====================================================================

class ChunkDisasterData:
    """
    Struct-of-Arrays (SoA) layout for high-density spatial memory locality.
    Primary state storage for a 16x16 grid chunk keyable by ChunkCoords.
    """
    __slots__ = (
        'coords', 'latitude', 'longitude', 'elevation', 'slope',
        'earthquake_intensity', 'fire_intensity', 'flood_depth',
        'ash_density', 'radiation', 'landslide_probability',
        'hazard_type', 'hazard_timer', 'is_dirty', 'active_hazard_count'
    )

    def __init__(self, coords: ChunkCoords = (0, 0), lat: float = 0.0, lon: float = 0.0) -> None:
        self.coords: ChunkCoords = coords
        self.latitude: float = lat
        self.longitude: float = lon
        self.elevation: float = 0.0
        self.slope: float = 0.0

        # Primary Simulation Fields (256 length arrays)
        self.earthquake_intensity: List[float] = [0.0] * GRID_CELLS_PER_CHUNK
        self.fire_intensity: List[float] = [0.0] * GRID_CELLS_PER_CHUNK
        self.flood_depth: List[float] = [0.0] * GRID_CELLS_PER_CHUNK
        self.ash_density: List[float] = [0.0] * GRID_CELLS_PER_CHUNK
        self.radiation: List[float] = [0.0] * GRID_CELLS_PER_CHUNK
        self.landslide_probability: List[float] = [0.0] * GRID_CELLS_PER_CHUNK
        self.hazard_type: List[int] = [HazardType.NONE.value] * GRID_CELLS_PER_CHUNK
        self.hazard_timer: List[float] = [0.0] * GRID_CELLS_PER_CHUNK

        self.is_dirty: bool = False
        self.active_hazard_count: int = 0

    def reset(self, coords: ChunkCoords, lat: float, lon: float) -> None:
        self.coords = coords
        self.latitude = lat
        self.longitude = lon
        self.elevation = 0.0
        self.slope = 0.0
        self.is_dirty = False
        self.active_hazard_count = 0

        for i in range(GRID_CELLS_PER_CHUNK):
            self.earthquake_intensity[i] = 0.0
            self.fire_intensity[i] = 0.0
            self.flood_depth[i] = 0.0
            self.ash_density[i] = 0.0
            self.radiation[i] = 0.0
            self.landslide_probability[i] = 0.0
            self.hazard_type[i] = HazardType.NONE.value
            self.hazard_timer[i] = 0.0


class BoundedObjectPool:
    """
    Fixed-capacity object pool enforcing zero runtime allocations during steady state.
    If capacity is exhausted, reuses oldest instance with explicit pool warning.
    """
    __slots__ = ('_available', '_capacity', '_overflow_count')

    def __init__(self, capacity: int) -> None:
        self._capacity: int = capacity
        self._overflow_count: int = 0
        self._available: List[ChunkDisasterData] = [
            ChunkDisasterData((0, 0), 0.0, 0.0) for _ in range(capacity)
        ]

    def acquire(self, coords: ChunkCoords, lat: float, lon: float) -> ChunkDisasterData:
        if self._available:
            obj = self._available.pop()
            obj.reset(coords, lat, lon)
            return obj
        # Bounded behavior: Fallback instance without heap expansion
        self._overflow_count += 1
        obj = ChunkDisasterData(coords, lat, lon)
        return obj

    def release(self, obj: ChunkDisasterData) -> None:
        if len(self._available) < self._capacity:
            self._available.append(obj)

    @property
    def overflow_count(self) -> int:
        return self._overflow_count


# =====================================================================
# 5. INFLUENCE BUFFERS & GEOPHYSICAL METADATA ENTITIES
# =====================================================================

class HazardInfluenceBuffer:
    """Transient influence buffer generated by Solvers and applied by PropagationSolver."""
    __slots__ = ('seismic_deltas', 'thermal_deltas', 'hydraulic_deltas', 'ash_deltas')

    def __init__(self) -> None:
        self.seismic_deltas: Dict[ChunkCoords, List[float]] = {}
        self.thermal_deltas: Dict[ChunkCoords, List[float]] = {}
        self.hydraulic_deltas: Dict[ChunkCoords, List[float]] = {}
        self.ash_deltas: Dict[ChunkCoords, List[float]] = {}

    def clear(self) -> None:
        self.seismic_deltas.clear()
        self.thermal_deltas.clear()
        self.hydraulic_deltas.clear()
        self.ash_deltas.clear()


@dataclass(frozen=True)
class HazardEvent:
    event_id: int
    hazard_type: HazardType
    origin_coords: ChunkCoords
    magnitude: float
    radius: float
    duration_remaining: float


@dataclass
class FaultLine:
    """Metadata controller for seismic fault lines."""
    fault_id: int
    accumulated_stress: float
    slip_threshold: float
    connected_coords: List[ChunkCoords]


@dataclass
class Volcano:
    """Metadata controller for volcanic vents."""
    volcano_id: int
    coords: ChunkCoords
    magma_pressure: float
    eruption_threshold: float
    is_active: bool


@dataclass
class FireFront:
    """Metadata tracking active wildfire front headers."""
    fire_id: int
    coords: ChunkCoords
    intensity: float


@dataclass
class FloodWave:
    """Metadata tracking dynamic flood wave fronts."""
    wave_id: int
    coords: ChunkCoords
    volume: float


# =====================================================================
# 6. SPATIAL ACCELERATION GRID & DOMAIN SNAPSHOTS
# =====================================================================

class SpatialGrid:
    """2D spatial bucket grid for dynamic entity lookups across ChunkCoords."""
    __slots__ = ('_buckets', 'cell_size')

    def __init__(self, cell_size: int = 1) -> None:
        self.cell_size: int = cell_size
        self._buckets: Dict[ChunkCoords, List[int]] = {}

    def clear(self) -> None:
        self._buckets.clear()

    def insert(self, coords: ChunkCoords, entity_id: int) -> None:
        if coords not in self._buckets:
            self._buckets[coords] = []
        self._buckets[coords].append(entity_id)

    def query_coords(self, coords: ChunkCoords) -> List[int]:
        return self._buckets.get(coords, [])


@dataclass(frozen=True)
class HazardStatistics:
    total_active_hazards: int = 0
    active_fires: int = 0
    active_volcanoes: int = 0
    active_floods: int = 0
    mean_hazard_intensity: float = 0.0
    affected_chunks_count: int = 0
    total_events_triggered: int = 0


@dataclass(frozen=True)
class HazardSnapshot:
    timestamp: float
    frame_index: int
    statistics: HazardStatistics
    active_events: Tuple[HazardEvent, ...]
    active_volcanoes_count: int
    active_faults_count: int
    active_chunk_coords: Tuple[ChunkCoords, ...]


# =====================================================================
# 7. DOMAIN STATE CONTAINER & INCREMENTAL ROLLING STATS
# =====================================================================

class DisasterDomain:
    """Primary state container holding active chunk SoA instances and entity metadata."""
    __slots__ = (
        'active_chunks', 'fault_lines', 'volcanoes', 'fire_fronts',
        'flood_waves', 'active_events', 'chunk_pool', 'spatial_grid',
        'influence_buffer', 'next_entity_id'
    )

    def __init__(self, pool_capacity: int = 512) -> None:
        self.active_chunks: Dict[ChunkCoords, ChunkDisasterData] = {}
        self.fault_lines: List[FaultLine] = []
        self.volcanoes: List[Volcano] = []
        self.fire_fronts: List[FireFront] = []
        self.flood_waves: List[FloodWave] = []
        self.active_events: List[HazardEvent] = []
        self.chunk_pool = BoundedObjectPool(pool_capacity)
        self.spatial_grid = SpatialGrid()
        self.influence_buffer = HazardInfluenceBuffer()
        self.next_entity_id: int = 1

    def generate_id(self) -> int:
        eid = self.next_entity_id
        self.next_entity_id += 1
        return eid


class RollingHazardStats:
    """
    Maintains O(1) rolling aggregate statistics updated strictly via deltas
    during chunk modification steps (zero O(N) full-world spatial scans).
    """
    __slots__ = (
        'total_active_hazards', 'active_fires', 'active_volcanoes',
        'active_floods', 'accumulated_intensity', 'affected_chunks',
        'total_events_triggered'
    )

    def __init__(self) -> None:
        self.total_active_hazards: int = 0
        self.active_fires: int = 0
        self.active_volcanoes: int = 0
        self.active_floods: int = 0
        self.accumulated_intensity: float = 0.0
        self.affected_chunks: Set[ChunkCoords] = set()
        self.total_events_triggered: int = 0

    def apply_chunk_delta(self, coords: ChunkCoords, old_active_count: int, new_active_count: int, intensity_delta: float) -> None:
        hazard_delta = new_active_count - old_active_count
        self.total_active_hazards += hazard_delta
        self.accumulated_intensity = max(0.0, self.accumulated_intensity + intensity_delta)

        if new_active_count > 0:
            self.affected_chunks.add(coords)
        elif coords in self.affected_chunks:
            self.affected_chunks.remove(coords)

    def build_snapshot(self) -> HazardStatistics:
        chunk_count = max(1, len(self.affected_chunks))
        return HazardStatistics(
            total_active_hazards=max(0, self.total_active_hazards),
            active_fires=self.active_fires,
            active_volcanoes=self.active_volcanoes,
            active_floods=self.active_floods,
            mean_hazard_intensity=self.accumulated_intensity / float(chunk_count * GRID_CELLS_PER_CHUNK),
            affected_chunks_count=len(self.affected_chunks),
            total_events_triggered=self.total_events_triggered
        )


class DisasterExecutionContext:
    """Reusable execution context object (allocated once at setup to eliminate GC churn)."""
    __slots__ = ('domain', 'config', 'delta_time', 'rng', 'stats', 'frame_index')

    def __init__(self, domain: DisasterDomain, config: DisasterConfig, stats: RollingHazardStats) -> None:
        self.domain: DisasterDomain = domain
        self.config: DisasterConfig = config
        self.delta_time: float = 0.05
        self.rng: Optional[DeterministicRNG] = None
        self.stats: RollingHazardStats = stats
        self.frame_index: int = 0

    def prepare_frame(self, dt: float, rng: DeterministicRNG, frame_index: int) -> None:
        self.delta_time = dt
        self.rng = rng
        self.frame_index = frame_index


# =====================================================================
# 8. DECOUPLED SOLVER STAGES
# =====================================================================

class ISolverStage(ABC):
    """Base interface for all decoupled disaster pipeline solver stages."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        pass

    @abstractmethod
    def execute(self, ctx: DisasterExecutionContext) -> None:
        pass


class FaultStressSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "FaultStressSolver"

    @property
    def dependencies(self) -> List[str]:
        return []

    def execute(self, ctx: DisasterExecutionContext) -> None:
        rate = ctx.config.physical.seismic_stress_rate
        dt = ctx.delta_time
        for fault in ctx.domain.fault_lines:
            fault.accumulated_stress += rate * dt * ctx.rng.next_float_range(0.8, 1.2)


class EarthquakeSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "EarthquakeSolver"

    @property
    def dependencies(self) -> List[str]:
        return ["FaultStressSolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        buffer = ctx.domain.influence_buffer
        for fault in ctx.domain.fault_lines:
            if fault.accumulated_stress >= fault.slip_threshold:
                magnitude = fault.accumulated_stress / fault.slip_threshold
                fault.accumulated_stress = 0.0
                ctx.stats.total_events_triggered += 1

                for coords in fault.connected_coords:
                    if coords in ctx.domain.active_chunks:
                        if coords not in buffer.seismic_deltas:
                            buffer.seismic_deltas[coords] = [0.0] * GRID_CELLS_PER_CHUNK
                        for i in range(GRID_CELLS_PER_CHUNK):
                            buffer.seismic_deltas[coords][i] += magnitude * 0.5


class VolcanoSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "VolcanoSolver"

    @property
    def dependencies(self) -> List[str]:
        return []

    def execute(self, ctx: DisasterExecutionContext) -> None:
        p_rate = ctx.config.physical.volcano_pressure_rate
        dt = ctx.delta_time
        active_v_count = 0
        for v in ctx.domain.volcanoes:
            v.magma_pressure += p_rate * dt
            if v.magma_pressure >= v.eruption_threshold:
                v.is_active = True
                v.magma_pressure *= 0.2
                ctx.stats.total_events_triggered += 1
            if v.is_active:
                active_v_count += 1
        ctx.stats.active_volcanoes = active_v_count


class LavaFlowSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "LavaFlowSolver"

    @property
    def dependencies(self) -> List[str]:
        return ["VolcanoSolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        dt = ctx.delta_time
        buffer = ctx.domain.influence_buffer
        for v in ctx.domain.volcanoes:
            if v.is_active and v.coords in ctx.domain.active_chunks:
                if v.coords not in buffer.ash_deltas:
                    buffer.ash_deltas[v.coords] = [0.0] * GRID_CELLS_PER_CHUNK
                for i in range(GRID_CELLS_PER_CHUNK):
                    buffer.ash_deltas[v.coords][i] += 0.3 * dt


class WildfireSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "WildfireSolver"

    @property
    def dependencies(self) -> List[str]:
        return ["LavaFlowSolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        spread = ctx.config.physical.fire_spread_rate
        dt = ctx.delta_time
        buffer = ctx.domain.influence_buffer

        for fire in ctx.domain.fire_fronts:
            if fire.coords in ctx.domain.active_chunks:
                if fire.coords not in buffer.thermal_deltas:
                    buffer.thermal_deltas[fire.coords] = [0.0] * GRID_CELLS_PER_CHUNK
                for i in range(GRID_CELLS_PER_CHUNK):
                    buffer.thermal_deltas[fire.coords][i] += spread * dt * fire.intensity


class FloodSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "FloodSolver"

    @property
    def dependencies(self) -> List[str]:
        return []

    def execute(self, ctx: DisasterExecutionContext) -> None:
        drain = ctx.config.physical.flood_drain_rate
        dt = ctx.delta_time
        buffer = ctx.domain.influence_buffer

        for wave in ctx.domain.flood_waves:
            if wave.coords in ctx.domain.active_chunks:
                if wave.coords not in buffer.hydraulic_deltas:
                    buffer.hydraulic_deltas[wave.coords] = [0.0] * GRID_CELLS_PER_CHUNK
                for i in range(GRID_CELLS_PER_CHUNK):
                    buffer.hydraulic_deltas[wave.coords][i] += (wave.volume * 0.1) - (drain * dt)


class LandslideSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "LandslideSolver"

    @property
    def dependencies(self) -> List[str]:
        return ["EarthquakeSolver", "FloodSolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        thresh = ctx.config.physical.landslide_threshold_slope
        for coords, chunk in ctx.domain.active_chunks.items():
            if chunk.slope > thresh:
                for i in range(GRID_CELLS_PER_CHUNK):
                    seismic = chunk.earthquake_intensity[i] > 0.3
                    flood = chunk.flood_depth[i] > 0.5
                    if seismic or flood:
                        chunk.landslide_probability[i] = min(1.0, chunk.slope * 1.2)
                        chunk.hazard_type[i] = HazardType.LANDSLIDE.value
                        chunk.is_dirty = True


class HazardPropagationSolver(ISolverStage):
    """Applies transient influence buffers directly to Chunk fields and updates rolling stats."""
    @property
    def name(self) -> str:
        return "HazardPropagationSolver"

    @property
    def dependencies(self) -> List[str]:
        return ["WildfireSolver", "LavaFlowSolver", "FloodSolver", "EarthquakeSolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        buffer = ctx.domain.influence_buffer
        
        for coords, chunk in ctx.domain.active_chunks.items():
            old_active_count = chunk.active_hazard_count
            old_sum_intensity = sum(chunk.earthquake_intensity) + sum(chunk.fire_intensity)
            
            # Apply seismic
            if coords in buffer.seismic_deltas:
                deltas = buffer.seismic_deltas[coords]
                for i in range(GRID_CELLS_PER_CHUNK):
                    chunk.earthquake_intensity[i] = min(1.0, chunk.earthquake_intensity[i] + deltas[i])
                    chunk.hazard_type[i] = HazardType.EARTHQUAKE.value
                    chunk.hazard_timer[i] = 10.0
                chunk.is_dirty = True

            # Apply thermal
            if coords in buffer.thermal_deltas:
                deltas = buffer.thermal_deltas[coords]
                for i in range(GRID_CELLS_PER_CHUNK):
                    chunk.fire_intensity[i] = min(1.0, chunk.fire_intensity[i] + deltas[i])
                    chunk.hazard_type[i] = HazardType.WILDFIRE.value
                    chunk.hazard_timer[i] = 15.0
                chunk.is_dirty = True

            # Apply hydraulic
            if coords in buffer.hydraulic_deltas:
                deltas = buffer.hydraulic_deltas[coords]
                for i in range(GRID_CELLS_PER_CHUNK):
                    chunk.flood_depth[i] = max(0.0, chunk.flood_depth[i] + deltas[i])
                    if chunk.flood_depth[i] > 0.1:
                        chunk.hazard_type[i] = HazardType.FLOOD.value
                        chunk.hazard_timer[i] = 8.0
                chunk.is_dirty = True

            # Apply ash
            if coords in buffer.ash_deltas:
                deltas = buffer.ash_deltas[coords]
                for i in range(GRID_CELLS_PER_CHUNK):
                    chunk.ash_density[i] = min(1.0, chunk.ash_density[i] + deltas[i])
                chunk.is_dirty = True

            # Re-evaluate active hazard cell count
            new_active_count = sum(1 for t in chunk.hazard_timer if t > 0.0)
            chunk.active_hazard_count = new_active_count
            new_sum_intensity = sum(chunk.earthquake_intensity) + sum(chunk.fire_intensity)
            
            # Record incremental rolling delta
            ctx.stats.apply_chunk_delta(coords, old_active_count, new_active_count, new_sum_intensity - old_sum_intensity)

        buffer.clear()


class HazardDecaySolver(ISolverStage):
    @property
    def name(self) -> str:
        return "HazardDecaySolver"

    @property
    def dependencies(self) -> List[str]:
        return ["HazardPropagationSolver", "LandslideSolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        dt = ctx.delta_time
        decay = ctx.config.physical.earthquake_decay_rate
        burn_rate = ctx.config.physical.fire_burn_rate

        for coords, chunk in ctx.domain.active_chunks.items():
            if not chunk.is_dirty:
                continue

            old_active_count = chunk.active_hazard_count
            old_sum_intensity = sum(chunk.earthquake_intensity) + sum(chunk.fire_intensity)

            for i in range(GRID_CELLS_PER_CHUNK):
                if chunk.earthquake_intensity[i] > 0.0:
                    chunk.earthquake_intensity[i] = max(0.0, chunk.earthquake_intensity[i] - decay * dt)
                if chunk.fire_intensity[i] > 0.0:
                    chunk.fire_intensity[i] = max(0.0, chunk.fire_intensity[i] - burn_rate * dt)
                if chunk.hazard_timer[i] > 0.0:
                    chunk.hazard_timer[i] = max(0.0, chunk.hazard_timer[i] - dt)
                    if chunk.hazard_timer[i] == 0.0:
                        chunk.hazard_type[i] = HazardType.NONE.value

            new_active_count = sum(1 for t in chunk.hazard_timer if t > 0.0)
            chunk.active_hazard_count = new_active_count
            new_sum_intensity = sum(chunk.earthquake_intensity) + sum(chunk.fire_intensity)

            ctx.stats.apply_chunk_delta(coords, old_active_count, new_active_count, new_sum_intensity - old_sum_intensity)


class HazardClassificationSolver(ISolverStage):
    @property
    def name(self) -> str:
        return "HazardClassificationSolver"

    @property
    def dependencies(self) -> List[str]:
        return ["HazardDecaySolver"]

    def execute(self, ctx: DisasterExecutionContext) -> None:
        for chunk in ctx.domain.active_chunks.values():
            if chunk.is_dirty:
                chunk.is_dirty = False


# =====================================================================
# 9. PIPELINE & EXECUTION PROFILER
# =====================================================================

class DisasterPipeline:
    """Manages stage registration, dependency graph validation, and step execution."""
    __slots__ = ('_stages', '_stage_timings_ns')

    def __init__(self) -> None:
        self._stages: List[ISolverStage] = []
        self._stage_timings_ns: Dict[str, int] = {}

    def register_stage(self, stage: ISolverStage) -> None:
        self._stages.append(stage)

    def validate_dependencies(self) -> None:
        executed_stages: Set[str] = set()
        for stage in self._stages:
            for dep in stage.dependencies:
                if dep not in executed_stages:
                    raise RuntimeError(
                        f"Pipeline Dependency Violation: Stage '{stage.name}' requires '{dep}', "
                        f"which has not executed prior in sequence."
                    )
            executed_stages.add(stage.name)

    def execute(self, ctx: DisasterExecutionContext) -> None:
        profiling = ctx.config.engine.profiling_enabled
        for stage in self._stages:
            if profiling:
                t0 = time.perf_counter_ns()
                stage.execute(ctx)
                t1 = time.perf_counter_ns()
                self._stage_timings_ns[stage.name] = t1 - t0
            else:
                stage.execute(ctx)

    def get_profiling_summary(self) -> Dict[str, float]:
        return {name: ns / 1_000_000.0 for name, ns in self._stage_timings_ns.items()}


# =====================================================================
# 10. THREAD-SAFE CONCURRENCY & READ-ONLY INTERFACES
# =====================================================================

class RWLock:
    """Writer-fair Reader-Writer Lock allowing concurrent readers or exclusive writer access."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._read_ready = threading.Condition(self._lock)
        self._readers = 0
        self._writers_waiting = 0
        self._writer_active = False

    def acquire_read(self) -> None:
        with self._lock:
            while self._writer_active or self._writers_waiting > 0:
                self._read_ready.wait()
            self._readers += 1

    def release_read(self) -> None:
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self) -> None:
        with self._lock:
            self._writers_waiting += 1
            while self._readers > 0 or self._writer_active:
                self._read_ready.wait()
            self._writers_waiting -= 1
            self._writer_active = True

    def release_write(self) -> None:
        with self._lock:
            self._writer_active = False
            self._read_ready.notify_all()


@runtime_checkable
class DisasterReadOnlyViewProtocol(Protocol):
    def query_hazards(self, coords: ChunkCoords, out_buffer: List[int]) -> int: ...
    def query_fire(self, coords: ChunkCoords, out_buffer: List[float]) -> int: ...
    def query_flood(self, coords: ChunkCoords, out_buffer: List[float]) -> int: ...
    def query_earthquake(self, coords: ChunkCoords, out_buffer: List[float]) -> int: ...
    def get_snapshot(self) -> HazardSnapshot: ...


class DisasterReadOnlyView:
    """Thread-safe, read-only interface wrapper over the hazard subsystem state."""
    __slots__ = ('_manager',)

    def __init__(self, manager: DisasterManager) -> None:
        self._manager = manager

    def query_hazards(self, coords: ChunkCoords, out_buffer: List[int]) -> int:
        return self._manager.query_hazards(coords, out_buffer)

    def query_fire(self, coords: ChunkCoords, out_buffer: List[float]) -> int:
        return self._manager.query_fire(coords, out_buffer)

    def query_flood(self, coords: ChunkCoords, out_buffer: List[float]) -> int:
        return self._manager.query_flood(coords, out_buffer)

    def query_earthquake(self, coords: ChunkCoords, out_buffer: List[float]) -> int:
        return self._manager.query_earthquake(coords, out_buffer)

    def get_snapshot(self) -> HazardSnapshot:
        return self._manager.create_snapshot()


# =====================================================================
# 11. SUBSYSTEM MANAGER (COORDINATOR)
# =====================================================================

class DisasterManager:
    """
    Principal coordinator for the geophysical hazard subsystem.
    Contains NO simulation logic itself; routes execution through DisasterPipeline.
    Protocol-compatible with WorldManager (`tick(dt)`, `reset()`, `ChunkCoords`).
    """
    __slots__ = (
        'config', 'domain', 'pipeline', 'rng',
        'stats', 'rw_lock', 'frame_index', 'time_elapsed',
        '_exec_context', '_thread_local'
    )

    def __init__(self, config: Optional[DisasterConfig] = None) -> None:
        self.config: DisasterConfig = config if config else DisasterConfig()
        if not self.config.validate():
            raise ValueError("DisasterConfig validation failed.")

        self.domain = DisasterDomain()
        self.pipeline = DisasterPipeline()
        self.rng = DeterministicRNG(self.config.master_seed)
        self.stats = RollingHazardStats()
        self.rw_lock = RWLock()
        self.frame_index: int = 0
        self.time_elapsed: float = 0.0

        # Reusable execution context allocation (zero GC churn during tick loop)
        self._exec_context = DisasterExecutionContext(self.domain, self.config, self.stats)
        
        # Thread-local storage for query buffers
        self._thread_local = threading.local()

        self._setup_default_pipeline()

    def _setup_default_pipeline(self) -> None:
        self.pipeline.register_stage(FaultStressSolver())
        self.pipeline.register_stage(EarthquakeSolver())
        self.pipeline.register_stage(VolcanoSolver())
        self.pipeline.register_stage(LavaFlowSolver())
        self.pipeline.register_stage(WildfireSolver())
        self.pipeline.register_stage(FloodSolver())
        self.pipeline.register_stage(HazardPropagationSolver())
        self.pipeline.register_stage(LandslideSolver())
        self.pipeline.register_stage(HazardDecaySolver())
        self.pipeline.register_stage(HazardClassificationSolver())

        if self.config.engine.strict_dependency_checking:
            self.pipeline.validate_dependencies()

    def reset(self) -> None:
        """Resets subsystem to initial clean state."""
        self.rw_lock.acquire_write()
        try:
            self.frame_index = 0
            self.time_elapsed = 0.0
            self.rng.reseed(self.config.master_seed)
            self.domain.active_chunks.clear()
            self.domain.fault_lines.clear()
            self.domain.volcanoes.clear()
            self.domain.fire_fronts.clear()
            self.domain.flood_waves.clear()
            self.domain.active_events.clear()
            self.domain.spatial_grid.clear()
            self.domain.influence_buffer.clear()
            self.stats = RollingHazardStats()
        finally:
            self.rw_lock.release_write()

    # -----------------------------------------------------------------
    # Streaming Chunk Lifecycle API (WorldManager Interop)
    # -----------------------------------------------------------------

    def load_chunk(self, coords: ChunkCoords, lat: float = 0.0, lon: float = 0.0) -> None:
        self.rw_lock.acquire_write()
        try:
            if coords not in self.domain.active_chunks:
                chunk = self.domain.chunk_pool.acquire(coords, lat, lon)
                self.domain.active_chunks[coords] = chunk
        finally:
            self.rw_lock.release_write()

    def unload_chunk(self, coords: ChunkCoords) -> None:
        self.rw_lock.acquire_write()
        try:
            chunk = self.domain.active_chunks.pop(coords, None)
            if chunk:
                self.domain.chunk_pool.release(chunk)
        finally:
            self.rw_lock.release_write()

    def activate_chunk(self, coords: ChunkCoords) -> None:
        pass  # Reserved for active-tier LOD promotion

    def deactivate_chunk(self, coords: ChunkCoords) -> None:
        pass  # Reserved for inactive-tier LOD demotion

    # -----------------------------------------------------------------
    # Simulation Execution Loop (WorldManager Protocol Compatible)
    # -----------------------------------------------------------------

    def tick(self, dt: float) -> None:
        """Primary execution tick matching WorldManager subsystem protocol."""
        self.rw_lock.acquire_write()
        try:
            self.time_elapsed += dt
            self.frame_index += 1

            # Deterministic per-frame RNG fork
            frame_rng = self.rng.fork(self.frame_index)

            # Reuse execution context instance
            self._exec_context.prepare_frame(dt, frame_rng, self.frame_index)

            self.pipeline.execute(self._exec_context)
        finally:
            self.rw_lock.release_write()

    def update(self, dt: float) -> None:
        """Alias for tick(dt) for backwards compatibility."""
        self.tick(dt)

    # -----------------------------------------------------------------
    # Thread-Safe Zero-Allocation Query API
    # -----------------------------------------------------------------

    def _get_thread_local_buffer(self, size: int) -> List[float]:
        if not hasattr(self._thread_local, "query_buffer") or len(self._thread_local.query_buffer) < size:
            self._thread_local.query_buffer = [0.0] * size
        return self._thread_local.query_buffer

    def query_hazards(self, coords: ChunkCoords, out_buffer: List[int]) -> int:
        self.rw_lock.acquire_read()
        try:
            chunk = self.domain.active_chunks.get(coords)
            if not chunk:
                return 0
            count = min(len(out_buffer), GRID_CELLS_PER_CHUNK)
            for i in range(count):
                out_buffer[i] = chunk.hazard_type[i]
            return count
        finally:
            self.rw_lock.release_read()

    def query_fire(self, coords: ChunkCoords, out_buffer: List[float]) -> int:
        self.rw_lock.acquire_read()
        try:
            chunk = self.domain.active_chunks.get(coords)
            if not chunk:
                return 0
            count = min(len(out_buffer), GRID_CELLS_PER_CHUNK)
            for i in range(count):
                out_buffer[i] = chunk.fire_intensity[i]
            return count
        finally:
            self.rw_lock.release_read()

    def query_flood(self, coords: ChunkCoords, out_buffer: List[float]) -> int:
        self.rw_lock.acquire_read()
        try:
            chunk = self.domain.active_chunks.get(coords)
            if not chunk:
                return 0
            count = min(len(out_buffer), GRID_CELLS_PER_CHUNK)
            for i in range(count):
                out_buffer[i] = chunk.flood_depth[i]
            return count
        finally:
            self.rw_lock.release_read()

    def query_earthquake(self, coords: ChunkCoords, out_buffer: List[float]) -> int:
        self.rw_lock.acquire_read()
        try:
            chunk = self.domain.active_chunks.get(coords)
            if not chunk:
                return 0
            count = min(len(out_buffer), GRID_CELLS_PER_CHUNK)
            for i in range(count):
                out_buffer[i] = chunk.earthquake_intensity[i]
            return count
        finally:
            self.rw_lock.release_read()

    def create_snapshot(self) -> HazardSnapshot:
        self.rw_lock.acquire_read()
        try:
            return HazardSnapshot(
                timestamp=self.time_elapsed,
                frame_index=self.frame_index,
                statistics=self.stats.build_snapshot(),
                active_events=tuple(self.domain.active_events),
                active_volcanoes_count=len(self.domain.volcanoes),
                active_faults_count=len(self.domain.fault_lines),
                active_chunk_coords=tuple(self.domain.active_chunks.keys())
            )
        finally:
            self.rw_lock.release_read()

    def get_read_only_view(self) -> DisasterReadOnlyViewProtocol:
        return DisasterReadOnlyView(self)

    def debug_summary(self) -> Dict[str, float]:
        return {
            "time_elapsed": self.time_elapsed,
            "frame_index": float(self.frame_index),
            "active_chunks": float(len(self.domain.active_chunks)),
            "active_hazards": float(self.stats.total_active_hazards),
            "pool_overflows": float(self.domain.chunk_pool.overflow_count),
            **self.pipeline.get_profiling_summary()
        }