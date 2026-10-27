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
res = 32
m_step = 256.0 / res
chunk_data = []

for py in range(res):
    row = []
    for px in range(res):
        wx = cx * 256.0 + px * m_step
        wy = cy * 256.0 + py * m_step
        h, w_str, b_str = tm.sample_surface_point(wx, wy)
        row.append((w_str, b_str, h))
    chunk_data.append(row)

# Let's count river, ocean, grassland tiles
river_count = sum(1 for r in chunk_data for c in r if "RIVER" in c[0])
print(f"Sampled {res}x{res} chunk at ({cx}, {cy}): found {river_count} river sample points!")
