import os
import sys
import time
import threading
import random

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import raylib
raylib.SetConfigFlags(raylib.FLAG_WINDOW_HIDDEN)

from project.renderer.raylib_renderer import RaylibSimulationRenderer
from project.civilization.settlement import world_settlement_mgr
from project.world.terrain import TerrainManager
from project.world.time import WorldTimeManager
from project.world.ancient_ruins import ancient_ruins_mgr

print("=== STARTING CONCURRENT MUTATION STRESS TEST ===")
renderer = RaylibSimulationRenderer(width=1280, height=720, world_width=14336.0, world_height=14336.0)
tm = TerrainManager(seed=42)
time_mgr = WorldTimeManager()

# Background worker continuously adding/removing structures
running = True
def structure_spammer():
    st_types = ["campfire", "dirt_dugout", "wooden_cabin", "cobblestone_house"]
    while running:
        st = random.choice(st_types)
        x = 7180.0 + random.uniform(-500, 500)
        y = 7180.0 + random.uniform(-500, 500)
        world_settlement_mgr.spawn_structure(st, x, y, "test_clan", tick=1)
        if len(world_settlement_mgr.structures) > 50:
            with world_settlement_mgr._lock:
                k = next(iter(world_settlement_mgr.structures))
                del world_settlement_mgr.structures[k]
        time.sleep(0.001)

spam_thread = threading.Thread(target=structure_spammer, daemon=True)
spam_thread.start()

# Main render thread rendering 120 frames at high speed
for f in range(120):
    renderer.render(
        entities_snapshot=[],
        terrain_manager=tm,
        pheromone_grid=None,
        system_timings={},
        sim_tick=f,
        stats_history=[],
        time_manager=time_mgr,
        god_affinity=50.0,
        ruins_manager=ancient_ruins_mgr,
    )

running = False
spam_thread.join(timeout=1.0)
renderer.close()
print("=== CONCURRENT MUTATION STRESS TEST PASSED WITH ZERO CRASHES! ===")
