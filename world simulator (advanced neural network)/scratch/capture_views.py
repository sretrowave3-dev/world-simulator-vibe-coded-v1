import pygame
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.world.terrain import TerrainManager
from project.renderer.texture_baker import ensure_baked_textures
from project.renderer.camera import Camera

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
screen = pygame.Surface((1280, 720))

tm = TerrainManager(seed=42)
textures = ensure_baked_textures()

from scratch.bench_hierarchical_v2 import SeamlessHierarchicalRenderer

renderer = SeamlessHierarchicalRenderer(textures, seed=42)
camera = Camera(screen_width=1280, screen_height=720)
camera.pos_x = 7168.0
camera.pos_y = 7168.0

# 1. Capture Far Zoom (0.08x)
camera.zoom = 0.08
screen.fill((10, 15, 20))
renderer.draw_terrain_grid(screen, camera, tm, sim_tick=10)
renderer.draw_vignette(screen)
pygame.image.save(screen, "world simulator (advanced neural network)/scratch/view_far_zoom.png")
print("Saved view_far_zoom.png")

# 2. Capture Mid Zoom (0.60x)
camera.zoom = 0.60
screen.fill((10, 15, 20))
renderer.draw_terrain_grid(screen, camera, tm, sim_tick=10)
renderer.draw_vignette(screen)
pygame.image.save(screen, "world simulator (advanced neural network)/scratch/view_mid_zoom.png")
print("Saved view_mid_zoom.png")

# 3. Capture Core Zoom In (1.40x)
camera.zoom = 1.40
screen.fill((10, 15, 20))
renderer.draw_terrain_grid(screen, camera, tm, sim_tick=10)
renderer.draw_vignette(screen)
pygame.image.save(screen, "world simulator (advanced neural network)/scratch/view_core_zoom.png")
print("Saved view_core_zoom.png")

renderer.close()
