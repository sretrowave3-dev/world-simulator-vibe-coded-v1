import pygame
import time
import os
import sys

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

sample_entities = []

renderer.camera.pos_x = 7168.0
renderer.camera.pos_y = 7168.0

print("=== CONTINUOUS ZOOM TEST (SIMULATING MOUSE WHEEL SCROLL) ===")
# Simulate user zooming in smoothly from 0.1 to 1.0 (20 steps)
zoom = 0.1
times = []
for step in range(30):
    renderer.camera.zoom = zoom
    t0 = time.perf_counter()
    renderer.render(
        entities_snapshot=sample_entities,
        terrain_manager=tm,
        pheromone_grid=grid,
        system_timings={},
        sim_tick=step,
        stats_history=[],
        time_manager=time_mgr,
        god_affinity=50.0,
    )
    t1 = time.perf_counter()
    dt_ms = (t1 - t0) * 1000.0
    times.append((zoom, dt_ms))
    zoom += 0.05

for z, ms in times:
    print(f"Zoom {z:4.2f}x: {ms:6.1f} ms {'🚨 LAG SPIKE!' if ms > 30 else ''}")

renderer.close()
