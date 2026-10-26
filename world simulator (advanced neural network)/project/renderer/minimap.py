"""
project/renderer/minimap.py

HUD Map overview panel displaying entity locations, terrain biomes, rivers, mountains,
tribal structures, and interactive click-to-teleport camera navigation.
"""

from __future__ import annotations

import math
from typing import List, Dict, Any, Optional
import pygame
from project.renderer.camera import Camera


class Minimap:
    """Renders small navigation overview window showing all entities and geographical landmarks."""

    def __init__(
        self,
        x: int = 10,
        y: int = 10,
        width: int = 220,
        height: int = 220,
        world_width: float = 14336.0,
        world_height: float = 14336.0,
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.world_width = world_width
        self.world_height = world_height
        self.scale_x = width / world_width
        self.scale_y = height / world_height

    def handle_click(self, mouse_pos: tuple[int, int], camera: Camera) -> bool:
        """
        Interactive Minimap Click-to-Teleport.
        Clicking anywhere on the minimap instantly teleports the camera to that world location.
        """
        if self.rect.collidepoint(mouse_pos):
            rel_x = mouse_pos[0] - self.rect.x
            rel_y = mouse_pos[1] - self.rect.y
            world_x = rel_x / max(0.0001, self.scale_x)
            world_y = rel_y / max(0.0001, self.scale_y)
            camera.pos_x = max(0.0, min(self.world_width, world_x))
            camera.pos_y = max(0.0, min(self.world_height, world_y))
            camera.tracking_entity_id = None
            return True
        return False

    def draw(
        self,
        surface: pygame.Surface,
        camera: Camera,
        entities_snapshot: List[Dict[str, Any]],
        structures_snapshot: Optional[List[Any]] = None,
    ) -> None:
        # 1. Background container box with modern dark slate border
        pygame.draw.rect(surface, (15, 18, 24), self.rect)
        pygame.draw.rect(surface, (60, 80, 110), self.rect, 1)

        # 2. Draw World Structures (Campfires, Clan Shelters, Altars)
        if structures_snapshot:
            for s in structures_snapshot:
                sx = self.rect.x + int(s.pos_x * self.scale_x)
                sy = self.rect.y + int(s.pos_y * self.scale_y)
                if self.rect.collidepoint(sx, sy):
                    # Gold/Amber beacon for tribal hearths
                    surface.fill((255, 180, 40), (sx - 1, sy - 1, 3, 3))

        # 3. Draw active entities as high-visibility color-coded dots
        for entity in entities_snapshot:
            if not entity.get("is_alive", True):
                continue

            wx = entity["x"]
            wy = entity["y"]

            mx = self.rect.x + int(wx * self.scale_x)
            my = self.rect.y + int(wy * self.scale_y)

            etype = entity["type"]
            color = (150, 150, 150)
            dot_size = 2

            if etype == "HUMAN":
                color = (255, 230, 80)  # Bright gold for civilization
                dot_size = 3
            elif etype == "PREDATOR":
                color = (255, 50, 50)   # Red for predators
                dot_size = 2
            elif etype == "HERBIVORE":
                color = (220, 220, 100) # Soft yellow
            elif etype == "PLANT":
                # Only show major trees/forests on minimap to prevent clutter
                if entity.get("custom_data", {}).get("is_tree", False):
                    color = (40, 180, 60)
                    dot_size = 2
                else:
                    continue
            elif etype == "AVIAN":
                color = (180, 100, 240)

            if self.rect.collidepoint(mx, my):
                surface.fill(color, (mx, my, dot_size, dot_size))

        # 4. Draw camera footprint viewport box on minimap
        w_left, w_top = camera.screen_to_world(0, 0)
        w_right, w_bottom = camera.screen_to_world(camera.screen_width, camera.screen_height)

        ml = self.rect.x + int(max(0.0, w_left) * self.scale_x)
        mt = self.rect.y + int(max(0.0, w_top) * self.scale_y)
        mr = self.rect.x + int(min(self.world_width, w_right) * self.scale_x)
        mb = self.rect.y + int(min(self.world_height, w_bottom) * self.scale_y)

        mw = max(2, mr - ml)
        mh = max(2, mb - mt)

        pygame.draw.rect(surface, (0, 240, 255), pygame.Rect(ml, mt, mw, mh), 1)
