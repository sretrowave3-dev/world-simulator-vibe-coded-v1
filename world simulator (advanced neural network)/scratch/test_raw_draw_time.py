import pygame
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, 'world simulator (advanced neural network)')

from project.renderer.renderer import SimulationRenderer
from project.world.terrain import TerrainManager
from project.ai.pheromone import PheromoneGrid
from project.world.time import WorldTimeManager

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

renderer = SimulationRenderer(width=1280, height=720, world_width=14336.0, world_height=14336.0)
tm = TerrainManager(seed=42)
grid = PheromoneGrid(width=100, height=100, cell_size=16.0)
time_mgr = WorldTimeManager()

sample_entities = [
    {"id": f"h_{i}", "type": "HUMAN", "species_id": "homo_sapiens", "x": 7168.0 + (i % 5) * 20, "y": 7168.0 + (i // 5) * 20, "radius": 4.0, "is_alive": True, "role": "LEADER" if i == 0 else "WARRIOR", "heading": 0.4}
    for i in range(15)
] + [
    {"id": f"p_{i}", "type": "PREDATOR", "species_id": "panther", "x": 7250.0 + i * 15, "y": 7200.0, "radius": 4.5, "is_alive": True, "heading": 1.1}
    for i in range(5)
]

renderer.camera.pos_x = 7168.0
renderer.camera.pos_y = 7168.0

print("=== RAW DRAW TIME (WITHOUT CLOCK.TICK SLEEP) ===")
zoom = 0.05
draw_times = []

for step in range(35):
    renderer.camera.zoom = zoom
    renderer.camera.pos_x += 15.0
    renderer.camera.pos_y += 10.0
    
    # Measure draw work
    t0 = time.perf_counter()
    renderer.screen.fill((24, 34, 28))
    renderer.overlays.draw_terrain(renderer.screen, renderer.camera, tm, False, 14336.0, 14336.0, sim_tick=step)
    renderer.overlays.draw_structures(renderer.screen, renderer.camera, sim_tick=step)
    renderer.overlays.draw_vignette(renderer.screen)
    t1 = time.perf_counter()
    
    draw_ms = (t1 - t0) * 1000.0
    draw_times.append((zoom, draw_ms))
    zoom += 0.05

renderer.close()

for z, ms in draw_times:
    print(f"Zoom {z:4.2f}x raw draw: {ms:5.2f} ms {'🚨 BOTTLENECK!' if ms > 10.0 else '⚡ LIGHTNING FAST'}")
