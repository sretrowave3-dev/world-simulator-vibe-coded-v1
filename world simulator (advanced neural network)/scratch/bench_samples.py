import pygame
import time
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.world.terrain import TerrainManager

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
tm = TerrainManager(seed=42)

# Benchmark 1: sample_surface_point at 32x32 vs 16x16 vs 8x8
for res in [32, 16, 12, 8]:
    t0 = time.perf_counter()
    for px in range(res):
        wx = 1280.0 + px * (256.0 / res)
        for py in range(res):
            wy = 1280.0 + py * (256.0 / res)
            tm.sample_surface_point(wx, wy)
    t1 = time.perf_counter()
    print(f"Sampling {res}x{res} ({res*res} points): {(t1 - t0)*1000.0:.2f} ms")
