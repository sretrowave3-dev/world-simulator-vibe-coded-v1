"""
project/renderer/__init__.py

Visual Pygame Rendering Subsystems for the Echo Evolution Simulator.
"""

try:
    from project.renderer.camera import Camera
    from project.renderer.minimap import Minimap
    from project.renderer.inspector import Inspector
    from project.renderer.overlays import OverlayRenderer
    from project.renderer.heatmaps import HeatmapRenderer
    from project.renderer.particles import ParticleSystemManager
    from project.renderer.debug_renderer import DebugRenderer
    from project.renderer.renderer import SimulationRenderer
    HAS_RENDERER = True
except ImportError:
    Camera = Minimap = Inspector = OverlayRenderer = None  # type: ignore
    HeatmapRenderer = ParticleSystemManager = DebugRenderer = SimulationRenderer = None  # type: ignore
    HAS_RENDERER = False

__all__ = [
    "Camera",
    "Minimap",
    "Inspector",
    "OverlayRenderer",
    "HeatmapRenderer",
    "ParticleSystemManager",
    "DebugRenderer",
    "SimulationRenderer",
    "HAS_RENDERER",
]
