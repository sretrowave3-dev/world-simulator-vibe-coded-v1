"""
Echo Evolution Simulator — Master Simulation Orchestrator (`simulation.py`)
===========================================================================

This module serves as the pure master simulation orchestrator for the Echo Evolution
Simulator. It owns the main simulation loop, controls high-precision execution timing,
manages thread-safe simulation state transitions, and enforces the deterministic pipeline
execution order across all registered engine subsystems.

Architectural Guarantees:
  • ZERO Domain Logic: Pure coordination, lifecycle management, and timing mechanics.
  • Strict Fixed Timestep Pipeline: Execution order strictly matches ARCHITECTURE.md.
  • Zero Allocations in Tick Loop: Pre-allocated timing contexts and profile buffers.
  • Decoupled Variable Rendering & Sync: Exposes interpolation alpha for smooth frames.
  • Production-Grade State Machine: Thread-safe, validated lifecycle management.

Python Version: 3.13+
"""

from __future__ import annotations

import collections
import enum
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    List,
    Protocol,
    Tuple,
    TypeAlias,
    runtime_checkable,
)

# Setup module logger
logger = logging.getLogger("EchoEvolution.Simulation")


# ============================================================================
# 1. PIPELINE STAGES & PROTOCOLS
# ============================================================================

@enum.unique
class PipelineStage(enum.Enum):
    """Enumeration of the frozen simulation execution order."""
    TIME = "Time"
    WEATHER = "Weather"
    DISASTERS = "Disasters"
    TERRAIN = "Terrain"
    PLANTS = "Plants"
    FOOD = "Food"
    PERCEPTION = "Perception"
    BRAIN = "Brain"
    DECISION = "Decision"
    MOVEMENT = "Movement"
    COMBAT = "Combat"
    DIGESTION = "Digestion"
    LEARNING = "Learning"
    GEMINI = "Gemini"
    REPRODUCTION = "Reproduction"
    MUTATION = "Mutation"
    SPECIES = "Species"
    CIVILIZATION = "Civilization"
    KNOWLEDGE = "Knowledge"
    EVENTS = "Events"
    STATISTICS = "Statistics"
    RENDERER_SYNC = "Renderer Sync"
    AUTOSAVE = "Autosave"


# Exact frozen pipeline sequence tuple using Enum safety
FROZEN_EXECUTION_ORDER: Final[Tuple[PipelineStage, ...]] = (
    PipelineStage.TIME,
    PipelineStage.WEATHER,
    PipelineStage.DISASTERS,
    PipelineStage.TERRAIN,
    PipelineStage.PLANTS,
    PipelineStage.FOOD,
    PipelineStage.PERCEPTION,
    PipelineStage.BRAIN,
    PipelineStage.DECISION,
    PipelineStage.MOVEMENT,
    PipelineStage.COMBAT,
    PipelineStage.DIGESTION,
    PipelineStage.LEARNING,
    PipelineStage.GEMINI,
    PipelineStage.REPRODUCTION,
    PipelineStage.MUTATION,
    PipelineStage.SPECIES,
    PipelineStage.CIVILIZATION,
    PipelineStage.KNOWLEDGE,
    PipelineStage.EVENTS,
    PipelineStage.STATISTICS,
    PipelineStage.RENDERER_SYNC,
    PipelineStage.AUTOSAVE,
)


@runtime_checkable
class SystemProtocol(Protocol):
    """Structural interface that all engine subsystems must satisfy."""

    def initialize(self) -> None:
        """Initializes system internal resources."""
        ...

    def tick(self, dt: float, sim_time: float, tick_count: int) -> None:
        ...

    def reset(self) -> None:
        ...

    def shutdown(self) -> None:
        ...


# Event Hook Callback Type
EventHookCallback: TypeAlias = Callable[["Simulation"], None]


# ============================================================================
# 2. STATE & LIFECYCLE MANAGEMENT
# ============================================================================

@enum.unique
class SimulationState(enum.Enum):
    """Explicit state machine of the simulation orchestrator."""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    SHUTDOWN = "SHUTDOWN"


class SimulationLifecycle:
    """Thread-safe lifecycle state machine manager."""

    __slots__ = ("_state", "_lock")

    def __init__(self) -> None:
        self._state: SimulationState = SimulationState.UNINITIALIZED
        self._lock: threading.Lock = threading.Lock()

    @property
    def current_state(self) -> SimulationState:
        with self._lock:
            return self._state

    def transition_to(self, target_state: SimulationState) -> None:
        """Enforces thread-safe, valid state transitions."""
        with self._lock:
            valid: bool = False
            current = self._state

            if target_state == SimulationState.SHUTDOWN:
                valid = True
            elif current == SimulationState.UNINITIALIZED and target_state == SimulationState.INITIALIZING:
                valid = True
            elif current == SimulationState.INITIALIZING and target_state == SimulationState.STOPPED:
                valid = True
            elif current == SimulationState.STOPPED and target_state in (
                SimulationState.RUNNING,
                SimulationState.INITIALIZING,
            ):
                valid = True
            elif current == SimulationState.RUNNING and target_state in (
                SimulationState.PAUSED,
                SimulationState.STOPPED,
            ):
                valid = True
            elif current == SimulationState.PAUSED and target_state in (
                SimulationState.RUNNING,
                SimulationState.STOPPED,
            ):
                valid = True

            if not valid:
                raise RuntimeError(
                    f"Invalid simulation state transition from {current.value} to {target_state.value}"
                )

            logger.info(f"Simulation Lifecycle State Changed: {current.value} -> {target_state.value}")
            self._state = target_state


# ============================================================================
# 3. METRICS & TIMING ENGINE
# ============================================================================

@dataclass(slots=True)
class SystemProfile:
    """Stores telemetry for a single registered subsystem."""
    stage: PipelineStage
    last_tick_ms: float = 0.0
    accumulated_ms: float = 0.0
    total_ticks: int = 0
    min_tick_ms: float = float("inf")
    max_tick_ms: float = 0.0

    @property
    def average_tick_ms(self) -> float:
        if self.total_ticks == 0:
            return 0.0
        return self.accumulated_ms / self.total_ticks

    def record_sample(self, duration_ms: float) -> None:
        self.last_tick_ms = duration_ms
        self.accumulated_ms += duration_ms
        self.total_ticks += 1
        if duration_ms < self.min_tick_ms:
            self.min_tick_ms = duration_ms
        if duration_ms > self.max_tick_ms:
            self.max_tick_ms = duration_ms

    def reset(self) -> None:
        self.last_tick_ms = 0.0
        self.accumulated_ms = 0.0
        self.total_ticks = 0
        self.min_tick_ms = float("inf")
        self.max_tick_ms = 0.0


@dataclass(slots=True)
class SimulationMetrics:
    """Comprehensive performance telemetry and profiling container."""
    tick_count: int = 0
    frame_count: int = 0
    simulation_time: float = 0.0
    real_time_elapsed: float = 0.0
    actual_ups: float = 0.0
    actual_fps: float = 0.0
    peak_ups: float = 0.0
    peak_fps: float = 0.0
    last_tick_duration_ms: float = 0.0
    min_tick_duration_ms: float = float("inf")
    worst_frame_ms: float = 0.0
    frame_jitter_ms: float = 0.0
    lag_spikes_detected: int = 0
    rolling_ups: float = 0.0
    rolling_fps: float = 0.0
    system_profiles: Dict[PipelineStage, SystemProfile] = field(default_factory=dict)

    _tick_durations: collections.deque[float] = field(
        default_factory=lambda: collections.deque(maxlen=100), init=False
    )

    def record_tick_time(self, duration_ms: float) -> None:
        self.last_tick_duration_ms = duration_ms
        self._tick_durations.append(duration_ms)
        if duration_ms < self.min_tick_duration_ms:
            self.min_tick_duration_ms = duration_ms
        if duration_ms > self.worst_frame_ms:
            self.worst_frame_ms = duration_ms

        if len(self._tick_durations) > 1:
            mean = sum(self._tick_durations) / len(self._tick_durations)
            variance = sum((x - mean) ** 2 for x in self._tick_durations) / len(self._tick_durations)
            self.frame_jitter_ms = variance ** 0.5

    def reset(self) -> None:
        self.tick_count = 0
        self.frame_count = 0
        self.simulation_time = 0.0
        self.real_time_elapsed = 0.0
        self.actual_ups = 0.0
        self.actual_fps = 0.0
        self.peak_ups = 0.0
        self.peak_fps = 0.0
        self.last_tick_duration_ms = 0.0
        self.min_tick_duration_ms = float("inf")
        self.worst_frame_ms = 0.0
        self.frame_jitter_ms = 0.0
        self.lag_spikes_detected = 0
        self.rolling_ups = 0.0
        self.rolling_fps = 0.0
        self._tick_durations.clear()
        for profile in self.system_profiles.values():
            profile.reset()


class SimulationClock:
    """High-precision deterministic clock managing fixed step execution and frame timing."""

    __slots__ = (
        "_target_ups",
        "_target_fps",
        "_fixed_dt",
        "_max_frame_skip",
        "_accumulator",
        "_last_time",
        "_start_time",
        "_simulation_time",
        "_tick_count",
        "_frame_count",
        "_ups_counter",
        "_fps_counter",
        "_last_ups_fps_update",
        "_measured_ups",
        "_measured_fps",
    )

    def __init__(
        self,
        target_ups: float = 60.0,
        target_fps: float = 60.0,
        max_frame_skip: int = 5,
    ) -> None:
        if target_ups <= 0.0:
            raise ValueError(f"target_ups must be positive, got {target_ups}")
        if target_fps <= 0.0:
            raise ValueError(f"target_fps must be positive, got {target_fps}")
        if max_frame_skip < 1:
            raise ValueError(f"max_frame_skip must be at least 1, got {max_frame_skip}")

        self._target_ups: float = target_ups
        self._target_fps: float = target_fps
        self._fixed_dt: float = 1.0 / target_ups
        self._max_frame_skip: int = max_frame_skip

        self._accumulator: float = 0.0
        self._last_time: float = 0.0
        self._start_time: float = 0.0
        self._simulation_time: float = 0.0
        self._tick_count: int = 0
        self._frame_count: int = 0

        self._ups_counter: int = 0
        self._fps_counter: int = 0
        self._last_ups_fps_update: float = 0.0
        self._measured_ups: float = 0.0
        self._measured_fps: float = 0.0

    @property
    def fixed_dt(self) -> float:
        return self._fixed_dt

    @property
    def simulation_time(self) -> float:
        return self._simulation_time

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def measured_ups(self) -> float:
        return self._measured_ups

    @property
    def measured_fps(self) -> float:
        return self._measured_fps

    @property
    def max_frame_skip(self) -> int:
        return self._max_frame_skip

    @property
    def remaining_accumulator(self) -> float:
        return self._accumulator

    @property
    def interpolation_alpha(self) -> float:
        """Interpolation alpha (0.0 to 1.0) for render frame smoothing."""
        return self._accumulator / self._fixed_dt

    def start(self) -> None:
        now = time.perf_counter()
        self._last_time = now
        self._start_time = now
        self._last_ups_fps_update = now
        self._accumulator = 0.0

    def reset(self) -> None:
        self._accumulator = 0.0
        self._last_time = 0.0
        self._start_time = 0.0
        self._simulation_time = 0.0
        self._tick_count = 0
        self._frame_count = 0
        self._ups_counter = 0
        self._fps_counter = 0
        self._last_ups_fps_update = 0.0
        self._measured_ups = 0.0
        self._measured_fps = 0.0

    def accumulate(self, max_lag_sec: float = 0.25) -> Tuple[float, bool]:
        """Advances high-precision time delta and applies lag clamping."""
        now = time.perf_counter()
        frame_time = now - self._last_time
        self._last_time = now
        lag_clamped = False

        if frame_time > max_lag_sec:
            frame_time = max_lag_sec
            lag_clamped = True

        self._accumulator += frame_time

        if now - self._last_ups_fps_update >= 1.0:
            elapsed = now - self._last_ups_fps_update
            self._measured_ups = self._ups_counter / elapsed
            self._measured_fps = self._fps_counter / elapsed
            self._ups_counter = 0
            self._fps_counter = 0
            self._last_ups_fps_update = now

        return frame_time, lag_clamped

    def should_step() -> bool:
        pass  # Overridden below

    def should_step(self) -> bool:
        """Determines if enough accumulated time exists for a fixed tick."""
        return self._accumulator >= self._fixed_dt

    def step_simulation(self) -> None:
        """Advances simulation tick time and count by one fixed delta."""
        self._accumulator -= self._fixed_dt
        self._simulation_time += self._fixed_dt
        self._tick_count += 1
        self._ups_counter += 1

    def step_frame(self) -> None:
        """Increments rendering frame counter."""
        self._frame_count += 1
        self._fps_counter += 1


# ============================================================================
# 4. MASTER SIMULATION ORCHESTRATOR
# ============================================================================

class Simulation:
    """
    Master Orchestrator for Echo Evolution Simulator.
    Owns execution loop, pipeline dispatching, metrics tracking, and clock timing.
    Strictly delegates domain logic to registered subsystems.
    """

    def __init__(
        self,
        world_seed: int = 1337,
        target_ups: float = 60.0,
        target_fps: float = 60.0,
        max_frame_skip: int = 5,
    ) -> None:
        self.world_seed: Final[int] = world_seed
        self._clock: SimulationClock = SimulationClock(
            target_ups=target_ups,
            target_fps=target_fps,
            max_frame_skip=max_frame_skip,
        )
        self._lifecycle: SimulationLifecycle = SimulationLifecycle()
        self._metrics: SimulationMetrics = SimulationMetrics()

        # Thread synchronization
        self._state_condition: threading.Condition = threading.Condition()

        # System Registry mapping PipelineStage -> implementation
        self._systems: Dict[PipelineStage, SystemProtocol] = {}

        # Pre-populate metric profiles for zero-allocation access
        for stage in FROZEN_EXECUTION_ORDER:
            self._metrics.system_profiles[stage] = SystemProfile(stage=stage)

        # Event Hooks
        self._hooks: Dict[str, List[EventHookCallback]] = {
            "before_initialize": [],
            "after_initialize": [],
            "before_tick": [],
            "after_tick": [],
            "before_shutdown": [],
            "after_shutdown": [],
        }

    # ------------------------------------------------------------------------
    # Event Hooks & Subsystem Registration API
    # ------------------------------------------------------------------------

    def register_hook(self, hook_name: str, callback: EventHookCallback) -> None:
        """Registers an event hook callback."""
        if hook_name not in self._hooks:
            raise KeyError(f"Unknown hook_name '{hook_name}'. Valid: {list(self._hooks.keys())}")
        if callback not in self._hooks[hook_name]:
            self._hooks[hook_name].append(callback)

    def _trigger_hooks(self, hook_name: str) -> None:
        """Invokes all registered callbacks for a specific hook."""
        for callback in self._hooks[hook_name]:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in hook '{hook_name}': {e}", exc_info=True)

    def register_system(self, stage: PipelineStage, system_instance: Any) -> None:
        """Registers a subsystem into the orchestrator registry."""
        if not isinstance(stage, PipelineStage):
            raise TypeError(f"Stage must be a PipelineStage enum, got {type(stage)}")

        if not isinstance(system_instance, SystemProtocol):
            logger.warning(
                f"Registering '{stage.value}': instance does not strictly satisfy SystemProtocol."
            )

        self._systems[stage] = system_instance
        logger.debug(f"Successfully registered system stage: {stage.value}")

    def get_system(self, stage: PipelineStage) -> Any:
        """Retrieves a registered system by PipelineStage enum."""
        if stage not in self._systems:
            raise KeyError(f"System stage '{stage.value}' is not registered in Orchestrator.")
        return self._systems[stage]

    # ------------------------------------------------------------------------
    # Public Lifecycle Management API
    # ------------------------------------------------------------------------

    def initialize(self) -> None:
        """Validates all required dependencies and initializes registered subsystems."""
        if self._lifecycle.current_state != SimulationState.UNINITIALIZED:
            raise RuntimeError(
                f"Cannot initialize simulation when in state {self._lifecycle.current_state.value}"
            )

        self._trigger_hooks("before_initialize")
        self._lifecycle.transition_to(SimulationState.INITIALIZING)
        logger.info(f"Initializing Echo Evolution Orchestrator [Seed: {self.world_seed}]...")

        # Strict Dependency Validation: All pipeline stages MUST be registered
        missing_stages = [stage for stage in FROZEN_EXECUTION_ORDER if stage not in self._systems]
        if missing_stages:
            missing_str = ", ".join(s.value for s in missing_stages)
            raise RuntimeError(f"Initialization Failed. Missing required subsystems: [{missing_str}]")

        # Initialize subsystems in exact pipeline order
        for stage in FROZEN_EXECUTION_ORDER:
            sys_obj = self._systems[stage]
            try:
                sys_obj.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize subsystem '{stage.value}': {e}", exc_info=True)
                raise RuntimeError(f"Subsystem '{stage.value}' initialization failed.") from e

        self._clock.reset()
        self._metrics.reset()
        self._lifecycle.transition_to(SimulationState.STOPPED)
        logger.info("Simulation Orchestrator initialization complete.")
        self._trigger_hooks("after_initialize")

    def run(self, max_ticks: Optional[int] = None) -> None:
        """
        Main simulation loop. Drives fixed updates, variable updates, and sync calls.
        """
        if self._lifecycle.current_state == SimulationState.UNINITIALIZED:
            self.initialize()

        if self._lifecycle.current_state == SimulationState.STOPPED:
            self._lifecycle.transition_to(SimulationState.RUNNING)

        self._clock.start()
        start_real_time = time.perf_counter()

        logger.info("Entering Main Simulation Loop.")

        try:
            while True:
                state = self._lifecycle.current_state

                if state == SimulationState.PAUSED:
                    with self._state_condition:
                        while self._lifecycle.current_state == SimulationState.PAUSED:
                            self._state_condition.wait(timeout=0.1)
                    continue

                if state not in (SimulationState.RUNNING, SimulationState.PAUSED):
                    break

                frame_delta, lag_clamped = self._clock.accumulate()
                if lag_clamped:
                    self._metrics.lag_spikes_detected += 1

                skipped = 0
                while self._clock.should_step() and skipped < self._clock.max_frame_skip:
                    self.tick()
                    skipped += 1

                    if max_ticks is not None and self._clock.tick_count >= max_ticks:
                        logger.info(f"Reached target tick limit ({max_ticks}). Pausing.")
                        self.pause()
                        break

                self.variable_update(frame_delta)
                self.late_update(frame_delta)
                self._clock.step_frame()

                time.sleep(0.0001)

        except Exception as e:
            logger.critical(f"Unhandled Exception in Simulation Main Loop: {e}", exc_info=True)
            self.stop()
            raise e
        finally:
            self._metrics.real_time_elapsed = time.perf_counter() - start_real_time

    def tick(self) -> None:
        """Executes a single fixed update step across all subsystems in exact frozen order."""
        self._trigger_hooks("before_tick")
        tick_start = time.perf_counter()

        self._clock.step_simulation()
        sim_time = self._clock.simulation_time
        tick_num = self._clock.tick_count
        dt = self._clock.fixed_dt

        self.fixed_update(dt, sim_time, tick_num)

        tick_duration_ms = (time.perf_counter() - tick_start) * 1000.0
        self._metrics.record_tick_time(tick_duration_ms)
        self._metrics.tick_count = tick_num
        self._metrics.simulation_time = sim_time
        self._metrics.actual_ups = self._clock.measured_ups
        self._metrics.actual_fps = self._clock.measured_fps

        if self._clock.measured_ups > self._metrics.peak_ups:
            self._metrics.peak_ups = self._clock.measured_ups
        if self._clock.measured_fps > self._metrics.peak_fps:
            self._metrics.peak_fps = self._clock.measured_fps

        self._trigger_hooks("after_tick")

    def fixed_update(self, dt: float, sim_time: float, tick_count: int) -> None:
        """Iterates over registered systems in exact frozen execution order and executes tick()."""
        for stage in FROZEN_EXECUTION_ORDER:
            system = self._systems.get(stage)
            if system is None:
                continue

            sys_start = time.perf_counter()
            try:
                system.tick(dt, sim_time, tick_count)
            except Exception as e:
                logger.error(f"Error executing tick on subsystem '{stage.value}': {e}", exc_info=True)
                raise RuntimeError(f"Subsystem '{stage.value}' failed during tick.") from e

            sys_elapsed_ms = (time.perf_counter() - sys_start) * 1000.0
            self._metrics.system_profiles[stage].record_sample(sys_elapsed_ms)

    def variable_update(self, delta_time: float) -> None:
        """Executes variable update hooks."""
        pass

    def late_update(self, delta_time: float) -> None:
        """Executes late frame operations after fixed ticks complete."""
        pass

    def pause(self) -> None:
        """Pauses the simulation."""
        if self._lifecycle.current_state == SimulationState.RUNNING:
            self._lifecycle.transition_to(SimulationState.PAUSED)
            with self._state_condition:
                self._state_condition.notify_all()

    def resume(self) -> None:
        """Resumes a paused simulation."""
        if self._lifecycle.current_state == SimulationState.PAUSED:
            self._lifecycle.transition_to(SimulationState.RUNNING)
            with self._state_condition:
                self._state_condition.notify_all()

    def stop(self) -> None:
        """Stops the simulation loop."""
        if self._lifecycle.current_state in (SimulationState.RUNNING, SimulationState.PAUSED):
            self._lifecycle.transition_to(SimulationState.STOPPED)
            with self._state_condition:
                self._state_condition.notify_all()

    def reset(self) -> None:
        """Resets orchestrator state and all registered subsystems."""
        logger.info("Resetting Master Simulation Orchestrator...")
        self.stop()

        for stage in reversed(FROZEN_EXECUTION_ORDER):
            system = self._systems.get(stage)
            if system is not None and hasattr(system, "reset"):
                try:
                    system.reset()
                except Exception as e:
                    logger.error(f"Error resetting subsystem '{stage.value}': {e}", exc_info=True)

        self._clock.reset()
        self._metrics.reset()
        self._lifecycle.transition_to(SimulationState.STOPPED)
        logger.info("Reset complete.")

    def shutdown(self) -> None:
        """Shuts down all subsystems and cleans up orchestrator resources."""
        self._trigger_hooks("before_shutdown")
        logger.info("Initiating Simulation Shutdown...")
        self.stop()

        for stage in reversed(FROZEN_EXECUTION_ORDER):
            system = self._systems.get(stage)
            if system is not None and hasattr(system, "shutdown"):
                try:
                    system.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down subsystem '{stage.value}': {e}", exc_info=True)

        self._systems.clear()
        self._lifecycle.transition_to(SimulationState.SHUTDOWN)
        logger.info("Simulation Shutdown successfully finished.")
        self._trigger_hooks("after_shutdown")

    # ------------------------------------------------------------------------
    # Public Query & Inspection APIs
    # ------------------------------------------------------------------------

    def is_running(self) -> bool:
        return self._lifecycle.current_state == SimulationState.RUNNING

    def get_tick(self) -> int:
        return self._clock.tick_count

    def get_simulation_time(self) -> float:
        return self._clock.simulation_time

    def get_metrics(self) -> SimulationMetrics:
        return self._metrics

    def get_interpolation_alpha(self) -> float:
        """Returns rendering interpolation alpha value."""
        return self._clock.interpolation_alpha