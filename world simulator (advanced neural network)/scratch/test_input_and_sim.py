import os
import sys
import time

BASE_DIR = os.path.abspath("world simulator (advanced neural network)")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from project.renderer.raylib_renderer import RaylibSimulationRenderer
import raylib
from raylib import *

print("Testing Raylib Input & UI...")
renderer = RaylibSimulationRenderer(width=1280, height=720)

mock_snapshot = [
    {
        "id": 1,
        "type": "HUMAN",
        "x": 100.0,
        "y": 100.0,
        "radius": 5.0,
        "health": 100.0,
        "max_health": 100.0,
        "energy": 90.0,
        "hydration": 85.0,
        "is_alive": True,
        "role": "LEADER",
        "species_id": "Homo_Sapiens",
        "equipped_tool": "Spear",
        "dopamine": 0.8,
        "serotonin": 0.7,
        "stress": 0.1,
        "curiosity": 0.9,
        "fear": 0.05,
        "consciousness": 0.88
    }
]

# Run 30 frames with handle_input called
for f in range(30):
    alive = renderer.handle_input(mock_snapshot)
    if not alive:
        break
    renderer.render(
        entities_snapshot=mock_snapshot,
        terrain_manager=None,
        pheromone_grid=None,
        system_timings={},
        sim_tick=f,
        stats_history=[],
        time_manager=None,
        god_affinity=60.0,
        ruins_manager=None
    )

print("Renderer input and render loop test passed successfully!")
renderer.close()
