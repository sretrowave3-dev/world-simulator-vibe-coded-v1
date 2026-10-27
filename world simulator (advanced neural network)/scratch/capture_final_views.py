import os
import sys
import pygame

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from project.renderer.renderer import SimulationRenderer
from project.world.terrain import TerrainManager
from project.ai.pheromone import PheromoneGrid
from project.world.time import WorldTimeManager
from project.civilization.settlement import world_settlement_mgr, WorldStructure
from project.world.ancient_ruins import ancient_ruins_mgr

renderer = SimulationRenderer(width=1280, height=720, world_width=14336.0, world_height=14336.0)
tm = TerrainManager(seed=42)
grid = PheromoneGrid(width=100, height=100, cell_size=16.0)
time_mgr = WorldTimeManager()

# Add sample structures
world_settlement_mgr.structures.clear()
s1 = WorldStructure(structure_id="s1", structure_type="campfire", pos_x=7180.0, pos_y=7180.0, clan_id="clan_1", built_tick=0)
s2 = WorldStructure(structure_id="s2", structure_type="timber_shelter", pos_x=7220.0, pos_y=7170.0, clan_id="clan_1", built_tick=0)
s3 = WorldStructure(structure_id="s3", structure_type="stone_house", pos_x=7140.0, pos_y=7210.0, clan_id="clan_1", built_tick=0)
world_settlement_mgr.structures["s1"] = s1
world_settlement_mgr.structures["s2"] = s2
world_settlement_mgr.structures["s3"] = s3

# Sample living entities
sample_entities = [
    # Human Leader with Axe
    {"id": "h_leader", "type": "HUMAN", "species_id": "homo_sapiens", "x": 7185.0, "y": 7185.0, "radius": 4.0, "is_alive": True, "role": "LEADER", "heading": 0.5, "equipped_tool": "STONE_AXE", "action": "TIMBER", "consciousness": 0.85},
    # Human Warrior with Spear
    {"id": "h_warrior", "type": "HUMAN", "species_id": "homo_sapiens", "x": 7195.0, "y": 7175.0, "radius": 4.0, "is_alive": True, "role": "WARRIOR", "heading": 2.1, "equipped_tool": "HUNTING_SPEAR", "action": "DEFEND", "consciousness": 0.4},
    # Human Miner with Pickaxe
    {"id": "h_miner", "type": "HUMAN", "species_id": "homo_sapiens", "x": 7160.0, "y": 7200.0, "radius": 4.0, "is_alive": True, "role": "WORKER", "heading": 3.4, "equipped_tool": "PICKAXE", "action": "MINE", "consciousness": 0.3},
    # Panther Predator stalking
    {"id": "p_predator", "type": "PREDATOR", "species_id": "panther", "x": 7260.0, "y": 7190.0, "radius": 4.5, "is_alive": True, "heading": 3.8},
    # Gazelle Herbivore
    {"id": "herb_1", "type": "HERBIVORE", "species_id": "gazelle", "x": 7130.0, "y": 7150.0, "radius": 3.8, "is_alive": True, "heading": 1.2},
    # Mature Trees with Fruit
    {"id": "tree_1", "type": "PLANT", "species_id": "oak_tree", "x": 7150.0, "y": 7170.0, "radius": 6.0, "is_alive": True, "custom_data": {"is_tree": True, "growth_stage": "tree", "fruit_kg": 15.0}},
    {"id": "tree_2", "type": "PLANT", "species_id": "apple_tree", "x": 7210.0, "y": 7210.0, "radius": 7.0, "is_alive": True, "custom_data": {"is_tree": True, "growth_stage": "ancient_tree", "fruit_kg": 35.0}},
]

renderer.camera.pos_x = 7180.0
renderer.camera.pos_y = 7180.0

out_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Capture Far Zoom (0.08x) - Continental Satellite Relief View
renderer.camera.zoom = 0.08
renderer.render(sample_entities, tm, grid, {}, 50, [], time_mgr, 60.0)
p1 = os.path.join(out_dir, "view_far_zoom_final.png")
pygame.image.save(renderer.screen, p1)
print(f"Captured: {p1}")

# 2. Capture Mid Zoom (0.60x) - Tactical Regional Overview
renderer.camera.zoom = 0.60
renderer.render(sample_entities, tm, grid, {}, 50, [], time_mgr, 60.0)
p2 = os.path.join(out_dir, "view_mid_zoom_final.png")
pygame.image.save(renderer.screen, p2)
print(f"Captured: {p2}")

# 3. Capture Core Zoom (1.40x) - Local Settlement & Organism Detail View
renderer.camera.zoom = 1.40
renderer.render(sample_entities, tm, grid, {}, 50, [], time_mgr, 60.0)
p3 = os.path.join(out_dir, "view_core_zoom_final.png")
pygame.image.save(renderer.screen, p3)
print(f"Captured: {p3}")

# 4. Capture Micro Zoom (2.60x) - Intimate Microscopic View of Characters & Photoreal Materials
renderer.camera.zoom = 2.60
renderer.render(sample_entities, tm, grid, {}, 50, [], time_mgr, 60.0)
p4 = os.path.join(out_dir, "view_micro_zoom_final.png")
pygame.image.save(renderer.screen, p4)
print(f"Captured: {p4}")

renderer.close()
print("All 4 final visual quality verification frames captured successfully!")
