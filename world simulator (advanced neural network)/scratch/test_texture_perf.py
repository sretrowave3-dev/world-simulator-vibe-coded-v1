import pygame
import time
import math
import numpy as np

# Verify that texture blitting and blending can run at 60+ FPS
pygame.init()
pygame.display.set_mode((1280, 720))

from project.renderer.texture_baker import ensure_baked_textures
textures = ensure_baked_textures()
print("Loaded textures for test:", list(textures.keys()))

screen = pygame.display.get_surface()
clock = pygame.time.Clock()

# Measure blit speed of 256x256 textured chunks across a 1280x720 screen
start = time.perf_counter()
for frame in range(100):
    for x in range(0, 1280, 256):
        for y in range(0, 720, 256):
            screen.blit(textures["grass_photoreal"], (x, y))
            # Blit semi-transparent river foam
            screen.blit(textures["river_foam"], (x, y))
    clock.tick()
end = time.perf_counter()

fps = 100 / (end - start)
print(f"Direct textured rendering benchmark: {fps:.1f} FPS (Target: 60 FPS)")
pygame.quit()
