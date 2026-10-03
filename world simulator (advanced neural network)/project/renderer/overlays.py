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


class OverlayRenderer:
    """Renders terrain grids, biome colorations, and debug grids with texture caching."""

    def __init__(self, cell_size: float = 16.0) -> None:
        self.cell_size = cell_size
        self._cached_surface: Optional[pygame.Surface] = None
        self._cached_world_size: Tuple[float, float] = (0.0, 0.0)

    def draw_terrain_grid(
        self,
        surface: pygame.Surface,
        camera: Camera,
        terrain_manager: TerrainManager,
        world_width: float = 2048.0,
        world_height: float = 2048.0,
    ) -> None:
        """Renders biome block boxes using an optimized pre-rendered world texture."""
        # 1. Build or rebuild cached surface if dimensions changed
        if self._cached_surface is None or self._cached_world_size != (world_width, world_height):
            self._cached_surface = pygame.Surface((int(world_width), int(world_height)))
            self._cached_world_size = (world_width, world_height)
            self._cached_surface.fill((10, 12, 16))  # Deep ambient space color

            # Draw ambient biomes with extremely dark/modern aesthetic
            for wy in range(0, int(world_height), int(self.cell_size)):
                for wx in range(0, int(world_width), int(self.cell_size)):
                    tile = terrain_manager.get_tile(wx, wy)
                    if tile:
                        biome_params = BIOME_CATALOG.get(tile.biome)
                        br, bg, bb = biome_params.color_rgb if biome_params else (34, 139, 34)
                        # Blend aggressively towards a very dark modern slate
                        # roughly 10% of the biome color, 90% dark slate
                        mr, mg, mb = (10 + int(br * 0.1), 14 + int(bg * 0.1), 20 + int(bb * 0.1))
                        
                        pygame.draw.rect(
                            self._cached_surface,
                            (mr, mg, mb),
                            pygame.Rect(wx, wy, int(self.cell_size), int(self.cell_size)),
                        )
                        # Draw subtle grid lines on the tile
                        pygame.draw.rect(
                            self._cached_surface,
                            (18, 22, 30),
                            pygame.Rect(wx, wy, int(self.cell_size), int(self.cell_size)),
                            1
                        )

        # 2. Viewport-Culled Fast Subsurface Blitting (Cuts CPU raster work by ~98%)
        zoom = camera.zoom
        min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=16.0)

        src_x = max(0, int(min_wx))
        src_y = max(0, int(min_wy))
        src_r = min(int(world_width), int(math.ceil(max_wx)))
        src_b = min(int(world_height), int(math.ceil(max_wy)))
        src_w = src_r - src_x
        src_h = src_b - src_y

        if src_w > 0 and src_h > 0:
            sub_surf = self._cached_surface.subsurface(pygame.Rect(src_x, src_y, src_w, src_h))
            dest_sx, dest_sy = camera.world_to_screen(src_x, src_y)
            dest_w = max(1, int(src_w * zoom))
            dest_h = max(1, int(src_h * zoom))

            if dest_w == src_w and dest_h == src_h:
                surface.blit(sub_surf, (dest_sx, dest_sy))
            else:
                scaled_slice = pygame.transform.scale(sub_surf, (dest_w, dest_h))
                surface.blit(scaled_slice, (dest_sx, dest_sy))

    def draw_terrain(
        self,
        surface: pygame.Surface,
        camera: Camera,
        terrain_manager: TerrainManager,
        show_grid: bool = True,
        world_width: float = 4096.0,
        world_height: float = 4096.0,
    ) -> None:
        """Draws terrain grid and biome tiles."""
        self.draw_terrain_grid(surface, camera, terrain_manager, world_width, world_height)

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
        relic_surf = pygame.Surface((altar_pulse_r * 2, altar_pulse_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(relic_surf, (0, 230, 255, 60), (altar_pulse_r, altar_pulse_r), altar_pulse_r)
        surface.blit(relic_surf, (asx - altar_pulse_r, asy - altar_pulse_r))

        # Relic diamond core
        d_size = max(3, int(10 * zoom))
        diamond_pts = [(asx, asy - d_size), (asx + d_size, asy), (asx, asy + d_size), (asx - d_size, asy)]
        pygame.draw.polygon(surface, (200, 250, 255), diamond_pts)
        pygame.draw.polygon(surface, (0, 240, 255), diamond_pts, 1)

        # 6. Overhead Ruins Inscription Label
        from project.renderer.ui import get_cached_text
        ruins_lbl = get_cached_text(pygame.font.SysFont("monospace", 12), "🏛️ FORBIDDEN SANCTUARY OF THE PRIMORDIALS", (0, 240, 255))
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
            aura_surf = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (160, 100, 255, 70), (pulse_r, pulse_r), pulse_r)
            pygame.draw.circle(aura_surf, (220, 180, 255, 140), (pulse_r, pulse_r), max(2, pulse_r // 2))
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
                if not hasattr(self, "_ambient_surface") or self._ambient_surface.get_size() != (sw, sh):
                    self._ambient_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
                
                # Tint towards deep indigo or blood-crimson eclipse
                r, g, b = ambient_tint
                self._ambient_surface.fill((r // 3, g // 4, b // 3, night_alpha))
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
            aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_s, (*aura_c[:3], 80), (aura_r, aura_r), aura_r)
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
                aura_surf = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
                if seed.abnormality == SeedAbnormality.BIOLUMINESCENT:
                    pygame.draw.circle(aura_surf, (0, 240, 255, 90), (pulse_r, pulse_r), pulse_r)
                elif seed.abnormality == SeedAbnormality.GIANT_GROWTH:
                    pygame.draw.circle(aura_surf, (255, 215, 0, 90), (pulse_r, pulse_r), pulse_r)
                else:
                    pygame.draw.circle(aura_surf, (200, 100, 255, 80), (pulse_r, pulse_r), pulse_r)
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
                font = pygame.font.SysFont("monospace", 10)
                txt_surf = get_cached_text(font, lbl_text, lbl_color)
                surface.blit(txt_surf, (sx - txt_surf.get_width() // 2, sy + ring_r + 2))
