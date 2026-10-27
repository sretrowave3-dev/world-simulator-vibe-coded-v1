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

# Chunk with river at (5, 10)
cx, cy = 5, 10
res = 64
m_step = 256.0 / res
surf = pygame.Surface((res, res))

for px in range(res):
    wx = cx * 256.0 + px * m_step
    for py in range(res):
        wy = cy * 256.0 + py * m_step
        h, w_str, b_type = tm.sample_surface_point(wx, wy)
        
        # Relief hillshade (sun from NW)
        hillshade = 0.88 + (h - 0.45) * 0.35 + (math.sin(wx * 0.06 + wy * 0.06) * 0.04)

        if "RIVER" in w_str or "STREAM" in w_str:
            # Alpine river matching joris-visser photo
            shimmer = math.sin(wx * 0.25 + wy * 0.2) * 12
            # Churning rapids foam
            churn = math.sin(wx * 0.15 + wy * 0.12) * math.cos(wx * 0.08 - wy * 0.14)
            foam_intensity = max(0.0, churn * 1.5)
            
            # Deep glacial azure base
            r_base = 42 + shimmer * 0.4
            g_base = 108 + shimmer * 0.8
            b_base = 168 + shimmer

            if foam_intensity > 0.4:
                foam_t = min(1.0, (foam_intensity - 0.4) * 2.2)
                r = int(r_base * (1.0 - foam_t) + 230 * foam_t)
                g = int(g_base * (1.0 - foam_t) + 242 * foam_t)
                b = int(b_base * (1.0 - foam_t) + 252 * foam_t)
            else:
                r, g, b = int(r_base), int(g_base), int(b_base)
                
            c = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        elif "OCEAN" in w_str:
            c = (14, 38, 75) if h < 0.2 else (22, 68, 128)
        elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
            val = int(245 * hillshade)
            c = (max(200, min(255, val)), max(205, min(255, val + 5)), 255)
        elif h > 0.68 or "MOUNTAIN" in b_type:
            val = int(105 * hillshade)
            c = (max(45, min(170, int(val * 0.95))), max(50, min(175, val)), max(55, min(180, int(val * 1.05))))
        elif "DESERT" in b_type or "BEACH" in b_type:
            c = (max(140, min(230, int(205 * hillshade))), max(120, min(205, int(180 * hillshade))), max(80, min(155, int(125 * hillshade))))
        elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
            c = (max(15, min(55, int(22 * hillshade))), max(45, min(125, int(82 * hillshade))), max(20, min(65, int(35 * hillshade))))
        else:
            # Lush grassland matching jake-nackos photo
            micro = math.sin(wx * 0.45) * math.cos(wy * 0.45) * 8.0 + math.sin(wx * 1.1 + wy * 0.9) * 4.0
            r = max(22, min(95, int((34 + micro * 0.6) * hillshade)))
            g = max(60, min(175, int((112 + micro * 1.8) * hillshade)))
            b = max(24, min(90, int((38 + micro * 0.7) * hillshade)))
            c = (r, g, b)

        surf.set_at((px, py), c)

out_path = "world simulator (advanced neural network)/scratch/test_chunk_64.png"
pygame.image.save(surf, out_path)
print(f"Generated test chunk image saved to: {out_path}")
