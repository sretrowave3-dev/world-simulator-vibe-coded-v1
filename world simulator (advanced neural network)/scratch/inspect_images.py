import pygame
import numpy as np

pygame.init()
i_grass = pygame.image.load('world simulator (advanced neural network)/model refrence/jake-nackos-C2PCa6DhlYE-unsplash.jpg')
i_river = pygame.image.load('world simulator (advanced neural network)/model refrence/joris-visser-8konJx6dY4g-unsplash.jpg')

print("Grass size:", i_grass.get_size())
print("River size:", i_river.get_size())

# Sample some crop regions
sub_grass = pygame.transform.smoothscale(i_grass.subsurface((500, 500, 1024, 1024)), (128, 128))
sub_river = pygame.transform.smoothscale(i_river.subsurface((500, 1000, 1024, 1024)), (128, 128))

# Get average colors
arr_g = pygame.surfarray.pixels3d(sub_grass)
arr_r = pygame.surfarray.pixels3d(sub_river)

print("Grass mean RGB:", arr_g.mean(axis=(0, 1)))
print("Grass min/max RGB:", arr_g.min(axis=(0, 1)), arr_g.max(axis=(0, 1)))

print("River mean RGB:", arr_r.mean(axis=(0, 1)))
print("River min/max RGB:", arr_r.min(axis=(0, 1)), arr_r.max(axis=(0, 1)))
