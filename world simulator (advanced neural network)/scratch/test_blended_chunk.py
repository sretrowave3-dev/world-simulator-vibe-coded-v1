import pygame
import math
import numpy as np
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.renderer.texture_baker import ensure_baked_textures
from project.world.terrain import TerrainManager

pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)
textures = ensure_baked_textures()
tm = TerrainManager(seed=42)

cx, cy = 5, 10
res = 128
surf = pygame.Surface((res, res))

# 1. Base tile: lush photorealistic grass from jake-nackos photo!
grass_tex = pygame.transform.smoothscale(textures["grass_photoreal"], (res, res))
rock_tex = pygame.transform.smoothscale(textures["river_rock"], (res, res))
water_tex = pygame.transform.smoothscale(textures["river_water"], (res, res))
foam_tex = pygame.transform.smoothscale(textures["river_foam"], (res, res))

surf.blit(grass_tex, (0, 0))

m_step = 256.0 / res

# River mask surface
river_surf = pygame.Surface((res, res), pygame.SRCALPHA)
bank_surf = pygame.Surface((res, res), pygame.SRCALPHA)

# Sample grid
for px in range(res):
    wx = cx * 256.0 + px * m_step
    for py in range(res):
        wy = cy * 256.0 + py * m_step
        h, w_str, b_type = tm.sample_surface_point(wx, wy)
        if "RIVER" in w_str:
            river_surf.set_at((px, py), (255, 255, 255, 255))
            bank_surf.set_at((px, py), (255, 255, 255, 255))

# Dilate bank by downscaling and upscaling with blur
small_bank = pygame.transform.smoothscale(bank_surf, (res // 4, res // 4))
blurred_bank = pygame.transform.smoothscale(small_bank, (res, res))

small_river = pygame.transform.smoothscale(river_surf, (res // 2, res // 2))
blurred_river = pygame.transform.smoothscale(small_river, (res, res))

# Blit bank rock using alpha mask
rock_layer = rock_tex.copy()
rock_layer.blit(blurred_bank, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
surf.blit(rock_layer, (0, 0))

# Blit river water using alpha mask
water_layer = water_tex.copy()
water_layer.blit(blurred_river, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
surf.blit(water_layer, (0, 0))

# Blit river foam overlay
foam_layer = foam_tex.copy()
foam_layer.blit(blurred_river, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
surf.blit(foam_layer, (0, 0))

out_path = "world simulator (advanced neural network)/scratch/test_photoreal_chunk.png"
pygame.image.save(surf, out_path)
print("Saved photorealistic blended chunk with 0 external dependencies to:", out_path)
