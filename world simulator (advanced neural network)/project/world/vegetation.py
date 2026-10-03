"""
project/world/vegetation.py

Planetary Flora & Vegetation Subsystem for the ALife Research Platform.

Features:
- Canopy layers, vegetation biomass, root depth, and ground coverage.
- Photosynthesis modeling driven by solar radiation, temperature, and moisture.
- Root competition and self-limiting ecological carrying capacities.
- Herbivore grazing interaction APIs.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class VegetationType(enum.IntEnum):
    NONE = 0
    GRASS = 1
    SHRUBS = 2
    FLOWERS = 3
    DECIDUOUS_TREES = 4
    CONIFEROUS_TREES = 5
    RAINFOREST_CANOPY = 6
    FUNGI = 7
    AQUATIC_ALGAE = 8


@dataclass(slots=True)
class VegetationPatch:
    veg_type: VegetationType = VegetationType.NONE
    biomass_kg: float = 0.0
    max_biomass_kg: float = 100.0
    canopy_height: float = 0.0
    density: float = 0.0  # 0.0 to 1.0 (coverage)
    health: float = 1.0   # 0.0 to 1.0
    root_depth: float = 0.5


class VegetationChunk:
    """Struct-of-Arrays (SoA) layout for vegetation across 16x16 chunk cells."""

    CELL_COUNT: int = 256  # 16x16
    SIDE: int = 16

    __slots__ = (
        "chunk_coords",
        "veg_type",
        "biomass",
        "max_biomass",
        "canopy_height",
        "density",
        "health",
        "root_depth",
    )

    def __init__(self, chunk_coords: Tuple[int, int]) -> None:
        self.chunk_coords = chunk_coords
        self.veg_type: List[int] = [VegetationType.NONE.value] * self.CELL_COUNT
        self.biomass: List[float] = [0.0] * self.CELL_COUNT
        self.max_biomass: List[float] = [100.0] * self.CELL_COUNT
        self.canopy_height: List[float] = [0.0] * self.CELL_COUNT
        self.density: List[float] = [0.0] * self.CELL_COUNT
        self.health: List[float] = [1.0] * self.CELL_COUNT
        self.root_depth: List[float] = [0.5] * self.CELL_COUNT

    def get_patch(self, local_x: int, local_y: int) -> VegetationPatch:
        idx = (local_y & 15) * 16 + (local_x & 15)
        return VegetationPatch(
            veg_type=VegetationType(self.veg_type[idx]),
            biomass_kg=self.biomass[idx],
            max_biomass_kg=self.max_biomass[idx],
            canopy_height=self.canopy_height[idx],
            density=self.density[idx],
            health=self.health[idx],
            root_depth=self.root_depth[idx],
        )

    def graze(self, local_x: int, local_y: int, requested_kg: float) -> float:
        """Herbivore grazing: consumes vegetation biomass."""
        idx = (local_y & 15) * 16 + (local_x & 15)
        if self.biomass[idx] <= 0.0:
            return 0.0

        consumed = min(self.biomass[idx], requested_kg)
        self.biomass[idx] -= consumed
        self.density[idx] = self.biomass[idx] / max(1.0, self.max_biomass[idx])
        return consumed

    def grow(
        self,
        dt: float,
        sunlight_flux: float,
        temperature_c: float,
        moisture: float,
        nitrogen_available: float,
    ) -> None:
        """Photosynthesis & biomass growth step."""
        if temperature_c < 0.0:
            return  # Growth halts below freezing

        # Thermal response curve (Bell curve peaking at 22C)
        temp_factor = math.exp(-0.5 * ((temperature_c - 22.0) / 10.0) ** 2)
        growth_rate = sunlight_flux * temp_factor * moisture * (0.5 + 0.5 * nitrogen_available) * 0.05 * dt

        for i in range(self.CELL_COUNT):
            if self.veg_type[i] == VegetationType.NONE.value or self.biomass[i] >= self.max_biomass[i]:
                continue

            # Logistic carrying capacity growth: dN/dt = r * N * (1 - N / K)
            current_b = self.biomass[i]
            max_b = self.max_biomass[i]
            delta = growth_rate * max(1.0, current_b) * (1.0 - (current_b / max_b))
            self.biomass[i] = min(max_b, current_b + max(0.0, delta))
            self.density[i] = self.biomass[i] / max_b
            self.canopy_height[i] = math.sqrt(self.density[i]) * 10.0


class VegetationManager:
    """
    Coordinator managing flora distribution and photosynthesis across active chunks.
    """

    def __init__(self) -> None:
        self.chunks: Dict[Tuple[int, int], VegetationChunk] = {}

    def get_or_create_chunk(self, chunk_coords: Tuple[int, int]) -> VegetationChunk:
        if chunk_coords not in self.chunks:
            self.chunks[chunk_coords] = VegetationChunk(chunk_coords)
        return self.chunks[chunk_coords]

    def query_vegetation(self, global_x: float, global_y: float) -> VegetationPatch:
        cx = int(math.floor(global_x / 16.0))
        cy = int(math.floor(global_y / 16.0))
        lx = int(math.floor(global_x)) % 16
        ly = int(math.floor(global_y)) % 16
        chunk = self.get_or_create_chunk((cx, cy))
        return chunk.get_patch(lx, ly)

    def tick(
        self,
        dt: float,
        sunlight_flux: float = 1.0,
        temperature_c: float = 20.0,
        moisture: float = 0.5,
    ) -> None:
        for chunk in self.chunks.values():
            chunk.grow(dt, sunlight_flux, temperature_c, moisture, nitrogen_available=0.5)

    def reset(self) -> None:
        self.chunks.clear()
