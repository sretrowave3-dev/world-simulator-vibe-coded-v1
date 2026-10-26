"""
project/systems/save_system.py

Smart Save System — v2.0
Manages periodic simulation checkpoints with:
- 3 rotating named autosave slots (autosave_slot_1/2/3)
- Adaptive trigger: immediate save if population nears extinction (<20 alive)
- Full manager wiring: gemini_sys, ruins_mgr, miracles_mgr included in snapshots
"""

from __future__ import annotations

import os
from typing import Set, List, Optional, Any
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity
from project.world.time import WorldTimeManager
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager
from project.core.persistence import PersistenceManager, SAVES_DIR

_AUTOSAVE_SLOTS   = 3       # number of rotating autosave slots
_EXTINCTION_ALARM = 20      # save immediately when alive count drops below this


class SaveSystem:
    """
    Manages periodic simulation checkpoints into saves/ directory.

    Autosave slots rotate through autosave_slot_1.dat → autosave_slot_2.dat → autosave_slot_3.dat
    so that the most recent 3 autosaves are always preserved.
    An extinction alarm triggers an emergency autosave regardless of tick interval.
    """

    def __init__(
        self,
        entities_list: List[Entity],
        time_mgr: Optional[WorldTimeManager] = None,
        soil_mgr: Optional[SoilManager] = None,
        water_mgr: Optional[WaterManager] = None,
        veg_mgr: Optional[VegetationManager] = None,
        res_mgr: Optional[ResourceManager] = None,
        gemini_sys: Optional[Any] = None,
        ruins_mgr: Optional[Any] = None,
        miracles_mgr: Optional[Any] = None,
        autosave_interval_ticks: int = 6000,
        filename: str = "autosave.dat",         # kept for back-compat, ignored (slots used)
    ) -> None:
        self._entities_list  = entities_list
        self._time_mgr       = time_mgr
        self._soil_mgr       = soil_mgr
        self._water_mgr      = water_mgr
        self._veg_mgr        = veg_mgr
        self._res_mgr        = res_mgr
        self._gemini_sys     = gemini_sys
        self._ruins_mgr      = ruins_mgr
        self._miracles_mgr   = miracles_mgr
        self.autosave_interval_ticks = autosave_interval_ticks
        self.enabled            = True
        self.last_saved_tick    = 0
        self._slot_index        = 0   # 0-based; rotates 0→1→2→0→...
        self._last_alive_count  = -1
        self._extinction_saved  = False

    @property
    def name(self) -> str:
        return "SaveSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.POST_UPDATE

    @property
    def priority(self) -> int:
        return ExecutionPriority.AUTOSAVE

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        os.makedirs(SAVES_DIR, exist_ok=True)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _all_managers_ready(self) -> bool:
        return all([self._time_mgr, self._soil_mgr, self._water_mgr,
                    self._veg_mgr, self._res_mgr])

    def _next_slot_name(self) -> str:
        """Advances the slot index and returns the filename for the next autosave."""
        self._slot_index = (self._slot_index + 1) % _AUTOSAVE_SLOTS
        return f"autosave_slot_{self._slot_index + 1}.dat"

    def _do_save(self, context: UpdateContext, label: str) -> None:
        """Core save routine — serialises world state and writes into the active universe's isolated autosaves."""
        if not self._all_managers_ready():
            return
        try:
            from project.core.quantum_persistence import quantum_persistence
            data = PersistenceManager.serialize_state(
                time_mgr     = self._time_mgr,
                soil_mgr     = self._soil_mgr,
                water_mgr    = self._water_mgr,
                veg_mgr      = self._veg_mgr,
                res_mgr      = self._res_mgr,
                entities_list= self._entities_list,
                gemini_sys   = self._gemini_sys,
                ruins_mgr    = self._ruins_mgr,
                miracles_mgr = self._miracles_mgr,
            )
            saved_path = quantum_persistence.save_universe_autosave(data, context.tick, cause=label)
            self.last_saved_tick = context.tick
            alive_count = sum(1 for e in self._entities_list if e.is_alive)
            univ = quantum_persistence.get_active_universe()
            print(
                f"\n[AUTOSAVE/{label}] 💾 Universe '{univ.world_name}' → {os.path.basename(saved_path)} "
                f"(Tick {context.tick:,}, {alive_count} alive)"
            )
        except Exception as e:
            print(f"\n[AUTOSAVE ERROR] Failed to save checkpoint: {e}")

    # ── lifecycle ────────────────────────────────────────────────────────────

    def update(self, context: UpdateContext) -> None:
        if not self.enabled or context.tick == 0:
            return

        alive_count = sum(1 for e in self._entities_list if e.is_alive)

        # ── Extinction alarm: capture emergency black-box capsule if established population crashes ──
        if context.tick > 50 and 0 < alive_count < _EXTINCTION_ALARM:
            if not self._extinction_saved:
                print(f"\n🚨 [EXTINCTION ALARM] Population critical ({alive_count} alive) — capturing blackbox time capsule!")
                try:
                    from project.core.quantum_persistence import quantum_persistence
                    data = PersistenceManager.serialize_state(
                        time_mgr     = self._time_mgr,
                        soil_mgr     = self._soil_mgr,
                        water_mgr    = self._water_mgr,
                        veg_mgr      = self._veg_mgr,
                        res_mgr      = self._res_mgr,
                        entities_list= self._entities_list,
                        gemini_sys   = self._gemini_sys,
                        ruins_mgr    = self._ruins_mgr,
                        miracles_mgr = self._miracles_mgr,
                    )
                    quantum_persistence.capture_blackbox(data, cause="EXTINCTION_ALARM")
                except Exception as ex:
                    print(f"⚠️ [EXTINCTION RECORDER ERROR] {ex}")
                self._extinction_saved = True
        else:
            self._extinction_saved = False   # reset when population recovers

        # ── Regular interval autosave ──
        if (
            self.autosave_interval_ticks > 0
            and context.tick % self.autosave_interval_ticks == 0
            and context.tick != self.last_saved_tick
        ):
            self._do_save(context, "INTERVAL")

        self._last_alive_count = alive_count

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
