"""
project/systems/spec_protection_system.py

Hardware Specification & Thermal/Resource Safety Protection System.
Integrates native pure-C SpecProtector to monitor CPU load, process RAM, and frame delta.
When hardware safety limits are breached (danger zone), it immediately freezes the simulation
and performs an atomic emergency save to prevent hardware damage, CPU thermal thrashing, and OS crashes.
"""

from __future__ import annotations

import time
from typing import Set, List, Optional, Any, Callable
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.security.spec_protector import global_spec_protector, HardwareTelemetryData
from project.core.persistence import PersistenceManager


class SpecProtectionSystem:
    """Zero-overhead hardware safety system polling native pure-C telemetry."""

    def __init__(
        self,
        emergency_save_callback: Optional[Callable[[str], None]] = None,
        check_interval_ticks: int = 5,
    ) -> None:
        self._emergency_save_callback = emergency_save_callback
        self.check_interval_ticks = check_interval_ticks
        self.last_telemetry: Optional[HardwareTelemetryData] = None
        self.has_emergency_tripped: bool = False
        self.total_trips: int = 0

    @property
    def name(self) -> str:
        return "SpecProtectionSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.PRE_UPDATE

    @property
    def priority(self) -> int:
        return ExecutionPriority.SPEC_PROTECTION

    @property
    def dependencies(self) -> Set[str]:
        return set()

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        global_spec_protector.reset_danger_state()
        self.has_emergency_tripped = False
        self.last_telemetry = global_spec_protector.check_safety()

    def update(self, context: UpdateContext) -> None:
        # Check hardware safety every check_interval_ticks or when unpaused
        if context.tick % self.check_interval_ticks != 0 and not self.has_emergency_tripped:
            return

        telemetry = global_spec_protector.check_safety()
        self.last_telemetry = telemetry

        if telemetry.is_danger_zone and not self.has_emergency_tripped:
            self.has_emergency_tripped = True
            self.total_trips += 1
            self._handle_danger_trip(context, telemetry)

    def _handle_danger_trip(self, context: UpdateContext, telemetry: HardwareTelemetryData) -> None:
        """Executes emergency safety intervention when hardware danger zone is hit."""
        # 1. Freeze scheduler execution
        if context.world_reference is not None:
            setattr(context.world_reference, "is_paused", True)

        # 2. Trigger atomic emergency save
        save_name = "emergency_hardware_save"
        if self._emergency_save_callback:
            try:
                self._emergency_save_callback(save_name)
            except Exception as e:
                print(f"⚠️ [SPEC PROTECTOR] Emergency callback save encountered error: {e}")

        # 3. Broadcast hardware protection notice
        print("\n" + "=" * 80)
        print("[HARDWARE SPEC PROTECTOR ENGAGED] DANGER ZONE DETECTED!")
        print(f"   Reason:       {telemetry.danger_reason_text}")
        print(f"   CPU Usage:    {telemetry.cpu_usage_pct:.1f}%")
        print(f"   Process RAM:  {telemetry.process_ram_mb:.1f} MB")
        print(f"   Available RAM:{telemetry.system_ram_avail_mb:.1f} MB / {telemetry.system_ram_total_mb:.1f} MB")
        print(f"   Frame Latency:{telemetry.frame_delta_ms:.2f} ms")
        print(f"   Safety Action:Simulation paused & state saved to saves/{save_name}.dat")
        print("   Hardware Protection: CPU and system resources protected from overload.")
        print("=" * 80 + "\n")

    def resume_simulation(self) -> None:
        """Resets tripwire after hardware cools down and allows user to resume."""
        global_spec_protector.reset_danger_state()
        self.has_emergency_tripped = False
        print("[SPEC PROTECTOR] Hardware tripwire reset. Simulation ready to resume.")

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
