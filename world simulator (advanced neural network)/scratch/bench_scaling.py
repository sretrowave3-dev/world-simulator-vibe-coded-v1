import pygame
import time
import os
import sys

# Test chunk scaling speed: transform.scale vs smoothscale for 50 chunks
pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

surf = pygame.Surface((64, 64))
surf.fill((34, 110, 48))

# Test smoothscale 50 times (simulating 50 chunks on screen)
t0 = time.perf_counter()
for _ in range(50):
    s = pygame.transform.smoothscale(surf, (180, 180))
t1 = time.perf_counter()
smooth_ms = (t1 - t0) * 1000.0

# Test standard scale 50 times
t2 = time.perf_counter()
for _ in range(50):
    s = pygame.transform.scale(surf, (180, 180))
t3 = time.perf_counter()
scale_ms = (t3 - t2) * 1000.0

print(f"50 chunks smoothscale: {smooth_ms:.2f} ms")
print(f"50 chunks fast scale:  {scale_ms:.2f} ms")
print(f"Speedup: {smooth_ms / max(0.001, scale_ms):.1f}x FASTER!")
