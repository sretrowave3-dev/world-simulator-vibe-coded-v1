"""
project/analytics/graphs.py

Real-time Pygame vector graph renderer plotting population curves onto panels.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
import pygame


class PopulationGraphRenderer:
    """Plots population census trends directly to a HUD Surface."""

    def __init__(self, x: int, y: int, width: int = 240, height: int = 150) -> None:
        self.rect = pygame.Rect(x, y, width, height)

    def draw_graph(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        history: List[Dict[str, int]],
    ) -> None:
        # Draw backdrop panel
        pygame.draw.rect(surface, (20, 20, 25), self.rect)
        pygame.draw.rect(surface, (80, 80, 100), self.rect, 1)

        # Title
        title_surf = font.render("Population History", True, (0, 255, 255))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 5))

        if len(history) < 2:
            no_data = font.render("Gathering telemetry...", True, (120, 120, 140))
            surface.blit(no_data, (self.rect.x + 15, self.rect.y + 40))
            return

        # Find maximum value in history to scale height
        max_val = 1
        for h in history:
            val = h.get("total", 0)
            if val > max_val:
                max_val = val

        # Drawing area boundaries
        graph_rect = pygame.Rect(
            self.rect.x + 15,
            self.rect.y + 25,
            self.rect.width - 30,
            self.rect.height - 40
        )

        # Draw axis lines
        pygame.draw.line(surface, (100, 100, 120), (graph_rect.x, graph_rect.y), (graph_rect.x, graph_rect.y + graph_rect.height), 1)
        pygame.draw.line(surface, (100, 100, 120), (graph_rect.x, graph_rect.y + graph_rect.height), (graph_rect.x + graph_rect.width, graph_rect.y + graph_rect.height), 1)

        # Plot line coordinates
        pts_bacteria: List[Tuple[int, int]] = []
        pts_herbivore: List[Tuple[int, int]] = []
        pts_predator: List[Tuple[int, int]] = []

        pt_count = len(history)
        step_x = graph_rect.width / (pt_count - 1)

        for i, h in enumerate(history):
            px = graph_rect.x + int(i * step_x)

            # Map values to pixel height (inversely due to Pygame y axis pointing down)
            def scale_y(val):
                ratio = val / max_val
                return graph_rect.y + graph_rect.height - int(ratio * graph_rect.height)

            pts_bacteria.append((px, scale_y(h.get("bacteria", 0))))
            pts_herbivore.append((px, scale_y(h.get("herbivore", 0))))
            pts_predator.append((px, scale_y(h.get("predator", 0))))

        # Draw lines
        if len(pts_bacteria) >= 2:
            pygame.draw.lines(surface, (0, 200, 200), False, pts_bacteria, 1)
        if len(pts_herbivore) >= 2:
            pygame.draw.lines(surface, (200, 200, 0), False, pts_herbivore, 1)
        if len(pts_predator) >= 2:
            pygame.draw.lines(surface, (255, 50, 50), False, pts_predator, 1)
