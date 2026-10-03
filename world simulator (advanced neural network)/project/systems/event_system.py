"""
project/systems/event_system.py

Event System recording immutable simulation event logs.
"""

from __future__ import annotations

from typing import Set, List, Dict, Any
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext


class EventSystem:
    """Collects and stores simulation events."""

    def __init__(self) -> None:
        self.events_log: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "EventSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.ANALYTICS

    @property
    def priority(self) -> int:
        return ExecutionPriority.EVENTS

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self.events_log.clear()

    def update(self, context: UpdateContext) -> None:
        pass

    def record_event(self, tick: int, event_type: str, data: Dict[str, Any]) -> None:
        self.events_log.append({
            "tick": tick,
            "event_type": event_type,
            "data": data,
        })
        if len(self.events_log) > 5000:
            self.events_log.pop(0)  # Evict oldest log

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
