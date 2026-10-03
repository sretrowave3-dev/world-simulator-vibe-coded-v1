"""
project/renderer/debug_renderer.py

Debug hud overlays rendering FPS statistics and Scheduler task performance durations.
"""

from __future__ import annotations

from typing import Dict
import pygame


_DEBUG_PANEL_SURF: Optional[pygame.Surface] = None


class DebugRenderer:
    """HUD overlay for developer and engine diagnostic readings."""

    @staticmethod
    def draw_diagnostics(
        surface: pygame.Surface,
        font: pygame.font.Font,
        fps: float,
        sim_tick: int,
        system_timings: Dict[str, float],
    ) -> None:
        """Draws performance timings overlay at top-left corner."""
        global _DEBUG_PANEL_SURF
        from project.security.spec_protector import global_spec_protector
        from project.renderer.ui import get_cached_text
        hw = global_spec_protector.check_safety()

        panel_rect = pygame.Rect(10, 220, 250, 205)
        # Reusable translucent background panel
        if _DEBUG_PANEL_SURF is None or _DEBUG_PANEL_SURF.get_size() != (panel_rect.width, panel_rect.height):
            _DEBUG_PANEL_SURF = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            _DEBUG_PANEL_SURF.fill((10, 10, 15, 185))

        surface.blit(_DEBUG_PANEL_SURF, (panel_rect.x, panel_rect.y))
        pygame.draw.rect(surface, (100, 100, 120), panel_rect, 1)

        # Draw metrics
        color = (0, 255, 255)
        text_color = (220, 220, 220)

        title_surf = get_cached_text(font, "Engine & Spec Guard", color)
        surface.blit(title_surf, (panel_rect.x + 10, panel_rect.y + 10))

        hw_badge_color = (0, 255, 120) if not hw.is_danger_zone else (255, 50, 50)
        metrics = [
            f"FPS: {fps:.1f}",
            f"Sim Tick: {sim_tick}",
            f"CPU Load: {hw.cpu_usage_pct:.1f}% (C-Shield)",
            f"Process RAM: {hw.process_ram_mb:.1f} MB",
            f"Avail RAM: {hw.system_ram_avail_mb:.0f} MB",
        ]

        curr_y = panel_rect.y + 35
        for m in metrics:
            surf = get_cached_text(font, m, text_color)
            surface.blit(surf, (panel_rect.x + 10, curr_y))
            curr_y += 18

        # Draw a small timing line if timings are present
        if system_timings:
            div_y = curr_y + 4
            pygame.draw.line(surface, (70, 70, 90), (panel_rect.x + 10, div_y), (panel_rect.x + panel_rect.width - 10, div_y))
            curr_y += 10

            sorted_timings = sorted(system_timings.items(), key=lambda item: item[1], reverse=True)[:2]
            for sys_name, duration_ms in sorted_timings:
                timing_str = f"{sys_name}: {duration_ms * 1000.0:.2f}ms"
                timing_surf = get_cached_text(font, timing_str, (250, 150, 100))
                surface.blit(timing_surf, (panel_rect.x + 10, curr_y))
                curr_y += 18
