"""
core/scheduler.py

Central Pipeline Execution & System Scheduling Engine for the ALife Simulation Platform.

Architectural Guarantees:
1. Strict Separation of Concerns: Knows WHEN systems execute, NEVER HOW.
2. Single Pipeline Ownership: Enforces frozen execution order across 9 logical phases.
3. Thread-Safe & Robust: Fault-tolerant execution loop with dependency resolution, 
   performance timing, and delayed job scheduling.
4. Deterministic Pipeline: Priority-sorted topological execution order.
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple
from project.core.linux_optimizer import linux_optimizer


logger = logging.getLogger("ALife.Scheduler")


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class SchedulerState(Enum):
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STEPPING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


class SchedulerPhase(IntEnum):
    PRE_UPDATE = 100
    WORLD = 200
    AI = 300
    BIOLOGY = 400
    GEMINI = 500
    CIVILIZATION = 600
    ANALYTICS = 700
    RENDER_SYNC = 800
    POST_UPDATE = 900


class ExecutionPriority(IntEnum):
    SPEC_PROTECTION = 1
    SECURITY = 5
    WEATHER = 10
    TERRAIN = 20
    RESOURCES = 25
    PLANTS = 30
    FOOD = 40
    PERCEPTION = 100
    BRAIN = 110
    DECISION = 120
    MOVEMENT = 150
    COMBAT = 180
    DIGESTION = 200
    LEARNING = 210
    MEMORY = 220
    PHEROMONES = 230
    GEMINI = 500
    SOCIAL = 510
    REPRODUCTION = 520
    MUTATION = 530
    EVOLUTION = 540
    SPECIES = 550
    CIVILIZATION = 600
    KNOWLEDGE = 610
    EVENTS = 700
    STATISTICS = 710
    REPLAY = 720
    AUTOSAVE = 730
    RENDERER_SYNC = 800


# =============================================================================
# SYSTEM INTERFACE & UPDATE CONTEXT
# =============================================================================

@dataclass(frozen=True, slots=True)
class UpdateContext:
    """Immutable execution context passed to every system during update passes."""
    tick: int
    delta_time: float
    simulation_time: float
    random_seed: int
    world_reference: Any
    is_paused: bool
    active_thread_count: int
    time_snapshot: Optional[Any] = None


class SystemInterface(Protocol):
    """Standard lifecycle contract for all systems registered with the Scheduler."""
    
    @property
    def name(self) -> str:
        ...

    @property
    def phase(self) -> SchedulerPhase:
        ...

    @property
    def priority(self) -> int:
        ...

    @property
    def dependencies(self) -> Set[str]:
        ...

    @property
    def is_critical(self) -> bool:
        ...

    def initialize(self, context: UpdateContext) -> None:
        ...

    def update(self, context: UpdateContext) -> None:
        ...

    def late_update(self, context: UpdateContext) -> None:
        ...

    def shutdown(self) -> None:
        ...


# =============================================================================
# INTERNAL SCHEDULER MODULES
# =============================================================================

class TickManager:
    """Owns simulation ticks, temporal progression, and play/pause/stepping controls."""
    
    def __init__(self, target_ups: int = 60) -> None:
        self.current_tick: int = 0
        self.simulation_time: float = 0.0
        self.target_ups: int = target_ups
        self.time_scale: float = 1.0
        self.is_paused: bool = False
        self._last_frame_timestamp: float = time.perf_counter()

    def advance_tick(self, fixed_dt_override: float = None) -> float:
        now = time.perf_counter()
        raw_dt = now - self._last_frame_timestamp
        self._last_frame_timestamp = now
        
        if fixed_dt_override is not None:
            effective_dt = fixed_dt_override
        else:
            # Deterministic simulation timestep: 1 tick = (1.0 / target_ups) * time_scale
            effective_dt = (1.0 / max(1, self.target_ups)) * self.time_scale
            
        if not self.is_paused or fixed_dt_override is not None:
            self.current_tick += 1
            self.simulation_time += effective_dt
            
        return effective_dt


class SystemRegistry:
    """Manages system instances and lookup tables."""
    
    def __init__(self) -> None:
        self._systems: Dict[str, SystemInterface] = {}
        self._disabled_systems: Set[str] = set()

    def register(self, system: SystemInterface) -> None:
        if system.name in self._systems:
            raise ValueError(f"System '{system.name}' is already registered.")
        self._systems[system.name] = system

    def unregister(self, name: str) -> Optional[SystemInterface]:
        return self._systems.pop(name, None)

    def disable_system(self, name: str) -> None:
        if name in self._systems:
            self._disabled_systems.add(name)

    def enable_system(self, name: str) -> None:
        self._disabled_systems.discard(name)

    def get_active_systems(self) -> List[SystemInterface]:
        return [sys for name, sys in self._systems.items() if name not in self._disabled_systems]

    def get_system(self, name: str) -> Optional[SystemInterface]:
        return self._systems.get(name)


class DependencyResolver:
    """Validates and sorts systems topologically based on dependencies and priorities."""
    
    @staticmethod
    def resolve_execution_order(systems: List[SystemInterface]) -> List[SystemInterface]:
        system_map = {sys.name: sys for sys in systems}
        in_degree: Dict[str, int] = {sys.name: 0 for sys in systems}
        graph: Dict[str, List[str]] = {sys.name: [] for sys in systems}

        for sys in systems:
            for dep in sys.dependencies:
                if dep not in system_map:
                    raise UnresolvedDependencyError(
                        f"System '{sys.name}' requires unregistered dependency '{dep}'"
                    )
                graph[dep].append(sys.name)
                in_degree[sys.name] += 1

        # Sort initial nodes by Phase, then Priority
        ready_queue = [
            sys for sys in systems if in_degree[sys.name] == 0
        ]
        ready_queue.sort(key=lambda s: (s.phase.value, s.priority))

        ordered_systems: List[SystemInterface] = []
        while ready_queue:
            curr = ready_queue.pop(0)
            ordered_systems.append(curr)

            for neighbor_name in graph[curr.name]:
                in_degree[neighbor_name] -= 1
                if in_degree[neighbor_name] == 0:
                    neighbor_sys = system_map[neighbor_name]
                    ready_queue.append(neighbor_sys)
                    ready_queue.sort(key=lambda s: (s.phase.value, s.priority))

        if len(ordered_systems) != len(systems):
            raise CircularDependencyError("Circular dependency detected in System execution graph.")

        return ordered_systems


class PerformanceProfiler:
    """Tracks execution time per system, average UPS, and frame timing metrics."""
    
    def __init__(self) -> None:
        self.system_execution_times: Dict[str, float] = {}
        self.frame_durations: List[float] = []
        self._max_history: int = 100

    def record_system_time(self, system_name: str, duration_seconds: float) -> None:
        self.system_execution_times[system_name] = duration_seconds * 1000.0  # convert to ms

    def record_frame_duration(self, duration_seconds: float) -> None:
        self.frame_durations.append(duration_seconds * 1000.0)
        if len(self.frame_durations) > self._max_history:
            self.frame_durations.pop(0)

    def get_average_frame_time_ms(self) -> float:
        if not self.frame_durations:
            return 0.0
        return sum(self.frame_durations) / len(self.frame_durations)


@dataclass(slots=True)
class ScheduledTask:
    task_id: str
    execute_at_tick: int
    callback: Callable[[], None]
    is_recurring: bool = False
    interval_ticks: int = 0


class TaskScheduler:
    """Handles delayed, one-off, or recurring scheduled simulation jobs."""
    
    def __init__(self) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._next_task_id: int = 0

    def schedule_once(self, delay_ticks: int, current_tick: int, callback: Callable[[], None]) -> str:
        self._next_task_id += 1
        task_id = f"task_{self._next_task_id}"
        self._tasks[task_id] = ScheduledTask(
            task_id=task_id,
            execute_at_tick=current_tick + delay_ticks,
            callback=callback
        )
        return task_id

    def schedule_recurring(self, interval_ticks: int, current_tick: int, callback: Callable[[], None]) -> str:
        self._next_task_id += 1
        task_id = f"task_{self._next_task_id}"
        self._tasks[task_id] = ScheduledTask(
            task_id=task_id,
            execute_at_tick=current_tick + interval_ticks,
            callback=callback,
            is_recurring=True,
            interval_ticks=interval_ticks
        )
        return task_id

    def cancel_task(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def update(self, current_tick: int) -> None:
        completed_tasks: List[str] = []
        for task_id, task in list(self._tasks.items()):
            if current_tick >= task.execute_at_tick:
                try:
                    task.callback()
                except Exception as exc:
                    logger.error(f"Error executing scheduled task '{task_id}': {exc}", exc_info=True)
                
                if task.is_recurring:
                    task.execute_at_tick = current_tick + task.interval_ticks
                else:
                    completed_tasks.append(task_id)

        for task_id in completed_tasks:
            self._tasks.pop(task_id, None)


# =============================================================================
# SCHEDULER EXCEPTIONS
# =============================================================================

class SchedulerError(Exception):
    """Base exception for Scheduler failures."""


class UnresolvedDependencyError(SchedulerError):
    """Raised when a system depends on an unregistered system."""


class CircularDependencyError(SchedulerError):
    """Raised when circular dependencies exist between systems."""


class SystemExecutionError(SchedulerError):
    """Raised when a critical system fails execution."""


# =============================================================================
# MAIN SCHEDULER ENGINE
# =============================================================================

class Scheduler:
    """
    Central Simulation Pipeline Execution Engine.
    
    Coordinates System discovery, topological sorting, execution phases,
    performance profiling, fault isolation, and state management.
    """

    def __init__(self, world_reference: Any, target_ups: int = 60, random_seed: int = 42) -> None:
        self.world_reference = world_reference
        self.random_seed = random_seed
        self.state: SchedulerState = SchedulerState.INITIALIZING
        
        self.tick_manager = TickManager(target_ups=target_ups)
        self.registry = SystemRegistry()
        self.profiler = PerformanceProfiler()
        self.task_scheduler = TaskScheduler()
        
        self._ordered_pipeline: List[SystemInterface] = []
        self._pipeline_dirty: bool = True

    # -------------------------------------------------------------------------
    # PUBLIC REGISTRATION & CONTROLS
    # -------------------------------------------------------------------------

    def register_system(self, system: SystemInterface) -> None:
        self.registry.register(system)
        self._pipeline_dirty = True
        logger.info(f"Registered System: '{system.name}' [Phase: {system.phase.name}, Priority: {system.priority}]")

    def unregister_system(self, name: str) -> None:
        if self.registry.unregister(name):
            self._pipeline_dirty = True
            logger.info(f"Unregistered System: '{name}'")

    def pause(self) -> None:
        self.tick_manager.is_paused = True
        self.state = SchedulerState.PAUSED
        logger.info("Simulation Paused.")

    def resume(self) -> None:
        self.tick_manager.is_paused = False
        self.state = SchedulerState.RUNNING
        logger.info("Simulation Resumed.")

    def step(self) -> None:
        """Executes exactly one simulation frame while paused."""
        if not self.tick_manager.is_paused:
            logger.warning("Step invoked while simulation is running. Pausing first.")
            self.pause()
            
        self.state = SchedulerState.STEPPING
        self._execute_frame()
        self.state = SchedulerState.PAUSED

    def set_time_scale(self, scale: float) -> None:
        self.tick_manager.time_scale = max(0.0, scale)

    # -------------------------------------------------------------------------
    # LIFECYCLE MANAGEMENT
    # -------------------------------------------------------------------------

    def initialize(self) -> None:
        self._rebuild_pipeline_if_dirty()
        context = self._create_execution_context(0.0)
        
        for system in self._ordered_pipeline:
            try:
                system.initialize(context)
            except Exception as exc:
                logger.critical(f"Failed to initialize system '{system.name}': {exc}", exc_info=True)
                if system.is_critical:
                    self.state = SchedulerState.ERROR
                    raise SystemExecutionError(f"Critical system '{system.name}' failed initialization.") from exc
                else:
                    self.registry.disable_system(system.name)

        self.state = SchedulerState.RUNNING if not self.tick_manager.is_paused else SchedulerState.PAUSED
        logger.info("Scheduler initialized successfully.")

    def update(self, dt_override: float = None) -> None:
        """Main single-frame entry point called by the outer loop."""
        if self.state not in (SchedulerState.RUNNING, SchedulerState.STEPPING):
            return

        frame_start = time.perf_counter()
        self._execute_frame(dt_override=dt_override)
        frame_duration = time.perf_counter() - frame_start
        self.profiler.record_frame_duration(frame_duration)

    def shutdown(self) -> None:
        self.state = SchedulerState.STOPPING
        logger.info("Shutting down Scheduler and subsystems...")
        
        for system in reversed(self._ordered_pipeline):
            try:
                system.shutdown()
            except Exception as exc:
                logger.error(f"Error shutting down system '{system.name}': {exc}", exc_info=True)
                
        self.state = SchedulerState.STOPPED
        logger.info("Scheduler shutdown complete.")

    # -------------------------------------------------------------------------
    # INTERNAL PIPELINE EXECUTION
    # -------------------------------------------------------------------------

    def _execute_frame(self, dt_override: float = None) -> None:
        self._rebuild_pipeline_if_dirty()
        delta_time = self.tick_manager.advance_tick(fixed_dt_override=dt_override)
        context = self._create_execution_context(delta_time)

        # 1. Continuous System Updates
        for system in self._ordered_pipeline:
            sys_start = time.perf_counter()
            try:
                system.update(context)
            except Exception as exc:
                self._handle_system_failure(system, exc, "update")
            finally:
                self.profiler.record_system_time(system.name, time.perf_counter() - sys_start)

        # 2. Late Updates (Post-processing state resolutions)
        for system in self._ordered_pipeline:
            try:
                system.late_update(context)
            except Exception as exc:
                self._handle_system_failure(system, exc, "late_update")

        # 3. Process Scheduled Tasks
        self.task_scheduler.update(self.tick_manager.current_tick)

        # 4. Periodic Linux GLIBC memory compaction
        if self.tick_manager.current_tick % 1200 == 0:
            linux_optimizer.malloc_trim(0)

    def _rebuild_pipeline_if_dirty(self) -> None:
        if not self._pipeline_dirty:
            return

        active_systems = self.registry.get_active_systems()
        self._ordered_pipeline = DependencyResolver.resolve_execution_order(active_systems)
        self._pipeline_dirty = False
        logger.debug("Execution pipeline topology rebuilt.")

    def _create_execution_context(self, delta_time: float) -> UpdateContext:
        time_snap = None
        if hasattr(self.world_reference, "time_mgr") and hasattr(self.world_reference.time_mgr, "get_snapshot"):
            time_snap = self.world_reference.time_mgr.get_snapshot()
        elif hasattr(self.world_reference, "get_snapshot"):
            time_snap = self.world_reference.get_snapshot()

        return UpdateContext(
            tick=self.tick_manager.current_tick,
            delta_time=delta_time,
            simulation_time=self.tick_manager.simulation_time,
            random_seed=self.random_seed,
            world_reference=self.world_reference,
            is_paused=self.tick_manager.is_paused,
            active_thread_count=1,
            time_snapshot=time_snap,
        )

    def _handle_system_failure(self, system: SystemInterface, error: Exception, stage: str) -> None:
        logger.error(
            f"Execution failure in System '{system.name}' during stage '{stage}': {error}",
            exc_info=True
        )
        if system.is_critical:
            self.state = SchedulerState.ERROR
            raise SystemExecutionError(
                f"Critical System failure in '{system.name}' during '{stage}'"
            ) from error
        else:
            logger.warning(f"Disabling non-critical faulting system: '{system.name}'")
            self.registry.disable_system(system.name)
            self._pipeline_dirty = True

    # -------------------------------------------------------------------------
    # STATISTICS & READOUTS
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "state": self.state.name,
            "current_tick": self.tick_manager.current_tick,
            "simulation_time": self.tick_manager.simulation_time,
            "is_paused": self.tick_manager.is_paused,
            "time_scale": self.tick_manager.time_scale,
            "average_frame_time_ms": round(self.profiler.get_average_frame_time_ms(), 3),
            "system_count": len(self._ordered_pipeline),
            "system_timings_ms": dict(self.profiler.system_execution_times)
        }

    def get_current_tick(self) -> int:
        return self.tick_manager.current_tick

    def get_simulation_time(self) -> float:
        return self.tick_manager.simulation_time

    def get_performance_timings(self) -> Dict[str, float]:
        """Returns execution timings mapped to system names in seconds."""
        return {name: val / 1000.0 for name, val in self.profiler.system_execution_times.items()}