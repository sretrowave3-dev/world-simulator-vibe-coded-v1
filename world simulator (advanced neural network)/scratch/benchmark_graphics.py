import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import time
import pygame
from project.renderer.renderer import SimulationRenderer
from project.world.terrain import TerrainManager
from project.ai.pheromone import PheromoneGrid

pygame.init()
renderer = SimulationRenderer(width=1280, height=720, world_width=4096.0, world_height=4096.0)
terrain_mgr = TerrainManager(seed=42)
pheromone_grid = PheromoneGrid(width=256, height=256, cell_size=16.0)

# 1,000 mock entities across species
entities_snapshot = []
species_types = ["BACTERIA", "PLANT", "HERBIVORE", "PREDATOR", "HUMAN", "AVIAN", "REPTILE"]
for i in range(1000):
    entities_snapshot.append({
        "id": f"ent_{i}",
        "type": species_types[i % len(species_types)],
        "x": float((i * 37) % 4096),
        "y": float((i * 73) % 4096),
        "radius": 2.5,
        "is_alive": True,
        "heading": 0.5,
        "role": "LEADER" if i == 0 else None,
        "consciousness": 0.9 if i == 0 else 0.0,
    })

# Warmup
for _ in range(10):
    renderer.render(entities_snapshot, terrain_mgr, pheromone_grid, {}, 100)

# Benchmark 200 frames
t0 = time.perf_counter()
frames = 200
for tick in range(frames):
    renderer.render(entities_snapshot, terrain_mgr, pheromone_grid, {"Physics": 0.001, "AI": 0.002}, tick)
t1 = time.perf_counter()

total_time = t1 - t0
fps = frames / total_time
frame_ms = (total_time / frames) * 1000.0

print("=" * 60)
print(f"🚀 CPU GRAPHICS BENCHMARK RESULTS (1,000 Entities @ 1280x720)")
print("=" * 60)
print(f"Total Time for {frames} Frames: {total_time:.3f} seconds")
print(f"Average Frame Render Time : {frame_ms:.2f} ms")
print(f"Effective Framerate       : {fps:.1f} FPS (Target: 60.0 FPS)")
print("=" * 60)

renderer.close()
