"""
project/world/resources.py

Planetary Natural Resource Subsystem for the ALife Research Platform.

Features:
- Discrete resource nodes (Minerals, Forestry, Stone Quarries, Crystal Vents, Rare Earths).
- Chunk-partitioned spatial indexing for fast foraging/mining queries.
- Closed regeneration loops and depletion mechanics.
- Thread-safe extraction transactions.
"""

from __future__ import annotations

import enum
import math
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


class ResourceType(enum.IntEnum):
    NONE = 0
    WOOD = 1
    STONE = 2
    IRON = 3
    GOLD = 4
    COAL = 5
    CRYSTAL = 6
    MEDICINE = 7
    OBSIDIAN = 8
    SAND = 9
    PEAT = 10
    RELIC = 11
    RARE_MINERALS = 12


@dataclass(slots=True)
class ResourceNode:
    node_id: int
    resource_type: ResourceType
    pos_x: float
    pos_y: float
    quantity: float
    max_capacity: float
    regeneration_rate_per_sec: float
    hardness: float  # 0.0 to 1.0 (mining difficulty / tool requirement)
    is_depleted: bool = False

    def harvest(self, amount: float, tool_efficiency: float = 1.0) -> float:
        """Extracts resource amount modulated by tool efficiency."""
        if self.is_depleted or self.quantity <= 0.0:
            return 0.0

        effective_harvest = min(self.quantity, amount * tool_efficiency)
        self.quantity -= effective_harvest
        if self.quantity <= 0.001:
            self.quantity = 0.0
            self.is_depleted = True
        return effective_harvest

    def regenerate(self, dt: float) -> None:
        if self.regeneration_rate_per_sec <= 0.0 or self.quantity >= self.max_capacity:
            return

        self.quantity = min(self.max_capacity, self.quantity + self.regeneration_rate_per_sec * dt)
        if self.quantity > 0.0:
            self.is_depleted = False


class ResourceManager:
    """
    Subsystem managing natural resource distribution, regeneration, and extraction.
    """

    CHUNK_SIZE: float = 64.0

    def __init__(self, seed: int = 1337) -> None:
        self.seed = seed
        self._nodes: Dict[int, ResourceNode] = {}
        self._chunk_node_map: Dict[Tuple[int, int], Set[int]] = {}
        self._next_node_id: int = 1
        self._lock = threading.Lock()

    def _chunk_coords(self, x: float, y: float) -> Tuple[int, int]:
        return (int(math.floor(x / self.CHUNK_SIZE)), int(math.floor(y / self.CHUNK_SIZE)))

    def spawn_node(
        self,
        resource_type: ResourceType,
        x: float,
        y: float,
        capacity: float = 1000.0,
        regeneration_rate: float = 0.5,
        hardness: float = 0.2,
    ) -> ResourceNode:
        with self._lock:
            nid = self._next_node_id
            self._next_node_id += 1

            node = ResourceNode(
                node_id=nid,
                resource_type=resource_type,
                pos_x=x,
                pos_y=y,
                quantity=capacity,
                max_capacity=capacity,
                regeneration_rate_per_sec=regeneration_rate,
                hardness=hardness,
            )
            self._nodes[nid] = node

            c_coords = self._chunk_coords(x, y)
            if c_coords not in self._chunk_node_map:
                self._chunk_node_map[c_coords] = set()
            self._chunk_node_map[c_coords].add(nid)
            return node

    def remove_node(self, node_id: int) -> bool:
        with self._lock:
            node = self._nodes.pop(node_id, None)
            if node is None:
                return False
            c_coords = self._chunk_coords(node.pos_x, node.pos_y)
            if c_coords in self._chunk_node_map:
                self._chunk_node_map[c_coords].discard(node_id)
            return True

    def tick(self, dt: float) -> None:
        """Regenerates all active resource nodes."""
        with self._lock:
            for node in self._nodes.values():
                node.regenerate(dt)

    def find_nearest_resource(
        self,
        x: float,
        y: float,
        resource_type: Optional[ResourceType] = None,
        max_radius: float = 100.0,
    ) -> Optional[Tuple[ResourceNode, float]]:
        """Finds closest non-depleted resource node within max_radius."""
        cx, cy = self._chunk_coords(x, y)
        rad_chunks = int(math.ceil(max_radius / self.CHUNK_SIZE))
        rad_sq = max_radius * max_radius

        best_node: Optional[ResourceNode] = None
        best_dist_sq = rad_sq

        with self._lock:
            for dx in range(-rad_chunks, rad_chunks + 1):
                for dy in range(-rad_chunks, rad_chunks + 1):
                    coords = (cx + dx, cy + dy)
                    node_ids = self._chunk_node_map.get(coords)
                    if not node_ids:
                        continue

                    for nid in node_ids:
                        node = self._nodes.get(nid)
                        if node is None or node.is_depleted or node.quantity <= 0.0:
                            continue
                        if resource_type is not None and node.resource_type != resource_type:
                            continue

                        dist_sq = (node.pos_x - x) ** 2 + (node.pos_y - y) ** 2
                        if dist_sq < best_dist_sq:
                            best_dist_sq = dist_sq
                            best_node = node

        if best_node is not None:
            return (best_node, math.sqrt(best_dist_sq))
        return None

    def reset(self) -> None:
        with self._lock:
            self._nodes.clear()
            self._chunk_node_map.clear()
            self._next_node_id = 1
