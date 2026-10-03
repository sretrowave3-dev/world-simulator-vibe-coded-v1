"""
project/core/memory_cache.py

Modernized RAM Cache & Synchronous Bridge Connector Module.
Wraps CacheBridgeHub with backwards-compatible interfaces for existing systems.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional
from project.core.cache_bridge import bridge_hub, MemoryBridgeChannel, CACHE_DIR


class FastMemoryCache:
    """
    JSON-backed RAM block for parallel sync tasks, backed by MemoryBridgeChannel.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self._channel = bridge_hub.get_or_create(name)

    def write(self, key: str, data: Any) -> None:
        current = self._channel.read_fast() or {}
        if not isinstance(current, dict):
            current = {}
        current[key] = data
        self._channel.write(current)

    def read(self, key: str) -> Any:
        current = self._channel.read_fast()
        if isinstance(current, dict):
            return current.get(key)
        return None

    def dump_to_disk(self) -> None:
        self._channel.flush_to_disk()

    def clear(self) -> None:
        self._channel.clear()


class JSONRepeaterSync:
    """
    Acts as a low-ping repeater, connector, and syncer between Backend (Physics) 
    and Frontend (UI). Utilizes double-buffered JSON RAM to eliminate thread lag.
    """
    def __init__(self) -> None:
        self._channel = bridge_hub.render_bridge

    def push_backend(self, state_data: Any) -> None:
        """Backend pushes state into the repeater cache as a fast JSON payload."""
        self._channel.write(state_data, fast_mirror=False)

    def pull_frontend(self) -> Any:
        """Frontend pulls the latest state with zero ping and zero JSON deserialization lag."""
        data = self._channel.read_fast()
        if data is None:
            data = self._channel.read()
        return data if data is not None else []


# Global Frontend/Backend Connector
frontend_repeater = JSONRepeaterSync()

# Core Tier 1 Memory Caches
ai_ram = FastMemoryCache("AI_Nodes")
physics_ram = FastMemoryCache("Physics_State")
civ_ram = FastMemoryCache("Civilization_Data")
ui_ram = FastMemoryCache("UI_Render_Buffer")

# Expanded Tier 2 Memory Caches
genetics_ram = FastMemoryCache("Genetics_Pool")
food_ram = FastMemoryCache("Food_Ecology")
weather_ram = FastMemoryCache("Atmospheric_Data")
social_ram = FastMemoryCache("Social_Network")
combat_ram = FastMemoryCache("Combat_Events")
pathfinding_ram = FastMemoryCache("Navigation_Mesh")
disease_ram = FastMemoryCache("Pathogen_Vectors")
terrain_ram = FastMemoryCache("Geology_State")
gemini_ram = FastMemoryCache("Gemini_Hivemind_Buffer")
telemetry_ram = FastMemoryCache("Telemetry_Metrics")
save_ram = FastMemoryCache("Save_Staging")


class DynamicRAMBank:
    """
    Dynamically allocates new independent JSON RAM blocks on-the-fly 
    for procedural systems, ensuring infinite scalability without code destruction.
    """
    def __init__(self) -> None:
        self._banks: Dict[str, FastMemoryCache] = {}
        self._lock = threading.Lock()

    def get_ram(self, name: str) -> FastMemoryCache:
        with self._lock:
            if name not in self._banks:
                self._banks[name] = FastMemoryCache(f"Dynamic_{name}")
            return self._banks[name]

    def flush_all_to_disk(self) -> None:
        bridge_hub.flush_all()


# Global dynamic RAM allocator
ram_allocator = DynamicRAMBank()
