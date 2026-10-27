import pygame
import time
import queue
import threading
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.world.terrain import TerrainManager
from project.renderer.texture_baker import ensure_baked_textures

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
tm = TerrainManager(seed=42)
textures = ensure_baked_textures()

# Test fast chunk generation with 16x16 resolution
def fast_get_chunk(cx, cy, tm, textures, res=16):
    surf = pygame.Surface((res, res))
    # Base grass
    surf.blit(pygame.transform.smoothscale(textures["grass_photoreal"], (res, res)), (0, 0))
    
    m_step = 256.0 / res
    has_river = False
    river_mask = pygame.Surface((res, res), pygame.SRCALPHA)
    
    for px in range(res):
        wx = cx * 256.0 + px * m_step
        for py in range(res):
            wy = cy * 256.0 + py * m_step
            h, w_str, b_type = tm.sample_surface_point(wx, wy)
            if "RIVER" in w_str:
                has_river = True
                river_mask.set_at((px, py), (255, 255, 255, 255))
                
    if has_river:
        water_layer = pygame.transform.smoothscale(textures["river_water"], (res, res)).copy()
        water_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(water_layer, (0, 0))
        
        foam_layer = pygame.transform.smoothscale(textures["river_foam"], (res, res)).copy()
        foam_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(foam_layer, (0, 0))
        
    return surf, has_river

t0 = time.perf_counter()
for i in range(10):
    s, r = fast_get_chunk(5 + i, 10, tm, textures, res=16)
t1 = time.perf_counter()

print(f"10 chunks at 16x16: {(t1 - t0)*1000.0:.2f} ms ({((t1 - t0)*1000.0)/10:.2f} ms per chunk)")
