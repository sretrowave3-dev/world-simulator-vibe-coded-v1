import pygame
import os
import math
import numpy as np

pygame.init()
ref_grass_path = "world simulator (advanced neural network)/model refrence/jake-nackos-C2PCa6DhlYE-unsplash.jpg"
ref_river_path = "world simulator (advanced neural network)/model refrence/joris-visser-8konJx6dY4g-unsplash.jpg"

print("Loading reference textures...")
img_grass = pygame.image.load(ref_grass_path)
img_river = pygame.image.load(ref_river_path)
print("Loaded grass:", img_grass.get_size(), "river:", img_river.get_size())

# Let's crop high quality 256x256 representative texture tiles
# Grass: lush green patch from center
grass_tile = pygame.Surface((256, 256))
grass_tile.blit(pygame.transform.smoothscale(img_grass.subsurface((1200, 1800, 1024, 1024)), (256, 256)), (0, 0))

# River gorge rock: dark wet rock from left side of gorge
rock_tile = pygame.Surface((256, 256))
rock_tile.blit(pygame.transform.smoothscale(img_river.subsurface((100, 1500, 700, 700)), (256, 256)), (0, 0))

# River water: deep turquoise water from center river
water_tile = pygame.Surface((256, 256))
water_tile.blit(pygame.transform.smoothscale(img_river.subsurface((1100, 2200, 600, 600)), (256, 256)), (0, 0))

# Whitewater rapids foam: from rapids region
foam_tile = pygame.Surface((256, 256))
foam_tile.blit(pygame.transform.smoothscale(img_river.subsurface((800, 1200, 600, 600)), (256, 256)), (0, 0))

print("Created 256x256 texture tiles successfully!")
