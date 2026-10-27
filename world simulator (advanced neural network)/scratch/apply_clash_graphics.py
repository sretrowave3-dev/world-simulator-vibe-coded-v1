import os
import re

overlays_path = r"world simulator (advanced neural network)\project\renderer\overlays.py"
baker_path = r"world simulator (advanced neural network)\project\renderer\texture_baker.py"
renderer_path = r"world simulator (advanced neural network)\project\renderer\renderer.py"

# --- 1. UPDATE TEXTURE_BAKER.PY ---
baker_code = '''"""
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
'''

with open(baker_path, "w", encoding="utf-8") as f:
    f.write(baker_code)
print("texture_baker.py updated successfully!")

# --- 2. UPDATE OVERLAYS.PY ---
with open(overlays_path, "r", encoding="utf-8") as f:
    o_text = f.read()

# Replace _compile_chunk_surface with clean, direct per-pixel Clash tile mapping
old_compile = """    def _compile_chunk_surface(self, cx: int, cy: int, terrain_manager: Any) -> pygame.Surface:
        \"\"\"Compiles a single high-definition terrain chunk surface with photorealistic materials.\"\"\"
        res = self.CHUNK_TEX_RES
        m_step = self.CHUNK_METERS / res
        surf = pygame.Surface((res, res))

        # Base lush photorealistic grass from reference photo
        if "grass_photoreal" in getattr(self, "_tex_res", {}):
            surf.blit(self._tex_res["grass_photoreal"], (0, 0))
        elif "grass_photoreal" in self.textures:
            surf.blit(pygame.transform.smoothscale(self.textures["grass_photoreal"], (res, res)), (0, 0))
        else:
            surf.fill((32, 105, 36))

        has_river = False
        has_mountain = False
        has_desert = False
        has_snow = False
        has_ocean = False

        river_mask = pygame.Surface((res, res), pygame.SRCALPHA)
        bank_mask = pygame.Surface((res, res), pygame.SRCALPHA)
        mountain_mask = pygame.Surface((res, res), pygame.SRCALPHA)
        desert_mask = pygame.Surface((res, res), pygame.SRCALPHA)
        snow_mask = pygame.Surface((res, res), pygame.SRCALPHA)
        ocean_mask = pygame.Surface((res, res), pygame.SRCALPHA)

        for px in range(res):
            wx = cx * self.CHUNK_METERS + px * m_step
            for py in range(res):
                wy = cy * self.CHUNK_METERS + py * m_step

                if hasattr(terrain_manager, "sample_surface_point"):
                    h, w_str, b_type = terrain_manager.sample_surface_point(wx, wy)
                elif hasattr(terrain_manager, "get_tile"):
                    tile = terrain_manager.get_tile(int(wx), int(wy))
                    if tile:
                        w_type = getattr(tile, "water_type", None)
                        w_str = str(w_type).upper() if w_type else ""
                        h = getattr(tile, "height", 0.4)
                        b_type = str(getattr(tile, "biome", "")).upper()
                    else:
                        w_str, h, b_type = "", 0.4, ""
                else:
                    w_str, h, b_type = "", 0.4, ""

                if "RIVER" in w_str or "STREAM" in w_str:
                    has_river = True
                    river_mask.set_at((px, py), (255, 255, 255, 255))
                    bank_mask.set_at((px, py), (255, 255, 255, 255))
                elif "OCEAN" in w_str:
                    has_ocean = True
                    ocean_mask.set_at((px, py), (255, 255, 255, 255))
                elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                    has_snow = True
                    snow_mask.set_at((px, py), (255, 255, 255, 255))
                elif h > 0.68 or "MOUNTAIN" in b_type:
                    has_mountain = True
                    mountain_mask.set_at((px, py), (255, 255, 255, 255))
                elif "DESERT" in b_type or "BEACH" in b_type:
                    has_desert = True
                    desert_mask.set_at((px, py), (255, 255, 255, 255))

        # Blend distinct biomes
        tex_map = getattr(self, "_tex_res", {})
        if has_desert:
            tex = tex_map.get("sand_dune") or (pygame.transform.smoothscale(self.textures["sand_dune"], (res, res)) if "sand_dune" in self.textures else None)
            if tex:
                d_surf = tex.copy()
                d_surf.blit(desert_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(d_surf, (0, 0))

        if has_mountain:
            tex = tex_map.get("mountain_stone") or (pygame.transform.smoothscale(self.textures["mountain_stone"], (res, res)) if "mountain_stone" in self.textures else None)
            if tex:
                m_surf = tex.copy()
                m_surf.blit(mountain_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(m_surf, (0, 0))

        if has_snow:
            tex = tex_map.get("snow_ice") or (pygame.transform.smoothscale(self.textures["snow_ice"], (res, res)) if "snow_ice" in self.textures else None)
            if tex:
                s_surf = tex.copy()
                s_surf.blit(snow_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(s_surf, (0, 0))

        if has_ocean:
            tex = tex_map.get("deep_ocean") or (pygame.transform.smoothscale(self.textures["deep_ocean"], (res, res)) if "deep_ocean" in self.textures else None)
            if tex:
                o_surf = tex.copy()
                o_surf.blit(ocean_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(o_surf, (0, 0))

        # River Gorge Canyon & Whitewater Rapids (100% matched to joris-visser reference photo)
        if has_river:
            self._river_chunks.add((cx, cy))
            small_b = pygame.transform.smoothscale(bank_mask, (max(4, res // 4), max(4, res // 4)))
            blurred_b = pygame.transform.smoothscale(small_b, (res, res))

            r_rock = tex_map.get("river_rock") or (pygame.transform.smoothscale(self.textures["river_rock"], (res, res)) if "river_rock" in self.textures else None)
            if r_rock:
                rock_layer = r_rock.copy()
                rock_layer.blit(blurred_b, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(rock_layer, (0, 0))

            r_water = tex_map.get("river_water") or (pygame.transform.smoothscale(self.textures["river_water"], (res, res)) if "river_water" in self.textures else None)
            if r_water:
                water_layer = r_water.copy()
                water_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(water_layer, (0, 0))

            r_foam = tex_map.get("river_foam") or (pygame.transform.smoothscale(self.textures["river_foam"], (res, res)) if "river_foam" in self.textures else None)
            if r_foam:
                foam_layer = r_foam.copy()
                foam_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(foam_layer, (0, 0))

        return surf"""

new_compile = """    def _compile_chunk_surface(self, cx: int, cy: int, terrain_manager: Any) -> pygame.Surface:
        \"\"\"Compiles a single high-definition terrain chunk using pre-rendered stylized Clash of Clans graphics.\"\"\"
        res = self.CHUNK_TEX_RES
        m_step = self.CHUNK_METERS / res
        surf = pygame.Surface((res, res))

        tex_map = getattr(self, "_tex_res", {})
        t_grass = tex_map.get("grass_photoreal")
        t_water = tex_map.get("river_water")
        t_sand = tex_map.get("sand_dune")
        t_mountain = tex_map.get("mountain_stone")
        t_snow = tex_map.get("snow_ice")
        t_ocean = tex_map.get("deep_ocean")

        has_sampler = hasattr(terrain_manager, "sample_surface_point")

        for px in range(res):
            wx = cx * self.CHUNK_METERS + px * m_step
            for py in range(res):
                wy = cy * self.CHUNK_METERS + py * m_step

                if has_sampler:
                    h, w_str, b_type = terrain_manager.sample_surface_point(wx, wy)
                else:
                    h, w_str, b_type = 0.4, "", ""

                # Direct sampling from pre-rendered Clash of Clans stylized textures (100% vibrant, 0 darkening)
                if "RIVER" in w_str or "STREAM" in w_str:
                    self._river_chunks.add((cx, cy))
                    c = t_water.get_at((px, py)) if t_water else (60, 195, 250)
                elif "OCEAN" in w_str:
                    c = t_ocean.get_at((px, py)) if t_ocean else (38, 125, 205)
                elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                    c = t_snow.get_at((px, py)) if t_snow else (248, 252, 255)
                elif h > 0.65 or "MOUNTAIN" in b_type:
                    c = t_mountain.get_at((px, py)) if t_mountain else (140, 150, 165)
                elif "DESERT" in b_type or "BEACH" in b_type or h < 0.38:
                    c = t_sand.get_at((px, py)) if t_sand else (238, 208, 132)
                elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
                    c = (65, 148, 48)
                else:
                    c = t_grass.get_at((px, py)) if t_grass else (104, 186, 56)

                surf.set_at((px, py), c)

        return surf"""

assert old_compile in o_text, "Could not find old _compile_chunk_surface in overlays.py"
o_text = o_text.replace(old_compile, new_compile, 1)

# Replace _get_overview_surface with Clash of Clans palette
old_overview_palette = """                # Relief hillshade (sun from NW: top-left)
                hillshade = 0.88 + (h - 0.45) * 0.35 + (math.sin(wx * 0.04 + wy * 0.04) * 0.04)

                # Modern Alpine and Photorealistic Biome Palette
                if "RIVER" in w_str or "STREAM" in w_str:
                    shimmer = math.sin(wx * 0.15 + wy * 0.12)
                    c = (225, 245, 255) if shimmer > 0.4 else (42, 115, 168)
                elif "OCEAN" in w_str:
                    c = (10, 24, 48) if h < 0.18 else ((18, 48, 92) if h < 0.28 else (26, 75, 140))
                elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                    c = (245, 248, 255)
                elif h > 0.65 or "MOUNTAIN" in b_type:
                    val = max(55, min(160, int(105 * hillshade)))
                    c = (val, int(val * 0.98), int(val * 1.05))
                elif h > 0.52:
                    c = (max(45, int(75 * hillshade)), max(60, int(98 * hillshade)), max(40, int(65 * hillshade)))
                elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
                    c = (max(16, int(22 * hillshade)), max(48, int(82 * hillshade)), max(20, int(32 * hillshade)))
                elif "DESERT" in b_type or "BEACH" in b_type:
                    c = (max(140, int(205 * hillshade)), max(120, int(180 * hillshade)), max(80, int(125 * hillshade)))
                elif "SWAMP" in b_type:
                    c = (max(28, int(42 * hillshade)), max(45, int(68 * hillshade)), max(30, int(50 * hillshade)))
                else:
                    micro = math.sin(wx * 0.25) * math.cos(wy * 0.25) * 6.0
                    r = max(20, min(80, int((32 + micro * 0.5) * hillshade)))
                    g = max(60, min(165, int((108 + micro * 1.5) * hillshade)))
                    b = max(22, min(85, int((36 + micro * 0.6) * hillshade)))
                    c = (r, g, b)"""

new_overview_palette = """                # Relief hillshade (sun from NW: top-left)
                hillshade = 0.92 + (h - 0.45) * 0.25

                # Clash of Clans / Supercell Vibrant Kingdom Palette
                if "RIVER" in w_str or "STREAM" in w_str:
                    c = (60, 195, 250)
                elif "OCEAN" in w_str:
                    c = (28, 92, 172) if h < 0.18 else ((38, 125, 205) if h < 0.28 else (52, 165, 235))
                elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                    c = (248, 252, 255)
                elif h > 0.65 or "MOUNTAIN" in b_type:
                    val = max(115, min(185, int(140 * hillshade)))
                    c = (val, int(val * 1.02), int(val * 1.08))
                elif "DESERT" in b_type or "BEACH" in b_type or h < 0.38:
                    c = (max(200, int(238 * hillshade)), max(170, int(208 * hillshade)), max(100, int(132 * hillshade)))
                elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
                    c = (max(45, int(65 * hillshade)), max(115, int(148 * hillshade)), max(35, int(48 * hillshade)))
                elif "SWAMP" in b_type:
                    c = (max(65, int(85 * hillshade)), max(110, int(135 * hillshade)), max(50, int(72 * hillshade)))
                else:
                    # Vibrant Clash Village Grassland with alternating mown stripes
                    mown = 10 if ((px // 4 + py // 4) % 2 == 0) else 0
                    r = max(70, min(145, int((104 + mown) * hillshade)))
                    g = max(140, min(230, int((186 + mown) * hillshade)))
                    b = max(40, min(100, int((56 + mown * 0.5) * hillshade)))
                    c = (r, g, b)"""

assert old_overview_palette in o_text, "Could not find old overview palette in overlays.py"
o_text = o_text.replace(old_overview_palette, new_overview_palette, 1)

# Subtle vignette instead of heavy dark borders
old_vig = """                    if d > 0.65:
                        alpha = int(min(100.0, (d - 0.65) / 0.35 * 100.0))
                        v_small.set_at((x, y), (8, 12, 10, alpha))"""

new_vig = """                    if d > 0.70:
                        alpha = int(min(45.0, (d - 0.70) / 0.30 * 45.0))
                        v_small.set_at((x, y), (20, 45, 25, alpha))"""

if old_vig in o_text:
    o_text = o_text.replace(old_vig, new_vig, 1)

with open(overlays_path, "w", encoding="utf-8") as f:
    f.write(o_text)
print("overlays.py updated with Clash of Clans palette!")

# --- 3. UPDATE RENDERER.PY ---
with open(renderer_path, "r", encoding="utf-8") as f:
    r_text = f.read()

r_text = r_text.replace("self.screen.fill((24, 34, 28))", "self.screen.fill((84, 168, 52))")

with open(renderer_path, "w", encoding="utf-8") as f:
    f.write(r_text)
print("renderer.py updated successfully!")
