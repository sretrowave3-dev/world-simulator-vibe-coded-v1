"""
project/core/cache_bridge.py

Modern Multi-Channel Cache Bridge & High-Performance Memory Bus.
Provides zero-latency, thread-decoupled memory channels between Backend Simulation,
AI Networks, Physics, Genetics, Telemetry, and Frontend Rendering with disk mirroring.
"""

from __future__ import annotations

import os
import time
import json
import threading
from typing import Any, Dict, List, Optional, Tuple
from project.core.linux_optimizer import linux_optimizer


CACHE_DIR = linux_optimizer.get_optimized_cache_dir("echo_evolution_simulator")
os.makedirs(CACHE_DIR, exist_ok=True)


class MemoryBridgeChannel:
    """
    High-speed, thread-safe memory bridge channel with dual-buffer RAM staging,
    atomic serialization, latency telemetry, and disk snapshot capabilities.
    """

    def __init__(self, name: str, disk_sync: bool = True) -> None:
        self.name = name
        self.disk_sync = disk_sync
        self.disk_path = os.path.join(CACHE_DIR, f"{name.lower()}_bridge.json")
        
        self._lock = threading.Lock()
        self._raw_json: Optional[str] = None
        self._cached_obj: Any = None
        
        # Telemetry metrics
        self.write_count = 0
        self.read_count = 0
        self.last_write_timestamp = 0.0
        self.last_read_timestamp = 0.0
        self.avg_write_latency_us = 0.0
        self.avg_read_latency_us = 0.0
        self.payload_size_bytes = 0

    def write(self, data: Any, fast_mirror: bool = True) -> None:
        """Pushes data into the bridge with microsecond latency tracking."""
        t0 = time.perf_counter()
        try:
            serialized = json.dumps(data)
            payload_len = len(serialized.encode("utf-8"))
        except Exception:
            serialized = "{}"
            payload_len = 2

        with self._lock:
            self._raw_json = serialized
            self._cached_obj = data
            self.write_count += 1
            self.last_write_timestamp = time.time()
            self.payload_size_bytes = payload_len

        dt_us = (time.perf_counter() - t0) * 1_000_000.0
        self.avg_write_latency_us = (self.avg_write_latency_us * 0.9) + (dt_us * 0.1)

        if fast_mirror and self.disk_sync and self.write_count % 100 == 0:
            self.flush_to_disk_async()

    def read(self) -> Any:
        """Reads parsed data with zero lock-contention ping."""
        t0 = time.perf_counter()
        with self._lock:
            self.read_count += 1
            self.last_read_timestamp = time.time()
            raw = self._raw_json
            cached = self._cached_obj

        if raw is not None:
            try:
                result = json.loads(raw)
            except Exception:
                result = cached
        else:
            result = cached

        dt_us = (time.perf_counter() - t0) * 1_000_000.0
        self.avg_read_latency_us = (self.avg_read_latency_us * 0.9) + (dt_us * 0.1)
        return result

    def read_fast(self) -> Any:
        """Ultra-fast zero-copy read without JSON re-parsing for same-process thread consumers."""
        with self._lock:
            self.read_count += 1
            return self._cached_obj

    def flush_to_disk(self) -> bool:
        """Atomically persists in-memory bridge state to cache directory."""
        with self._lock:
            payload = self._raw_json

        if payload is None:
            return False

        try:
            temp_path = self.disk_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(payload)
            os.replace(temp_path, self.disk_path)
            return True
        except Exception:
            return False

    def flush_to_disk_async(self) -> None:
        """Flushes cache in a background daemon thread."""
        threading.Thread(target=self.flush_to_disk, daemon=True).start()

    def clear(self) -> None:
        with self._lock:
            self._raw_json = None
            self._cached_obj = None
            self.payload_size_bytes = 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "writes": self.write_count,
            "reads": self.read_count,
            "size_kb": round(self.payload_size_bytes / 1024.0, 2),
            "write_latency_us": round(self.avg_write_latency_us, 1),
            "read_latency_us": round(self.avg_read_latency_us, 1),
            "disk_path": self.disk_path,
        }


class CacheBridgeHub:
    """
    Central Nervous System for Simulation Data Buses.
    Manages dedicated channels for Rendering, AI, Physics, Genetics,
    Ecosystem, Telemetry, and Save buffering.
    """

    _instance: Optional[CacheBridgeHub] = None
    _hub_lock = threading.Lock()

    def __new__(cls) -> CacheBridgeHub:
        with cls._hub_lock:
            if cls._instance is None:
                cls._instance = super(CacheBridgeHub, cls).__new__(cls)
                cls._instance._init_hub()
            return cls._instance

    def _init_hub(self) -> None:
        self.channels: Dict[str, MemoryBridgeChannel] = {}
        self.cache_dir = CACHE_DIR
        
        # 1. Register Core Architecture Bridge Channels
        self.render_bridge = self.get_or_create("Render_Bridge")
        self.ai_bridge = self.get_or_create("AI_Neural_Bridge")
        self.physics_bridge = self.get_or_create("Physics_Spatial_Bridge")
        self.genetics_bridge = self.get_or_create("Genetics_Allele_Bridge")
        self.ecosystem_bridge = self.get_or_create("Ecosystem_Food_Bridge")
        self.telemetry_bridge = self.get_or_create("Telemetry_Profiler_Bridge")
        self.save_bridge = self.get_or_create("Save_Checkpoint_Bridge")
        self.social_bridge = self.get_or_create("Civilization_Social_Bridge")

    def get_or_create(self, name: str, disk_sync: bool = True) -> MemoryBridgeChannel:
        """Retrieves or dynamically creates a dedicated bridge channel."""
        if name not in self.channels:
            self.channels[name] = MemoryBridgeChannel(name, disk_sync=disk_sync)
        return self.channels[name]

    def flush_all(self) -> int:
        """Flushes all channels to disk cache directory."""
        count = 0
        for ch in self.channels.values():
            if ch.flush_to_disk():
                count += 1
        return count

    def clear_all(self) -> None:
        for ch in self.channels.values():
            ch.clear()

    def get_hub_metrics(self) -> List[Dict[str, Any]]:
        return [ch.get_stats() for ch in self.channels.values()]


# Global Bridge Hub Singleton
bridge_hub = CacheBridgeHub()
