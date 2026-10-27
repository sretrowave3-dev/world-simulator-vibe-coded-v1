import re
import os

overlays_path = r"world simulator (advanced neural network)\project\renderer\overlays.py"
renderer_path = r"world simulator (advanced neural network)\project\renderer\renderer.py"

# --- 1. PATCH OVERLAYS.PY ---
with open(overlays_path, "r", encoding="utf-8") as f:
    text = f.read()

# Add _tex_res init
if "self._tex_res" not in text:
    old_init = """        self.textures: Dict[str, pygame.Surface] = {}
        try:
            from project.renderer.texture_baker import ensure_baked_textures
            self.textures = ensure_baked_textures()
        except Exception:
            pass"""
    new_init = """        self.textures: Dict[str, pygame.Surface] = {}
        try:
            from project.renderer.texture_baker import ensure_baked_textures
            self.textures = ensure_baked_textures()
        except Exception:
            pass
        self._tex_res: Dict[str, pygame.Surface] = {
            k: pygame.transform.smoothscale(surf, (self.CHUNK_TEX_RES, self.CHUNK_TEX_RES))
            for k, surf in self.textures.items()
        }"""
    assert old_init in text, "Could not find textures init in overlays.py"
    text = text.replace(old_init, new_init, 1)

# Pre-scaled texture usage in _compile_chunk_surface
old_compile = """        # Base lush photorealistic grass from reference photo
        if "grass_photoreal" in self.textures:
            surf.blit(pygame.transform.smoothscale(self.textures["grass_photoreal"], (res, res)), (0, 0))
        else:
            surf.fill((32, 105, 36))"""

new_compile = """        # Base lush photorealistic grass from reference photo
        if "grass_photoreal" in getattr(self, "_tex_res", {}):
            surf.blit(self._tex_res["grass_photoreal"], (0, 0))
        elif "grass_photoreal" in self.textures:
            surf.blit(pygame.transform.smoothscale(self.textures["grass_photoreal"], (res, res)), (0, 0))
        else:
            surf.fill((32, 105, 36))"""
if old_compile in text:
    text = text.replace(old_compile, new_compile, 1)

old_biome_blits = """        # Blend distinct biomes
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

        # River Gorge Canyon & Whitewater Rapids (100% matched to joris-visser reference photo)
        if has_river:
            self._river_chunks.add((cx, cy))
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
                surf.blit(foam_layer, (0, 0))"""

new_biome_blits = """        # Blend distinct biomes
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
                surf.blit(foam_layer, (0, 0))"""
if old_biome_blits in text:
    text = text.replace(old_biome_blits, new_biome_blits, 1)

# Smooth scaling at close zoom and living atmosphere in draw_terrain_grid
old_chunk_scale = """                    # Chunk is ready: scale and blit
                    key = (cx, cy, dest_cw, dest_ch)
                    scaled_chunk = self._scaled_chunk_cache.get(key)
                    if scaled_chunk is None:
                        scaled_chunk = pygame.transform.scale(chunk_surf, (dest_cw, dest_ch))
                        if len(self._scaled_chunk_cache) > 256:
                            for k in list(self._scaled_chunk_cache.keys())[:128]:
                                del self._scaled_chunk_cache[k]
                        self._scaled_chunk_cache[key] = scaled_chunk

                    sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                    surface.blit(scaled_chunk, (sx, sy))

            # Dynamic river rapids churn
            flow_phase = (sim_tick * 0.12)
            for cy in range(start_cy, end_cy + 1):
                for cx in range(start_cx, end_cx + 1):
                    if (cx, cy) in self._river_chunks:
                        sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                        for fi in range(4):
                            fx = sx + int((math.sin(flow_phase + fi * 1.5 + cx) * 0.35 + 0.5) * dest_cw)
                            fy = sy + int((math.cos(flow_phase * 0.7 + fi * 1.2 + cy) * 0.35 + 0.5) * dest_ch)
                            if 0 <= fx < sw and 0 <= fy < sh:
                                pygame.draw.circle(surface, (230, 245, 255), (fx, fy), max(2, int(3.0 * zoom)))"""

new_chunk_scale = """                    # Chunk is ready: scale and blit
                    key = (cx, cy, dest_cw, dest_ch)
                    scaled_chunk = self._scaled_chunk_cache.get(key)
                    if scaled_chunk is None:
                        if zoom >= 0.85 and dest_cw <= 1024:
                            scaled_chunk = pygame.transform.smoothscale(chunk_surf, (dest_cw, dest_ch))
                        else:
                            scaled_chunk = pygame.transform.scale(chunk_surf, (dest_cw, dest_ch))
                        if len(self._scaled_chunk_cache) > 256:
                            for k in list(self._scaled_chunk_cache.keys())[:128]:
                                del self._scaled_chunk_cache[k]
                        self._scaled_chunk_cache[key] = scaled_chunk

                    sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                    surface.blit(scaled_chunk, (sx, sy))

            # Dynamic river rapids churn & whitewater froth (joris-visser reference asset)
            flow_phase = (sim_tick * 0.12)
            for cy in range(start_cy, end_cy + 1):
                for cx in range(start_cx, end_cx + 1):
                    if (cx, cy) in self._river_chunks:
                        sx, sy = camera.world_to_screen(cx * self.CHUNK_METERS, cy * self.CHUNK_METERS)
                        for fi in range(5):
                            fx = sx + int((math.sin(flow_phase + fi * 1.4 + cx) * 0.38 + 0.5) * dest_cw)
                            fy = sy + int((math.cos(flow_phase * 0.75 + fi * 1.1 + cy) * 0.38 + 0.5) * dest_ch)
                            if 0 <= fx < sw and 0 <= fy < sh:
                                r_size = max(2, int(3.5 * zoom))
                                pygame.draw.circle(surface, (240, 250, 255), (fx, fy), r_size)
                                if zoom >= 1.0:
                                    pygame.draw.circle(surface, (170, 220, 250), (fx - 1, fy - 1), max(1, r_size - 1))

            # Living grassland wind-sway effect at close zoom (jake-nackos reference asset)
            if zoom >= 0.75:
                wind_t = sim_tick * 0.035
                for wi in range(16):
                    wx = int((math.sin(wind_t + wi * 1.8) * 0.45 + 0.5) * sw)
                    wy = int((math.cos(wind_t * 0.65 + wi * 2.4) * 0.45 + 0.5) * sh)
                    sway = int(math.sin(wind_t * 2.0 + wi) * 4.0 * zoom)
                    pygame.draw.line(surface, (55, 140, 68), (wx, wy), (wx + sway, wy - int(6 * zoom)), max(1, int(zoom)))"""
if old_chunk_scale in text:
    text = text.replace(old_chunk_scale, new_chunk_scale, 1)

# Convert alpha on vignette
old_vig = """            self._vignette_surface = pygame.transform.smoothscale(v_small, (sw, sh))"""
new_vig = """            scaled = pygame.transform.smoothscale(v_small, (sw, sh))
            try:
                self._vignette_surface = scaled.convert_alpha()
            except Exception:
                self._vignette_surface = scaled"""
if old_vig in text:
    text = text.replace(old_vig, new_vig, 1)

# Remove in-function imports
text = text.replace("        from project.civilization.settlement import world_settlement_mgr\n", "")
text = text.replace("        from project.world.seeds import SeedAbnormality\n", "")

with open(overlays_path, "w", encoding="utf-8") as f:
    f.write(text)
print("overlays.py patched successfully!")

# --- 2. PATCH RENDERER.PY ---
with open(renderer_path, "r", encoding="utf-8") as f:
    r_text = f.read()

# Add top-level imports to renderer.py
old_r_top = """from project.world.terrain import TerrainManager
from project.ai.pheromone import PheromoneGrid, PheromoneType
from project.analytics.graphs import PopulationGraphRenderer"""

new_r_top = """from project.world.terrain import TerrainManager
from project.ai.pheromone import PheromoneGrid, PheromoneType
from project.analytics.graphs import PopulationGraphRenderer
from project.world.ancient_ruins import ancient_ruins_mgr
from project.world.miracles import world_miracles_mgr
from project.world.seeds import world_seed_growth_mgr, SeedAbnormality
from project.civilization.settlement import world_settlement_mgr
from project.core.quantum_persistence import quantum_persistence
from project.core.git_save_manager import git_save_manager
from project.core.gpu_manager import gpu_mgr"""

if old_r_top in r_text:
    r_text = r_text.replace(old_r_top, new_r_top, 1)

# Remove in-function imports from renderer.py
r_text = r_text.replace("        from project.world.ancient_ruins import ancient_ruins_mgr\n", "")
r_text = r_text.replace("        from project.world.miracles import world_miracles_mgr\n", "")
r_text = r_text.replace("        from project.world.seeds import world_seed_growth_mgr\n", "")
r_text = r_text.replace("            from project.core.quantum_persistence import quantum_persistence\n", "")
r_text = r_text.replace("                from project.core.git_save_manager import git_save_manager\n", "")
r_text = r_text.replace("            from project.civilization.settlement import world_settlement_mgr\n", "")
r_text = r_text.replace("        from project.core.gpu_manager import gpu_mgr\n", "")

with open(renderer_path, "w", encoding="utf-8") as f:
    f.write(r_text)
print("renderer.py patched successfully!")
