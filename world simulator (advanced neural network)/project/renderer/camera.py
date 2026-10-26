"""
project/renderer/camera.py

2D Camera Viewport Offset, Multi-Tier Zoom, and Smooth Entity Tracking engine.
Optimized for massive expanded worlds (14,000+ meters) with exponential smooth zooming,
fast preset overview navigation, and mouse-centered scaling.
"""

from __future__ import annotations

import math
from typing import Tuple, Optional


class Camera:
    """Manages viewport offsets, zoom factors, and mouse dragging/tracking."""

    def __init__(
        self,
        screen_width: int = 1280,
        screen_height: int = 720,
        zoom_min: float = 0.01,   # Expanded to view 14,000+ meter continents in one frame
        zoom_max: float = 8.0,    # Close-up microscopic inspector
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom_min = zoom_min
        self.zoom_max = zoom_max

        # Center camera on (0, 0) initially
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        self.zoom: float = 0.35

        # ID of entity to track/follow
        self.tracking_entity_id: Optional[str] = None

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        """Converts continuous world space coords to pixel screen space coords."""
        sx = int((wx - self.pos_x) * self.zoom + self.screen_width * 0.5)
        sy = int((wy - self.pos_y) * self.zoom + self.screen_height * 0.5)
        return (sx, sy)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Converts pixel screen space coords to continuous world space coords."""
        wx = (sx - self.screen_width * 0.5) / self.zoom + self.pos_x
        wy = (sy - self.screen_height * 0.5) / self.zoom + self.pos_y
        return (wx, wy)

    def get_visible_world_bounds(self, margin: float = 40.0) -> Tuple[float, float, float, float]:
        """Returns (min_wx, min_wy, max_wx, max_wy) visible within screen viewport with margin."""
        half_w = (self.screen_width * 0.5) / self.zoom + margin
        half_h = (self.screen_height * 0.5) / self.zoom + margin
        return (self.pos_x - half_w, self.pos_y - half_h, self.pos_x + half_w, self.pos_y + half_h)

    def pan(self, dx: float, dy: float) -> None:
        """Pans the camera. Pan speed scales inversely with zoom for effortless movement."""
        self.pos_x -= dx / self.zoom
        self.pos_y -= dy / self.zoom
        self.tracking_entity_id = None  # Clear track on manual pan

    def zoom_at_screen(self, zoom_delta: float, sx: float, sy: float) -> None:
        """
        Smooth exponential zoom centered on a specific screen location (e.g. mouse cursor).
        Provides silky smooth control at macro (0.01) and micro (8.0) scales alike.
        """
        wx, wy = self.screen_to_world(sx, sy)

        # Multiplicative scaling feels natural across both macro and micro ranges
        if zoom_delta > 0:
            scale_factor = 1.15 if zoom_delta < 0.2 else (1.0 + zoom_delta)
            new_zoom = self.zoom * scale_factor
        elif zoom_delta < 0:
            scale_factor = 1.15 if abs(zoom_delta) < 0.2 else (1.0 / max(0.1, 1.0 - abs(zoom_delta)))
            new_zoom = self.zoom / scale_factor
        else:
            return

        self.zoom = max(self.zoom_min, min(self.zoom_max, new_zoom))

        # Adjust position to keep the exact world point anchored under the cursor
        self.pos_x = wx - (sx - self.screen_width * 0.5) / self.zoom
        self.pos_y = wy - (sy - self.screen_height * 0.5) / self.zoom

    def set_preset_view(self, target_zoom: float, target_x: Optional[float] = None, target_y: Optional[float] = None) -> None:
        """Sets an exact zoom preset and optionally centers on target coordinates."""
        self.zoom = max(self.zoom_min, min(self.zoom_max, target_zoom))
        if target_x is not None:
            self.pos_x = target_x
        if target_y is not None:
            self.pos_y = target_y
        self.tracking_entity_id = None

    def update_follow(self, target_x: float, target_y: float, interpolation_factor: float = 0.12) -> None:
        """Interpolates camera target position toward tracked entity."""
        self.pos_x += (target_x - self.pos_x) * interpolation_factor
        self.pos_y += (target_y - self.pos_y) * interpolation_factor

    def resize(self, screen_width: int, screen_height: int) -> None:
        """Updates camera screen viewport dimensions during window resize."""
        self.screen_width = max(640, screen_width)
        self.screen_height = max(480, screen_height)
