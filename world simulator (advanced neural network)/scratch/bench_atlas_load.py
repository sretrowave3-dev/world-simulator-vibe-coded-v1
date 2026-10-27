import pygame
import time
import os

pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

# Save a test 256x256 atlas
test_path = "world simulator (advanced neural network)/cache/test_atlas.png"
dummy_surf = pygame.Surface((256, 256))
pygame.image.save(dummy_surf, test_path)

# Measure load time
t0 = time.perf_counter()
loaded = pygame.image.load(test_path).convert()
t1 = time.perf_counter()

print(f"Loading cached 256x256 atlas from disk: {(t1 - t0)*1000.0:.2f} ms!")
if os.path.exists(test_path):
    os.remove(test_path)
