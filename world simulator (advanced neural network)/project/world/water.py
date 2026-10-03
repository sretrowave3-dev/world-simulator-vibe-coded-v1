"""
project/world/water.py

Planetary Hydrology & Water Dynamics Subsystem for the ALife Research Platform.

Features:
- Water depth, flow vectors (flow_x, flow_y), salinity, purity, and temperature.
- Hydraulic transport, evaporation, and precipitation absorption.
- Thirst replenishment and swimming dynamics query interfaces.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class WaterType(enum.IntEnum):
    NONE = 0
    FRESHWATER_RIVER = 1
    FRESHWATER_LAKE = 2
    OCEAN = 3
    SWAMP_WATER = 4
    GLACIAL_ICE = 5


@dataclass(slots=True)
class WaterState:
    water_type: WaterType = WaterType.NONE
    depth: float = 0.0          # Water column depth in meters
    flow_x: float = 0.0         # Surface flow vector X (m/s)
    flow_y: float = 0.0         # Surface flow vector Y (m/s)
    salinity: float = 0.0       # 0.0 (pure fresh) to 35.0 (marine ppt)
    purity: float = 1.0         # 0.0 (toxic) to 1.0 (clean drinkable)
    temperature_c: float = 15.0 # Water temperature

    @property
    def is_drinkable(self) -> bool:
        return self.depth > 0.05 and self.salinity < 5.0 and self.purity > 0.5


class WaterChunk:
    """Struct-of-Arrays (SoA) layout for water bodies across 16x16 chunk cells."""

    CELL_COUNT: int = 256  # 16x16
    SIDE: int = 16

    __slots__ = (
        "chunk_coords",
        "water_type",
        "depth",
        "flow_x",
        "flow_y",
        "salinity",
        "purity",
        "temperature",
    )

    def __init__(self, chunk_coords: Tuple[int, int]) -> None:
        self.chunk_coords = chunk_coords
        self.water_type: List[int] = [WaterType.NONE.value] * self.CELL_COUNT
        self.depth: List[float] = [0.0] * self.CELL_COUNT
        self.flow_x: List[float] = [0.0] * self.CELL_COUNT
        self.flow_y: List[float] = [0.0] * self.CELL_COUNT
        self.salinity: List[float] = [0.0] * self.CELL_COUNT
        self.purity: List[float] = [1.0] * self.CELL_COUNT
        self.temperature: List[float] = [15.0] * self.CELL_COUNT

    def get_state(self, local_x: int, local_y: int) -> WaterState:
        idx = (local_y & 15) * 16 + (local_x & 15)
        return WaterState(
            water_type=WaterType(self.water_type[idx]),
            depth=self.depth[idx],
            flow_x=self.flow_x[idx],
            flow_y=self.flow_y[idx],
            salinity=self.salinity[idx],
            purity=self.purity[idx],
            temperature_c=self.temperature[idx],
        )

    def drink(self, local_x: int, local_y: int, volume_liters: float) -> Tuple[float, float]:
        """
        Organism drinking transaction.
        Returns (actual_liters_drank, toxicity_ingested).
        """
        idx = (local_y & 15) * 16 + (local_x & 15)
        if self.depth[idx] <= 0.01:
            return (0.0, 0.0)

        # 1 cubic meter of water = 1000 liters
        depth_drawn = (volume_liters / 1000.0)
        actual_drawn = min(self.depth[idx], depth_drawn)
        self.depth[idx] -= actual_drawn

        actual_liters = actual_drawn * 1000.0
        toxicity = (1.0 - self.purity[idx]) * (1.0 if self.salinity[idx] > 5.0 else 0.5)

        return (actual_liters, toxicity)

    def tick_hydrology(self, dt: float, ambient_temp: float, rainfall: float) -> None:
        """Evaporation, precipitation replenishment, and thermal equilibration."""
        for i in range(self.CELL_COUNT):
            if rainfall > 0.0:
                self.depth[i] += rainfall * 0.01 * dt
                # Rain cleanses salinity & impurities
                self.salinity[i] = max(0.0, self.salinity[i] - 0.01 * dt)
                self.purity[i] = min(1.0, self.purity[i] + 0.005 * dt)

            if self.depth[i] > 0.0:
                # Evaporation driven by temperature
                evap_rate = max(0.0, ambient_temp * 0.0001) * dt
                self.depth[i] = max(0.0, self.depth[i] - evap_rate)
                if self.depth[i] <= 0.001:
                    self.depth[i] = 0.0
                    self.water_type[i] = WaterType.NONE.value


class WaterManager:
    """
    Subsystem coordinator managing hydrological bodies and dynamic flow queries.
    """

    def __init__(self) -> None:
        self.chunks: Dict[Tuple[int, int], WaterChunk] = {}

    def get_or_create_chunk(self, chunk_coords: Tuple[int, int]) -> WaterChunk:
        if chunk_coords not in self.chunks:
            self.chunks[chunk_coords] = WaterChunk(chunk_coords)
        return self.chunks[chunk_coords]

    def query_water(self, global_x: float, global_y: float) -> WaterState:
        cx = int(math.floor(global_x / 16.0))
        cy = int(math.floor(global_y / 16.0))
        lx = int(math.floor(global_x)) % 16
        ly = int(math.floor(global_y)) % 16
        chunk = self.get_or_create_chunk((cx, cy))
        return chunk.get_state(lx, ly)

    def tick(self, dt: float, ambient_temp: float = 20.0, rainfall: float = 0.0) -> None:
        for chunk in self.chunks.values():
            chunk.tick_hydrology(dt, ambient_temp, rainfall)

    def reset(self) -> None:
        self.chunks.clear()
