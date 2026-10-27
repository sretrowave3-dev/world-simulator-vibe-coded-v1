import pygame
import numpy as np

pygame.init()
i_river = pygame.image.load('world simulator (advanced neural network)/model refrence/joris-visser-8konJx6dY4g-unsplash.jpg')
w, h = i_river.get_size()

# Sample rock on the left/right, deep water in the center, and white foam in the center rapids
# Let's inspect center slice
center_crop = pygame.transform.smoothscale(i_river.subsurface((w//4, h//4, w//2, h//2)), (256, 256))
arr = pygame.surfarray.pixels3d(center_crop)

# Let's find white foam (high brightness in R,G,B)
brightness = arr.sum(axis=2) / 3.0
foam_mask = brightness > 160
deep_water_mask = (arr[:, :, 2] > 70) & (brightness < 120) & (arr[:, :, 2] > arr[:, :, 0] * 1.2)
rock_mask = (brightness < 70) & (arr[:, :, 2] < 70)

print("Foam RGB:", arr[foam_mask].mean(axis=0) if np.any(foam_mask) else "None")
print("Deep water RGB:", arr[deep_water_mask].mean(axis=0) if np.any(deep_water_mask) else "None")
print("Dark rock RGB:", arr[rock_mask].mean(axis=0) if np.any(rock_mask) else "None")
