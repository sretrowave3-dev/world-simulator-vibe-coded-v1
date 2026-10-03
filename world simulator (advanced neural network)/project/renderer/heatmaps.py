"""
project/renderer/heatmaps.py

Atmospheric and chemical grid visual overlay layers using Pygame.
"""

from __future__ import annotations

from typing import Tuple, List, Dict, Optional
import pygame
from project.renderer.camera import Camera
from project.ai.pheromone import PheromoneGrid, PheromoneType


class HeatmapRenderer:
    """Renders semi-transparent grids for temperature, moisture, and pheromones."""

    def __init__(self, cell_size: float = 16.0) -> None:
        self.cell_size = cell_size
        self._overlay_surface: Optional[pygame.Surface] = None

    def draw_pheromone_overlay(
        self,
        surface: pygame.Surface,
        camera: Camera,
        pheromone_grid: PheromoneGrid,
        p_type: PheromoneType,
        color_rgb: Tuple[int, int, int],
    ) -> None:
        """Draws spatial color intensity representing pheromone grid concentrations."""
        # Find bounds of cells visible to camera
        min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=pheromone_grid.cell_size)

        # Snap bounds to pheromone cell grid coordinates
        min_gx = max(0, int(min_wx / pheromone_grid.cell_size))
        max_gx = min(pheromone_grid.width - 1, int(max_wx / pheromone_grid.cell_size))
        min_gy = max(0, int(min_wy / pheromone_grid.cell_size))
        max_gy = min(pheromone_grid.height - 1, int(max_wy / pheromone_grid.cell_size))

        ch = p_type.value
        g = pheromone_grid.grids[ch]
        w = pheromone_grid.width

        # Scale size based on zoom
        cell_pixel_size = max(1, int(pheromone_grid.cell_size * camera.zoom))

        # Reusable single SRCALPHA canvas
        surf_sz = surface.get_size()
        if self._overlay_surface is None or self._overlay_surface.get_size() != surf_sz:
            self._overlay_surface = pygame.Surface(surf_sz, pygame.SRCALPHA)
        self._overlay_surface.fill((0, 0, 0, 0))

        has_drawn = False
        r, g_col, b = color_rgb
        for gy in range(min_gy, max_gy + 1):
            y_offset = gy * w
            for gx in range(min_gx, max_gx + 1):
                val = g[y_offset + gx]
                if val > 0.05:
                    wx = gx * pheromone_grid.cell_size
                    wy = gy * pheromone_grid.cell_size
                    sx, sy = camera.world_to_screen(wx, wy)

                    # Compute alpha color intensity [0 to 180]
                    alpha = min(180, int(val * 15.0))
                    if alpha > 5:
                        pygame.draw.rect(
                            self._overlay_surface,
                            (r, g_col, b, alpha),
                            pygame.Rect(sx, sy, cell_pixel_size, cell_pixel_size)
                        )
                        has_drawn = True

        if has_drawn:
            surface.blit(self._overlay_surface, (0, 0))
