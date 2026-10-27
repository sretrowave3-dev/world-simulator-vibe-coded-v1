"""
project/core/activity_chronicler.py

Smart Simulation Activity Chronicler and Storyteller.
Aggregates, deduplicates, and curates simulation activities so that terminal-based
users "see everything without actually seeing it" in an intelligent, evocative,
non-spamming activity feed.
"""

from __future__ import annotations

import sys
import time
import threading
from typing import Dict, List, Any, Optional, Tuple


class ActivityChronicler:
    """
    Intelligent simulation event aggregator, narrative synthesizer, and terminal feed.
    Prevents log spamming while keeping users completely aware of life, civilization,
    predation, climate, and discoveries across the simulated world.
    """

    def __init__(self) -> None:
        self.is_terminal_mode: bool = False
        self.verbosity: str = "smart"  # "smart", "quiet", "all", "off"
        self._lock = threading.Lock()

        # Tracking state for rate-limiting and delta calculations
        self.last_pulse_tick: int = 0
        self.pulse_interval_ticks: int = 90  # ~3 seconds at 30 UPS pace
        self.last_phase: Optional[str] = None
        self.last_day: int = -1
        self.last_weather: Optional[str] = None

        # Short-term aggregation buffers (cleared every pulse window)
        self.buffered_civ_events: List[str] = []
        self.buffered_tech: List[str] = []
        self.buffered_structures: List[str] = []
        self.buffered_hunts: List[Dict[str, Any]] = []
        self.buffered_births: Dict[str, int] = {}
        self.buffered_deaths: Dict[str, int] = {}
        self.buffered_discoveries: List[str] = []
        self.buffered_miracles: List[str] = []
        self.buffered_disasters: List[str] = []

    def set_terminal_mode(self, enabled: bool) -> None:
        """Enables or disables terminal activity streaming."""
        self.is_terminal_mode = enabled

    def set_verbosity(self, level: str) -> str:
        """Sets feed verbosity: smart, quiet, all, or off."""
        lvl = level.lower().strip()
        if lvl in ("smart", "quiet", "all", "off", "on"):
            if lvl == "on":
                lvl = "smart"
            self.verbosity = lvl
            return f"Activity feed mode set to '{self.verbosity}'."
        return f"Unknown feed mode '{level}'. Available: smart, quiet, all, off."

    # -------------------------------------------------------------------------
    # Thread-Safe Terminal Logging
    # -------------------------------------------------------------------------
    def log_to_terminal(self, message: str, force: bool = False) -> None:
        """
        Prints a curated message to stdout with ANSI line-clearing so the CMD> prompt
        remains clean and untangled.
        """
        if self.verbosity == "off" and not force:
            return
        if not self.is_terminal_mode and not force:
            return

        with self._lock:
            try:
                # \r\033[K clears the current line (e.g. CMD> ) before writing the update
                # and then restores the CMD> prompt on a fresh line.
                sys.stdout.write(f"\r\033[K{message}\nCMD> ")
                sys.stdout.flush()
            except Exception:
                try:
                    print(message)
                except Exception:
                    pass

    # -------------------------------------------------------------------------
    # Event Ingestion Hooks
    # -------------------------------------------------------------------------
    def record_tech_discovery(self, tech_name: str, tier_name: str, clan_id: str = "Genesis Tribe") -> None:
        """Records emergence of a new technology."""
        desc = f"🔥 [{clan_id}] Discovered '{tech_name}'! Technology advanced to {tier_name} Tier."
        self.buffered_tech.append(desc)
        if self.verbosity == "all":
            self.log_to_terminal(desc)

    def record_construction(self, structure_type: str, pos: Tuple[float, float], clan_id: str = "genesis_tribe") -> None:
        """Records construction of a new architectural shelter or site."""
        clean_name = structure_type.replace("_", " ").title()
        desc = f"🏕️  [{clan_id.replace('_', ' ').title()}] Constructed a {clean_name} at ({pos[0]:.0f}, {pos[1]:.0f})."
        self.buffered_structures.append(desc)
        if self.verbosity == "all":
            self.log_to_terminal(desc)

    def record_craft(self, item_name: str, item_type: str, clan_id: str = "Genesis Tribe") -> None:
        """Records tool/weapon/garment crafting."""
        desc = f"🔨 [{clan_id}] Crafted {item_name} ({item_type})."
        self.buffered_civ_events.append(desc)
        if self.verbosity == "all":
            self.log_to_terminal(desc)

    def record_hunt(self, predator_sp: str, prey_sp: str, pos: Tuple[float, float], counterattack: bool = False) -> None:
        """Records predation or defensive counterattack."""
        self.buffered_hunts.append({
            "predator": predator_sp,
            "prey": prey_sp,
            "pos": pos,
            "counterattack": counterattack,
        })
        if self.verbosity == "all":
            if counterattack:
                self.log_to_terminal(f"🛡️  [Tribe Defense] Hunters counterattacked an aggressive {predator_sp}!")
            else:
                self.log_to_terminal(f"⚔️  [Wildlife] A {predator_sp.title()} hunted a {prey_sp.title()}.")

    def record_birth(self, species_name: str, entity_type: str) -> None:
        """Records entity birth."""
        sp = species_name.replace("_", " ").title()
        self.buffered_births[sp] = self.buffered_births.get(sp, 0) + 1
        if self.verbosity == "all":
            self.log_to_terminal(f"🌱 [Birth] A new {sp} was born into the ecosystem.")

    def record_death(self, species_name: str, reason: str = "natural") -> None:
        """Records entity mortality."""
        sp = species_name.replace("_", " ").title()
        self.buffered_deaths[sp] = self.buffered_deaths.get(sp, 0) + 1
        if self.verbosity == "all":
            self.log_to_terminal(f"💀 [Death] A {sp} passed away ({reason}).")

    def record_ruins_progress(self, message: str) -> None:
        """Records ancient sanctuary ruins exploration progress."""
        desc = f"🏛️  [Ancient Ruins] {message}"
        self.buffered_discoveries.append(desc)
        if self.verbosity in ("all", "smart"):
            self.log_to_terminal(desc)

    def record_miracle(self, miracle_type: str, description: str) -> None:
        """Records celestial divine miracles."""
        desc = f"✨ [Celestial Miracle] {miracle_type}: {description}"
        self.buffered_miracles.append(desc)
        self.log_to_terminal(desc, force=True)

    def record_disaster(self, hazard_type: str, details: str) -> None:
        """Records natural disaster warnings or impacts."""
        desc = f"🌋 [Disaster Warning] {hazard_type}: {details}"
        self.buffered_disasters.append(desc)
        self.log_to_terminal(desc, force=True)

    # -------------------------------------------------------------------------
    # Master Periodic Engine Update (Called from Backend Sim Loop)
    # -------------------------------------------------------------------------
    def update(
        self,
        current_tick: int,
        time_mgr: Any,
        entities_list: List[Any],
        weather_mgr: Optional[Any] = None,
    ) -> None:
        """
        Called once per tick in simulation_worker.
        Detects diurnal shifts, compiles status heartbeat, and synthesizes batched events.
        """
        if not self.is_terminal_mode or self.verbosity == "off":
            return

        # 1. Diurnal Cycle & Day/Night Transitions (Evocative narrative milestones)
        time_snap = time_mgr.get_snapshot() if hasattr(time_mgr, "get_snapshot") else None
        if time_snap:
            day_num = time_snap.day
            df = time_snap.daylight_factor
            cur_phase = "MIDDAY" if df > 0.6 else ("DAWN" if df > 0.15 and time_snap.day_fraction < 0.5 else ("DUSK" if df > 0.15 else "NIGHT"))

            if self.last_phase is not None and cur_phase != self.last_phase:
                self._announce_diurnal_shift(cur_phase, day_num, time_snap)
            self.last_phase = cur_phase
            self.last_day = day_num

        # 2. Periodic Pulse Bar & Smart Batched Digest
        if current_tick - self.last_pulse_tick >= self.pulse_interval_ticks:
            self.last_pulse_tick = current_tick
            self._flush_pulse_digest(current_tick, time_snap, entities_list, weather_mgr)

    def _announce_diurnal_shift(self, phase: str, day_num: int, time_snap: Any) -> None:
        """Broadcasts evocative narrative transitions between dawn, midday, dusk, and night."""
        if self.verbosity in ("off", "quiet"):
            return

        if phase == "DAWN":
            msg = f"☀️  [Dawn Breaks] Morning sunlight warms the continent (Day {day_num}). Herds awaken and begin foraging across grasslands."
        elif phase == "MIDDAY":
            lux = getattr(time_snap, "daylight_factor", 1.0) * 98000.0
            msg = f"🌞 [Midday Zenith] High sun reaches its peak ({lux:,.0f} Lux). Flora photosynthesis flourishes; activity peaks."
        elif phase == "DUSK":
            msg = f"🌆 [Dusk Settles] Amber twilight falls across the horizon. Organisms seek shelter or roosts as temperatures cool."
        else:  # NIGHT
            msg = f"🌙 [Nightfall] Darkness envelopes the wilderness. Nocturnal predators awaken; humans gather around campfire embers."
        self.log_to_terminal(msg)

    def _flush_pulse_digest(
        self,
        current_tick: int,
        time_snap: Any,
        entities_list: List[Any],
        weather_mgr: Optional[Any],
    ) -> None:
        """Compiles clean, non-spam status bar and flushed activity highlights."""
        alive = [e for e in entities_list if getattr(e, "is_alive", False)]
        if not alive:
            self.log_to_terminal(f"─── [Tick {current_tick:,} | ⚠️ Ecosystem Dormant: 0 active organisms] ───")
            return

        # Demographic count
        humans = sum(1 for e in alive if str(getattr(e, "species_id", "")).lower() in ("homo_sapiens", "human") or getattr(e, "entity_type", None) and e.entity_type.name == "HUMAN")
        herbivores = sum(1 for e in alive if str(getattr(e, "species_id", "")).lower() in ("gazelle", "deer", "rabbit", "herbivore") or getattr(e, "entity_type", None) and e.entity_type.name == "HERBIVORE")
        predators = sum(1 for e in alive if str(getattr(e, "species_id", "")).lower() in ("panther", "wolf", "predator") or getattr(e, "entity_type", None) and e.entity_type.name in ("PREDATOR", "CARNIVORE"))
        plants = sum(1 for e in alive if "tree" in str(getattr(e, "species_id", "")).lower() or "plant" in str(getattr(e, "species_id", "")).lower() or "fern" in str(getattr(e, "species_id", "")).lower() or getattr(e, "entity_type", None) and e.entity_type.name == "PLANT")
        others = len(alive) - (humans + herbivores + predators + plants)

        # Built structures count
        from project.civilization.settlement import world_settlement_mgr
        num_structures = len([s for s in world_settlement_mgr.structures.values() if s.is_active])

        # Weather / Atmosphere metrics
        temp_str = "23.5°C"
        weather_str = "Clear"
        if weather_mgr and hasattr(weather_mgr, "grid") and hasattr(weather_mgr.grid, "mean_temperature"):
            try:
                temp_c = weather_mgr.grid.mean_temperature()
                temp_str = f"{temp_c:.1f}°C"
            except Exception:
                pass

        day_str = f"Day {time_snap.day}, {self.last_phase or 'DAY'}" if time_snap else "Day 1"

        # ── Step A: World Status Pulse Bar ──
        if self.verbosity != "quiet":
            pulse_bar = (
                f"─── [Tick {current_tick:,} | {day_str} | 👥 {humans} Humans ({num_structures} Structures) | "
                f"🦌 {herbivores} Prey | 🐆 {predators} Predators | 🌿 {plants} Flora | 🌡️ {temp_str}] ───"
            )
            self.log_to_terminal(pulse_bar)

        # ── Step B: Civilization Breakthroughs ──
        for tech_msg in self.buffered_tech:
            self.log_to_terminal(tech_msg)
        for struct_msg in self.buffered_structures:
            self.log_to_terminal(struct_msg)
        if self.buffered_civ_events:
            # Aggregate minor crafts
            sample_craft = self.buffered_civ_events[0]
            if len(self.buffered_civ_events) == 1:
                self.log_to_terminal(sample_craft)
            else:
                self.log_to_terminal(f"🔨 [Genesis Tribe] Clan crafted {len(self.buffered_civ_events)} tools and survival provisions.")

        # ── Step C: Predation & Wildlife Hunts ──
        if self.buffered_hunts:
            counterattacks = [h for h in self.buffered_hunts if h["counterattack"]]
            normal_hunts = [h for h in self.buffered_hunts if not h["counterattack"]]

            if counterattacks:
                self.log_to_terminal(f"🛡️  [Tribal Defense] Clan hunters repelled {len(counterattacks)} aggressive predator attack(s) near the settlement!")
            if normal_hunts:
                if len(normal_hunts) == 1:
                    h = normal_hunts[0]
                    self.log_to_terminal(f"⚔️  [Wildlife] A {h['predator'].title()} hunted a {h['prey'].title()} in the wilderness.")
                else:
                    self.log_to_terminal(f"⚔️  [Wildlife] Ecosystem predation: {len(normal_hunts)} successful hunts recorded across perimeter ranges.")

        # ── Step D: Life Demographics & Ecosystem Pulse ──
        total_births = sum(self.buffered_births.values())
        total_deaths = sum(self.buffered_deaths.values())
        if total_births > 0 or total_deaths > 0:
            birth_details = ", ".join(f"{cnt} {sp}" for sp, cnt in list(self.buffered_births.items())[:3])
            death_details = ", ".join(f"{cnt} {sp}" for sp, cnt in list(self.buffered_deaths.items())[:2])
            parts = []
            if total_births > 0:
                parts.append(f"+{total_births} births ({birth_details})")
            if total_deaths > 0:
                parts.append(f"{total_deaths} mortalities ({death_details})")
            self.log_to_terminal(f"🌱 [Ecosystem Pulse] {' | '.join(parts)}")

        # ── Step E: Discoveries, Miracles, and Hazards ──
        for d in self.buffered_discoveries:
            self.log_to_terminal(d)
        for m in self.buffered_miracles:
            self.log_to_terminal(m)
        for hz in self.buffered_disasters:
            self.log_to_terminal(hz)

        # Clear buffered aggregation for next window
        self.buffered_civ_events.clear()
        self.buffered_tech.clear()
        self.buffered_structures.clear()
        self.buffered_hunts.clear()
        self.buffered_births.clear()
        self.buffered_deaths.clear()
        self.buffered_discoveries.clear()
        self.buffered_miracles.clear()
        self.buffered_disasters.clear()


# Global Singleton Instance
activity_chronicler = ActivityChronicler()
