"""
project/renderer/brain_visualizer.py

Live Neural Network Graph Visualizer for real-time AI telemetry rendering.
"""

from __future__ import annotations

import math
from typing import Dict, Any, List, Tuple
import pygame
from project.renderer.ui import get_cached_text


class BrainVisualizer:
    """Draws a live node-link diagram of an entity's neural network."""

    def __init__(self, x: int, y: int, width: int = 800, height: int = 250) -> None:
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, ai_metrics: Dict[str, Any]) -> None:
        """Renders the neural graph based on the deep‑cloned ai_metrics payload.

        Expected keys in ``ai_metrics``:
            - ``net_sizes``: List[int] layer sizes (including working memory)
            - ``net_outputs``: List[List[float]] current neuron activations per layer
            - ``net_weights``: List[List[List[float]]] weight matrices per layer
        """
        # Background container
        pygame.draw.rect(surface, (15, 15, 20), self.rect)
        pygame.draw.rect(surface, (0, 255, 255), self.rect, 2)

        # Header
        title = get_cached_text(font, "LIVE NEURAL GRAPH VISUALIZER", (0, 255, 255))
        surface.blit(title, (self.rect.x + 10, self.rect.y + 10))

        net_sizes: List[int] = ai_metrics.get("net_sizes", [])
        net_outputs: List[List[float]] = ai_metrics.get("net_outputs", [])
        net_weights: List[List[List[float]]] = ai_metrics.get("net_weights", [])

        if not net_sizes or not net_weights:
            hint = get_cached_text(font, "Awaiting neural topology...", (150, 150, 150))
            surface.blit(hint, (self.rect.x + 20, self.rect.y + 40))
            return

        num_layers = len(net_sizes)
        if num_layers < 2:
            return

        # Layout calculations
        pad_x, pad_y = 80, 50
        usable_w = self.rect.width - pad_x * 2
        usable_h = self.rect.height - pad_y * 2
        layer_spacing_x = usable_w / (num_layers - 1)

        # Compute node positions (limit visual nodes to 16 per layer for performance)
        node_positions: List[List[Tuple[int, int]]] = []
        for l_idx, n_nodes in enumerate(net_sizes):
            render_nodes = min(n_nodes, 16)
            node_spacing_y = 0
            if render_nodes > 1:
                node_spacing_y = usable_h / (render_nodes - 1)
            layer_pos = []
            cx = self.rect.x + pad_x + int(l_idx * layer_spacing_x)
            for n_idx in range(render_nodes):
                if render_nodes == 1:
                    cy = self.rect.y + pad_y + usable_h // 2
                else:
                    cy = self.rect.y + pad_y + int(n_idx * node_spacing_y)
                layer_pos.append((cx, cy))
            node_positions.append(layer_pos)

        # Draw synaptic connections (weights)
        for l_idx, w_layer in enumerate(net_weights):
            in_nodes = node_positions[l_idx]
            out_nodes = node_positions[l_idx + 1]
            for out_i, out_pos in enumerate(out_nodes):
                if out_i >= len(w_layer):
                    continue
                node_weights = w_layer[out_i]
                for in_i, in_pos in enumerate(in_nodes):
                    if in_i >= len(node_weights):
                        continue
                    w_val = node_weights[in_i]
                    # Only draw significant weights to reduce clutter and improve performance
                    if abs(w_val) < 0.2:
                        continue
                    # Color: Green for positive (excitatory), Red for negative (inhibitory)
                    if w_val > 0:
                        color = (0, min(255, int(w_val * 200)), 0)
                    else:
                        color = (min(255, int(abs(w_val) * 200)), 0, 0)
                    thickness = max(1, min(3, int(abs(w_val) * 1.5)))
                    pygame.draw.line(surface, color, in_pos, out_pos, thickness)

        # Draw neurons (activations)
        for l_idx, layer_pos in enumerate(node_positions):
            activations = []
            if net_outputs and l_idx < len(net_outputs):
                activations = net_outputs[l_idx]
            for n_idx, (nx, ny) in enumerate(layer_pos):
                act_val = activations[n_idx] if n_idx < len(activations) else 0.0
                intensity = min(255, max(0, int((act_val + 1.0) * 127.5)))
                if l_idx == 0:
                    node_color = (intensity // 2, intensity // 2, 255)
                elif l_idx == num_layers - 1:
                    node_color = (0, intensity, intensity)
                else:
                    node_color = (intensity, 0, intensity)
                pygame.draw.circle(surface, node_color, (nx, ny), 6)
                pygame.draw.circle(surface, (200, 200, 200), (nx, ny), 6, 1)

        # Labels for input / output sides
        in_lbl = get_cached_text(font, "Sensory Inputs", (150, 150, 255))
        surface.blit(in_lbl, (self.rect.x + pad_x - 40, self.rect.y + 25))
        out_lbl = get_cached_text(font, "Motor Outputs", (150, 255, 255))
        surface.blit(out_lbl, (self.rect.x + self.rect.width - pad_x - 40, self.rect.y + 25))
