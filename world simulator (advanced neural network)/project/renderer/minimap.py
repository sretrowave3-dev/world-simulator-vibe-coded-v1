"""
project/renderer/minimap.py

HUD Map overview panel displaying entity locations and camera footprints.
"""

from __future__ import annotations

from typing import List, Dict, Any
import pygame
from project.renderer.camera import Camera


class Minimap:
    """Renders small navigation overview window showing all entities."""

    def __init__(
        self,
        x: int = 10,
        y: int = 10,
        width: int = 200,
        height: int = 200,
        world_width: float = 4096.0,
        world_height: float = 4096.0,
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.world_width = world_width
        self.world_height = world_height
        self.scale_x = width / world_width
        self.scale_y = height / world_height

    def draw(
        self,
        surface: pygame.Surface,
        camera: Camera,
        entities_snapshot: List[Dict[str, Any]],
    ) -> None:
        # Draw background container box
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 1)

        # Draw all active entities as color-coded pixel dots
        for entity in entities_snapshot:
            if not entity.get("is_alive", True):
                continue

            wx = entity["x"]
            wy = entity["y"]
            
            mx = self.rect.x + int(wx * self.scale_x)
            my = self.rect.y + int(wy * self.scale_y)

            # Color dots by type
            etype = entity["type"]
            color = (150, 150, 150)
            if etype == "BACTERIA":
                color = (0, 200, 200)
            elif etype == "PLANT":
                color = (0, 200, 0)
            elif etype == "HERBIVORE":
                color = (200, 200, 0)
            elif etype == "PREDATOR":
                color = (255, 0, 0)
            elif etype == "HUMAN":
                color = (255, 255, 255)

            if self.rect.collidepoint(mx, my):
                surface.fill(color, (mx, my, 2, 2))

        # Draw camera footprint rectangle on minimap
        # Convert screen corners to world coords
        w_left, w_top = camera.screen_to_world(0, 0)
        w_right, w_bottom = camera.screen_to_world(camera.screen_width, camera.screen_height)

        # Map to minimap coordinates
        ml = self.rect.x + int(max(0.0, w_left) * self.scale_x)
        mt = self.rect.y + int(max(0.0, w_top) * self.scale_y)
        mr = self.rect.x + int(min(self.world_width, w_right) * self.scale_x)
        mb = self.rect.y + int(min(self.world_height, w_bottom) * self.scale_y)

        mw = max(1, mr - ml)
        mh = max(1, mb - mt)

        pygame.draw.rect(surface, (0, 255, 255), pygame.Rect(ml, mt, mw, mh), 1)
