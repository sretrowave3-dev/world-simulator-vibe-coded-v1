import pygame
import numpy as np

for name in ["view_far_zoom.png", "view_mid_zoom.png", "view_core_zoom.png"]:
    p = f"world simulator (advanced neural network)/scratch/{name}"
    surf = pygame.image.load(p)
    arr = pygame.surfarray.pixels3d(surf)
    print(f"=== {name} ({surf.get_size()}) ===")
    print(f"  Mean RGB: {arr.mean(axis=(0, 1)).astype(int)}")
    print(f"  Min RGB:  {arr.min(axis=(0, 1))}")
    print(f"  Max RGB:  {arr.max(axis=(0, 1))}")
    # Check green saturation vs blue vs earth tones
    is_water = (arr[:, :, 2] > arr[:, :, 0] * 1.3) & (arr[:, :, 2] > 60)
    is_green = (arr[:, :, 1] > arr[:, :, 0] * 1.2) & (arr[:, :, 1] > arr[:, :, 2] * 1.2)
    is_rock = (np.abs(arr[:, :, 0].astype(int) - arr[:, :, 1].astype(int)) < 15) & (arr[:, :, 0] < 120) & (arr[:, :, 0] > 40)
    print(f"  Water pixels: {np.sum(is_water)} | Green land: {np.sum(is_green)} | Rock/Mountains: {np.sum(is_rock)}")
