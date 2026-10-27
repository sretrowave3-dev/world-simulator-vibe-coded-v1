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
]

renderer.camera.pos_x = 7168.0
renderer.camera.pos_y = 7168.0
renderer.camera.zoom = 1.40

print("=== BREAKDOWN AT ZOOM 1.40x ===")

# Test 1: overlays.draw_terrain
t0 = time.perf_counter()
renderer.overlays.draw_terrain(renderer.screen, renderer.camera, tm, False, 14336.0, 14336.0, sim_tick=10)
t1 = time.perf_counter()
print(f"1. draw_terrain: {(t1 - t0)*1000.0:.2f} ms")

# Test 2: overlays.draw_structures
t0 = time.perf_counter()
renderer.overlays.draw_structures(renderer.screen, renderer.camera, sim_tick=10)
t1 = time.perf_counter()
print(f"2. draw_structures: {(t1 - t0)*1000.0:.2f} ms")

# Test 3: overlays.draw_ancient_ruins
from project.world.ancient_ruins import ancient_ruins_mgr
t0 = time.perf_counter()
renderer.overlays.draw_ancient_ruins(renderer.screen, renderer.camera, ancient_ruins_mgr, sim_tick=10)
t1 = time.perf_counter()
print(f"3. draw_ancient_ruins: {(t1 - t0)*1000.0:.2f} ms")

# Test 4: Entity drawing loop
t0 = time.perf_counter()
# Run entity draw segment
sun_props = {"daylight_factor": 1.0, "day_fraction": 0.5, "phase": "MIDDAY"}
zoom = renderer.camera.zoom
min_wx, min_wy, max_wx, max_wy = renderer.camera.get_visible_world_bounds(margin=60.0)
for entity in sample_entities:
    sx, sy = renderer.camera.world_to_screen(entity["x"], entity["y"])
    hr = max(5, int(entity["radius"] * 3.5 * zoom))
    pygame.draw.circle(renderer.screen, (180, 130, 75), (sx, sy), hr)
t1 = time.perf_counter()
print(f"4. Entity draw loop: {(t1 - t0)*1000.0:.2f} ms")

# Test 5: overlays.draw_vignette
t0 = time.perf_counter()
renderer.overlays.draw_vignette(renderer.screen)
t1 = time.perf_counter()
print(f"5. draw_vignette: {(t1 - t0)*1000.0:.2f} ms")

# Test 6: overlays.draw_day_night_sky
t0 = time.perf_counter()
renderer.overlays.draw_day_night_sky(renderer.screen, renderer.camera, sun_props)
t1 = time.perf_counter()
print(f"6. draw_day_night_sky: {(t1 - t0)*1000.0:.2f} ms")

# Test 7: UI & Inspector
t0 = time.perf_counter()
renderer.inspector.draw(renderer.screen, renderer.font)
for btn in renderer.buttons:
    btn.draw(renderer.screen, renderer.font)
t1 = time.perf_counter()
print(f"7. UI draw: {(t1 - t0)*1000.0:.2f} ms")

# Test 8: display.flip
t0 = time.perf_counter()
pygame.display.flip()
t1 = time.perf_counter()
print(f"8. display.flip: {(t1 - t0)*1000.0:.2f} ms")

renderer.close()
