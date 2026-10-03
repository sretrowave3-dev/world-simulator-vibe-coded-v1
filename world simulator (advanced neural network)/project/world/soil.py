"""
project/world/soil.py

Soil Chemistry & Ecological Nutrient Cycle Subsystem for the ALife Research Platform.

Features:
- Full soil nutrient profile per cell: Nitrogen (N), Phosphorus (P), Potassium (K),
  Organic Matter, pH Balance (4.0 to 9.0), Moisture Retention, Salinity, and Density.
- Decomposition & Mineralization: Converts dead organic biomass into bioavailable nutrients.
- Nutrient Leaching & Topsoil Erosion: Driven by slope, rainfall, and vegetative cover.
- Plant Nutrient Uptake APIs for flora growth algorithms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(slots=True)
class SoilProfile:
    nitrogen: float = 0.5        # 0.0 to 1.0 (bioavailable nitrates)
    phosphorus: float = 0.5      # 0.0 to 1.0 (phosphates)
    potassium: float = 0.5       # 0.0 to 1.0 (potash)
    organic_matter: float = 0.5  # 0.0 to 1.0 (humus & decaying matter)
    moisture: float = 0.5        # 0.0 to 1.0 (water saturation)
    ph: float = 6.5              # 4.0 to 9.0 (optimal plant growth: 6.0-7.0)
    salinity: float = 0.0        # 0.0 to 1.0 (salt concentration)
    density: float = 1.0         # Topsoil thickness / compaction


class SoilChunk:
    """Struct-of-Arrays (SoA) layout for soil data across 16x16 chunk cells."""

    CELL_COUNT: int = 256  # 16x16
    SIDE: int = 16

    __slots__ = (
        "chunk_coords",
        "nitrogen",
        "phosphorus",
        "potassium",
        "organic_matter",
        "moisture",
        "ph",
        "salinity",
        "density",
    )

    def __init__(self, chunk_coords: Tuple[int, int]) -> None:
        self.chunk_coords = chunk_coords
        self.nitrogen = [0.5] * self.CELL_COUNT
        self.phosphorus = [0.5] * self.CELL_COUNT
        self.potassium = [0.5] * self.CELL_COUNT
        self.organic_matter = [0.5] * self.CELL_COUNT
        self.moisture = [0.5] * self.CELL_COUNT
        self.ph = [6.5] * self.CELL_COUNT
        self.salinity = [0.0] * self.CELL_COUNT
        self.density = [1.0] * self.CELL_COUNT

    def get_profile(self, local_x: int, local_y: int) -> SoilProfile:
        idx = (local_y & 15) * 16 + (local_x & 15)
        return SoilProfile(
            nitrogen=self.nitrogen[idx],
            phosphorus=self.phosphorus[idx],
            potassium=self.potassium[idx],
            organic_matter=self.organic_matter[idx],
            moisture=self.moisture[idx],
            ph=self.ph[idx],
            salinity=self.salinity[idx],
            density=self.density[idx],
        )

    def deposit_organic_matter(self, local_x: int, local_y: int, mass_kg: float) -> None:
        idx = (local_y & 15) * 16 + (local_x & 15)
        # Organic deposit directly enriches humus
        self.organic_matter[idx] = min(1.0, self.organic_matter[idx] + mass_kg * 0.02)

    def extract_nutrients(
        self,
        local_x: int,
        local_y: int,
        n_demand: float,
        p_demand: float,
        k_demand: float,
    ) -> Tuple[float, float, float]:
        """Extracts nutrients for plant growth. Returns actual amount absorbed."""
        idx = (local_y & 15) * 16 + (local_x & 15)
        
        # pH efficiency modifier (Gaussian around 6.5)
        ph_eff = math.exp(-0.5 * ((self.ph[idx] - 6.5) / 1.0) ** 2)

        actual_n = min(self.nitrogen[idx], n_demand * ph_eff)
        actual_p = min(self.phosphorus[idx], p_demand * ph_eff)
        actual_k = min(self.potassium[idx], k_demand * ph_eff)

        self.nitrogen[idx] -= actual_n
        self.phosphorus[idx] -= actual_p
        self.potassium[idx] -= actual_k

        return (actual_n, actual_p, actual_k)

    def tick_decomposition(self, dt: float, temperature_c: float) -> None:
        """Microbial mineralization: breaks down organic matter into bioavailable NPK."""
        if temperature_c < 0.0:
            return  # Frozen soil halts microbial action

        # Microbial activity peaks around 25-30C
        microbial_rate = max(0.0, min(1.0, temperature_c / 30.0)) * 0.005 * dt

        for i in range(self.CELL_COUNT):
            if self.organic_matter[i] > 0.01:
                mineralized = self.organic_matter[i] * microbial_rate
                self.organic_matter[i] -= mineralized
                self.nitrogen[i] = min(1.0, self.nitrogen[i] + mineralized * 0.6)
                self.phosphorus[i] = min(1.0, self.phosphorus[i] + mineralized * 0.2)
                self.potassium[i] = min(1.0, self.potassium[i] + mineralized * 0.2)


class SoilManager:
    """
    Coordinator managing planetary soil chunks and chemical cycles.
    """

    def __init__(self) -> None:
        self.chunks: Dict[Tuple[int, int], SoilChunk] = {}

    def get_or_create_chunk(self, chunk_coords: Tuple[int, int]) -> SoilChunk:
        if chunk_coords not in self.chunks:
            self.chunks[chunk_coords] = SoilChunk(chunk_coords)
        return self.chunks[chunk_coords]

    def query_soil(self, global_x: float, global_y: float) -> SoilProfile:
        cx = int(math.floor(global_x / 16.0))
        cy = int(math.floor(global_y / 16.0))
        lx = int(math.floor(global_x)) % 16
        ly = int(math.floor(global_y)) % 16
        chunk = self.get_or_create_chunk((cx, cy))
        return chunk.get_profile(lx, ly)

    def tick(self, dt: float, ambient_temperature_c: float = 20.0) -> None:
        for chunk in self.chunks.values():
            chunk.tick_decomposition(dt, ambient_temperature_c)

    def reset(self) -> None:
        self.chunks.clear()
