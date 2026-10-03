"""
project/renderer/camera.py

2D Camera Viewport Offset, Zoom, and Entity Tracking engine.
"""

from __future__ import annotations

from typing import Tuple, Optional


class Camera:
    """Manages viewport offsets, zoom factors, and mouse dragging/tracking."""

    def __init__(
        self,
        screen_width: int = 1280,
        screen_height: int = 720,
        zoom_min: float = 0.05,
        zoom_max: float = 10.0,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom_min = zoom_min
        self.zoom_max = zoom_max

        # Center camera on (0, 0) initially
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        self.zoom: float = 0.5

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

    def get_visible_world_bounds(self, margin: float = 20.0) -> Tuple[float, float, float, float]:
        """Returns (min_wx, min_wy, max_wx, max_wy) visible within screen viewport with margin."""
        half_w = (self.screen_width * 0.5) / self.zoom + margin
        half_h = (self.screen_height * 0.5) / self.zoom + margin
        return (self.pos_x - half_w, self.pos_y - half_h, self.pos_x + half_w, self.pos_y + half_h)

    def pan(self, dx: float, dy: float) -> None:
        """Pans the camera. Pan speed scales inversely with zoom."""
        self.pos_x -= dx / self.zoom
        self.pos_y -= dy / self.zoom
        self.tracking_entity_id = None  # Clear track on manual pan

    def zoom_at_screen(self, zoom_delta: float, sx: float, sy: float) -> None:
        """Zooms centered on a specific screen location (e.g. mouse cursor position)."""
        wx, wy = self.screen_to_world(sx, sy)
        
        # Apply zoom limits
        old_zoom = self.zoom
        self.zoom = max(self.zoom_min, min(self.zoom_max, self.zoom + zoom_delta))
        
        # Adjust position to keep the world point under the mouse cursor
        self.pos_x = wx - (sx - self.screen_width * 0.5) / self.zoom
        self.pos_y = wy - (sy - self.screen_height * 0.5) / self.zoom

    def update_follow(self, target_x: float, target_y: float, interpolation_factor: float = 0.1) -> None:
        """Interpolates camera target position toward tracked entity."""
        self.pos_x += (target_x - self.pos_x) * interpolation_factor
        self.pos_y += (target_y - self.pos_y) * interpolation_factor

    def resize(self, screen_width: int, screen_height: int) -> None:
        """Updates camera screen viewport dimensions during window resize."""
        self.screen_width = max(640, screen_width)
        self.screen_height = max(480, screen_height)
