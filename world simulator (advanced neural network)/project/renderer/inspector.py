"""
project/renderer/inspector.py

Sidebar Inspector GUI drawing entity vitals, need states, emergent roles, and neural parameters.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import pygame


class Inspector:
    """Sidebar HUD displaying details of the selected entity."""

    def __init__(self, x: int, y: int, width: int = 300, height: int = 600) -> None:
        self.rect = pygame.Rect(x, y, width, height)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        selected_entity_snapshot: Optional[Dict[str, Any]],
        needs_snapshot: Optional[Dict[str, float]],
    ) -> None:
        """Renders sidebar data panel for inspected entity."""
        # Draw background container
        pygame.draw.rect(surface, (25, 25, 30), self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 2)

        title_color = (255, 255, 255)
        text_color = (200, 200, 200)

        from project.renderer.ui import get_cached_text

        title_surface = get_cached_text(font, "Entity Inspector", title_color)
        surface.blit(title_surface, (self.rect.x + 10, self.rect.y + 10))

        # Horizontal divider line
        pygame.draw.line(
            surface,
            (80, 80, 100),
            (self.rect.x + 10, self.rect.y + 35),
            (self.rect.x + self.rect.width - 10, self.rect.y + 35),
            1
        )

        if not selected_entity_snapshot:
            # Draw placeholder message
            ph_surface = get_cached_text(font, "Click an entity to inspect", (120, 120, 140))
            surface.blit(ph_surface, (self.rect.x + 15, self.rect.y + 50))
            return

        # Render properties list safely
        eid = str(selected_entity_snapshot.get("id", "Unknown"))
        etype = str(selected_entity_snapshot.get("type", "Unknown"))
        role_title = str(selected_entity_snapshot.get("role_title", "Organism"))
        gen = selected_entity_snapshot.get("generation", 1)
        synapses = selected_entity_snapshot.get("synapses", 0)
        con = selected_entity_snapshot.get("consciousness", 0.0)

        mem_mb = float(selected_entity_snapshot.get("memory_mb", 0.0))
        act = selected_entity_snapshot.get("action", "IDLE")
        dop = selected_entity_snapshot.get("dopamine", 0.0)
        fear = selected_entity_snapshot.get("fear", 0.0)
        cur = selected_entity_snapshot.get("curiosity", 0.0)
        
        labels = [
            f"ID: {eid[:18]}",
            f"Type: {etype} | Mode: {act}",
            f"Role: {role_title}",
            f"Gen: {gen} | Synapses: {synapses}",
            f"Memory: {mem_mb:.1f} MB (High-Cap Replay)",
            f"Psychology: Dop={dop:.2f} Fear={fear:.2f} Cur={cur:.2f}",
            f"Pos: ({selected_entity_snapshot.get('x', 0):.1f}, {selected_entity_snapshot.get('y', 0):.1f})",
            f"Health: {selected_entity_snapshot.get('health', 0):.1f}/{selected_entity_snapshot.get('max_health', 1):.1f}",
        ]
        if con > 0.0:
            labels.append(f"Consciousness: {con * 100.0:.1f}%")

        curr_y = self.rect.y + 45
        for label in labels:
            lbl_surface = get_cached_text(font, label, text_color)
            surface.blit(lbl_surface, (self.rect.x + 15, curr_y))
            curr_y += 18

        # Draw needs/drives section if available
        if needs_snapshot:
            pygame.draw.line(surface, (80, 80, 100), (self.rect.x + 10, curr_y + 6), (self.rect.x + self.rect.width - 10, curr_y + 6), 1)
            curr_y += 14

            header_surface = get_cached_text(font, "Physiological & Psych Drives:", title_color)
            surface.blit(header_surface, (self.rect.x + 10, curr_y))
            curr_y += 20

            for need_name, value in needs_snapshot.items():
                val_clamped = max(0.0, min(1.0, float(value)))
                lbl_surface = get_cached_text(font, f"{need_name.capitalize()}: {val_clamped * 100.0:.1f}%", text_color)
                surface.blit(lbl_surface, (self.rect.x + 15, curr_y))
                
                # Render need progress bar with dynamic color gradient
                bar_rect = pygame.Rect(self.rect.x + 15, curr_y + 16, self.rect.width - 30, 5)
                pygame.draw.rect(surface, (40, 40, 50), bar_rect)
                
                fill_w = int((self.rect.width - 30) * val_clamped)
                if val_clamped < 0.35:
                    fill_color = (60, 210, 80)
                elif val_clamped < 0.70:
                    fill_color = (235, 185, 45)
                else:
                    fill_color = (240, 55, 55)

                if fill_w > 0:
                    pygame.draw.rect(surface, fill_color, pygame.Rect(bar_rect.x, bar_rect.y, fill_w, 5))
                curr_y += 24

        # Draw AI Psychological Parameters if brain is active
        ai_metrics = selected_entity_snapshot.get("ai_metrics")
        if ai_metrics and isinstance(ai_metrics, dict):
            pygame.draw.line(surface, (80, 80, 100), (self.rect.x + 10, curr_y + 6), (self.rect.x + self.rect.width - 10, curr_y + 6), 1)
            curr_y += 14
            
            header_surface = get_cached_text(font, "Psychological AI Matrix:", (0, 255, 255))
            surface.blit(header_surface, (self.rect.x + 10, curr_y))
            curr_y += 20
            
            ai_score = ai_metrics.get("intelligence_score", 0.0)
            lbl = get_cached_text(font, f"Cognitive Potential: {ai_score:.1f}", text_color)
            surface.blit(lbl, (self.rect.x + 15, curr_y))
            curr_y += 18
            
            plasticity = ai_metrics.get("plasticity", 1.0)
            lbl = get_cached_text(font, f"Synaptic Plasticity: {plasticity:.2f}", text_color)
            surface.blit(lbl, (self.rect.x + 15, curr_y))
            curr_y += 18
            
            # Working Memory Vector Visualization
            mem = ai_metrics.get("working_memory", [])
            if mem:
                lbl = get_cached_text(font, "Recurrent Memory:", text_color)
                surface.blit(lbl, (self.rect.x + 15, curr_y))
                curr_y += 18
                
                mem_w = (self.rect.width - 40) // max(1, len(mem))
                for i, val in enumerate(mem):
                    cell_rect = pygame.Rect(self.rect.x + 15 + i * (mem_w + 2), curr_y, mem_w, 12)
                    intensity = min(255, max(0, int((val + 1.0) * 127.5)))
                    pygame.draw.rect(surface, (intensity, intensity, 255 - intensity), cell_rect)
                    pygame.draw.rect(surface, (100, 100, 100), cell_rect, 1)
                curr_y += 20
            
            reward = ai_metrics.get("last_reward", 0.0)
            lbl = get_cached_text(font, f"Hebbian Signal: {reward:+.2f}", text_color)
            surface.blit(lbl, (self.rect.x + 15, curr_y))
