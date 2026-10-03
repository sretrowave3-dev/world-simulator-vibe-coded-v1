"""
project/utils/noise.py

High-performance procedural noise generation algorithms for procedural world generation,
elevation grids, climate synthesis, resource clustering, and biome mapping.

Features:
- Deterministic 2D/3D Perlin noise.
- Fast Simplex 2D noise.
- Voronoi / Worley cellular noise (F1, F2 distances, cell ID derivation).
- Fractal Brownian Motion (fBm) with octave synthesis, persistence, and lacunarity.
- Ridged Multifractal noise (for sharp mountain ranges).
- Continuous Domain Warping for natural organic textures.
"""

from __future__ import annotations

import math
from typing import Tuple, List


# =============================================================================
# PERLIN GRADIENTS & PERMUTATION TABLES
# =============================================================================

# Standard 256-entry base permutation table
_PERM_BASE: Tuple[int, ...] = (
    151, 160, 137, 91, 90, 15, 131, 13, 201, 95, 96, 53, 194, 233, 7, 225,
    140, 36, 103, 30, 69, 142, 8, 99, 37, 240, 21, 10, 23, 190, 6, 148,
    247, 120, 234, 75, 0, 26, 197, 62, 94, 252, 219, 203, 117, 35, 11, 32,
    57, 177, 33, 88, 237, 149, 56, 87, 174, 20, 125, 136, 171, 168, 68, 175,
    74, 165, 71, 134, 139, 48, 27, 166, 77, 146, 158, 231, 83, 111, 229, 122,
    60, 211, 133, 230, 220, 105, 92, 41, 55, 46, 245, 40, 244, 102, 143, 54,
    65, 25, 63, 161, 1, 216, 80, 73, 209, 76, 132, 187, 208, 89, 18, 169,
    200, 196, 135, 130, 116, 188, 159, 86, 164, 100, 109, 198, 173, 186, 3, 64,
    52, 217, 226, 250, 124, 123, 5, 202, 38, 147, 118, 126, 255, 82, 85, 212,
    207, 206, 59, 227, 47, 16, 58, 17, 182, 189, 28, 42, 223, 183, 170, 213,
    119, 248, 152, 2, 44, 154, 163, 70, 221, 153, 101, 155, 167, 43, 172, 9,
    129, 22, 39, 253, 19, 98, 108, 110, 79, 113, 224, 232, 178, 185, 112, 104,
    218, 246, 97, 228, 251, 34, 242, 193, 238, 210, 144, 12, 191, 179, 162, 241,
    81, 51, 145, 235, 249, 14, 239, 107, 49, 192, 214, 31, 181, 199, 106, 157,
    184, 84, 204, 176, 115, 121, 50, 45, 127, 4, 150, 254, 138, 236, 205, 93,
    222, 114, 67, 29, 24, 72, 243, 141, 128, 195, 78, 66, 215, 61, 156, 180
)

# 2D Simplex skew constants
_F2: float = 0.5 * (math.sqrt(3.0) - 1.0)
_G2: float = (3.0 - math.sqrt(3.0)) / 6.0

# 2D Gradients for Simplex noise
_GRAD2: Tuple[Tuple[int, int], ...] = (
    (1, 1), (-1, 1), (1, -1), (-1, -1),
    (1, 0), (-1, 0), (0, 1), (0, -1)
)


class FastNoise:
    """
    Stateful noise generator parameterizing seed-based permutation arrays and multi-fractal pipelines.
    """

    def __init__(self, seed: int = 1337) -> None:
        self.seed: int = seed & 0xFFFFFFFF
        self._perm: List[int] = [0] * 512
        self.reseed(seed)

    def reseed(self, seed: int) -> None:
        self.seed = seed & 0xFFFFFFFF
        # Build shuffled permutation table based on seed
        p = list(_PERM_BASE)
        # Deterministic Fisher-Yates shuffle
        s = self.seed
        for i in range(255, 0, -1):
            s = (s * 1664525 + 1013904223) & 0xFFFFFFFF
            j = s % (i + 1)
            p[i], p[j] = p[j], p[i]

        for i in range(256):
            self._perm[i] = p[i]
            self._perm[256 + i] = p[i]

    # -------------------------------------------------------------------------
    # 2D PERLIN NOISE
    # -------------------------------------------------------------------------

    @staticmethod
    def _fade(t: float) -> float:
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @staticmethod
    def _grad2d(hash_val: int, x: float, y: float) -> float:
        h = hash_val & 7
        u = x if h < 4 else y
        v = y if h < 4 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def perlin2d(self, x: float, y: float) -> float:
        """Standard 2D Perlin gradient noise in range [-1.0, 1.0]."""
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255

        xf = x - math.floor(x)
        yf = y - math.floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        p = self._perm
        aa = p[p[xi] + yi]
        ab = p[p[xi] + yi + 1]
        ba = p[p[xi + 1] + yi]
        bb = p[p[xi + 1] + yi + 1]

        x1 = (1.0 - u) * self._grad2d(aa, xf, yf) + u * self._grad2d(ba, xf - 1.0, yf)
        x2 = (1.0 - u) * self._grad2d(ab, xf, yf - 1.0) + u * self._grad2d(bb, xf - 1.0, yf - 1.0)

        return (1.0 - v) * x1 + v * x2

    # -------------------------------------------------------------------------
    # 2D SIMPLEX NOISE
    # -------------------------------------------------------------------------

    def simplex2d(self, x: float, y: float) -> float:
        """2D Simplex noise with lower computational overhead in range [-1.0, 1.0]."""
        s = (x + y) * _F2
        i = int(math.floor(x + s))
        j = int(math.floor(y + s))

        t = (i + j) * _G2
        x0 = x - (i - t)
        y0 = y - (j - t)

        if x0 > y0:
            i1, j1 = 1, 0
        else:
            i1, j1 = 0, 1

        x1 = x0 - i1 + _G2
        y1 = y0 - j1 + _G2
        x2 = x0 - 1.0 + 2.0 * _G2
        y2 = y0 - 1.0 + 2.0 * _G2

        ii = i & 255
        jj = j & 255
        p = self._perm

        # Calculate contributions from 3 corners
        t0 = 0.5 - x0 * x0 - y0 * y0
        if t0 < 0:
            n0 = 0.0
        else:
            t0 *= t0
            gi0 = p[ii + p[jj]] % 8
            n0 = t0 * t0 * (_GRAD2[gi0][0] * x0 + _GRAD2[gi0][1] * y0)

        t1 = 0.5 - x1 * x1 - y1 * y1
        if t1 < 0:
            n1 = 0.0
        else:
            t1 *= t1
            gi1 = p[ii + i1 + p[jj + j1]] % 8
            n1 = t1 * t1 * (_GRAD2[gi1][0] * x1 + _GRAD2[gi1][1] * y1)

        t2 = 0.5 - x2 * x2 - y2 * y2
        if t2 < 0:
            n2 = 0.0
        else:
            t2 *= t2
            gi2 = p[ii + 1 + p[jj + 1]] % 8
            n2 = t2 * t2 * (_GRAD2[gi2][0] * x2 + _GRAD2[gi2][1] * y2)

        return 70.0 * (n0 + n1 + n2)

    # -------------------------------------------------------------------------
    # VORONOI / CELLULAR (WORLEY) NOISE
    # -------------------------------------------------------------------------

    def voronoi2d(self, x: float, y: float) -> Tuple[float, float, int]:
        """
        Calculates 2D Voronoi / Cellular noise.
        Returns:
            (F1 distance, F2 distance, cell_id)
        """
        xi = int(math.floor(x))
        yi = int(math.floor(y))

        min_d1 = 999.0
        min_d2 = 999.0
        closest_id = 0

        p = self._perm
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cx = xi + dx
                cy = yi + dy
                h = p[(cx & 255) + p[cy & 255]]
                
                # Deterministic feature point within unit cell
                px = cx + ((h * 13) % 256) / 256.0
                py = cy + ((h * 29) % 256) / 256.0

                dist = math.hypot(x - px, y - py)
                if dist < min_d1:
                    min_d2 = min_d1
                    min_d1 = dist
                    closest_id = h
                elif dist < min_d2:
                    min_d2 = dist

        return (min_d1, min_d2, closest_id)

    # -------------------------------------------------------------------------
    # FRACTAL BROWNIAN MOTION (fBm)
    # -------------------------------------------------------------------------

    def fbm2d(
        self,
        x: float,
        y: float,
        octaves: int = 4,
        lacunarity: float = 2.0,
        persistence: float = 0.5
    ) -> float:
        """
        Fractal Brownian Motion combining multiple octaves of Perlin noise.
        Normalized output in range [0.0, 1.0].
        """
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_val = 0.0

        for _ in range(octaves):
            val = self.perlin2d(x * frequency, y * frequency)
            total += val * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        # Normalize to [0.0, 1.0]
        return (total / max_val + 1.0) * 0.5

    # -------------------------------------------------------------------------
    # RIDGED MULTIFRACTAL NOISE
    # -------------------------------------------------------------------------

    def ridged2d(
        self,
        x: float,
        y: float,
        octaves: int = 4,
        lacunarity: float = 2.0,
        persistence: float = 0.5
    ) -> float:
        """
        Ridged multifractal noise for sharp mountain peaks and tectonic ridges.
        Output in range [0.0, 1.0].
        """
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_val = 0.0

        for _ in range(octaves):
            val = abs(self.simplex2d(x * frequency, y * frequency))
            val = 1.0 - val  # Invert to create sharp ridges
            val *= val       # Sharpen peaks
            total += val * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return total / max_val

    # -------------------------------------------------------------------------
    # CONTINUOUS DOMAIN WARPING
    # -------------------------------------------------------------------------

    def domain_warp2d(
        self,
        x: float,
        y: float,
        warp_strength: float = 4.0,
        octaves: int = 4
    ) -> float:
        """
        Applies continuous domain warping for fluid, organic terrain boundaries.
        f(p + strength * g(p))
        """
        qx = self.fbm2d(x + 0.0, y + 0.0, octaves=octaves)
        qy = self.fbm2d(x + 5.2, y + 1.3, octaves=octaves)

        rx = self.fbm2d(x + warp_strength * qx + 1.7, y + warp_strength * qy + 9.2, octaves=octaves)
        ry = self.fbm2d(x + warp_strength * qx + 8.3, y + warp_strength * qy + 2.8, octaves=octaves)

        return self.fbm2d(x + warp_strength * rx, y + warp_strength * ry, octaves=octaves)
