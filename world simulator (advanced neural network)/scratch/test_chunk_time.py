import pygame
import time
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')

from project.renderer.overlays import OverlayRenderer
from project.world.terrain import TerrainManager

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

ov = OverlayRenderer()
tm = TerrainManager(seed=42)

# Measure time to generate 1 chunk
times = []
for cx in range(10):
    for cy in range(10):
        t0 = time.perf_counter()
        surf = ov._get_chunk_surface(cx, cy, tm)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

print(f"Average time per chunk: {sum(times)/len(times):.2f} ms")
print(f"Max time for a chunk:   {max(times):.2f} ms")
print(f"Min time for a chunk:   {min(times):.2f} ms")
