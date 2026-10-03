"""
project/renderer/particles.py

Juice & FX Particle Emitter simulation engine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple


from collections import deque


@dataclass
class Particle:
    pos_x: float
    pos_y: float
    vel_x: float
    vel_y: float
    color_rgb: Tuple[int, int, int]
    alpha: float
    scale: float
    lifespan_sec: float
    age_sec: float = 0.0


class ParticleSystemManager:
    """Manages particle simulations and rendering ticks."""

    def __init__(self, max_particles: int = 1000) -> None:
        self.max_particles = max_particles
        self.particles: deque[Particle] = deque(maxlen=max_particles)

    def spawn(
        self,
        pos_x: float,
        pos_y: float,
        vel_x: float,
        vel_y: float,
        color_rgb: Tuple[int, int, int],
        scale: float = 2.0,
        lifespan: float = 1.0,
    ) -> None:
        """Spawns a new visual particle in O(1) time."""
        self.particles.append(
            Particle(
                pos_x=pos_x,
                pos_y=pos_y,
                vel_x=vel_x,
                vel_y=vel_y,
                color_rgb=color_rgb,
                alpha=1.0,
                scale=scale,
                lifespan_sec=lifespan,
            )
        )

    def tick(self, dt: float) -> None:
        """Updates particle coordinates and ages them out."""
        active = deque(maxlen=self.max_particles)
        for p in self.particles:
            p.age_sec += dt
            if p.age_sec < p.lifespan_sec:
                # Euler motion step
                p.pos_x += p.vel_x * dt
                p.pos_y += p.vel_y * dt
                # Fade out alpha linearily
                p.alpha = max(0.0, 1.0 - (p.age_sec / p.lifespan_sec))
                active.append(p)
        self.particles = active

    def clear(self) -> None:
        self.particles.clear()
