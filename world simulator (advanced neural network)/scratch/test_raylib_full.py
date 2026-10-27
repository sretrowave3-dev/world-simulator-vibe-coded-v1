import os
import sys
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath("world simulator (advanced neural network)")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from project.renderer.raylib_renderer import RaylibSimulationRenderer
import raylib
from raylib import *

print("Starting Raylib Full Test...")
renderer = RaylibSimulationRenderer(width=1280, height=720)

# Create mock entities
mock_entities = [
    {
        "id": 1,
        "type": "HUMAN",
        "pos": [100.0, 100.0],
        "energy": 85.0,
        "health": 95.0,
        "hydration": 80.0,
        "alive": True,
        "is_alive": True,
        "generation": 3,
        "action": "Gathering",
        "state": "GATHERING",
        "role": "Woodcutter",
        "inventory": ["wood", "berries"],
        "equipped_tool": "Stone Axe",
        "target_pos": [150.0, 120.0],
        "psychology": {
            "dopamine": 0.8,
            "serotonin": 0.6,
            "stress": 0.2,
            "curiosity": 0.9,
            "fear": 0.1,
            "consciousness": 0.75,
            "dominant_drive": "CURIOSITY"
        }
    },
    {
        "id": 2,
        "type": "HERBIVORE",
        "pos": [180.0, 140.0],
        "energy": 60.0,
        "health": 80.0,
        "hydration": 70.0,
        "alive": True,
        "is_alive": True,
        "generation": 2,
        "action": "Grazing",
        "state": "GRAZING",
        "psychology": {
            "dopamine": 0.5,
            "serotonin": 0.5,
            "stress": 0.1,
            "curiosity": 0.4,
            "fear": 0.05,
            "consciousness": 0.3,
            "dominant_drive": "HUNGER"
        }
    },
    {
        "id": 3,
        "type": "PREDATOR",
        "pos": [220.0, 200.0],
        "energy": 90.0,
        "health": 100.0,
        "hydration": 65.0,
        "alive": True,
        "is_alive": True,
        "generation": 1,
        "action": "Stalking",
        "state": "HUNTING",
        "psychology": {
            "dopamine": 0.7,
            "serotonin": 0.4,
            "stress": 0.3,
            "curiosity": 0.6,
            "fear": 0.0,
            "consciousness": 0.45,
            "dominant_drive": "PREDATION"
        }
    },
    {
        "id": 4,
        "type": "PLANT",
        "pos": [120.0, 160.0],
        "energy": 100.0,
        "health": 100.0,
        "hydration": 100.0,
        "alive": True,
        "is_alive": True
    },
    {
        "id": 5,
        "type": "BACTERIA",
        "pos": [90.0, 80.0],
        "energy": 40.0,
        "health": 50.0,
        "hydration": 50.0,
        "alive": True,
        "is_alive": True
    }
]

# Run 100 frames
print("Running 100 render loop frames...")
start_time = time.time()
for frame in range(100):
    # Select entity 1 to test inspector
    renderer.selected_entity_id = 1
    
    # Toggle ADV DEV mode on to test all advanced panels
    renderer.adv_dev_mode = True
    
    # Check that checkboxes are active
    renderer.checkboxes[1].checked = True # Minimap
    renderer.checkboxes[2].checked = True # Diagnostics
    
    # Slightly adjust camera zoom to test zoom scaling
    renderer.camera.zoom = 0.1 + (frame % 20) * 0.05
    
    renderer.render(
        entities_snapshot=mock_entities,
        terrain_manager=None,
        pheromone_grid=None,
        system_timings={"Sim": 1.2, "Neural": 0.8},
        sim_tick=frame,
        stats_history=[{"total_pop": 5 + i % 3} for i in range(frame + 1)],
        time_manager=None,
        god_affinity=78.5,
        ruins_manager=None
    )
    
    if WindowShouldClose():
        print(f"Window closed at frame {frame}")
        break

total_time = time.time() - start_time
print(f"100 frames completed in {total_time:.2f} seconds ({100/total_time:.1f} FPS)!")

renderer.close()
print("Renderer successfully closed!")
