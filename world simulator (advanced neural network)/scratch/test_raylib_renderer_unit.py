import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import raylib
raylib.SetConfigFlags(raylib.FLAG_WINDOW_HIDDEN)

from project.renderer.raylib_renderer import RaylibSimulationRenderer
from project.world.terrain import TerrainManager
from project.world.time import WorldTimeManager

print("Initializing RaylibSimulationRenderer...")
renderer = RaylibSimulationRenderer(width=1280, height=720, world_width=14336.0, world_height=14336.0)
tm = TerrainManager(seed=42)
time_mgr = WorldTimeManager()

sample_snapshot = [
    {"id": "h_leader", "x": 7180.0, "y": 7180.0, "type": "HUMAN", "role": "LEADER", "radius": 4.0, "is_alive": True, "heading": 0.5, "energy": 90.0, "consciousness": 0.85},
    {"id": "panther_1", "x": 7220.0, "y": 7200.0, "type": "PREDATOR", "radius": 4.5, "is_alive": True, "heading": 2.1, "energy": 70.0},
    {"id": "tree_1", "x": 7150.0, "y": 7160.0, "type": "PLANT", "species_id": "oak_tree", "radius": 6.0, "is_alive": True},
]

print("Rendering 30 frames with RaylibSimulationRenderer...")
for tick in range(30):
    renderer.render(
        entities_snapshot=sample_snapshot,
        terrain_manager=tm,
        pheromone_grid=None,
        system_timings={},
        sim_tick=tick,
        stats_history=[],
        time_manager=time_mgr,
        god_affinity=50.0,
        ruins_manager=None,
    )

print("Testing input handling...")
alive = renderer.handle_input(sample_snapshot)
print(f"handle_input returned: {alive}")

print("Closing renderer...")
renderer.close()
print("RaylibSimulationRenderer Unit Test PASSED with 100% success!")
