"""
project/core/world_telemetry.py

World State Telemetry & Active User Analytics Collector.
Provides multi-tier telemetry extraction:
1. SUMMARY: High-level population, climate, and evolutionary metrics.
2. DEEP: Granular ecosystem health, species genetics, neural complexity, and civilization logs.
3. FULL: Serialized simulation snapshot ("literally everything" - entities, genomes, brains, terrain).

Guarantees:
- Strict Opt-In Gatekeeping: zero data leaves without explicit user consent.
- Complete PII & Secret Scrubbing: sanitizes all paths and tokens.
- Lightweight Compression: large world states are compressed (zlib + base64) for free webhook/REST delivery.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import time
import zlib
from typing import Dict, Any, List, Optional
from project.core.user_profile import user_profile_manager
from project.core.telemetry_dispatcher import telemetry_dispatcher, TelemetrySanitizer
from project.core.telemetry_config import (
    DEFAULT_WORLD_STATE_LEVEL,
    MAX_UNCOMPRESSED_PAYLOAD_BYTES,
)


class WorldTelemetryCollector:
    """Collects and packages world states and active user heartbeats."""

    def __init__(self) -> None:
        self.session_id: str = f"sess_{int(time.time())}_{os.urandom(4).hex()}"
        self.session_start_time: float = time.time()
        self.last_heartbeat_time: float = 0.0
        self.last_world_dispatch_tick: int = 0

    def get_uptime_seconds(self) -> float:
        return time.time() - self.session_start_time

    # -------------------------------------------------------------------------
    # 1. Active User Heartbeat (How many people are running it)
    # -------------------------------------------------------------------------
    def dispatch_heartbeat(
        self,
        tick: int = 0,
        entities_count: int = 0,
        fps: float = 60.0,
        ups: float = 60.0,
        status: str = "active",
    ) -> None:
        """Dispatches an active user heartbeat ping (counts live users & sessions)."""
        prof = user_profile_manager.get_profile()
        if not prof.privacy_and_telemetry.get("consent_given", False):
            return

        client_id = prof.privacy_and_telemetry.get("anonymized_client_id", "anon_default")
        app_version = "2.1.0"
        
        # Read commit SHA if available
        commit_sha = "unknown"
        commit_file = os.path.join(os.path.dirname(__file__), "..", "..", ".current_commit")
        if os.path.exists(commit_file):
            try:
                with open(commit_file, "r", encoding="utf-8") as f:
                    commit_sha = f.read().strip()[:7]
            except Exception:
                pass

        heartbeat_data = {
            "client_id": client_id,
            "session_id": self.session_id,
            "status": status,  # "active", "heartbeat", "paused", "shutdown"
            "uptime_seconds": round(self.get_uptime_seconds(), 1),
            "sim_tick": tick,
            "entities_alive": entities_count,
            "performance": {
                "fps": round(fps, 1),
                "ups": round(ups, 1),
            },
            "environment": {
                "os": platform.system(),
                "os_release": platform.release(),
                "python": platform.python_version(),
                "app_version": app_version,
                "commit_sha": commit_sha,
                "is_offline_mode": prof.gemini.get("is_offline", False),
            }
        }

        telemetry_dispatcher.record_event(
            event_type="ACTIVE_USER_HEARTBEAT",
            details=heartbeat_data,
            severity="INFO",
        )
        self.last_heartbeat_time = time.time()

    # -------------------------------------------------------------------------
    # 2. Multi-Tier World State Telemetry ("Summary to literally everything")
    # -------------------------------------------------------------------------
    def build_summary_state(
        self,
        entities_list: List[Any],
        time_mgr: Optional[Any] = None,
        weather_mgr: Optional[Any] = None,
        soil_mgr: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Tier 1: High-level world summary."""
        alive_entities = [e for e in entities_list if getattr(e, "is_alive", True)]
        
        # Breakdown by species / role
        species_counts: Dict[str, int] = {}
        total_energy = 0.0
        total_health = 0.0
        max_gen = 0

        for e in alive_entities:
            sp = getattr(e, "species_id", e.__class__.__name__)
            species_counts[sp] = species_counts.get(sp, 0) + 1
            total_energy += getattr(e, "energy", 0.0)
            total_health += getattr(e, "health", 0.0)
            gen = getattr(e, "generation", 0)
            if gen > max_gen:
                max_gen = gen

        n_alive = len(alive_entities)
        avg_energy = round(total_energy / max(1, n_alive), 1)
        avg_health = round(total_health / max(1, n_alive), 1)

        sim_tick = getattr(time_mgr, "current_tick", 0) if time_mgr else 0
        sim_sec = getattr(time_mgr, "total_seconds", 0.0) if time_mgr else 0.0

        return {
            "tier": "SUMMARY",
            "tick": sim_tick,
            "simulation_seconds": round(sim_sec, 1),
            "sim_days": round(sim_sec / 86400.0, 2) if sim_sec else 0.0,
            "population": {
                "total_alive": n_alive,
                "species_breakdown": species_counts,
                "average_energy": avg_energy,
                "average_health": avg_health,
                "max_generation": max_gen,
                "species_diversity_count": len(species_counts),
            },
            "climate": {
                "season": getattr(weather_mgr, "current_season", "SPRING") if weather_mgr else "UNKNOWN",
                "temperature_c": getattr(weather_mgr, "current_temp", 22.0) if weather_mgr else 22.0,
            }
        }

    def build_deep_state(
        self,
        entities_list: List[Any],
        time_mgr: Optional[Any] = None,
        weather_mgr: Optional[Any] = None,
        soil_mgr: Optional[Any] = None,
        water_mgr: Optional[Any] = None,
        ruins_mgr: Optional[Any] = None,
        miracles_mgr: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Tier 2: Detailed ecosystem, neural metrics, genetics, and civilization telemetry."""
        base = self.build_summary_state(entities_list, time_mgr, weather_mgr, soil_mgr)
        base["tier"] = "DEEP"

        alive_entities = [e for e in entities_list if getattr(e, "is_alive", True)]

        # Find top 5 oldest organisms
        sorted_by_age = sorted(alive_entities, key=lambda e: getattr(e, "age", 0.0), reverse=True)
        oldest_records = []
        for e in sorted_by_age[:5]:
            oldest_records.append({
                "id": getattr(e, "entity_id", "unknown"),
                "species": getattr(e, "species_id", e.__class__.__name__),
                "age": round(getattr(e, "age", 0.0), 1),
                "generation": getattr(e, "generation", 0),
                "health": round(getattr(e, "health", 0.0), 1),
            })

        # Genetic and behavioral metrics
        speed_sum = 0.0
        metabolism_sum = 0.0
        with_brains = 0

        for e in alive_entities:
            speed_sum += getattr(e, "speed", 1.0)
            metabolism_sum += getattr(e, "metabolism_rate", 1.0)
            if hasattr(e, "brain") and e.brain is not None:
                with_brains += 1

        n = max(1, len(alive_entities))
        base["ecosystem_details"] = {
            "oldest_organisms": oldest_records,
            "neural_agents_count": with_brains,
            "average_speed": round(speed_sum / n, 2),
            "average_metabolism": round(metabolism_sum / n, 2),
        }

        # Ruins and Ancient Monuments
        if ruins_mgr and hasattr(ruins_mgr, "monoliths"):
            base["ancient_ruins"] = {
                "total_monoliths": len(getattr(ruins_mgr, "monoliths", [])),
                "active_portals": len(getattr(ruins_mgr, "portals", [])),
            }

        # Miracles
        if miracles_mgr and hasattr(miracles_mgr, "event_log"):
            base["recent_miracles_count"] = len(getattr(miracles_mgr, "event_log", []))

        return base

    def build_full_state(
        self,
        entities_list: List[Any],
        time_mgr: Optional[Any] = None,
        weather_mgr: Optional[Any] = None,
        soil_mgr: Optional[Any] = None,
        water_mgr: Optional[Any] = None,
        veg_mgr: Optional[Any] = None,
        res_mgr: Optional[Any] = None,
        gemini_sys: Optional[Any] = None,
        ruins_mgr: Optional[Any] = None,
        miracles_mgr: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Tier 3: 'Literally Everything' — Complete serialized ECS simulation dump."""
        from project.core.persistence import PersistenceManager

        # Full engine state serialization
        full_dict = PersistenceManager.serialize_state(
            time_mgr=time_mgr,
            soil_mgr=soil_mgr,
            water_mgr=water_mgr,
            veg_mgr=veg_mgr,
            res_mgr=res_mgr,
            entities_list=entities_list,
            gemini_sys=gemini_sys,
            ruins_mgr=ruins_mgr,
            miracles_mgr=miracles_mgr,
        )

        full_dict["tier"] = "FULL_DUMP"
        full_dict["export_timestamp"] = time.time()
        full_dict["session_id"] = self.session_id

        # Check payload size; compress if large
        raw_json = json.dumps(full_dict, default=str)
        raw_bytes = raw_json.encode("utf-8")

        if len(raw_bytes) > MAX_UNCOMPRESSED_PAYLOAD_BYTES:
            compressed = zlib.compress(raw_bytes, level=6)
            b64_str = base64.b64encode(compressed).decode("ascii")
            return {
                "tier": "FULL_DUMP_COMPRESSED",
                "compression": "zlib+base64",
                "uncompressed_bytes": len(raw_bytes),
                "compressed_bytes": len(compressed),
                "entities_count": len(entities_list),
                "payload_b64": b64_str,
            }

        return full_dict

    def dispatch_world_state(
        self,
        entities_list: List[Any],
        time_mgr: Optional[Any] = None,
        weather_mgr: Optional[Any] = None,
        soil_mgr: Optional[Any] = None,
        water_mgr: Optional[Any] = None,
        veg_mgr: Optional[Any] = None,
        res_mgr: Optional[Any] = None,
        ruins_mgr: Optional[Any] = None,
        miracles_mgr: Optional[Any] = None,
        force_level: Optional[str] = None,
    ) -> bool:
        """Packages and dispatches the world state based on consent and configured level."""
        prof = user_profile_manager.get_profile()
        if not prof.privacy_and_telemetry.get("consent_given", False):
            return False

        level = (force_level or prof.privacy_and_telemetry.get("world_data_level") or DEFAULT_WORLD_STATE_LEVEL).upper()

        if level == "SUMMARY":
            payload = self.build_summary_state(entities_list, time_mgr, weather_mgr, soil_mgr)
            event_type = "WORLD_STATE_SUMMARY"
        elif level == "DEEP":
            payload = self.build_deep_state(entities_list, time_mgr, weather_mgr, soil_mgr, water_mgr, ruins_mgr, miracles_mgr)
            event_type = "WORLD_STATE_DEEP"
        else:  # "FULL"
            payload = self.build_full_state(
                entities_list, time_mgr, weather_mgr, soil_mgr, water_mgr,
                veg_mgr, res_mgr, None, ruins_mgr, miracles_mgr
            )
            event_type = "WORLD_STATE_FULL_DUMP"

        telemetry_dispatcher.record_event(
            event_type=event_type,
            details=payload,
            severity="INFO",
        )
        self.last_world_dispatch_tick = getattr(time_mgr, "current_tick", 0) if time_mgr else 0
        return True


# Global singleton
world_telemetry_collector = WorldTelemetryCollector()
