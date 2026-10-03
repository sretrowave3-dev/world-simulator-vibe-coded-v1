"""
project/ai/pheromone.py

Chemical Scent & Pheromone Diffusion Subsystem for the ALife Platform.

Features:
- Multi-channel chemical scent grids (Food Trails, Alarm / Danger, Mating Scents, Territory).
- 2D Laplacian spatial diffusion and exponential evaporation decay (NumPy SIMD Vectorized).
- Gradient sensing APIs enabling chemotactic navigation toward scent sources.
"""

from __future__ import annotations

import enum
import math
from typing import Dict, List, Optional, Tuple
import numpy as np


class PheromoneType(enum.IntEnum):
    FOOD_TRAIL = 0
    DANGER_ALARM = 1
    MATE_ATTRACTANT = 2
    TERRITORY_MARK = 3
    RECRUITMENT = 4


class PheromoneGrid:
    """
    2D discrete chemical concentration grid supporting multi-channel diffusion and decay.
    Accelerated with vectorized 2D NumPy array slicing for high-throughput Linux execution.
    """

    CHANNEL_COUNT: int = 5

    def __init__(
        self,
        width: int = 128,
        height: int = 128,
        cell_size: float = 8.0,
        diffusion_rate: float = 0.15,
        decay_rates: Optional[Dict[PheromoneType, float]] = None,
    ) -> None:
        self.width = int(width)
        self.height = int(height)
        self.cell_size = float(cell_size)
        self.inv_cell_size = 1.0 / self.cell_size
        self.diffusion_rate = diffusion_rate

        # Default decay rates per second
        self.decay_rates: Dict[int, float] = {
            PheromoneType.FOOD_TRAIL.value: 0.05,
            PheromoneType.DANGER_ALARM.value: 0.15,
            PheromoneType.MATE_ATTRACTANT.value: 0.03,
            PheromoneType.TERRITORY_MARK.value: 0.005,
            PheromoneType.RECRUITMENT.value: 0.08,
        }
        if decay_rates:
            for pt, rate in decay_rates.items():
                self.decay_rates[pt.value] = rate

        # Contiguous 3D float32 array: [channel, y, x]
        self._np_grids = np.zeros((self.CHANNEL_COUNT, self.height, self.width), dtype=np.float32)
        # Flat 1D views for backward compatibility: [channel][y * width + x]
        self.grids: List[np.ndarray] = [self._np_grids[ch].ravel() for ch in range(self.CHANNEL_COUNT)]

    def _get_index(self, gx: int, gy: int) -> int:
        return (gy % self.height) * self.width + (gx % self.width)

    def deposit(self, x: float, y: float, pheromone_type: PheromoneType, intensity: float) -> None:
        """Deposits chemical scent at continuous coordinates (x, y)."""
        gx = int(math.floor(x * self.inv_cell_size))
        gy = int(math.floor(y * self.inv_cell_size))
        if 0 <= gx < self.width and 0 <= gy < self.height:
            ch = pheromone_type.value
            self._np_grids[ch, gy, gx] = min(100.0, float(self._np_grids[ch, gy, gx]) + intensity)

    def sample(self, x: float, y: float, pheromone_type: PheromoneType) -> float:
        """Samples scalar chemical concentration at coordinates (x, y)."""
        gx = int(math.floor(x * self.inv_cell_size))
        gy = int(math.floor(y * self.inv_cell_size))
        if 0 <= gx < self.width and 0 <= gy < self.height:
            return float(self._np_grids[pheromone_type.value, gy, gx])
        return 0.0

    def sample_gradient(self, x: float, y: float, pheromone_type: PheromoneType) -> Tuple[float, float]:
        """
        Samples the 2D gradient vector (dC/dx, dC/dy) of chemical concentration.
        Points toward increasing scent intensity.
        """
        gx = int(math.floor(x * self.inv_cell_size))
        gy = int(math.floor(y * self.inv_cell_size))
        if not (1 <= gx < self.width - 1 and 1 <= gy < self.height - 1):
            return (0.0, 0.0)

        ch = pheromone_type.value
        g = self._np_grids[ch]

        # Central difference approximation
        dx = float(g[gy, gx + 1] - g[gy, gx - 1]) * 0.5
        dy = float(g[gy + 1, gx] - g[gy - 1, gx]) * 0.5

        return (dx, dy)

    def tick(self, dt: float) -> None:
        """Diffuses and evaporates chemical concentrations across all channels using SIMD NumPy vectorization."""
        diff_coeff = self.diffusion_rate * dt
        for ch in range(self.CHANNEL_COUNT):
            decay = math.exp(-self.decay_rates[ch] * dt)
            g = self._np_grids[ch]

            # Fast vectorized 2D 4-point Laplacian kernel
            center = g[1:-1, 1:-1]
            if np.any(center > 0.001):
                laplacian = (
                    g[1:-1, :-2] + g[1:-1, 2:] +
                    g[:-2, 1:-1] + g[2:, 1:-1] -
                    4.0 * center
                )
                updated = (center + diff_coeff * laplacian) * decay
                g[1:-1, 1:-1] = np.where(updated > 0.001, updated, 0.0)
            else:
                g[1:-1, 1:-1] = 0.0

            # Dissipate world borders
            g[0, :] = 0.0
            g[-1, :] = 0.0
            g[:, 0] = 0.0
            g[:, -1] = 0.0

    def clear(self) -> None:
        self._np_grids.fill(0.0)
