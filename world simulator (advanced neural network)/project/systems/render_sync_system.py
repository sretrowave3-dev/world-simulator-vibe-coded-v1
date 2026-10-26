"""
project/systems/render_sync_system.py

Render Sync System packing visual interpolation frames and telemetry packets for rendering views.
"""

from __future__ import annotations

from typing import Set, List, Dict, Any
import threading
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity


class RenderSyncSystem:
    """Synchronizes simulation states with renderer snapshots in a thread-safe manner."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list
        self._render_snapshot: List[Dict[str, Any]] = []
        self.snapshot_lock = threading.Lock()

    @property
    def name(self) -> str:
        return "RenderSyncSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.RENDER_SYNC

    @property
    def priority(self) -> int:
        return ExecutionPriority.RENDERER_SYNC

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        with self.snapshot_lock:
            self._render_snapshot.clear()

    def update(self, context: UpdateContext) -> None:
        # Create a lightweight visual copy of active entities
        new_snap = []
        for e in self._entities_list:
            if not e.is_alive:
                continue
                
            needs_obj = e.custom_data.get("needs")
            if needs_obj and hasattr(needs_obj, "to_dict"):
                needs_dict = needs_obj.to_dict()
            else:
                h_rat = max(0.0, min(1.0, 1.0 - (e.energy / max(1.0, e.max_energy))))
                t_rat = max(0.0, min(1.0, 1.0 - (e.hydration / max(1.0, e.max_hydration))))
                f_rat = max(0.0, min(1.0, 1.0 - (e.stamina / max(1.0, e.max_stamina))))
                needs_dict = {
                    "hunger": round(h_rat, 3),
                    "thirst": round(t_rat, 3),
                    "fatigue": round(f_rat, 3),
                    "fear": round(float(e.custom_data.get("fear", 0.0)), 3),
                    "curiosity": round(float(e.custom_data.get("curiosity", 0.4)), 3),
                }

            snap_data = {
                "id": e.entity_id,
                "type": e.entity_type.name,
                "x": e.pos_x,
                "y": e.pos_y,
                "z": e.pos_z,
                "radius": e.radius,
                "health": e.health,
                "max_health": e.max_health,
                "is_alive": e.is_alive,
                "heading": e.heading_angle,
                "generation": getattr(e, "generation", 1),
                "role": e.custom_data.get("emergent_role", "CITIZEN"),
                "role_title": e.custom_data.get("role_title", "Organism"),
                "consciousness": e.custom_data.get("consciousness_level", 0.0),
                "synapses": e.brain.total_synaptic_connections if e.brain else 0,
                "memory_mb": getattr(e, "memory_footprint_mb", 51.13 if e.entity_type.name == "HUMAN" else (e.memory.memory_size_mb if hasattr(e, "memory") and hasattr(e.memory, "memory_size_mb") else 0.01)),
                "action": getattr(e, "current_action", "IDLE"),
                "dopamine": round(float(e.custom_data.get("dopamine", 0.40)), 3),
                "fear": round(float(e.custom_data.get("fear", 0.0)), 3),
                "stress": round(float(e.custom_data.get("stress", 0.10)), 3),
                "species_id": str(getattr(e, "species_id", "")),
                "fruit_type": str(e.custom_data.get("fruit_type", "")),
                "has_abnormality": bool(e.custom_data.get("has_abnormality", False)),
                "abnormality_trait": str(e.custom_data.get("abnormality_trait", "")),
                "bioluminescent": bool(e.custom_data.get("bioluminescent", False)),
                "glow_color": e.custom_data.get("glow_color"),
                "giant": bool(e.custom_data.get("giant", False)),
                "needs": needs_dict,
                "ai_metrics": None
            }
            
            # Deep clone active psychological parameters for Inspector UI rendering
            if e.brain:
                # Calculate active intelligence score based on genetics and current energy
                age = getattr(e, 'age_ticks', 0)
                energy = getattr(e, 'energy', 10.0)
                brain_mut = getattr(e, 'genes', {}).get("brain_plasticity", 1.0)
                ai_score = (age * 0.1) + (energy * 0.5) * brain_mut
                
                # Direct zero-copy references for high-speed 60FPS synchronization
                snap_data["ai_metrics"] = {
                    "intelligence_score": ai_score,
                    "plasticity": brain_mut,
                    "working_memory": list(e.brain.working_memory),
                    "last_reward": e.custom_data.get("last_learning_reward", 0.0),
                    "net_sizes": list(e.brain.layer_sizes),
                    "net_outputs": e.brain.layer_outputs or [],
                    "net_weights": e.brain.weights,
                }
                
            new_snap.append(snap_data)
        
        with self.snapshot_lock:
            self._render_snapshot = new_snap
            
        import time
        from project.core.memory_cache import frontend_repeater
        
        # Save snap into JSON RAM Cache for instantaneous decoupled access
        frontend_repeater.push_backend(self._render_snapshot)

    def get_snapshot(self) -> List[Dict]:
        """Returns the synchronized state for visual rendering."""
        from project.core.memory_cache import frontend_repeater
        
        # Pull from JSON RAM repeater with zero ping
        cached = frontend_repeater.pull_frontend()
        if cached:
            return cached
            
        with self.snapshot_lock:
            return self._render_snapshot.copy()

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
