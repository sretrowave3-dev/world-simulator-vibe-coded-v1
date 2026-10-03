"""
project/utils/spatial_hash.py

High-performance 2D Spatial Hash Grid for O(1) amortized spatial partitioning,
proximity queries, vision cones, collision candidates, and nearest neighbor searches.

Architectural Guarantees:
- O(1) amortized insertion, update, and removal of dynamic entities.
- Fast radial queries without full-population iteration.
- Zero external dependencies.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar

T = TypeVar("T")
GridCoords = Tuple[int, int]


class SpatialHashGrid(Generic[T]):
    """
    Infinite 2D Spatial Hash Table.
    Divides continuous 2D space into uniform grid cells of cell_size.
    """

    __slots__ = ("cell_size", "inv_cell_size", "_buckets", "_entity_cells")

    def __init__(self, cell_size: float = 32.0) -> None:
        if cell_size <= 0.0:
            raise ValueError(f"cell_size must be positive, got {cell_size}")
        self.cell_size: float = cell_size
        self.inv_cell_size: float = 1.0 / cell_size
        self._buckets: Dict[GridCoords, Set[T]] = {}
        self._entity_cells: Dict[T, GridCoords] = {}

    def _hash_coords(self, x: float, y: float) -> GridCoords:
        return (int(math.floor(x * self.inv_cell_size)), int(math.floor(y * self.inv_cell_size)))

    def clear(self) -> None:
        """Clears all buckets and entity tracking."""
        self._buckets.clear()
        self._entity_cells.clear()

    @property
    def count(self) -> int:
        """Returns total number of tracked entities."""
        return len(self._entity_cells)

    def insert(self, entity: T, x: float, y: float) -> None:
        """Inserts an entity at position (x, y). If already present, updates location."""
        cell = self._hash_coords(x, y)
        old_cell = self._entity_cells.get(entity)

        if old_cell is not None:
            if old_cell == cell:
                return  # Still in the same cell
            self._buckets[old_cell].discard(entity)
            if not self._buckets[old_cell]:
                del self._buckets[old_cell]

        if cell not in self._buckets:
            self._buckets[cell] = set()
        self._buckets[cell].add(entity)
        self._entity_cells[entity] = cell

    def update_position(self, entity: T, x: float, y: float) -> bool:
        """
        Updates entity position.
        Returns True if entity crossed cell boundaries, False otherwise.
        """
        cell = self._hash_coords(x, y)
        old_cell = self._entity_cells.get(entity)

        if old_cell == cell:
            return False

        if old_cell is not None and old_cell in self._buckets:
            self._buckets[old_cell].discard(entity)
            if not self._buckets[old_cell]:
                del self._buckets[old_cell]

        if cell not in self._buckets:
            self._buckets[cell] = set()
        self._buckets[cell].add(entity)
        self._entity_cells[entity] = cell
        return True

    def remove(self, entity: T) -> bool:
        """Removes an entity from the spatial grid. Returns True if removed."""
        cell = self._entity_cells.pop(entity, None)
        if cell is None:
            return False

        if cell in self._buckets:
            self._buckets[cell].discard(entity)
            if not self._buckets[cell]:
                del self._buckets[cell]
        return True

    def get_cell(self, entity: T) -> Optional[GridCoords]:
        """Returns current grid coordinates of entity."""
        return self._entity_cells.get(entity)

    # -------------------------------------------------------------------------
    # SPATIAL QUERIES
    # -------------------------------------------------------------------------

    def query_radius(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        position_getter: Optional[Callable[[T], Tuple[float, float]]] = None
    ) -> List[T]:
        """
        Queries all entities within Euclidean radius of (center_x, center_y).
        If position_getter is provided, does exact distance filtering.
        Otherwise returns all entities in overlapping grid buckets.
        """
        if radius < 0.0:
            return []

        min_cell_x = int(math.floor((center_x - radius) * self.inv_cell_size))
        max_cell_x = int(math.floor((center_x + radius) * self.inv_cell_size))
        min_cell_y = int(math.floor((center_y - radius) * self.inv_cell_size))
        max_cell_y = int(math.floor((center_y + radius) * self.inv_cell_size))

        results: List[T] = []
        rad_sq = radius * radius

        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                bucket = self._buckets.get((cx, cy))
                if bucket is not None:
                    if position_getter is not None:
                        for entity in bucket:
                            ex, ey = position_getter(entity)
                            dx = ex - center_x
                            dy = ey - center_y
                            if (dx * dx + dy * dy) <= rad_sq:
                                results.append(entity)
                    else:
                        for entity in bucket:
                            ex = getattr(entity, "pos_x", None)
                            if ex is not None:
                                ey = getattr(entity, "pos_y", 0.0)
                                dx = ex - center_x
                                dy = ey - center_y
                                if (dx * dx + dy * dy) <= rad_sq:
                                    results.append(entity)
                            else:
                                results.append(entity)

        return results

    def query_box(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        position_getter: Optional[Callable[[T], Tuple[float, float]]] = None
    ) -> List[T]:
        """Queries all entities within axis-aligned bounding box."""
        min_cell_x = int(math.floor(min_x * self.inv_cell_size))
        max_cell_x = int(math.floor(max_x * self.inv_cell_size))
        min_cell_y = int(math.floor(min_y * self.inv_cell_size))
        max_cell_y = int(math.floor(max_y * self.inv_cell_size))

        results: List[T] = []

        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                bucket = self._buckets.get((cx, cy))
                if bucket is not None:
                    if position_getter is not None:
                        for entity in bucket:
                            ex, ey = position_getter(entity)
                            if min_x <= ex <= max_x and min_y <= ey <= max_y:
                                results.append(entity)
                    else:
                        results.extend(bucket)

        return results

    def query_nearest(
        self,
        center_x: float,
        center_y: float,
        max_radius: float,
        position_getter: Callable[[T], Tuple[float, float]],
        filter_predicate: Optional[Callable[[T], bool]] = None
    ) -> Optional[Tuple[T, float]]:
        """
        Finds the nearest entity within max_radius matching filter_predicate.
        Returns: (nearest_entity, distance) or None.
        """
        candidates = self.query_radius(center_x, center_y, max_radius)
        if not candidates:
            return None

        best_entity: Optional[T] = None
        best_dist_sq: float = max_radius * max_radius

        for entity in candidates:
            if filter_predicate is not None and not filter_predicate(entity):
                continue
            ex, ey = position_getter(entity)
            dx = ex - center_x
            dy = ey - center_y
            d_sq = dx * dx + dy * dy
            if d_sq <= best_dist_sq:
                best_dist_sq = d_sq
                best_entity = entity

        if best_entity is not None:
            return (best_entity, math.sqrt(best_dist_sq))
        return None
