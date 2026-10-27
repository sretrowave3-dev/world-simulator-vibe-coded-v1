"""
project/renderer/texture_baker.py

Pre-rendered stylized textures inspired by Clash of Clans aesthetic:
- Lush vibrant emerald-lime village grass with clean mown stripes and wild daisies
- Clear tropical cyan river channels with gentle wave caustics
- Stylized rounded riverbank cobblestones and pebbles
- Crisp white shoreline rapids foam
- Warm sunny golden beach dunes
- Clean beveled granite cliff rocks
- Pristine bright marshmallow snow
- Vibrant coastal sapphire blue ocean
"""

import os
import math
import pygame
import numpy as np
from typing import Dict, Optional, Tuple

TEXTURE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "assets", "textures")


def make_seamless(surf: pygame.Surface, border: int = 16) -> pygame.Surface:
    """Creates a seamless tileable texture from a pygame Surface using boundary cross-fade."""
    w, h = surf.get_size()
    arr = pygame.surfarray.array3d(surf).astype(np.float32)
    
    for x in range(border):
        t = (x / border) * 0.5
        left_col = arr[x, :].copy()
        right_col = arr[w - 1 - x, :].copy()
        arr[x, :] = left_col * (0.5 + t) + right_col * (0.5 - t)
        arr[w - 1 - x, :] = right_col * (0.5 + t) + left_col * (0.5 - t)
        
    for y in range(border):
        t = (y / border) * 0.5
        top_row = arr[:, y].copy()
        bottom_row = arr[:, h - 1 - y].copy()
        arr[:, y] = top_row * (0.5 + t) + bottom_row * (0.5 - t)
        arr[:, h - 1 - y] = bottom_row * (0.5 + t) + top_row * (0.5 - t)
        
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(arr)


def bake_clash_grass(size: int = 128) -> pygame.Surface:
    """Vibrant lush Clash of Clans village lawn with clean mowing stripes and daisies."""
    s = pygame.Surface((size, size))
    col_base = (104, 186, 56)
    col_stripe = (116, 198, 66)
    col_dark = (92, 172, 48)
    s.fill(col_base)
    sub = 16
    for y in range(0, size, sub):
        for x in range(0, size, sub):
            if ((x // sub) + (y // sub)) % 2 == 0:
                pygame.draw.rect(s, col_stripe, (x, y, sub, sub))
    for y in range(0, size, 8):
        for x in range(0, size, 8):
            h = (x * 37 + y * 73) % 100
            if h < 25:
                pygame.draw.line(s, (135, 215, 80), (x, y + 3), (x + 1, y), 1)
            elif h > 85:
                pygame.draw.line(s, col_dark, (x, y + 2), (x, y), 1)
    for fx, fy in [(24, 36), (88, 18), (44, 92), (108, 76), (16, 112), (64, 64)]:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            s.set_at((fx + dx, fy + dy), (252, 252, 255))
        s.set_at((fx, fy), (255, 225, 65))
    return make_seamless(s, border=16)


def bake_clash_water(size: int = 128) -> pygame.Surface:
    """Clear tropical cyan river water with clean wave ripples."""
    s = pygame.Surface((size, size))
    s.fill((45, 165, 225))
    for y in range(size):
        for x in range(size):
            w1 = math.sin(x * 0.15 + y * 0.1) * 15
            w2 = math.cos(x * 0.08 - y * 0.12) * 12
            v = int(w1 + w2)
            if v > 14:
                s.set_at((x, y), (120, 225, 255))
            elif v > 5:
                s.set_at((x, y), (75, 195, 245))
            elif v < -14:
                s.set_at((x, y), (30, 120, 185))
    return make_seamless(s, border=16)


def bake_clash_rock(size: int = 128) -> pygame.Surface:
    """Clean rounded river cobblestones."""
    s = pygame.Surface((size, size))
    s.fill((135, 145, 158))
    for y in range(0, size, 16):
        for x in range(0, size, 16):
            r = ((x * 17 + y * 29) % 5) + 5
            pygame.draw.circle(s, (160, 172, 188), (x + 8, y + 8), r)
            pygame.draw.circle(s, (180, 192, 208), (x + 7, y + 7), max(2, r - 2))
            pygame.draw.circle(s, (95, 105, 118), (x + 8, y + 8), r, 1)
    return make_seamless(s, border=16)


def bake_clash_foam(size: int = 128) -> pygame.Surface:
    """Crisp white shoreline foam with alpha."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    for y in range(0, size, 12):
        for x in range(0, size, 12):
            if (x + y) % 24 == 0:
                pygame.draw.circle(s, (245, 252, 255, 210), (x + 6, y + 6), 4)
                pygame.draw.circle(s, (220, 245, 255, 140), (x + 6, y + 6), 6)
    return s


def bake_clash_sand(size: int = 128) -> pygame.Surface:
    """Sunny warm golden sand with stylized ripples."""
    s = pygame.Surface((size, size))
    s.fill((240, 210, 135))
    for y in range(size):
        for x in range(size):
            ripple = math.sin((x * 0.2 + y * 0.1)) * 14
            if ripple > 7:
                s.set_at((x, y), (250, 225, 155))
            elif ripple < -7:
                s.set_at((x, y), (222, 188, 112))
    return make_seamless(s, border=16)


def bake_clash_mountain(size: int = 128) -> pygame.Surface:
    """Clean faceted cliff stone with sunlit bevels."""
    s = pygame.Surface((size, size))
    s.fill((128, 138, 152))
    for y in range(0, size, 24):
        for x in range(0, size, 24):
            pts = [(x, y + 24), (x + 12, y), (x + 24, y + 24)]
            pygame.draw.polygon(s, (175, 185, 200), pts)
            pts_shadow = [(x + 12, y), (x + 24, y + 24), (x + 12, y + 24)]
            pygame.draw.polygon(s, (95, 105, 118), pts_shadow)
    return make_seamless(s, border=16)


def bake_clash_snow(size: int = 128) -> pygame.Surface:
    """Crisp bright marshmallow alpine snow."""
    s = pygame.Surface((size, size))
    s.fill((246, 250, 255))
    for y in range(size):
        for x in range(size):
            h = math.sin(x * 0.1 + y * 0.1) * 10
            if h < -6:
                s.set_at((x, y), (210, 230, 248))
    return make_seamless(s, border=16)


def bake_clash_ocean(size: int = 128) -> pygame.Surface:
    """Vibrant coastal sapphire ocean."""
    s = pygame.Surface((size, size))
    s.fill((34, 112, 195))
    for y in range(size):
        for x in range(size):
            caustic = math.sin(x * 0.08 + y * 0.07) * 12 + math.cos(x * 0.05 - y * 0.09) * 10
            if caustic > 10:
                s.set_at((x, y), (60, 165, 235))
            elif caustic < -10:
                s.set_at((x, y), (22, 85, 160))
    return make_seamless(s, border=16)


def ensure_baked_textures(force_rebake: bool = False) -> Dict[str, pygame.Surface]:
    """Ensures stylized Clash of Clans pre-rendered textures are baked and loaded."""
    os.makedirs(TEXTURE_CACHE_DIR, exist_ok=True)
    
    expected_files = {
        "grass_photoreal": "grass_photoreal.png",
        "river_water": "river_water.png",
        "river_rock": "river_rock.png",
        "river_foam": "river_foam.png",
        "sand_dune": "sand_dune.png",
        "mountain_stone": "mountain_stone.png",
        "snow_ice": "snow_ice.png",
        "deep_ocean": "deep_ocean.png"
    }

    all_exist = all(os.path.exists(os.path.join(TEXTURE_CACHE_DIR, fn)) for fn in expected_files.values())

    if not all_exist or force_rebake:
        generators = {
            "grass_photoreal.png": bake_clash_grass,
            "river_water.png": bake_clash_water,
            "river_rock.png": bake_clash_rock,
            "river_foam.png": bake_clash_foam,
            "sand_dune.png": bake_clash_sand,
            "mountain_stone.png": bake_clash_mountain,
            "snow_ice.png": bake_clash_snow,
            "deep_ocean.png": bake_clash_ocean,
        }
        for fn, gen in generators.items():
            surf = gen()
            pygame.image.save(surf, os.path.join(TEXTURE_CACHE_DIR, fn))

    textures: Dict[str, pygame.Surface] = {}
    has_display = pygame.display.get_surface() is not None
    for key, fn in expected_files.items():
        fp = os.path.join(TEXTURE_CACHE_DIR, fn)
        if os.path.exists(fp):
            try:
                raw_surf = pygame.image.load(fp)
                if has_display:
                    textures[key] = raw_surf.convert_alpha() if "foam" in key else raw_surf.convert()
                else:
                    textures[key] = raw_surf
            except Exception:
                pass
                
    return textures
