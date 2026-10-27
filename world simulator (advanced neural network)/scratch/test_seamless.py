import pygame
import numpy as np

def make_seamless(surf: pygame.Surface, border: int = 32) -> pygame.Surface:
    """Creates a seamless tileable texture from a pygame Surface using boundary cross-fade."""
    w, h = surf.get_size()
    arr = pygame.surfarray.array3d(surf).astype(np.float32)
    
    # Horizontal wrap blending
    for x in range(border):
        t = (x / border) * 0.5
        left_col = arr[x, :].copy()
        right_col = arr[w - 1 - x, :].copy()
        arr[x, :] = left_col * (0.5 + t) + right_col * (0.5 - t)
        arr[w - 1 - x, :] = right_col * (0.5 + t) + left_col * (0.5 - t)
        
    # Vertical wrap blending
    for y in range(border):
        t = (y / border) * 0.5
        top_row = arr[:, y].copy()
        bottom_row = arr[:, h - 1 - y].copy()
        arr[:, y] = top_row * (0.5 + t) + bottom_row * (0.5 - t)
        arr[:, h - 1 - y] = bottom_row * (0.5 + t) + top_row * (0.5 - t)
        
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(arr)

pygame.init()
img_grass = pygame.image.load("world simulator (advanced neural network)/model refrence/jake-nackos-C2PCa6DhlYE-unsplash.jpg")
tile = pygame.transform.smoothscale(img_grass.subsurface((1000, 1500, 1024, 1024)), (256, 256))
seamless_grass = make_seamless(tile)
print("Seamless grass generated:", seamless_grass.get_size())
