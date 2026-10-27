import pygame
import time
import math
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.world.terrain import TerrainManager

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
tm = TerrainManager(seed=42)

cache_dir = "world simulator (advanced neural network)/cache"
os.makedirs(cache_dir, exist_ok=True)
atlas_path = os.path.join(cache_dir, "continental_atlas_42.png")

def get_or_create_atlas(tm, path, res=256, world_w=14336.0, world_h=14336.0):
    if os.path.exists(path):
        t0 = time.perf_counter()
        surf = pygame.image.load(path)
        t1 = time.perf_counter()
        print(f"Loaded existing atlas from disk in {(t1 - t0)*1000.0:.2f} ms!")
        return surf
        
    print(f"Generating high-definition continental atlas ({res}x{res})...")
    t0 = time.perf_counter()
    surf = pygame.Surface((res, res))
    step_x = world_w / res
    step_y = world_h / res
    
    for px in range(res):
        wx = px * step_x
        for py in range(res):
            wy = py * step_y
            h, w_str, b_type = tm.sample_surface_point(wx, wy)
            
            # Sun from NW
            hillshade = 0.88 + (h - 0.45) * 0.35 + (math.sin(wx * 0.04 + wy * 0.04) * 0.04)
            
            if "RIVER" in w_str or "STREAM" in w_str:
                # Glacial azure river with frothing rapids crests
                shimmer = math.sin(wx * 0.15 + wy * 0.12)
                c = (225, 245, 255) if shimmer > 0.4 else (42, 115, 168)
            elif "OCEAN" in w_str:
                if h < 0.18:
                    c = (10, 24, 48)   # Deep marine abyss
                elif h < 0.28:
                    c = (18, 48, 92)   # Continental shelf
                else:
                    c = (26, 75, 140)  # Coastal shallows
            elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                c = (245, 248, 255)    # Alpine snow
            elif h > 0.65 or "MOUNTAIN" in b_type:
                val = max(55, min(160, int(105 * hillshade)))
                c = (val, int(val * 0.98), int(val * 1.05))
            elif h > 0.52:
                c = (max(45, int(75 * hillshade)), max(60, int(98 * hillshade)), max(40, int(65 * hillshade)))
            elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
                c = (max(16, int(22 * hillshade)), max(48, int(82 * hillshade)), max(20, int(32 * hillshade)))
            elif "DESERT" in b_type or "BEACH" in b_type:
                c = (max(140, int(205 * hillshade)), max(120, int(180 * hillshade)), max(80, int(125 * hillshade)))
            elif "SWAMP" in b_type:
                c = (max(28, int(42 * hillshade)), max(45, int(68 * hillshade)), max(30, int(50 * hillshade)))
            else:
                # Lush emerald grassland
                micro = math.sin(wx * 0.25) * math.cos(wy * 0.25) * 6.0
                r = max(20, min(80, int((32 + micro * 0.5) * hillshade)))
                g = max(60, min(165, int((108 + micro * 1.5) * hillshade)))
                b = max(22, min(85, int((36 + micro * 0.6) * hillshade)))
                c = (r, g, b)
                
            surf.set_at((px, py), c)
            
    pygame.image.save(surf, path)
    t1 = time.perf_counter()
    print(f"Generated & saved atlas to disk in {(t1 - t0)*1000.0:.2f} ms!")
    return surf

# First call: generates & caches
atlas1 = get_or_create_atlas(tm, atlas_path, res=256)
# Second call: loads from cache
atlas2 = get_or_create_atlas(tm, atlas_path, res=256)
