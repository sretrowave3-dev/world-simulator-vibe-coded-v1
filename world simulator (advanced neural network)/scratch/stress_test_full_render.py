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

print("=== REAL SIMULATION RENDER LOOP STRESS TEST (CONTINUOUS ZOOM & PAN) ===")
zoom = 0.05
step_times = []

# Simulate user zooming in smoothly from 0.05 to 2.0 while panning camera
for step in range(35):
    renderer.camera.zoom = zoom
    renderer.camera.pos_x += 15.0  # Pan 15m every frame
    renderer.camera.pos_y += 10.0
    
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
    step_times.append((zoom, dt_ms))
    zoom += 0.05

renderer.close()

# Report stats
print("\nResults:")
lag_count = 0
for z, ms in step_times:
    is_lag = ms > 16.67
    if is_lag:
        lag_count += 1
    tag = "[LAG SPIKE]" if is_lag else "[60 FPS SOLID]"
    print(f"  Zoom {z:4.2f}x: {ms:5.2f} ms {tag}")

print(f"\nTotal steps: {len(step_times)} | Lag spikes (>16.6ms): {lag_count} | 60 FPS Rate: {((len(step_times)-lag_count)/len(step_times))*100:.1f}%\n")
