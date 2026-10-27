import pygame
import math
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from project.world.terrain import TerrainManager
tm = TerrainManager(seed=42)

# Generate a 512x512 vibrant Clash of Clans overview atlas
res = 512
surf = pygame.Surface((res, res))
world_width = 14336.0
world_height = 14336.0
step_x = world_width / res
step_y = world_height / res

for px in range(res):
    wx = px * step_x
    for py in range(res):
        wy = py * step_y
        h, w_str, b_type = tm.sample_surface_point(wx, wy)
        
        hillshade = 0.92 + (h - 0.45) * 0.25
        
        if "RIVER" in w_str or "STREAM" in w_str:
            c = (60, 195, 250)
        elif "OCEAN" in w_str:
            c = (28, 92, 172) if h < 0.18 else ((38, 125, 205) if h < 0.28 else (52, 165, 235))
        elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
            c = (248, 252, 255)
        elif h > 0.65 or "MOUNTAIN" in b_type:
            val = max(115, min(185, int(140 * hillshade)))
            c = (val, int(val * 1.02), int(val * 1.08))
        elif "DESERT" in b_type or "BEACH" in b_type or h < 0.38:
            c = (max(200, int(238 * hillshade)), max(170, int(208 * hillshade)), max(100, int(132 * hillshade)))
        elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
            c = (max(45, int(65 * hillshade)), max(115, int(148 * hillshade)), max(35, int(48 * hillshade)))
        else:
            mown = 10 if ((px // 4 + py // 4) % 2 == 0) else 0
            r = max(70, min(145, int((104 + mown) * hillshade)))
            g = max(140, min(230, int((186 + mown) * hillshade)))
            b = max(40, min(100, int((56 + mown * 0.5) * hillshade)))
            c = (r, g, b)
            
        surf.set_at((px, py), c)

arr = pygame.surfarray.pixels3d(surf)
print("New Clash Atlas:")
print("  Mean RGB:", arr.mean(axis=(0, 1)).astype(int).tolist())
print("  Min RGB: ", arr.min(axis=(0, 1)).tolist())
print("  Max RGB: ", arr.max(axis=(0, 1)).tolist())

pygame.image.save(surf, "world simulator (advanced neural network)/scratch/test_clash_atlas_preview.png")
print("Saved test_clash_atlas_preview.png!")
