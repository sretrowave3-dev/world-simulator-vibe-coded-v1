"""
Master World Coordinator for the Echo Evolution Simulator.

Coordinates spatial chunk registries, spatial bounds, deterministic seed derivation,
environment context queries, and event broadcasting without executing simulation pipeline
algorithms directly.
"""

from __future__ import annotations

import collections
import logging
import math
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Callable,
    Dict,
    Final,
    FrozenSet,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeAlias,
    runtime_checkable,
)

logger: logging.Logger = logging.getLogger(__name__)

ChunkCoords: TypeAlias = Tuple[int, int]
WorldCoords: TypeAlias = Tuple[float, float]

ENGINE_WORLD_NAMESPACE: Final[uuid.UUID] = uuid.UUID("e716e25f-256d-4b82-9383-e18e1b000000")


# ============================================================================
# DETERMINISTIC HASHING & RNG
# ============================================================================


def deterministic_chunk_hash(world_seed: int, chunk_x: int, chunk_y: int) -> int:
    """
    Cross-platform 64-bit integer mix hash (Murmur3/SplitMix style).
    
    Guarantees bitwise-identical chunk seed derivation across OS platform runs
    independent of Python's runtime hash seed randomization.
    """
    h = (world_seed & 0xFFFFFFFFFFFFFFFF) ^ (chunk_x * 0x9E3779B97F4A7C15 & 0xFFFFFFFFFFFFFFFF)
    h = (h ^ (chunk_y * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF
    h = (h ^ (h >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    h = (h ^ (h >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    h = h ^ (h >> 31)
    return h & 0x7FFFFFFF


def generate_deterministic_world_uuid(seed: int) -> str:
    """Generate a deterministic UUID string based on the world seed."""
    return str(uuid.uuid5(ENGINE_WORLD_NAMESPACE, f"world_seed_{seed}"))


class DeterministicRNG:
    """Engine-wide 64-bit SplitMix-based deterministic random number generator."""

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        self._state: int = seed & 0xFFFFFFFFFFFFFFFF

    def next_uint32(self) -> int:
        """Generate next uint32 in sequence."""
        self._state = (self._state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self._state
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) >> 32

    def next_float(self) -> float:
        """Generate float in range [0.0, 1.0)."""
        return self.next_uint32() / 4294967296.0


# ============================================================================
# READ-WRITE SYNCHRONIZATION (WRITER-FAIR)
# ============================================================================


class WriterFairReaderWriterLock:
    """
    Writer-fair Reader-Writer Lock to prevent writer starvation during heavy read workloads.
    
    When writers are waiting, arriving readers block until pending writers acquire and release
    the lock.
    """

    def __init__(self) -> None:
        self._cond = threading.Condition(threading.Lock())
        self._readers = 0
        self._writers = 0
        self._writers_waiting = 0

    def acquire_read(self) -> None:
        with self._cond:
            while self._writers > 0 or self._writers_waiting > 0:
                self._cond.wait()
            self._readers += 1

    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    def acquire_write(self) -> None:
        with self._cond:
            self._writers_waiting += 1
            while self._writers > 0 or self._readers > 0:
                self._cond.wait()
            self._writers_waiting -= 1
            self._writers += 1

    def release_write(self) -> None:
        with self._cond:
            self._writers -= 1
            self._cond.notify_all()


# ============================================================================
# ENUMS & EVENTS
# ============================================================================


class ChunkState(Enum):
    """Lifecycle states for spatial chunks in the streaming registry."""

    UNLOADED = auto()
    QUEUED_FOR_LOAD = auto()
    LOADING = auto()
    LOADED = auto()
    ACTIVE = auto()
    INACTIVE = auto()
    UNLOADING = auto()


class WorldState(Enum):
    """Lifecycle states for the WorldManager state machine."""

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    PAUSED = auto()
    SHUTDOWN = auto()


class WorldEventType(Enum):
    """Event types emitted through the system event dispatcher."""

    CHUNK_LOADED = "world.chunk_loaded"
    CHUNK_UNLOADED = "world.chunk_unloaded"
    CHUNK_ACTIVATED = "world.chunk_activated"
    CHUNK_DEACTIVATED = "world.chunk_deactivated"
    WORLD_GENERATED = "world.generated"
    WORLD_RESET = "world.reset"


# ============================================================================
# EXCEPTIONS
# ============================================================================


class WorldException(Exception):
    """Base exception class for world domain errors."""

    pass


class InvalidLifecycleTransitionError(WorldException):
    """Raised when an operation is requested that violates current WorldState."""

    pass


class InvalidChunkCoordinatesError(WorldException):
    """Raised when chunk coordinates fall outside valid operational bounds."""

    pass


class MissingSubsystemError(WorldException):
    """Raised when a required environmental subsystem protocol is missing or invalid."""

    pass


# ============================================================================
# SUBSYSTEM & EVENT PROTOCOLS
# ============================================================================


@runtime_checkable
class EventDispatcherProtocol(Protocol):
    """Protocol for engine-wide event publishing."""

    def dispatch(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event with payload to subscribed handlers."""
        ...


@runtime_checkable
class TerrainReadOnlyViewProtocol(Protocol):
    """Protocol for read-only access to terrain data."""

    def get_elevation_grid(self) -> Any: ...


@runtime_checkable
class WeatherReadOnlyViewProtocol(Protocol):
    """Protocol for read-only access to weather/climate data."""

    def get_climate_grid(self) -> Any: ...


@runtime_checkable
class FoodReadOnlyViewProtocol(Protocol):
    """Protocol for read-only access to food biomass data."""

    def get_biomass_grid(self) -> Any: ...


@runtime_checkable
class DisasterReadOnlyViewProtocol(Protocol):
    """Protocol for read-only access to hazard maps."""

    def get_hazard_grid(self) -> Any: ...


@runtime_checkable
class TerrainManagerProtocol(Protocol):
    """Protocol defining the required interface for the TerrainManager subsystem."""

    def tick(self, dt: float) -> None: ...
    def query_elevation(self, x: float, y: float) -> float: ...
    def query_biome(self, x: float, y: float) -> int: ...
    def load_chunk(self, chunk_x: int, chunk_y: int, seed: int) -> None: ...
    def unload_chunk(self, chunk_x: int, chunk_y: int) -> None: ...
    def get_read_only_view(self) -> TerrainReadOnlyViewProtocol: ...
    def reset(self) -> None: ...


@runtime_checkable
class WeatherManagerProtocol(Protocol):
    """Protocol defining the required interface for the WeatherManager subsystem."""

    def tick(self, dt: float) -> None: ...
    def query_climate(self, x: float, y: float) -> Tuple[float, float, float]: ...
    def get_read_only_view(self) -> WeatherReadOnlyViewProtocol: ...
    def reset(self) -> None: ...


@runtime_checkable
class FoodManagerProtocol(Protocol):
    """Protocol defining the required interface for the FoodManager subsystem."""

    def tick(self, dt: float) -> None: ...
    def query_food_density(self, x: float, y: float) -> float: ...
    def load_chunk(self, chunk_x: int, chunk_y: int) -> None: ...
    def unload_chunk(self, chunk_x: int, chunk_y: int) -> None: ...
    def get_read_only_view(self) -> FoodReadOnlyViewProtocol: ...
    def reset(self) -> None: ...


@runtime_checkable
class DisasterManagerProtocol(Protocol):
    """Protocol defining the required interface for the DisasterManager subsystem."""

    def tick(self, dt: float) -> None: ...
    def query_hazards(self, x: float, y: float) -> float: ...
    def get_read_only_view(self) -> DisasterReadOnlyViewProtocol: ...
    def reset(self) -> None: ...


# ============================================================================
# DATACLASSES
# ============================================================================


@dataclass(slots=True, frozen=True)
class WorldConfig:
    """Immutable global world configuration parameters."""

    width: float
    length: float
    min_height: float
    max_height: float
    chunk_size: float
    seed: int
    streaming_radius: int = 2
    max_loaded_chunks: int = 1024
    max_chunk_loads_per_frame: int = 8

    def __post_init__(self) -> None:
        if self.width <= 0.0 or self.length <= 0.0:
            raise ValueError(f"World dimensions must be positive. Got ({self.width}, {self.length})")
        if self.min_height >= self.max_height:
            raise ValueError(f"min_height ({self.min_height}) must be strictly less than max_height ({self.max_height})")
        if self.chunk_size <= 0.0:
            raise ValueError(f"chunk_size must be positive. Got {self.chunk_size}")
        if self.streaming_radius < 0:
            raise ValueError(f"streaming_radius must be non-negative. Got {self.streaming_radius}")

    @property
    def max_chunk_x(self) -> int:
        return max(0, math.ceil(self.width / self.chunk_size) - 1)

    @property
    def max_chunk_y(self) -> int:
        return max(0, math.ceil(self.length / self.chunk_size) - 1)


@dataclass(slots=True)
class ChunkMetadata:
    """
    Spatial metadata and lifecycle tracking for a single chunk.
    Does not store population, entities, or cached environment data.
    """

    chunk_id: str
    coords: ChunkCoords
    state: ChunkState = ChunkState.UNLOADED
    dirty: bool = False
    version: int = 0
    last_access_timestamp: float = 0.0

    def mark_dirty(self) -> None:
        self.dirty = True
        self.version += 1

    def touch(self, current_time: float) -> None:
        self.last_access_timestamp = current_time


@dataclass(slots=True)
class EnvironmentContext:
    """Point environmental query container."""

    x: float = 0.0
    y: float = 0.0
    elevation: float = 0.0
    biome_id: int = 0
    temperature: float = 0.0
    precipitation: float = 0.0
    wind_speed: float = 0.0
    hazard_intensity: float = 0.0
    food_density: float = 0.0
    is_valid: bool = False

    def reset(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.elevation = 0.0
        self.biome_id = 0
        self.temperature = 0.0
        self.precipitation = 0.0
        self.wind_speed = 0.0
        self.hazard_intensity = 0.0
        self.food_density = 0.0
        self.is_valid = False


@dataclass(slots=True, frozen=True)
class WorldMetadata:
    """Immutable metadata snapshot of the world instance."""

    world_uuid: str
    seed: int
    dimensions: Tuple[float, float, float, float]
    chunk_size: float
    total_chunks_in_grid: int


@dataclass(slots=True, frozen=True)
class WorldStatistics:
    """World subsystem operational metrics."""

    world_uuid: str
    state: WorldState
    unloaded_chunks: int
    queued_chunks: int
    loaded_chunks: int
    active_chunks: int
    total_registered_chunks: int


@dataclass(slots=True, frozen=True)
class WorldSnapshot:
    """Thread-safe snapshot exposing read-only subsystem views."""

    world_uuid: str
    seed: int
    bounds: Tuple[float, float, float, float]
    loaded_chunks: FrozenSet[ChunkCoords]
    active_chunks: FrozenSet[ChunkCoords]
    metadata: WorldMetadata
    terrain_view: TerrainReadOnlyViewProtocol
    weather_view: WeatherReadOnlyViewProtocol
    food_view: FoodReadOnlyViewProtocol
    disaster_view: DisasterReadOnlyViewProtocol


# ============================================================================
# MASTER WORLD COORDINATOR
# ============================================================================


class WorldManager:
    """
    Master World Coordinator for Echo Evolution Simulator.
    
    Manages spatial chunking, deterministic seed generation, environmental context queries,
    and event broadcasting. Ticking of individual subsystems is driven by simulation.py.
    """

    def __init__(
        self,
        config: WorldConfig,
        terrain_manager: TerrainManagerProtocol,
        weather_manager: WeatherManagerProtocol,
        food_manager: FoodManagerProtocol,
        disaster_manager: DisasterManagerProtocol,
        event_dispatcher: Optional[EventDispatcherProtocol] = None,
    ) -> None:
        if not isinstance(terrain_manager, TerrainManagerProtocol):
            raise MissingSubsystemError("terrain_manager does not satisfy TerrainManagerProtocol")
        if not isinstance(weather_manager, WeatherManagerProtocol):
            raise MissingSubsystemError("weather_manager does not satisfy WeatherManagerProtocol")
        if not isinstance(food_manager, FoodManagerProtocol):
            raise MissingSubsystemError("food_manager does not satisfy FoodManagerProtocol")
        if not isinstance(disaster_manager, DisasterManagerProtocol):
            raise MissingSubsystemError("disaster_manager does not satisfy DisasterManagerProtocol")

        self._config: Final[WorldConfig] = config
        self._world_uuid: Final[str] = generate_deterministic_world_uuid(config.seed)

        self._terrain: Final[TerrainManagerProtocol] = terrain_manager
        self._weather: Final[WeatherManagerProtocol] = weather_manager
        self._food: Final[FoodManagerProtocol] = food_manager
        self._disasters: Final[DisasterManagerProtocol] = disaster_manager
        self._event_dispatcher: Final[Optional[EventDispatcherProtocol]] = event_dispatcher

        self._state: WorldState = WorldState.UNINITIALIZED
        self._state_lock: Final[threading.RLock] = threading.RLock()
        self._rw_lock: Final[WriterFairReaderWriterLock] = WriterFairReaderWriterLock()

        self._rng: Final[DeterministicRNG] = DeterministicRNG(config.seed)

        self._chunk_registry: Final[Dict[ChunkCoords, ChunkMetadata]] = {}
        self._loaded_chunks: Final[Set[ChunkCoords]] = set()
        self._active_chunks: Final[Set[ChunkCoords]] = set()
        self._load_queue: Final[collections.deque[ChunkCoords]] = collections.deque()

        # Thread-local storage for zero-allocation point queries
        self._tls: Final[threading.local] = threading.local()

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------

    @property
    def world_uuid(self) -> str:
        return self._world_uuid

    @property
    def seed(self) -> int:
        return self._config.seed

    @property
    def state(self) -> WorldState:
        with self._state_lock:
            return self._state

    @property
    def config(self) -> WorldConfig:
        return self._config

    # ------------------------------------------------------------------------
    # Spatial Coordinate Conversions & Hash Generation
    # ------------------------------------------------------------------------

    def world_to_chunk(self, x: float, y: float) -> ChunkCoords:
        return (
            int(math.floor(x / self._config.chunk_size)),
            int(math.floor(y / self._config.chunk_size)),
        )

    def chunk_to_world(self, chunk_x: int, chunk_y: int) -> WorldCoords:
        return (
            float(chunk_x) * self._config.chunk_size,
            float(chunk_y) * self._config.chunk_size,
        )

    def is_within_bounds(self, x: float, y: float) -> bool:
        return 0.0 <= x <= self._config.width and 0.0 <= y <= self._config.length

    def is_valid_chunk_coord(self, chunk_x: int, chunk_y: int) -> bool:
        return 0 <= chunk_x <= self._config.max_chunk_x and 0 <= chunk_y <= self._config.max_chunk_y

    def get_chunk_seed(self, chunk_x: int, chunk_y: int) -> int:
        return deterministic_chunk_hash(self._config.seed, chunk_x, chunk_y)

    # ------------------------------------------------------------------------
    # Lifecycle Operations
    # ------------------------------------------------------------------------

    def initialize(self) -> None:
        with self._state_lock:
            if self._state != WorldState.UNINITIALIZED:
                raise InvalidLifecycleTransitionError(
                    f"Cannot initialize WorldManager from state {self._state.name}"
                )
            self._state = WorldState.INITIALIZING
            logger.info("Initializing WorldManager [%s]...", self._world_uuid)

            self.clear_world()
            self._terrain.reset()
            self._weather.reset()
            self._food.reset()
            self._disasters.reset()

            self._state = WorldState.INITIALIZED

    def generate_world(self) -> None:
        with self._state_lock:
            if self._state not in (WorldState.INITIALIZED, WorldState.PAUSED):
                raise InvalidLifecycleTransitionError(
                    f"Cannot generate world from state {self._state.name}"
                )

            center_x = self._config.width / 2.0
            center_y = self._config.length / 2.0
            self.stream_chunks(center_x, center_y)
            self.process_streaming_queue(budget=self._config.max_loaded_chunks)

            self._dispatch_event(WorldEventType.WORLD_GENERATED, {"uuid": self._world_uuid})

    def pause(self) -> None:
        with self._state_lock:
            if self._state == WorldState.RUNNING:
                self._state = WorldState.PAUSED

    def resume(self) -> None:
        with self._state_lock:
            if self._state in (WorldState.INITIALIZED, WorldState.PAUSED):
                self._state = WorldState.RUNNING

    def reset(self) -> None:
        with self._state_lock:
            self.clear_world()
            self._terrain.reset()
            self._weather.reset()
            self._food.reset()
            self._disasters.reset()
            self._state = WorldState.INITIALIZED
            self._dispatch_event(WorldEventType.WORLD_RESET, {"uuid": self._world_uuid})

    def shutdown(self) -> None:
        with self._state_lock:
            if self._state == WorldState.SHUTDOWN:
                return
            self.clear_world()
            self._state = WorldState.SHUTDOWN

    def clear_world(self) -> None:
        self._rw_lock.acquire_write()
        try:
            for coords in list(self._loaded_chunks):
                self._unload_chunk_internal(coords[0], coords[1])

            self._chunk_registry.clear()
            self._loaded_chunks.clear()
            self._active_chunks.clear()
            self._load_queue.clear()
        finally:
            self._rw_lock.release_write()

    # ------------------------------------------------------------------------
    # Frame Lifecycle & Pipeline Synchronization Hooks
    # ------------------------------------------------------------------------

    def begin_frame(self) -> None:
        """World-level bookkeeping executed prior to subsystem pipeline ticks."""
        self.process_streaming_queue()

    def end_frame(self) -> None:
        """World-level post-frame cleanup or snapshot syncing hooks."""
        pass

    def tick_terrain(self, dt: float) -> None:
        self._terrain.tick(dt)

    def tick_weather(self, dt: float) -> None:
        self._weather.tick(dt)

    def tick_food(self, dt: float) -> None:
        self._food.tick(dt)

    def tick_disasters(self, dt: float) -> None:
        self._disasters.tick(dt)

    # ------------------------------------------------------------------------
    # Spatial Chunk Management & Queued Streaming
    # ------------------------------------------------------------------------

    def is_chunk_loaded(self, chunk_x: int, chunk_y: int) -> bool:
        self._rw_lock.acquire_read()
        try:
            return (chunk_x, chunk_y) in self._loaded_chunks
        finally:
            self._rw_lock.release_read()

    def is_chunk_active(self, chunk_x: int, chunk_y: int) -> bool:
        self._rw_lock.acquire_read()
        try:
            return (chunk_x, chunk_y) in self._active_chunks
        finally:
            self._rw_lock.release_read()

    def load_chunk_immediate(self, chunk_x: int, chunk_y: int) -> None:
        """Immediately load chunk synchronously."""
        if not self.is_valid_chunk_coord(chunk_x, chunk_y):
            raise InvalidChunkCoordinatesError(f"Chunk ({chunk_x}, {chunk_y}) out of bounds.")

        self._rw_lock.acquire_write()
        try:
            self._load_chunk_internal(chunk_x, chunk_y)
        finally:
            self._rw_lock.release_write()

    def _load_chunk_internal(self, chunk_x: int, chunk_y: int) -> None:
        coords = (chunk_x, chunk_y)
        metadata = self._chunk_registry.get(coords)

        if metadata is None:
            metadata = ChunkMetadata(chunk_id=f"c_{chunk_x}_{chunk_y}", coords=coords)
            self._chunk_registry[coords] = metadata

        if metadata.state in (ChunkState.LOADED, ChunkState.ACTIVE):
            return

        metadata.state = ChunkState.LOADING
        chunk_seed = self.get_chunk_seed(chunk_x, chunk_y)

        self._terrain.load_chunk(chunk_x, chunk_y, chunk_seed)
        self._food.load_chunk(chunk_x, chunk_y)

        metadata.state = ChunkState.LOADED
        self._loaded_chunks.add(coords)

        self._dispatch_event(
            WorldEventType.CHUNK_LOADED,
            {"coords": coords, "seed": chunk_seed},
        )

    def unload_chunk(self, chunk_x: int, chunk_y: int) -> None:
        self._rw_lock.acquire_write()
        try:
            self._unload_chunk_internal(chunk_x, chunk_y)
        finally:
            self._rw_lock.release_write()

    def _unload_chunk_internal(self, chunk_x: int, chunk_y: int) -> None:
        coords = (chunk_x, chunk_y)
        metadata = self._chunk_registry.get(coords)
        if metadata is None or metadata.state == ChunkState.UNLOADED:
            return

        if metadata.state == ChunkState.ACTIVE:
            self._deactivate_chunk_internal(chunk_x, chunk_y)

        metadata.state = ChunkState.UNLOADING

        self._food.unload_chunk(chunk_x, chunk_y)
        self._terrain.unload_chunk(chunk_x, chunk_y)

        metadata.state = ChunkState.UNLOADED
        self._loaded_chunks.discard(coords)

        self._dispatch_event(
            WorldEventType.CHUNK_UNLOADED,
            {"coords": coords},
        )

    def activate_chunk(self, chunk_x: int, chunk_y: int) -> None:
        self._rw_lock.acquire_write()
        try:
            coords = (chunk_x, chunk_y)
            if coords not in self._loaded_chunks:
                self._load_chunk_internal(chunk_x, chunk_y)

            metadata = self._chunk_registry[coords]
            metadata.state = ChunkState.ACTIVE
            self._active_chunks.add(coords)

            self._dispatch_event(
                WorldEventType.CHUNK_ACTIVATED,
                {"coords": coords},
            )
        finally:
            self._rw_lock.release_write()

    def deactivate_chunk(self, chunk_x: int, chunk_y: int) -> None:
        self._rw_lock.acquire_write()
        try:
            self._deactivate_chunk_internal(chunk_x, chunk_y)
        finally:
            self._rw_lock.release_write()

    def _deactivate_chunk_internal(self, chunk_x: int, chunk_y: int) -> None:
        coords = (chunk_x, chunk_y)
        if coords in self._active_chunks:
            self._active_chunks.remove(coords)
            metadata = self._chunk_registry.get(coords)
            if metadata:
                metadata.state = ChunkState.INACTIVE

            self._dispatch_event(
                WorldEventType.CHUNK_DEACTIVATED,
                {"coords": coords},
            )

    def stream_chunks(self, focus_x: float, focus_y: float) -> None:
        """Queue chunks around focus for incremental loading using deque."""
        if not self.is_within_bounds(focus_x, focus_y):
            return

        center_chunk = self.world_to_chunk(focus_x, focus_y)
        radius = self._config.streaming_radius

        min_cx = max(0, center_chunk[0] - radius)
        max_cx = min(self._config.max_chunk_x, center_chunk[0] + radius)
        min_cy = max(0, center_chunk[1] - radius)
        max_cy = min(self._config.max_chunk_y, center_chunk[1] + radius)

        self._rw_lock.acquire_write()
        try:
            target_active: Set[ChunkCoords] = set()
            for cx in range(min_cx, max_cx + 1):
                for cy in range(min_cy, max_cy + 1):
                    coords = (cx, cy)
                    target_active.add(coords)

                    metadata = self._chunk_registry.get(coords)
                    if metadata is None:
                        metadata = ChunkMetadata(chunk_id=f"c_{cx}_{cy}", coords=coords)
                        self._chunk_registry[coords] = metadata

                    if metadata.state == ChunkState.UNLOADED:
                        metadata.state = ChunkState.QUEUED_FOR_LOAD
                        self._load_queue.append(coords)

            currently_active = set(self._active_chunks)
            for cx, cy in currently_active - target_active:
                self._deactivate_chunk_internal(cx, cy)

            for cx, cy in target_active:
                if (cx, cy) in self._loaded_chunks:
                    self._deactivate_chunk_internal(cx, cy) if False else None
                    metadata = self._chunk_registry[(cx, cy)]
                    if metadata.state != ChunkState.ACTIVE:
                        metadata.state = ChunkState.ACTIVE
                        self._active_chunks.add((cx, cy))
        finally:
            self._rw_lock.release_write()

    def process_streaming_queue(self, budget: Optional[int] = None) -> int:
        """Process queued chunk loading up to frame budget limits in O(1) time per chunk."""
        limit = budget if budget is not None else self._config.max_chunk_loads_per_frame
        processed = 0

        self._rw_lock.acquire_write()
        try:
            while self._load_queue and processed < limit:
                coords = self._load_queue.popleft()
                if coords not in self._loaded_chunks:
                    self._load_chunk_internal(coords[0], coords[1])
                    coords_meta = self._chunk_registry[coords]
                    coords_meta.state = ChunkState.ACTIVE
                    self._active_chunks.add(coords)
                    processed += 1
            return processed
        finally:
            self._rw_lock.release_write()

    # ------------------------------------------------------------------------
    # Thread-Safe Environmental Context Query Interface
    # ------------------------------------------------------------------------

    def get_environment(
        self, x: float, y: float, out_context: Optional[EnvironmentContext] = None
    ) -> EnvironmentContext:
        """
        Query environmental point features using thread-local storage or custom buffer.
        Optimized for concurrent parallel worker threads.
        """
        if out_context is not None:
            ctx = out_context
        else:
            if not hasattr(self._tls, "context"):
                self._tls.context = EnvironmentContext()
            ctx = self._tls.context

        ctx.reset()

        if not self.is_within_bounds(x, y):
            ctx.is_valid = False
            return ctx

        self._rw_lock.acquire_read()
        try:
            ctx.x = x
            ctx.y = y
            ctx.elevation = self._terrain.query_elevation(x, y)
            ctx.biome_id = self._terrain.query_biome(x, y)

            temp, precip, wind = self._weather.query_climate(x, y)
            ctx.temperature = temp
            ctx.precipitation = precip
            ctx.wind_speed = wind

            ctx.hazard_intensity = self._disasters.query_hazards(x, y)
            ctx.food_density = self._food.query_food_density(x, y)
            ctx.is_valid = True
            return ctx
        finally:
            self._rw_lock.release_read()

    # ------------------------------------------------------------------------
    # Internal Event Helper
    # ------------------------------------------------------------------------

    def _dispatch_event(self, event_type: WorldEventType, payload: Dict[str, Any]) -> None:
        if self._event_dispatcher is not None:
            self._event_dispatcher.dispatch(event_type.value, payload)

    # ------------------------------------------------------------------------
    # Statistics & Immutable Snapshots
    # ------------------------------------------------------------------------

    def get_statistics(self) -> WorldStatistics:
        self._rw_lock.acquire_read()
        try:
            counts = {state: 0 for state in ChunkState}
            for metadata in self._chunk_registry.values():
                counts[metadata.state] += 1

            return WorldStatistics(
                world_uuid=self._world_uuid,
                state=self.state,
                unloaded_chunks=counts[ChunkState.UNLOADED],
                queued_chunks=counts[ChunkState.QUEUED_FOR_LOAD],
                loaded_chunks=len(self._loaded_chunks),
                active_chunks=len(self._active_chunks),
                total_registered_chunks=len(self._chunk_registry),
            )
        finally:
            self._rw_lock.release_read()

    def get_snapshot(self) -> WorldSnapshot:
        """Generate a thread-safe snapshot exposing read-only subsystem views."""
        self._rw_lock.acquire_read()
        try:
            bounds = (0.0, self._config.width, 0.0, self._config.length)

            metadata = WorldMetadata(
                world_uuid=self._world_uuid,
                seed=self._config.seed,
                dimensions=(
                    self._config.width,
                    self._config.length,
                    self._config.min_height,
                    self._config.max_height,
                ),
                chunk_size=self._config.chunk_size,
                total_chunks_in_grid=(self._config.max_chunk_x + 1) * (self._config.max_chunk_y + 1),
            )

            return WorldSnapshot(
                world_uuid=self._world_uuid,
                seed=self._config.seed,
                bounds=bounds,
                loaded_chunks=frozenset(self._loaded_chunks),
                active_chunks=frozenset(self._active_chunks),
                metadata=metadata,
                terrain_view=self._terrain.get_read_only_view(),
                weather_view=self._weather.get_read_only_view(),
                food_view=self._food.get_read_only_view(),
                disaster_view=self._disasters.get_read_only_view(),
            )
        finally:
            self._rw_lock.release_read()