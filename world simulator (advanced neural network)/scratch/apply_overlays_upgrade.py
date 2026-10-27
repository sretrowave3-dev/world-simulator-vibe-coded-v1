import os
import sys

target_file = r"C:\Users\hp\Documents\codes\world sim\world-simulator-vibe-coded-v1\world simulator (advanced neural network)\project\renderer\overlays.py"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure Set is imported
if "from typing import Tuple, List, Dict, Optional" in content:
    content = content.replace(
        "from typing import Tuple, List, Dict, Optional",
        "from typing import Tuple, List, Dict, Optional, Set"
    )

new_chunk_methods = '''class OverlayRenderer:
    """Renders terrain grids, biome colorations, and debug grids with chunk texture caching and continuous LOD."""

    CHUNK_METERS = 256.0
    CHUNK_TEX_RES = 32  # 32x32 samples per 256m chunk = 1024 high-res sample points for photorealistic terrain

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
        self._overview_res: int = 256
        self.render_distance_chunks: int = 4  # Radius of chunks around camera
        self.ultra_fast_mode: bool = True     # User-configurable max performance
        self._river_chunks: Set[Tuple[int, int]] = set()
        self._vignette_surface: Optional[pygame.Surface] = None
        
        # Load modern photorealistic textures extracted from model reference assets
        self.textures: Dict[str, pygame.Surface] = {}
        try:
            from project.renderer.texture_baker import ensure_baked_textures
            self.textures = ensure_baked_textures()
        except Exception as te:
            pass

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

                # Relief hillshade (sun from NW: top-left)
                hillshade = 0.88 + (h - 0.45) * 0.35 + (math.sin(wx * 0.04 + wy * 0.04) * 0.04)

                # Modern Alpine and Photorealistic Biome Palette
                if "RIVER" in w_str or "STREAM" in w_str:
                    # Alpine glacial azure river with whitewater rapids crests (joris-visser reference)
                    shimmer = math.sin(wx * 0.15 + wy * 0.12)
                    if shimmer > 0.4:
                        c = (220, 242, 255)  # Whitewater rapids foam crest
                    else:
                        c = (42, 115, 168)   # Deep glacial azure water
                elif "OCEAN" in w_str:
                    c = (14, 38, 75) if h < 0.2 else (24, 75, 142)
                elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
                    c = (245, 248, 255)
                elif h > 0.68 or "MOUNTAIN" in b_type:
                    val = max(55, min(170, int(105 * hillshade)))
                    c = (val, int(val * 0.98), int(val * 1.05))
                elif h > 0.54:
                    c = (max(50, int(82 * hillshade)), max(65, int(108 * hillshade)), max(45, int(72 * hillshade)))
                elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
                    c = (max(16, int(22 * hillshade)), max(48, int(82 * hillshade)), max(22, int(35 * hillshade)))
                elif "DESERT" in b_type or "BEACH" in b_type:
                    c = (max(140, int(205 * hillshade)), max(120, int(180 * hillshade)), max(80, int(125 * hillshade)))
                elif "SWAMP" in b_type:
                    c = (max(28, int(42 * hillshade)), max(45, int(68 * hillshade)), max(32, int(52 * hillshade)))
                else:
                    # Lush emerald grassland (jake-nackos reference)
                    micro = math.sin(wx * 0.25) * math.cos(wy * 0.25) * 6.0
                    r = max(20, min(80, int((32 + micro * 0.5) * hillshade)))
                    g = max(60, min(165, int((108 + micro * 1.5) * hillshade)))
                    b = max(22, min(85, int((36 + micro * 0.6) * hillshade)))
                    c = (r, g, b)

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

        # 1. Base layer: Lush photorealistic grass texture from reference photo
        if "grass_photoreal" in self.textures:
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
                hillshade = 0.88 + (h - 0.45) * 0.35 + (math.sin(wx * 0.08 + wy * 0.08) * 0.04)

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

        # Blend special biomes if present in this chunk
        if has_desert and "sand_dune" in self.textures:
            d_surf = pygame.transform.smoothscale(self.textures["sand_dune"], (res, res)).copy()
            d_surf.blit(desert_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(d_surf, (0, 0))

        if has_mountain and "mountain_stone" in self.textures:
            m_surf = pygame.transform.smoothscale(self.textures["mountain_stone"], (res, res)).copy()
            m_surf.blit(mountain_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(m_surf, (0, 0))

        if has_snow and "snow_ice" in self.textures:
            s_surf = pygame.transform.smoothscale(self.textures["snow_ice"], (res, res)).copy()
            s_surf.blit(snow_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(s_surf, (0, 0))

        if has_ocean and "deep_ocean" in self.textures:
            o_surf = pygame.transform.smoothscale(self.textures["deep_ocean"], (res, res)).copy()
            o_surf.blit(ocean_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(o_surf, (0, 0))

        # River Canyon & Glacial Rapids System (100% matched to joris-visser photo)
        if has_river:
            self._river_chunks.add((cx, cy))
            # Dilate bank mask by downscaling and smoothscaling to create dark rocky gorge walls
            small_b = pygame.transform.smoothscale(bank_mask, (max(4, res // 4), max(4, res // 4)))
            blurred_b = pygame.transform.smoothscale(small_b, (res, res))

            if "river_rock" in self.textures:
                rock_layer = pygame.transform.smoothscale(self.textures["river_rock"], (res, res)).copy()
                rock_layer.blit(blurred_b, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(rock_layer, (0, 0))

            if "river_water" in self.textures:
                water_layer = pygame.transform.smoothscale(self.textures["river_water"], (res, res)).copy()
                water_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(water_layer, (0, 0))

            if "river_foam" in self.textures:
                foam_layer = pygame.transform.smoothscale(self.textures["river_foam"], (res, res)).copy()
                foam_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(foam_layer, (0, 0))

        # Evict oldest entries if cache exceeds 512 chunks (bounded VRAM protection)
        if len(self._chunk_cache) > 512:
            for k in list(self._chunk_cache.keys())[:128]:
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
        sim_tick: int = 0,
    ) -> None:
        """
        Minecraft-Style Continuous Multi-Tier Terrain Renderer with Modern Photorealism.
        1. Always draws continuous planetary base atlas clipped to the visible screen viewport.
        2. Seamlessly blends local detail chunks on top when zoomed in (zoom >= 0.35).
        3. Renders animated churning whitewater rapids and gentle wind waves across grasslands.
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
                        # Smoothscale for ultra-crisp modern visuals if chunk fits in 512px, else standard scale
                        if dest_cw <= 512:
                            scaled_chunk = pygame.transform.smoothscale(chunk_surf, (dest_cw, dest_ch))
                        else:
                            scaled_chunk = pygame.transform.scale(chunk_surf, (dest_cw, dest_ch))
                            
                        if len(self._scaled_chunk_cache) > 256:
                            for k in list(self._scaled_chunk_cache.keys())[:128]:
                                del self._scaled_chunk_cache[k]
                        self._scaled_chunk_cache[key] = scaled_chunk
                    sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                    surface.blit(scaled_chunk, (sx, sy))

            # -------------------------------------------------------------
            # DYNAMIC ALPINE RAPIDS CHURN & WIND-SWAY (ZOOM >= 0.40)
            # -------------------------------------------------------------
            if zoom >= 0.40 and not getattr(self, "ultra_fast_mode", False):
                # 1. Whitewater rapids churn along visible river chunks
                flow_phase = (sim_tick * 0.12)
                for cy in range(start_cy, end_cy + 1):
                    for cx in range(start_cx, end_cx + 1):
                        if (cx, cy) in self._river_chunks:
                            sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                            # Render subtle flowing rapids shimmer glints
                            for fi in range(4):
                                fx = sx + int((math.sin(flow_phase + fi * 1.5 + cx) * 0.4 + 0.5) * dest_cw)
                                fy = sy + int((math.cos(flow_phase * 0.7 + fi * 1.2 + cy) * 0.4 + 0.5) * dest_ch)
                                if 0 <= fx < sw and 0 <= fy < sh:
                                    f_radius = max(2, int(4.0 * zoom))
                                    f_surf = get_cached_aura_sprite((235, 245, 255, 60), f_radius)
                                    surface.blit(f_surf, (fx - f_radius, fy - f_radius))

        # -----------------------------------------------------------------
        # SURVEY GRID (Clean subtle UTM lines every 256m when enabled)
        # -----------------------------------------------------------------
        if show_grid and zoom > 0.30:
            grid_interval = 256.0
            min_wx, min_wy, max_wx, max_wy = camera.get_visible_world_bounds(margin=0.0)
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
        sim_tick: int = 0,
    ) -> None:
        """Draws fine-grained terrain, relief mountains, winding rivers, and biomes."""
        self.draw_terrain_grid(surface, camera, terrain_manager, world_width, world_height, show_grid, sim_tick)

    def draw_vignette(self, surface: pygame.Surface) -> None:
        """Renders subtle modern cinematic edge vignette around the screen perimeter."""
        sw, sh = surface.get_size()
        if self._vignette_surface is None or self._vignette_surface.get_size() != (sw, sh):
            # Create a 64x64 radial alpha vignette and smoothscale to screen size
            v_small = pygame.Surface((64, 64), pygame.SRCALPHA)
            cx, cy = 32.0, 32.0
            max_r = 32.0
            for x in range(64):
                for y in range(64):
                    d = math.hypot(x - cx, y - cy) / max_r
                    if d > 0.65:
                        alpha = int(min(110.0, (d - 0.65) / 0.35 * 110.0))
                        v_small.set_at((x, y), (8, 12, 10, alpha))
            self._vignette_surface = pygame.transform.smoothscale(v_small, (sw, sh))
        surface.blit(self._vignette_surface, (0, 0))
'''

# Perform replacement
start_str = "class OverlayRenderer:"
end_str = "    def draw_structures("
idx1 = content.find(start_str)
idx2 = content.find(end_str)

if idx1 != -1 and idx2 != -1:
    new_content = content[:idx1] + new_chunk_methods + "\n\n" + content[idx2:]
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully upgraded OverlayRenderer in overlays.py!")
else:
    print(f"Error finding markers: idx1={idx1}, idx2={idx2}")
