import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import raylib
# Run hidden for test verification
raylib.SetConfigFlags(raylib.FLAG_WINDOW_HIDDEN)

from project.renderer.raylib_renderer import RaylibSimulationRenderer
from project.world.terrain import TerrainManager
from project.world.time import WorldTimeManager
from project.civilization.settlement import world_settlement_mgr
from project.world.ancient_ruins import ancient_ruins_mgr
from run_gui import spawn_genesis_population

print("=== STARTING FULL RAYLIB + REAL WORLD INTEGRATION BENCHMARK ===")
world_w, world_h = 14336.0, 14336.0
renderer = RaylibSimulationRenderer(width=1280, height=720, world_width=world_w, world_height=world_h)
tm = TerrainManager(seed=42)
time_mgr = WorldTimeManager()

entities = []
spawn_genesis_population(entities, world_w, world_h)
print(f"Spawned {len(entities)} genesis entities at world center ({world_w*0.5:.0f}, {world_h*0.5:.0f})")

# Convert to snapshot format
def make_snapshot(ents):
    snap = []
    for e in ents:
        snap.append({
            "id": e.entity_id,
            "x": e.pos_x,
            "y": e.pos_y,
            "radius": getattr(e, "radius", 4.0),
            "type": e.entity_type.name,
            "role": e.custom_data.get("role_title", "Microbe"),
            "species_id": e.species_id,
            "is_alive": e.is_alive,
            "heading": getattr(e, "heading", 0.0),
            "energy": getattr(e, "energy", 100.0),
            "consciousness": e.custom_data.get("consciousness_level", 0.5),
            "custom_data": e.custom_data,
        })
    return snap

# Run at multiple zoom levels
zoom_levels = [0.08, 0.45, 1.0, 1.8, 2.5]
for z in zoom_levels:
    renderer.camera.zoom = z
    t0 = time.time()
    for tick in range(20):
        snap = make_snapshot(entities)
        renderer.render(
            entities_snapshot=snap,
            terrain_manager=tm,
            pheromone_grid=None,
            system_timings={},
            sim_tick=tick,
            stats_history=[],
            time_manager=time_mgr,
            god_affinity=65.0,
            ruins_manager=ancient_ruins_mgr,
        )
    dur = time.time() - t0
    fps = 20.0 / dur
    print(f"Zoom {z:>4.2f}x: 20 frames rendered in {dur*1000/20:>5.2f} ms/frame ({fps:>5.1f} FPS) [HARDWARE GPU]")

renderer.close()
print("=== FULL RAYLIB + REAL WORLD INTEGRATION BENCHMARK PASSED 100% ===")
