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

sample_entities = [
    {"id": f"e_{i}", "type": "HUMAN" if i % 2 == 0 else "HERBIVORE", "species_id": "homo_sapiens" if i % 2 == 0 else "gazelle", "x": 7000.0 + (i % 20) * 10, "y": 7000.0 + (i // 20) * 10, "radius": 4.0, "is_alive": True, "heading": 0.5}
    for i in range(100)
]

renderer.camera.pos_x = 7168.0
renderer.camera.pos_y = 7168.0

print("=== PROFILING RENDER PERFORMANCE AT MULTIPLE ZOOM LEVELS ===")

zoom_levels = [0.05, 0.15, 0.30, 0.35, 0.50, 0.80, 1.20, 2.00]

for z in zoom_levels:
    renderer.camera.zoom = z
    # Measure warm-up frame
    t0 = time.perf_counter()
    renderer.render(
        entities_snapshot=sample_entities,
        terrain_manager=tm,
        pheromone_grid=grid,
        system_timings={},
        sim_tick=10,
        stats_history=[],
        time_manager=time_mgr,
        god_affinity=50.0,
    )
    t1 = time.perf_counter()
    warm_ms = (t1 - t0) * 1000.0
    
    # Measure subsequent frame (cached)
    t2 = time.perf_counter()
    renderer.render(
        entities_snapshot=sample_entities,
        terrain_manager=tm,
        pheromone_grid=grid,
        system_timings={},
        sim_tick=11,
        stats_history=[],
        time_manager=time_mgr,
        god_affinity=50.0,
    )
    t3 = time.perf_counter()
    cached_ms = (t3 - t2) * 1000.0
    
    # Measure with camera panning by 20 meters (simulating player movement)
    renderer.camera.pos_x += 20.0
    t4 = time.perf_counter()
    renderer.render(
        entities_snapshot=sample_entities,
        terrain_manager=tm,
        pheromone_grid=grid,
        system_timings={},
        sim_tick=12,
        stats_history=[],
        time_manager=time_mgr,
        god_affinity=50.0,
    )
    t5 = time.perf_counter()
    pan_ms = (t5 - t4) * 1000.0
    
    print(f"Zoom {z:4.2f}x | First frame: {warm_ms:6.1f}ms | Cached frame: {cached_ms:6.1f}ms | Pan frame: {pan_ms:6.1f}ms")

renderer.close()
