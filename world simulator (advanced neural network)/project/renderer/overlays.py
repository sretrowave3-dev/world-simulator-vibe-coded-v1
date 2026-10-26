"""
project/renderer/overlays.py

Grid and environment visual overlays using Pygame with hardware-optimized caching.
"""

from __future__ import annotations

import math
from typing import Tuple, List, Dict, Optional
import pygame
from project.renderer.camera import Camera
from project.world.terrain import TerrainManager
from project.world.biomes import BiomeType, BIOME_CATALOG
from project.renderer.ui import get_cached_text, get_cached_aura_sprite


class OverlayRenderer:
    """Renders terrain grids, biome colorations, and debug grids with chunk texture caching and continuous LOD."""

    CHUNK_METERS = 256.0
    CHUNK_TEX_RES = 10  # 10x10 per 256m chunk = 100 samples! Rapid 1.8ms generation with crisp terrain

    def __init__(self, cell_size: float = 16.0) -> None:
        self.cell_size = cell_size
        self._cached_surface: Optional[pygame.Surface] = None
        self._cached_world_size: Tuple[float, float] = (0.0, 0.0)
        self._chunk_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._scaled_chunk_cache: Dict[Tuple[int, int, int, int], pygame.Surface] = {}
        self._cached_macro_surf: Optional[pygame.Surface] = None
        self._cached_macro_key: Optional[Tuple[int, int, int, int, int, int]] = None
        self._ambient_surface: Optional[pygame.Surface] = None
        self._last_ambient_tint: Optional[Tuple[int, int, int, int]] = None
        self._overview_surface: Optional[pygame.Surface] = None
        self._overview_res: int = 128
        self.render_distance_chunks: int = 4  # Radius of chunks around camera
        self.ultra_fast_mode: bool = True     # User-configurable max performance
        
        # Initialize safe font for overlay HUD text badges
        if not pygame.font.get_init():
            pygame.font.init()
        try:
            self.font = pygame.font.SysFont("Segoe UI", 12)
        except Exception:
            self.font = pygame.font.Font(None, 16)
        try:
            self.monospace_12_font = pygame.font.SysFont("monospace", 12)
        except Exception:
            self.monospace_12_font = self.font
        try:
            self.monospace_10_font = pygame.font.SysFont("monospace", 10)
        except Exception:
            self.monospace_10_font = self.font

    def _get_overview_surface(self, terrain_manager: Any, world_width: float = 14336.0, world_height: float = 14336.0) -> pygame.Surface:
        """Precomputes or returns continuous high-res global satellite atlas for instantaneous 60+ FPS at macro scales."""
        if self._overview_surface is not None:
            return self._overview_surface

        res = self._overview_res
        surf = pygame.Surface((res, res))
        step_x = world_width / res
        step_y = world_height / res

        has_sampler = hasattr(terrain_manager, "sample_surface_point")

        for px in range(res):
            wx = px * step_x
            for py in range(res):
                wy = py * step_y
                if has_sampler:
                    h, w_str, b_type = terrain_manager.sample_surface_point(wx, wy)
                else:
                    h, w_str, b_type = 0.4, "", ""

                if "RIVER" in w_str or "STREAM" in w_str:
                    c = (45, 120, 220)
                elif "OCEAN" in w_str:
                    c = (20, 55, 125) if h < 0.2 else (26, 75, 150)
                elif h > 0.8 or "SNOW" in b_type or "ICE" in b_type:
                    c = (240, 248, 255)
                elif h > 0.65 or "MOUNTAIN" in b_type:
                    c = (115, 120, 130)
                elif h > 0.54:
                    c = (85, 105, 75)
                elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
                    c = (22, 85, 38)
                elif "DESERT" in b_type or "BEACH" in b_type:
                    c = (195, 172, 118)
                elif "SWAMP" in b_type:
                    c = (42, 68, 52)
                else:
                    c = (48, 118, 54)

                surf.set_at((px, py), c)

        self._overview_surface = surf
        return surf

    def _get_chunk_surface(self, cx: int, cy: int, terrain_manager: Any) -> pygame.Surface:
        key = (cx, cy)
        if key in self._chunk_cache:
            return self._chunk_cache[key]

        res = self.CHUNK_TEX_RES
        m_step = self.CHUNK_METERS / res
        surf = pygame.Surface((res, res))

        has_sampler = hasattr(terrain_manager, "sample_surface_point")

        for px in range(res):
            wx = cx * self.CHUNK_METERS + px * m_step
            for py in range(res):
                wy = cy * self.CHUNK_METERS + py * m_step

                if has_sampler:
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

                # Relief hillshade (sun from NW: top-left)
                hillshade = 0.90 + (h - 0.45) * 0.35 + (math.sin(wx * 0.08 + wy * 0.08) * 0.04)

                # Organic Natural Palette (100% matched to overview atlas)
                if "RIVER" in w_str or "STREAM" in w_str:
                    shimmer = int(math.sin(wx * 0.2 + wy * 0.15) * 15)
                    r = max(20, min(60, int(35 + shimmer * 0.5)))
                    g = max(100, min(160, int(135 + shimmer)))
                    b = max(190, min(255, int(230 + shimmer * 0.8)))
                elif "OCEAN" in w_str:
                    if h < 0.2:
                        r, g, b = (14, 38, 75)
                    else:
                        r, g, b = (22, 68, 128)
                elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                    snow_val = max(210, min(255, int(245 * hillshade)))
                    r, g, b = (snow_val, min(255, snow_val + 5), 255)
                elif h > 0.68 or "MOUNTAIN" in b_type:
                    gray_val = max(55, min(170, int(110 * hillshade)))
                    r = max(50, min(160, int(gray_val * 0.98)))
                    g = max(55, min(165, gray_val))
                    b = max(65, min(175, int(gray_val * 1.08)))
                elif h > 0.54:
                    r = max(60, min(140, int(95 * hillshade)))
                    g = max(75, min(150, int(115 * hillshade)))
                    b = max(55, min(120, int(85 * hillshade)))
                elif "FOREST" in b_type or "RAINFOREST" in b_type or "JUNGLE" in b_type:
                    r = max(15, min(55, int(22 * hillshade)))
                    g = max(45, min(125, int(88 * hillshade)))
                    b = max(20, min(65, int(38 * hillshade)))
                elif "DESERT" in b_type or "BEACH" in b_type:
                    r = max(140, min(230, int(195 * hillshade)))
                    g = max(120, min(205, int(172 * hillshade)))
                    b = max(80, min(155, int(118 * hillshade)))
                elif "SWAMP" in b_type:
                    r = max(25, min(75, int(42 * hillshade)))
                    g = max(40, min(105, int(68 * hillshade)))
                    b = max(30, min(80, int(52 * hillshade)))
                else:
                    dither = math.sin(wx * 0.35) * math.cos(wy * 0.35) * 6.0
                    r = max(28, min(85, int((48 + dither) * hillshade)))
                    g = max(65, min(160, int((118 + dither * 1.5) * hillshade)))
                    b = max(32, min(95, int((54 + dither * 0.8) * hillshade)))

                surf.set_at((px, py), (r, g, b))

        # Evict oldest entries if cache exceeds 1000 chunks
        if len(self._chunk_cache) > 1000:
            for k in list(self._chunk_cache.keys())[:200]:
                del self._chunk_cache[k]

        self._chunk_cache[key] = surf
        return surf

    def draw_terrain_grid(
        self,
        surface: pygame.Surface,
        camera: Camera,
        terrain_manager: Any,
        world_width: float = 14336.0,
        world_height: float = 14336.0,
        show_grid: bool = False,
    ) -> None:
        """
        Minecraft-Style Continuous Multi-Tier Terrain Renderer.
        1. Always draws the continuous planetary base atlas clipped to the visible screen viewport,
           preventing massive RAM allocations and eliminating abrupt zoom pops.
        2. Seamlessly blends local detail chunks on top when zoomed in (zoom >= 0.35).
        3. Never causes black voids, memory spikes, or jarring transitions.
        """
        zoom = camera.zoom
        sw = surface.get_width()
        sh = surface.get_height()

        # -----------------------------------------------------------------
        # TIER 1: CONTINUOUS WORLD BASE ATLAS (VIEWPORT-CLIPPED, 0% RAM LEAK)
        # Macro overview cached rendering for zoom < 0.35
        # -----------------------------------------------------------------
        if zoom < 0.35:
            base_map = self._get_overview_surface(terrain_manager, world_width, world_height)
            res = self._overview_res
            step_x = world_width / res
            step_y = world_height / res

            # Visible world bounds in world space
            min_wx = max(0.0, camera.pos_x - (sw * 0.5) / zoom)
            min_wy = max(0.0, camera.pos_y - (sh * 0.5) / zoom)
            max_wx = min(world_width, camera.pos_x + (sw * 0.5) / zoom)
            max_wy = min(world_height, camera.pos_y + (sh * 0.5) / zoom)

            if max_wx > min_wx and max_wy > min_wy:
                # Map world bounds into base_map pixel grid
                px0 = int(min_wx / world_width * res)
                py0 = int(min_wy / world_height * res)
                px1 = min(res, int(math.ceil(max_wx / world_width * res)))
                py1 = min(res, int(math.ceil(max_wy / world_height * res)))

                sub_w = max(1, px1 - px0)
                sub_h = max(1, py1 - py0)

                dest_x, dest_y = camera.world_to_screen(px0 * step_x, py0 * step_y)
                dest_w = max(1, int(sub_w * step_x * zoom))
                dest_h = max(1, int(sub_h * step_y * zoom))

                macro_key = (px0, py0, sub_w, sub_h, dest_w, dest_h)
                if self._cached_macro_key == macro_key and self._cached_macro_surf is not None:
                    surface.blit(self._cached_macro_surf, (dest_x, dest_y))
                else:
                    sub = base_map.subsurface((px0, py0, sub_w, sub_h))
                    self._cached_macro_surf = pygame.transform.scale(sub, (dest_w, dest_h))
                    self._cached_macro_key = macro_key
                    surface.blit(self._cached_macro_surf, (dest_x, dest_y))

        # -----------------------------------------------------------------
        # TIER 2: LOCAL DETAIL CHUNKS (SEAMLESS OVERLAY WHEN ZOOM >= 0.35)
        # Scaled-chunk dictionary cache (0% CPU scaling load during gameplay)
        # -----------------------------------------------------------------
        else:
            margin = 32.0
            chunk_min_wx, chunk_min_wy, chunk_max_wx, chunk_max_wy = camera.get_visible_world_bounds(margin=margin)

            start_cx = max(0, int(chunk_min_wx // self.CHUNK_METERS))
            end_cx = min(int(world_width // self.CHUNK_METERS), int(chunk_max_wx // self.CHUNK_METERS) + 1)
            start_cy = max(0, int(chunk_min_wy // self.CHUNK_METERS))
            end_cy = min(int(world_height // self.CHUNK_METERS), int(chunk_max_wy // self.CHUNK_METERS) + 1)

            dest_cw = max(1, int(math.ceil(self.CHUNK_METERS * zoom))) + 1
            dest_ch = max(1, int(math.ceil(self.CHUNK_METERS * zoom))) + 1

            for cy in range(start_cy, end_cy + 1):
                for cx in range(start_cx, end_cx + 1):
                    key = (cx, cy, dest_cw, dest_ch)
                    scaled_chunk = self._scaled_chunk_cache.get(key)
                    if scaled_chunk is None:
                        chunk_surf = self._get_chunk_surface(cx, cy, terrain_manager)
                        scaled_chunk = pygame.transform.scale(chunk_surf, (dest_cw, dest_ch))
                        if len(self._scaled_chunk_cache) > 256:
                            for k in list(self._scaled_chunk_cache.keys())[:128]:
                                del self._scaled_chunk_cache[k]
                        self._scaled_chunk_cache[key] = scaled_chunk
                    sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                    surface.blit(scaled_chunk, (sx, sy))

        # -----------------------------------------------------------------
        # SURVEY GRID (Clean subtle UTM lines every 256m when enabled)
        # -----------------------------------------------------------------
        if show_grid and zoom > 0.30:
            grid_interval = 256.0
            gx = math.floor(min_wx / grid_interval) * grid_interval
            while gx <= max_wx:
                sx, _ = camera.world_to_screen(gx, 0)
                pygame.draw.line(surface, (30, 42, 58), (sx, 0), (sx, sh), 1)
                gx += grid_interval
            gy = math.floor(min_wy / grid_interval) * grid_interval
            while gy <= max_wy:
                _, sy = camera.world_to_screen(0, gy)
                pygame.draw.line(surface, (30, 42, 58), (0, sy), (sw, sy), 1)
                gy += grid_interval

    def preload_chunks_around(self, center_x: float, center_y: float, radius_m: float, terrain_manager: Any, world_w: float = 14336.0, world_h: float = 14336.0) -> None:
        """Pre-populates chunk surface cache and overview map for instant 60 FPS on frame 1."""
        self._get_overview_surface(terrain_manager, world_w, world_h)
        min_cx = int(max(0, (center_x - radius_m)) // self.CHUNK_METERS)
        max_cx = int(min(world_w // self.CHUNK_METERS, (center_x + radius_m) // self.CHUNK_METERS))
        min_cy = int(max(0, (center_y - radius_m)) // self.CHUNK_METERS)
        max_cy = int(min(world_h // self.CHUNK_METERS, (center_y + radius_m) // self.CHUNK_METERS))
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                self._get_chunk_surface(cx, cy, terrain_manager)

    def draw_terrain(
        self,
        surface: pygame.Surface,
        camera: Camera,
        terrain_manager: Any,
        show_grid: bool = False,
        world_width: float = 14336.0,
        world_height: float = 14336.0,
    ) -> None:
        """Draws fine-grained terrain, relief mountains, winding rivers, and biomes."""
        self.draw_terrain_grid(surface, camera, terrain_manager, world_width, world_height, show_grid)


    def draw_structures(
        self,
        surface: pygame.Surface,
        camera: Camera,
        sim_tick: int = 0,
    ) -> None:
        """Renders rich Minecraft-style tiered shelters, campfires, stone fortress houses, and altars."""
        from project.civilization.settlement import world_settlement_mgr
        min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=80.0)
        zoom = camera.zoom

        for s in world_settlement_mgr.structures.values():
            if not s.is_active:
                continue
            if s.pos_x < min_wx or s.pos_x > max_wx or s.pos_y < min_wy or s.pos_y > max_wy:
                continue

            sx, sy = camera.world_to_screen(s.pos_x, s.pos_y)

            # ── 1. CAMPFIRE / TORCH HEARTH (Minecraft Survival Campfire) ──
            if s.structure_type == "campfire":
                glow_r = max(12, int(38.0 * zoom))
                flicker = math.sin(sim_tick * 0.28 + s.pos_x) * 18
                glow_alpha = max(30, min(120, int(75 + flicker)))
                glow_surf = get_cached_aura_sprite((255, 145, 25, glow_alpha), glow_r)
                surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

                # Stone ring with charcoal ash
                ring_r = max(4, int(7.5 * zoom))
                pygame.draw.circle(surface, (28, 25, 24), (sx, sy), ring_r)
                pygame.draw.circle(surface, (110, 105, 100), (sx, sy), ring_r, max(1, int(2 * zoom)))

                # Flickering dancing flame
                flame_h = max(3, int((5.0 + math.sin(sim_tick * 0.35) * 2.0) * zoom))
                pygame.draw.circle(surface, (255, 90, 20), (sx, sy - flame_h // 3), max(2, int(4.0 * zoom)))
                pygame.draw.circle(surface, (255, 225, 60), (sx, sy - flame_h // 2), max(1, int(2.5 * zoom)))

            # ── 2. TIER 1: EMERGENCY DIRT DUGOUT (Minecraft Day 1 survival hole) ──
            elif s.structure_type == "dirt_dugout":
                dw = max(12, int(22.0 * zoom))
                dh = max(9, int(16.0 * zoom))
                # Earth mound with grass rim
                pygame.draw.ellipse(surface, (95, 65, 35), (sx - dw // 2, sy - dh // 2, dw, dh))
                pygame.draw.arc(surface, (45, 110, 50), (sx - dw // 2, sy - dh // 2, dw, dh), 0, math.pi, max(1, int(2 * zoom)))
                # Wood support beam over burrow
                pygame.draw.rect(surface, (120, 80, 40), (sx - dw // 3, sy - int(dh * 0.2), dw // 3 * 2, max(2, int(3 * zoom))))
                # Burrow doorway with warm interior lantern glow
                door_r = max(2, int(dw * 0.22))
                pygame.draw.circle(surface, (25, 15, 8), (sx, sy + max(1, int(dh * 0.15))), door_r)
                pygame.draw.circle(surface, (255, 180, 50, 150), (sx, sy + max(1, int(dh * 0.15))), max(1, door_r // 2))

            # ── 3. TIER 2: WOODEN PLANK CABIN (Minecraft Timber Planks, Door & Wall Torches) ──
            elif s.structure_type in ("wooden_cabin", "tribal_shelter"):
                hw = max(16, int(32.0 * zoom))
                hh = max(14, int(24.0 * zoom))
                # Soft drop shadow
                pygame.draw.ellipse(surface, (0, 0, 0, 90), (sx - hw // 2 - 2, sy + hh // 2 - 4, hw + 4, 8))
                # Wood plank walls with horizontal plank lines
                pygame.draw.rect(surface, (155, 105, 52), (sx - hw // 2, sy - hh // 2, hw, hh))
                pygame.draw.rect(surface, (95, 60, 28), (sx - hw // 2, sy - hh // 2, hw, hh), max(1, int(1.5 * zoom)))
                if zoom > 0.4:
                    for line_y in [sy - hh // 4, sy, sy + hh // 4]:
                        pygame.draw.line(surface, (115, 75, 35), (sx - hw // 2 + 1, line_y), (sx + hw // 2 - 1, line_y), 1)

                # Sloped timber roof
                roof_peak = sy - hh // 2 - max(5, int(12 * zoom))
                pygame.draw.polygon(surface, (185, 135, 65), [
                    (sx - hw // 2 - 4, sy - hh // 2),
                    (sx, roof_peak),
                    (sx + hw // 2 + 4, sy - hh // 2),
                ])
                pygame.draw.polygon(surface, (110, 70, 30), [
                    (sx - hw // 2 - 4, sy - hh // 2),
                    (sx, roof_peak),
                    (sx + hw // 2 + 4, sy - hh // 2),
                ], max(1, int(1.5 * zoom)))

                # Wooden plank door with brass latch
                door_w = max(3, hw // 4)
                door_h = max(5, int(hh * 0.65))
                pygame.draw.rect(surface, (70, 42, 18), (sx - door_w // 2, sy + hh // 2 - door_h, door_w, door_h))
                pygame.draw.circle(surface, (215, 180, 50), (sx + door_w // 3, sy + hh // 2 - door_h // 2), max(1, int(1.5 * zoom)))

                # Wall Torches with glowing light halos (Minecraft Light Level 14)
                for tx_off in [-hw // 2 + 2, hw // 2 - 2]:
                    tx, ty = sx + tx_off, sy - hh // 4
                    pygame.draw.rect(surface, (90, 55, 25), (tx - 1, ty, 2, max(3, int(5 * zoom))))
                    flame_color = (255, 200, 50) if sim_tick % 2 == 0 else (255, 150, 30)
                    pygame.draw.circle(surface, flame_color, (tx, ty - 1), max(2, int(3 * zoom)))

            # ── 4. TIER 3: COBBLESTONE FORTRESS HOUSE (Minecraft Stone Masonry, Chimney & Smoke) ──
            elif s.structure_type == "cobblestone_house":
                cw = max(22, int(42.0 * zoom))
                ch = max(18, int(32.0 * zoom))
                # Soft ground shadow
                pygame.draw.ellipse(surface, (0, 0, 0, 95), (sx - cw // 2 - 3, sy + ch // 2 - 5, cw + 6, 10))

                # Cobblestone masonry walls
                pygame.draw.rect(surface, (125, 130, 136), (sx - cw // 2, sy - ch // 2, cw, ch))
                pygame.draw.rect(surface, (65, 70, 75), (sx - cw // 2, sy - ch // 2, cw, ch), max(1, int(2 * zoom)))

                # Masonry stone courses
                if zoom > 0.4:
                    for cy_off in [sy - ch // 3, sy, sy + ch // 3]:
                        pygame.draw.line(surface, (85, 90, 95), (sx - cw // 2 + 2, cy_off), (sx + cw // 2 - 2, cy_off), 1)

                # Stone battlements / crenelations along the roof
                c_thick = max(3, int(6 * zoom))
                pygame.draw.rect(surface, (145, 150, 158), (sx - cw // 2 - 2, sy - ch // 2 - c_thick, cw + 4, c_thick))
                # Crenels
                for cr_x in range(sx - cw // 2, sx + cw // 2, max(6, int(10 * zoom))):
                    pygame.draw.rect(surface, (160, 165, 172), (cr_x, sy - ch // 2 - c_thick - max(2, int(3 * zoom)), max(3, int(5 * zoom)), max(2, int(3 * zoom))))

                # Reinforced oak door with iron bands
                door_w = max(4, cw // 4)
                door_h = max(6, int(ch * 0.6))
                pygame.draw.rect(surface, (55, 35, 18), (sx - door_w // 2, sy + ch // 2 - door_h, door_w, door_h))
                pygame.draw.rect(surface, (85, 90, 95), (sx - door_w // 2, sy + ch // 2 - int(door_h * 0.7), door_w, max(1, int(2 * zoom))))
                pygame.draw.rect(surface, (85, 90, 95), (sx - door_w // 2, sy + ch // 2 - int(door_h * 0.3), door_w, max(1, int(2 * zoom))))

                # Stone Chimney with warm smoke puff
                chim_w = max(3, int(6 * zoom))
                chim_h = max(5, int(11 * zoom))
                chim_x = sx + cw // 2 - max(4, int(8 * zoom))
                chim_y = sy - ch // 2 - chim_h
                pygame.draw.rect(surface, (85, 90, 95), (chim_x, chim_y, chim_w, chim_h))
                pygame.draw.rect(surface, (55, 60, 65), (chim_x, chim_y, chim_w, chim_h), 1)

                # Rising animated chimney smoke puffs
                for sp_i in range(3):
                    puff_prog = (sim_tick * 0.4 + sp_i * 6) % 18
                    puff_y = chim_y - int(puff_prog * zoom)
                    puff_x = chim_x + max(1, chim_w // 2) + int(math.sin(puff_prog * 0.5) * 4 * zoom)
                    puff_r = max(2, int((3.0 + puff_prog * 0.25) * zoom))
                    pygame.draw.circle(surface, (195, 200, 205, 140), (puff_x, puff_y), puff_r)

            # ── 5. TIER 4: FORTIFIED GREAT HALL (Minecraft Castle Keep) ──
            elif s.structure_type == "fortified_hall":
                fw = max(32, int(60.0 * zoom))
                fh = max(24, int(46.0 * zoom))
                # Grand Castle Keep Foundation
                pygame.draw.rect(surface, (105, 110, 115), (sx - fw // 2, sy - fh // 2, fw, fh))
                pygame.draw.rect(surface, (55, 60, 65), (sx - fw // 2, sy - fh // 2, fw, fh), max(2, int(2.5 * zoom)))

                # Flanking stone watchtowers
                tower_w = max(8, int(14 * zoom))
                tower_h = fh + max(6, int(12 * zoom))
                for tw_x in [sx - fw // 2 - tower_w, sx + fw // 2]:
                    pygame.draw.rect(surface, (88, 92, 98), (tw_x, sy - fh // 2 - max(6, int(12 * zoom)), tower_w, tower_h))
                    pygame.draw.rect(surface, (45, 50, 55), (tw_x, sy - fh // 2 - max(6, int(12 * zoom)), tower_w, tower_h), 1)
                    # Tower brazier fire
                    pygame.draw.circle(surface, (255, 185, 40), (tw_x + tower_w // 2, sy - fh // 2 - max(6, int(12 * zoom))), max(2, int(3 * zoom)))

                # Grand Hall double doors
                gdoor_w = max(6, fw // 4)
                gdoor_h = max(8, int(fh * 0.6))
                pygame.draw.rect(surface, (48, 30, 15), (sx - gdoor_w // 2, sy + fh // 2 - gdoor_h, gdoor_w, gdoor_h))
                pygame.draw.line(surface, (25, 15, 8), (sx, sy + fh // 2 - gdoor_h), (sx, sy + fh // 2), 1)

            # ── 6. SACRED ALTAR OF THE MONOLITH ──
            elif s.structure_type == "sacred_altar":
                altar_r = max(8, int(18.0 * zoom))
                pygame.draw.circle(surface, (255, 215, 0, 40), (sx, sy), altar_r + 6)
                pygame.draw.circle(surface, (245, 215, 90), (sx, sy), altar_r, max(2, int(3 * zoom)))
                pygame.draw.circle(surface, (255, 255, 255), (sx, sy), max(3, int(5 * zoom)))

            # Live Occupancy HUD Badge (e.g. 🛖 4/6 Cabin)
            if s.capacity > 0 and zoom > 0.28:
                occ_cnt = len(s.occupants)
                color = (120, 255, 160) if occ_cnt < s.capacity else (255, 215, 80)
                tier_badge = "Dugout" if s.tier == 1 else ("Cabin" if s.tier == 2 else ("House" if s.tier == 3 else "Keep"))
                occ_str = f"🛖 {occ_cnt}/{s.capacity} {tier_badge}"
                from project.renderer.ui import get_cached_text
                lbl = get_cached_text(self.font if hasattr(self, 'font') else None, occ_str, color)
                if lbl:
                    surface.blit(lbl, (sx - lbl.get_width() // 2, sy - max(14, int(26 * zoom))))

    def draw_tree_canopy(
        self,
        surface: pygame.Surface,
        sx: int,
        sy: int,
        pixel_r: int,
        stage: str,
        fruit_kg: float,
        zoom: float,
        sim_tick: int,
    ) -> None:
        """Renders mature tree trunk, layered foliage crown, and fruit blossoms."""
        trunk_w = max(2, int(pixel_r * 0.35))
        trunk_h = max(4, int(pixel_r * 0.75))
        # 1. Tree trunk
        pygame.draw.rect(surface, (105, 60, 25), (sx - trunk_w // 2, sy, trunk_w, trunk_h))
        # 2. Main green canopy crown
        crown_r = max(4, pixel_r)
        foliage_color = (25, 115, 40) if stage != "ancient_tree" else (18, 90, 32)
        pygame.draw.circle(surface, foliage_color, (sx, sy - max(2, int(crown_r * 0.4))), crown_r)
        # Inner crown highlight
        pygame.draw.circle(surface, (45, 150, 60), (sx - int(crown_r * 0.2), sy - max(3, int(crown_r * 0.5))), max(2, int(crown_r * 0.6)))

        # 3. Fruit blossoms / apples if available
        if fruit_kg > 0.5 and zoom > 0.25:
            num_fruits = min(5, max(1, int(fruit_kg // 3)))
            for fi in range(num_fruits):
                ang = fi * 1.25 + 0.5
                fx = sx + int(math.cos(ang) * (crown_r * 0.5))
                fy = (sy - max(2, int(crown_r * 0.4))) + int(math.sin(ang) * (crown_r * 0.5))
                pygame.draw.circle(surface, (240, 60, 40), (fx, fy), max(1, int(2 * zoom)))

    def draw_world_boundaries(
        self,
        surface: pygame.Surface,
        camera: Camera,
        width: float,
        height: float,
        ruins_manager: Optional[Any] = None,
    ) -> None:
        """Draws boundaries indicating the edges of the simulation map with the mysterious Northern breach opening."""
        b_min_x = getattr(ruins_manager, "breach_min_x", 2360.0) if ruins_manager else 2360.0
        b_max_x = getattr(ruins_manager, "breach_max_x", 2540.0) if ruins_manager else 2540.0

        p00 = camera.world_to_screen(0, 0)
        p_breach_left = camera.world_to_screen(b_min_x, 0)
        p_breach_right = camera.world_to_screen(b_max_x, 0)
        p10 = camera.world_to_screen(width, 0)
        p11 = camera.world_to_screen(width, height)
        p01 = camera.world_to_screen(0, height)

        border_color = (200, 50, 50)
        # North Wall (Left segment up to the breach)
        pygame.draw.line(surface, border_color, p00, p_breach_left, 3)
        # North Wall (Right segment past the breach)
        pygame.draw.line(surface, border_color, p_breach_right, p10, 3)
        # East, South, West Walls
        pygame.draw.line(surface, border_color, p10, p11, 3)
        pygame.draw.line(surface, border_color, p11, p01, 3)
        pygame.draw.line(surface, border_color, p01, p00, 3)

        # Draw glowing ancient runic gateposts at the breach edges
        for bx in [b_min_x, b_max_x]:
            bsx, bsy = camera.world_to_screen(bx, 0)
            pygame.draw.circle(surface, (0, 230, 255), (bsx, bsy), max(3, int(6 * camera.zoom)))
            pygame.draw.circle(surface, (255, 255, 255), (bsx, bsy), max(1, int(3 * camera.zoom)))

    def draw_ancient_ruins(
        self,
        surface: pygame.Surface,
        camera: Camera,
        ruins_manager: Any,
        sim_tick: int,
    ) -> None:
        """Renders the ancient ceremonial pathway, colonnade pillars, and the Primordial Hall."""
        if not ruins_manager:
            return

        # Frustum culling check for the ruins complex
        min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=150.0)
        if max_wx < ruins_manager.hall_min_x - 100 or min_wx > ruins_manager.hall_max_x + 100:
            return
        if max_wy < ruins_manager.hall_min_y - 50 or min_wy > ruins_manager.path_start_y + 100:
            return

        zoom = camera.zoom

        # 1. Flagstone Obsidian Pathway
        pw_x = ruins_manager.path_min_x
        pw_w = ruins_manager.path_max_x - ruins_manager.path_min_x
        pw_y = ruins_manager.path_end_y
        pw_h = ruins_manager.path_start_y - ruins_manager.path_end_y

        psx, psy = camera.world_to_screen(pw_x, pw_y)
        psw = max(4, int(pw_w * zoom))
        psh = max(4, int(pw_h * zoom))
        path_rect = pygame.Rect(psx, psy, psw, psh)

        # Draw dark paved pathway
        pygame.draw.rect(surface, (35, 42, 55), path_rect)
        pygame.draw.rect(surface, (0, 180, 220), path_rect, 1)

        # Central luminescent runic line
        mid_sx, start_sy = camera.world_to_screen(ruins_manager.altar_pos[0], ruins_manager.path_start_y)
        _, end_sy = camera.world_to_screen(ruins_manager.altar_pos[0], ruins_manager.path_end_y)
        pygame.draw.line(surface, (0, 230, 255), (mid_sx, start_sy), (mid_sx, end_sy), max(1, int(2 * zoom)))

        # 2. Grand Hall Floor Area
        hw_x = ruins_manager.hall_min_x
        hw_y = ruins_manager.hall_min_y
        hw_w = ruins_manager.hall_max_x - ruins_manager.hall_min_x
        hw_h = ruins_manager.hall_max_y - ruins_manager.hall_min_y

        hsx, hsy = camera.world_to_screen(hw_x, hw_y)
        hsw = max(8, int(hw_w * zoom))
        hsh = max(8, int(hw_h * zoom))
        hall_rect = pygame.Rect(hsx, hsy, hsw, hsh)

        # Draw hall foundation
        pygame.draw.rect(surface, (24, 30, 42), hall_rect)
        pygame.draw.rect(surface, (0, 200, 255), hall_rect, 2)

        # Draw decorative inner sanctuary floor ring
        asx, asy = camera.world_to_screen(ruins_manager.altar_pos[0], ruins_manager.altar_pos[1])
        mandala_r = max(6, int(70.0 * zoom))
        pygame.draw.circle(surface, (45, 60, 85), (asx, asy), mandala_r)
        pygame.draw.circle(surface, (0, 220, 255), (asx, asy), mandala_r, 1)
        pygame.draw.circle(surface, (0, 160, 200), (asx, asy), max(2, int(mandala_r * 0.5)), 1)

        # 3. Flanking Archive & Relic Chambers
        for cpos in [ruins_manager.west_archive_pos, ruins_manager.east_relic_pos]:
            csx, csy = camera.world_to_screen(cpos[0], cpos[1])
            cr = max(4, int(22.0 * zoom))
            pygame.draw.circle(surface, (30, 38, 52), (csx, csy), cr)
            pygame.draw.circle(surface, (0, 200, 240), (csx, csy), cr, 1)

        # 4. Colonnade Stone Pillars
        for pillar in ruins_manager.pillars:
            plx, ply = camera.world_to_screen(pillar.pos_x, pillar.pos_y)
            pr = max(2, int(pillar.radius * zoom))
            # Base
            pygame.draw.circle(surface, (110, 115, 125), (plx, ply), pr + 2)
            pygame.draw.circle(surface, (160, 165, 175), (plx, ply), pr)
            # Glowing celestial core
            pulse = math.sin(sim_tick * 0.08 + pillar.pos_y * 0.05) * 0.3 + 0.7
            core_r = max(1, int((pr - 2) * pulse))
            if core_r > 0:
                pygame.draw.circle(surface, pillar.glow_color, (plx, ply), core_r)

        # 5. Central Floating Primordial Celestial Relic
        altar_pulse_r = max(4, int(24.0 * zoom + math.sin(sim_tick * 0.1) * 3))
        relic_surf = get_cached_aura_sprite((0, 230, 255, 60), altar_pulse_r)
        surface.blit(relic_surf, (asx - altar_pulse_r, asy - altar_pulse_r))

        # Relic diamond core
        d_size = max(3, int(10 * zoom))
        diamond_pts = [(asx, asy - d_size), (asx + d_size, asy), (asx, asy + d_size), (asx - d_size, asy)]
        pygame.draw.polygon(surface, (200, 250, 255), diamond_pts)
        pygame.draw.polygon(surface, (0, 240, 255), diamond_pts, 1)

        # 6. Overhead Ruins Inscription Label
        ruins_lbl = get_cached_text(self.monospace_12_font, "🏛️ FORBIDDEN SANCTUARY OF THE PRIMORDIALS", (0, 240, 255))
        surface.blit(ruins_lbl, (asx - ruins_lbl.get_width() // 2, hsy - 18))

    def draw_stardust_deposits(
        self,
        surface: pygame.Surface,
        camera: Camera,
        miracles_mgr: Any,
        sim_tick: int,
    ) -> None:
        """Renders glowing celestial stardust fragments from meteor showers."""
        if not miracles_mgr or not hasattr(miracles_mgr, "stardust_deposits"):
            return

        zoom = camera.zoom
        min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=30.0)

        for dep in miracles_mgr.stardust_deposits:
            if dep.is_collected:
                continue
            if dep.pos_x < min_wx or dep.pos_x > max_wx or dep.pos_y < min_wy or dep.pos_y > max_wy:
                continue

            sx, sy = camera.world_to_screen(dep.pos_x, dep.pos_y)
            pulse_r = max(4, int(10 * zoom + math.sin(sim_tick * 0.15 + dep.pos_x) * 3))
            
            # Shimmering stardust aura
            aura_surf = get_cached_aura_sprite((160, 100, 255, 70), pulse_r)
            surface.blit(aura_surf, (sx - pulse_r, sy - pulse_r))

            # Diamond core
            c_sz = max(2, int(4 * zoom))
            pts = [(sx, sy - c_sz), (sx + c_sz, sy), (sx, sy + c_sz), (sx - c_sz, sy)]
            pygame.draw.polygon(surface, (255, 255, 255), pts)

    def draw_day_night_sky(
        self,
        surface: pygame.Surface,
        camera: Camera,
        sun_props: Dict[str, Any],
        is_eclipse: bool = False,
    ) -> None:
        """Renders celestial sun disc, solar corona, moonlight, and atmospheric day-night lighting."""
        sw, sh = surface.get_size()
        df = 0.05 if is_eclipse else sun_props.get("daylight_factor", 1.0)
        frac = sun_props.get("day_fraction", 0.5)
        phase = "SOLAR ECLIPSE" if is_eclipse else sun_props.get("phase", "MIDDAY")
        sun_color = (255, 50, 40) if is_eclipse else sun_props.get("sun_color_rgb", (255, 240, 180))
        ambient_tint = (160, 30, 50) if is_eclipse else sun_props.get("ambient_tint_rgb", (255, 255, 255))

        # 1. Atmospheric Ambient Lighting Tint Overlay
        if df < 0.92 or is_eclipse:
            night_alpha = min(200, int((1.0 - df) * 190)) if is_eclipse else min(170, int((1.0 - df) * 160))
            if night_alpha > 5:
                if self._ambient_surface is None or self._ambient_surface.get_size() != (sw, sh):
                    self._ambient_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    self._last_ambient_tint = None
                
                # Tint towards deep indigo or blood-crimson eclipse
                r, g, b = ambient_tint
                tint_tuple = (r // 3, g // 4, b // 3, night_alpha)
                if self._last_ambient_tint != tint_tuple:
                    self._ambient_surface.fill(tint_tuple)
                    self._last_ambient_tint = tint_tuple
                surface.blit(self._ambient_surface, (0, 0))

        # 2. Celestial Sun / Moon Disc in Upper Sky Arc
        sky_margin_x = 340
        sky_w = max(200, sw - (sky_margin_x * 2))
        
        if 0.20 <= frac <= 0.80:
            # Daytime Sun Traversal (East to West)
            prog = (frac - 0.20) / 0.60
            sun_x = sky_margin_x + int(prog * sky_w)
            sun_y = max(18, int(52 - math.sin(prog * math.pi) * 32))

            # Outer radiant solar corona
            corona_color = (*sun_color[:3], 45)
            corona_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(corona_surf, (255, 220, 100, 50), (24, 24), 22)
            pygame.draw.circle(corona_surf, (255, 245, 180, 120), (24, 24), 14)
            surface.blit(corona_surf, (sun_x - 24, sun_y - 24))

            # Core Sun Disc
            pygame.draw.circle(surface, sun_color, (sun_x, sun_y), 8)
            pygame.draw.circle(surface, (255, 255, 255), (sun_x, sun_y), 5)
        else:
            # Night Moon Traversal
            night_prog = ((frac - 0.80) % 1.0) / 0.40
            moon_x = sky_margin_x + int(night_prog * sky_w)
            moon_y = max(18, int(50 - math.sin(night_prog * math.pi) * 28))

            # Lunar glow
            moon_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(moon_surf, (180, 210, 255, 40), (18, 18), 16)
            surface.blit(moon_surf, (moon_x - 18, moon_y - 18))

            # Silver Moon Disc
            pygame.draw.circle(surface, (225, 235, 255), (moon_x, moon_y), 6)
            pygame.draw.circle(surface, (25, 30, 55), (moon_x + 2, moon_y - 1), 5)  # Crescent shadow

    def draw_food_icon(
        self,
        surface: pygame.Surface,
        sx: int,
        sy: int,
        food_type: str,
        pixel_r: int,
        has_abnormality: bool = False,
        glow_color: Optional[Tuple[int, int, int]] = None,
        zoom: float = 1.0,
    ) -> None:
        """Renders distinctive icons, shapes, and symbols for various food types."""
        f_low = food_type.lower()
        r = max(3, pixel_r)

        # Draw abnormal aura if mutated
        if has_abnormality or glow_color:
            aura_c = glow_color or (0, 240, 255)
            aura_r = r + 4
            aura_s = get_cached_aura_sprite((*aura_c[:3], 80), aura_r)
            surface.blit(aura_s, (sx - aura_r, sy - aura_r))

        if "meat" in f_low:
            # 🥩 Meat: Crimson steak with bone notch
            rect = pygame.Rect(sx - r, sy - int(r * 0.7), r * 2, int(r * 1.4))
            pygame.draw.ellipse(surface, (210, 45, 45), rect)
            pygame.draw.ellipse(surface, (245, 110, 110), rect, 1)
            pygame.draw.circle(surface, (255, 255, 240), (sx - r // 3, sy), max(1, r // 4))

        elif "mango" in f_low:
            # 🥭 Mango: Golden stone-fruit teardrop with warm orange gradient & leaf
            rect = pygame.Rect(sx - int(r * 1.1), sy - r, int(r * 2.2), r * 2)
            pygame.draw.ellipse(surface, (255, 165, 0), rect)
            pygame.draw.ellipse(surface, (255, 215, 30), pygame.Rect(sx - int(r * 0.8), sy - int(r * 0.8), int(r * 1.6), int(r * 1.2)))
            pygame.draw.circle(surface, (40, 180, 50), (sx + int(r * 0.6), sy - r), max(1, r // 3))

        elif "cucumber" in f_low:
            # 🥒 Cucumber: Slender jade-green gourd with ridges
            c_w = max(4, int(r * 2.4))
            c_h = max(3, int(r * 0.9))
            c_rect = pygame.Rect(sx - c_w // 2, sy - c_h // 2, c_w, c_h)
            pygame.draw.ellipse(surface, (40, 160, 70), c_rect)
            pygame.draw.ellipse(surface, (80, 210, 110), c_rect, 1)
            for dot_x in [sx - c_w // 4, sx, sx + c_w // 4]:
                pygame.draw.circle(surface, (20, 100, 40), (dot_x, sy), max(1, c_h // 4))

        elif "berry" in f_low:
            # 🫐 Berry: Clustered indigo pearls
            sub_r = max(2, int(r * 0.55))
            pygame.draw.circle(surface, (110, 50, 220), (sx - sub_r // 2, sy - sub_r // 2), sub_r)
            pygame.draw.circle(surface, (140, 80, 255), (sx + sub_r // 2, sy - sub_r // 2), sub_r)
            pygame.draw.circle(surface, (90, 40, 190), (sx, sy + sub_r // 2), sub_r)
            pygame.draw.circle(surface, (50, 200, 80), (sx, sy - sub_r), max(1, sub_r // 2))

        elif "honey" in f_low:
            # 🍯 Honey: Amber hexagon jar
            pts = [
                (sx, sy - r), (sx + int(r * 0.86), sy - r // 2), (sx + int(r * 0.86), sy + r // 2),
                (sx, sy + r), (sx - int(r * 0.86), sy + r // 2), (sx - int(r * 0.86), sy - r // 2)
            ]
            pygame.draw.polygon(surface, (255, 195, 20), pts)
            pygame.draw.polygon(surface, (255, 240, 120), pts, 1)

        elif "grain" in f_low or "wheat" in f_low:
            # 🌾 Wheat / Grain: Golden sheaf stalks
            pygame.draw.line(surface, (215, 185, 80), (sx, sy + r), (sx, sy - r), 2)
            pygame.draw.ellipse(surface, (245, 215, 100), pygame.Rect(sx - r // 2, sy - r, r, r // 2))
            pygame.draw.ellipse(surface, (245, 215, 100), pygame.Rect(sx - r // 2, sy - r // 2, r, r // 2))

        elif "mushroom" in f_low:
            # 🍄 Mushroom: Red spotted dome cap
            pygame.draw.rect(surface, (230, 225, 215), (sx - r // 4, sy, r // 2, r))
            pygame.draw.arc(surface, (220, 40, 40), pygame.Rect(sx - r, sy - r, r * 2, r * 2), 0, math.pi, r)
            pygame.draw.circle(surface, (255, 255, 255), (sx - r // 3, sy - r // 3), max(1, r // 4))
            pygame.draw.circle(surface, (255, 255, 255), (sx + r // 3, sy - r // 3), max(1, r // 4))

        elif "grass" in f_low:
            # 🌿 Grass: Triple emerald green blades
            pygame.draw.line(surface, (50, 190, 50), (sx - r // 2, sy + r // 2), (sx - r, sy - r), 2)
            pygame.draw.line(surface, (70, 220, 70), (sx, sy + r // 2), (sx, sy - int(r * 1.2)), 2)
            pygame.draw.line(surface, (50, 190, 50), (sx + r // 2, sy + r // 2), (sx + r, sy - r), 2)

        else:
            # 🍎 Default Apple / Fruit: Crimson sphere with leaf
            pygame.draw.circle(surface, (235, 40, 50), (sx, sy), r)
            pygame.draw.circle(surface, (255, 100, 110), (sx - r // 3, sy - r // 3), max(1, r // 3))
            pygame.draw.circle(surface, (40, 190, 50), (sx + r // 2, sy - r), max(1, r // 3))

    def draw_discarded_seeds(
        self,
        surface: pygame.Surface,
        camera: Camera,
        seed_growth_mgr: Any,
        sim_tick: int,
    ) -> None:
        """Renders live discarded seeds with growth rings and abnormality sparkles."""
        if not seed_growth_mgr or not hasattr(seed_growth_mgr, "active_seeds"):
            return

        from project.world.seeds import SeedAbnormality
        zoom = camera.zoom
        min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=20.0)

        for seed in getattr(seed_growth_mgr, "active_seeds", []):
            if seed.is_mature:
                continue
            if seed.pos_x < min_wx or seed.pos_x > max_wx or seed.pos_y < min_wy or seed.pos_y > max_wy:
                continue

            sx, sy = camera.world_to_screen(seed.pos_x, seed.pos_y)
            base_r = max(3, int(4.0 * zoom))

            # 1. Mutated Genetic Abnormality Aura
            if seed.has_abnormality:
                pulse_r = base_r + 3 + int(math.sin(sim_tick * 0.18 + seed.pos_x) * 2)
                if seed.abnormality == SeedAbnormality.BIOLUMINESCENT:
                    abn_col = (0, 240, 255, 90)
                elif seed.abnormality == SeedAbnormality.GIANT_GROWTH:
                    abn_col = (255, 215, 0, 90)
                else:
                    abn_col = (200, 100, 255, 80)
                aura_surf = get_cached_aura_sprite(abn_col, pulse_r)
                surface.blit(aura_surf, (sx - pulse_r, sy - pulse_r))

            # 2. Seed Cotyledon Body
            if seed.stage == "SAPLING":
                pygame.draw.line(surface, (60, 160, 40), (sx, sy), (sx, sy - base_r * 2), 2)
                pygame.draw.circle(surface, (70, 220, 60), (sx - base_r, sy - base_r * 2), base_r)
                pygame.draw.circle(surface, (70, 220, 60), (sx + base_r, sy - base_r * 2), base_r)
            elif seed.stage == "SPROUT":
                pygame.draw.ellipse(surface, (100, 180, 50), pygame.Rect(sx - base_r, sy - base_r, base_r * 2, base_r * 2))
                pygame.draw.line(surface, (120, 230, 70), (sx, sy), (sx + base_r, sy - base_r * 2), 2)
            else:
                pygame.draw.ellipse(surface, (139, 85, 35), pygame.Rect(sx - base_r, sy - int(base_r * 0.7), base_r * 2, int(base_r * 1.4)))
                pygame.draw.ellipse(surface, (180, 120, 60), pygame.Rect(sx - base_r, sy - int(base_r * 0.7), base_r * 2, int(base_r * 1.4)), 1)

            # 3. Circular Growth Progress Ring
            ring_r = base_r + 3
            if ring_r > 2:
                prog_rad = max(0.1, seed.growth_progress * 2.0 * math.pi)
                ring_rect = pygame.Rect(sx - ring_r, sy - ring_r, ring_r * 2, ring_r * 2)
                pygame.draw.arc(surface, (40, 60, 40), ring_rect, 0, 2 * math.pi, 1)
                pygame.draw.arc(surface, (80, 255, 120), ring_rect, -math.pi / 2, -math.pi / 2 + prog_rad, 2)

            # 4. Zoomed-in Seed Annotation
            if zoom >= 0.75:
                from project.renderer.ui import get_cached_text
                lbl_text = f"🌱 {seed.parent_fruit} ({int(seed.growth_progress * 100)}%)"
                if seed.has_abnormality:
                    lbl_text = f"✨ {seed.parent_fruit} [{seed.abnormality_trait}] ({int(seed.growth_progress * 100)}%)"
                lbl_color = (180, 255, 180) if not seed.has_abnormality else (255, 230, 100)
                txt_surf = get_cached_text(self.monospace_10_font, lbl_text, lbl_color)
                surface.blit(txt_surf, (sx - txt_surf.get_width() // 2, sy + ring_r + 2))
