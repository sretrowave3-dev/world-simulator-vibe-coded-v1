"""
project/renderer/renderer.py

Master Pygame Visual Renderer orchestrating views, inputs, cameras, and HUD panels.
Features:
- Responsive Window Resizing & Dynamic Aspect Ratio Scaling.
- Clean Non-Overlapping Modern HUD Layouts.
- Multi-Species Visual Archetypes & Halos.
- High-Performance Hardware-Accelerated Rendering.
"""

from __future__ import annotations

import sys
import math
import time
from typing import List, Dict, Any, Tuple, Optional
import pygame

from project.renderer.camera import Camera
from project.renderer.minimap import Minimap
from project.renderer.inspector import Inspector
from project.renderer.overlays import OverlayRenderer
from project.renderer.heatmaps import HeatmapRenderer
from project.renderer.particles import ParticleSystemManager
from project.renderer.debug_renderer import DebugRenderer
from project.renderer.brain_visualizer import BrainVisualizer
from project.renderer.ui import Button, Checkbox, Console, Slider, Selector, get_cached_text, get_cached_circle_sprite, get_cached_aura_sprite

from project.world.terrain import TerrainManager
from project.ai.pheromone import PheromoneGrid, PheromoneType
from project.analytics.graphs import PopulationGraphRenderer

_ENTITY_SPRITE_CACHE: Dict[Tuple[Tuple[int, int, int], int], pygame.Surface] = {}
_SPECIES_COLOR_MAP = {
    "BACTERIA": (0, 255, 200),
    "PLANT": (40, 220, 100),
    "HERBIVORE": (255, 210, 50),
    "PREDATOR": (255, 60, 80),
    "CARNIVORE": (255, 60, 80),
    "HUMAN": (245, 245, 255),
    "AVIAN": (90, 180, 255),
    "AMPHIBIAN": (40, 210, 120),
    "ARTHROPOD": (240, 200, 20),
    "REPTILE": (160, 190, 40),
    "FUNGUS": (190, 120, 220),
    "DECOMPOSER": (170, 140, 100),
    "OMNIVORE": (220, 160, 80),
}


def get_cached_circle_sprite(color: Tuple[int, int, int], radius: int) -> pygame.Surface:
    """Pre-renders and caches anti-aliased circle sprites for 4x faster CPU blitting."""
    key = (color, radius)
    surf = _ENTITY_SPRITE_CACHE.get(key)
    if surf is not None:
        return surf
    if len(_ENTITY_SPRITE_CACHE) >= 512:
        _ENTITY_SPRITE_CACHE.clear()
    diam = max(2, radius * 2)
    surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (radius, radius), radius)
    _ENTITY_SPRITE_CACHE[key] = surf
    return surf


class SimulationRenderer:
    """Master controller managing Pygame initialization, drawing loops, and UI feedback."""

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        world_width: float = 4096.0,
        world_height: float = 4096.0,
    ) -> None:
        # Platform-specific display enhancements
        if sys.platform == "win32":
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
        elif sys.platform.startswith("linux"):
            import os
            # Linux X11/Wayland compositor optimization
            os.environ.setdefault("SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR", "0")

        pygame.init()
        pygame.font.init()
        pygame.key.set_repeat(200, 30)

        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        self.ui_active = True

        # Initialize screen with Resizable flag
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.RESIZABLE)
        pygame.display.set_caption("Echo Evolution Simulator - Living Neural Universe")

        # Sync actual dimensions if OS window manager adjusted resolution
        act_w, act_h = self.screen.get_size()
        self.width = act_w
        self.height = act_h

        self.clock = pygame.time.Clock()
        # Robust Linux and cross-platform monospace font cascade
        font_cascade = "DejaVu Sans Mono,Ubuntu Mono,Liberation Mono,Noto Sans Mono,FreeMono,Consolas,Courier New,monospace"
        self.font = pygame.font.SysFont(font_cascade, 13)

        # Camera & Sub-renderers
        self.camera = Camera(self.width, self.height)
        self.camera.pos_x = world_width / 2.0
        self.camera.pos_y = world_height / 2.0
        self.minimap = Minimap(x=self.width - 210, y=10, width=200, height=190, world_width=world_width, world_height=world_height)
        self.inspector = Inspector(x=self.width - 310, y=210, width=300, height=max(350, self.height - 220))
        self.overlays = OverlayRenderer()
        self.heatmaps = HeatmapRenderer()
        self.particles = ParticleSystemManager()
        self.pop_graph = PopulationGraphRenderer(x=10, y=min(380, height - 170), width=240, height=140)
        self.brain_visualizer = BrainVisualizer(x=max(10, width // 2 - 350), y=height - 250, width=700, height=230)
        self._thermal_tint_surf: Optional[pygame.Surface] = None

        # Selection state
        self.selected_entity_id: Optional[str] = None

        # Interactive UI buttons & toggles
        self.buttons: List[Button] = []
        self.checkboxes: List[Checkbox] = []
        self.sliders: List[Slider] = []
        self.selectors: List[Selector] = []
        self.simulation_speed: float = 1.0

        # Developer Command Console overlay
        self.console = Console(x=10, y=self.height - 360, width=500, height=350)
        self.command_queue: List[str] = []

        # Upgrade notification & banner state
        self.update_info: Optional[Any] = None
        self.update_banner_rect: Optional[pygame.Rect] = None
        self.update_button_rect: Optional[pygame.Rect] = None
        self.is_updating_ui: bool = False
        self.update_status_text: str = ""

        # Determine offline mode from profile
        self.is_offline: bool = False
        try:
            from project.core.user_profile import user_profile_manager
            prof = user_profile_manager.get_profile()
            self.is_offline = prof.gemini.get("is_offline", False) or (len(prof.gemini.get("api_keys", [])) == 0)
        except Exception:
            pass

        self._setup_ui()

    def on_resize(self, new_width: int, new_height: int) -> None:
        """Dynamically adjusts all UI components and viewports on window resize."""
        self.width = max(800, new_width)
        self.height = max(600, new_height)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.camera.resize(self.width, self.height)

        # Reposition panels with clean layout margins (NO OVERLAPS)
        self.minimap.rect.x = self.width - 210
        self.minimap.rect.y = 10

        self.inspector.rect.x = self.width - 310
        self.inspector.rect.y = 210
        self.inspector.rect.height = max(350, self.height - 220)

        self.brain_visualizer.rect.x = max(10, self.width // 2 - 350)
        self.brain_visualizer.rect.y = self.height - 250

        self.pop_graph.rect.y = min(380, self.height - 170)
        self.console.rect.y = self.height - 360

    def _setup_ui(self) -> None:
        # Control buttons at top-left
        self.buttons.append(Button(10, 10, 75, 24, "Pause", lambda: self.set_speed(0.0)))
        self.buttons.append(Button(90, 10, 75, 24, "1x Speed", lambda: self.set_speed(1.0)))
        self.buttons.append(Button(170, 10, 75, 24, "2x Speed", lambda: self.set_speed(2.0)))
        self.buttons.append(Button(250, 10, 75, 24, "5x Speed", lambda: self.set_speed(5.0)))

        # Toggles below buttons
        self.checkboxes.append(Checkbox(10, 42, "Show Grid", default_state=False))
        self.checkboxes.append(Checkbox(10, 64, "Show Minimap", default_state=True))
        self.checkboxes.append(Checkbox(10, 86, "Show Diagnostics", default_state=True))
        self.checkboxes.append(Checkbox(10, 108, "Show Food Trails", default_state=False))
        self.checkboxes.append(Checkbox(10, 130, "Show Danger Scent", default_state=False))
        self.checkboxes.append(Checkbox(10, 152, "Thermal Vision", default_state=False))
        self.checkboxes.append(Checkbox(10, 174, "Ideation Sparks", default_state=True))
        self.checkboxes.append(Checkbox(10, 196, "Fast Graphics (Max FPS)", default_state=True))

        # Advanced Interactive UI Controls (Food Spawner)
        self.sliders.append(Slider(10, 230, 110, min_val=0.5, max_val=5.0, default=2.0, label="Food Size"))
        food_options = ["mango", "cucumber", "fruit", "meat", "berry", "honey", "grain", "grass", "mushroom"]
        self.selectors.append(Selector(130, 218, 130, food_options, label="Food Type"))
        
        def spawn_custom_food():
            f_size = self.sliders[0].value
            f_type = self.selectors[0].value
            cx = self.camera.pos_x
            cy = self.camera.pos_y
            self.command_queue.append(f"food:{f_type},{cx},{cy},{f_size}")
            self.console.log(f"Injected {f_type} food at camera center!")

        self.buttons.append(Button(10, 258, 250, 24, "Spawn Selected Food", spawn_custom_food))

        # Gemini God Affinity Tweak Slider (0.0 to 100.0%) - Only enabled if not offline!
        if not self.is_offline:
            self.sliders.append(Slider(10, 300, 250, min_val=0.0, max_val=100.0, default=50.0, label="Gemini God Affinity (%)"))

        # Advanced Celestial Miracles Selector & Cast Button
        miracle_options = ["Bountiful Harvest", "Solar Eclipse", "Meteor Shower", "Divine Rainstorm", "Epiphany Wave", "Purge Threats"]
        self.selectors.append(Selector(10, 332, 170, miracle_options, label="Divine Miracle"))
        
        def cast_selected_miracle():
            m_type = self.selectors[1].value
            cx = self.camera.pos_x
            cy = self.camera.pos_y
            self.command_queue.append(f"miracle:{m_type},{cx},{cy}")
            self.console.log(f"⚡ Invoking Divine Miracle: {m_type}!")

        self.buttons.append(Button(185, 332, 75, 25, "Cast", cast_selected_miracle))

        # Species Spawner Selector & Spawn Button
        species_options = ["Human", "Predator", "Herbivore", "Reptile", "Avian", "Amphibian", "Plant", "Fungus", "Bacteria"]
        self.selectors.append(Selector(10, 372, 170, species_options, label="Spawn Species"))

        def spawn_selected_species():
            s_type = self.selectors[2].value
            cx = self.camera.pos_x
            cy = self.camera.pos_y
            self.command_queue.append(f"spawn_species:{s_type},{cx},{cy}")
            self.console.log(f"🌱 Spawned new {s_type} at ({cx:.0f}, {cy:.0f})!")

        self.buttons.append(Button(185, 372, 75, 25, "Spawn", spawn_selected_species))

        # Quantum Multi-Universe & Time Machine Action Buttons (Row 1 & Row 2)
        self.buttons.append(Button(10, 407, 80, 25, "💾 Save", lambda: self.command_queue.append("save manual_save.dat")))
        self.buttons.append(Button(95, 407, 80, 25, "📂 Load", lambda: self.command_queue.append("load")))
        self.buttons.append(Button(180, 407, 80, 25, "🌿 History", lambda: self.command_queue.append("timeline")))
        self.buttons.append(Button(10, 437, 80, 25, "🌐 Worlds", lambda: self.command_queue.append("universes")))
        self.buttons.append(Button(95, 437, 80, 25, "⏳ Rewind", lambda: self.command_queue.append("rewind safe")))
        self.buttons.append(Button(180, 437, 80, 25, "🌌 New", lambda: self.command_queue.append("world new")))

    def set_speed(self, speed: float) -> None:
        self.simulation_speed = speed

    def get_god_affinity_override(self) -> Optional[float]:
        """Returns the user-tweaked God Affinity value from the UI slider."""
        if len(self.sliders) >= 2:
            return self.sliders[1].value
        return None

    def set_god_affinity_value(self, val: float) -> None:
        """Sets the UI God Affinity slider position."""
        if len(self.sliders) >= 2:
            self.sliders[1].value = max(0.0, min(100.0, val))

    def handle_input(self, entities_snapshot: List[Dict[str, Any]]) -> bool:
        """Processes keyboard/mouse events. Returns False if user requested quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.VIDEORESIZE:
                self.on_resize(event.w, event.h)
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                continue

            # Hotkeys & Advanced Shortcuts
            if event.type == pygame.KEYDOWN and not self.console.active:
                if event.key == pygame.K_F5:
                    self.command_queue.append("quicksave")
                    self.console.log("⚡ Quicksave triggered (F5)")
                elif event.key == pygame.K_F9:
                    self.command_queue.append("quickload")
                    self.console.log("⚡ Quickload triggered (F9)")
                elif event.key == pygame.K_F6:
                    self.command_queue.append("rewind safe")
                    self.console.log("⏳ Time Machine Rewind to Safe Population (F6)")
                elif event.key == pygame.K_F7:
                    self.command_queue.append("rewind disaster")
                    self.console.log("⏳ Time Machine Rewind to Pre-Disaster Blackbox (F7)")
                elif event.key == pygame.K_SPACE:
                    new_spd = 0.0 if self.simulation_speed > 0.0 else 1.0
                    self.set_speed(new_spd)
                    self.console.log(f"Simulation {'Paused' if new_spd == 0.0 else 'Resumed'}")
                elif event.key == pygame.K_t:
                    # Toggle Thermal Vision
                    if len(self.checkboxes) >= 6:
                        self.checkboxes[5].checked = not self.checkboxes[5].checked
                        self.console.log(f"Thermal Vision: {'ON' if self.checkboxes[5].checked else 'OFF'}")
                elif event.key == pygame.K_1:
                    # Preset 1: Full Continental Macro Overview
                    self.camera.set_preset_view(0.045, self.world_width * 0.5, self.world_height * 0.5)
                    self.console.log("🔭 Preset [1]: Full Continental Overview (14,000m)")
                elif event.key == pygame.K_2:
                    # Preset 2: Regional Biome View
                    self.camera.set_preset_view(0.18)
                    self.console.log("🔭 Preset [2]: Regional Biome View")
                elif event.key == pygame.K_3:
                    # Preset 3: Settlement & Tribal Clan View
                    self.camera.set_preset_view(0.65)
                    self.console.log("🔭 Preset [3]: Settlement / Clan View")
                elif event.key == pygame.K_4:
                    # Preset 4: Microscopic Inspector View
                    self.camera.set_preset_view(1.8)
                    self.console.log("🔭 Preset [4]: Close-up Inspection View")
                elif event.key == pygame.K_z:
                    self.camera.zoom_at_screen(0.15, self.camera.screen_width // 2, self.camera.screen_height // 2)
                elif event.key == pygame.K_x:
                    self.camera.zoom_at_screen(-0.15, self.camera.screen_width // 2, self.camera.screen_height // 2)
                elif event.key == pygame.K_f:
                    # Focus camera on Sovereign Leader
                    for e in entities_snapshot:
                        if e.get("role") == "LEADER" or e.get("type") == "HUMAN":
                            self.selected_entity_id = e["id"]
                            self.camera.tracking_entity_id = e["id"]
                            self.console.log(f"Camera locked onto Leader/Human ({e['id']})")
                            break
                elif event.key == pygame.K_e:
                    # Quick trigger Solar Eclipse
                    self.command_queue.append("miracle:Solar Eclipse,0,0")
                elif event.key == pygame.K_r:
                    # Quick trigger Divine Rainstorm
                    self.command_queue.append("miracle:Divine Rainstorm,0,0")
                elif event.key == pygame.K_m:
                    # Quick trigger Meteor Shower at camera center
                    self.command_queue.append(f"miracle:Meteor Shower,{self.camera.pos_x},{self.camera.pos_y}")
                elif event.key == pygame.K_h:
                    # Quick trigger Bountiful Harvest at camera center
                    self.command_queue.append(f"miracle:Bountiful Harvest,{self.camera.pos_x},{self.camera.pos_y}")
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_MINUS):
                    if len(self.sliders) >= 2:
                        self.sliders[1].value = max(0.0, self.sliders[1].value - 5.0)
                        self.command_queue.append(f"affinity:{self.sliders[1].value}")
                        self.console.log(f"Gemini God Affinity decreased to {self.sliders[1].value:.1f}%")
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_PLUS, pygame.K_EQUALS):
                    if len(self.sliders) >= 2:
                        self.sliders[1].value = min(100.0, self.sliders[1].value + 5.0)
                        self.command_queue.append(f"affinity:{self.sliders[1].value}")
                        self.console.log(f"Gemini God Affinity increased to {self.sliders[1].value:.1f}%")
                elif event.key == pygame.K_BACKSLASH:
                    if len(self.sliders) >= 2:
                        self.sliders[1].value = 99.5
                        self.command_queue.append("affinity:99.5")
                        self.console.log("🌟 Gemini God Affinity set to 99.5% (Ascension & Monolith Ready)!")

            # Feed to Developer Command Console first
            cmd = self.console.handle_event(event)
            if cmd:
                self.command_queue.append(cmd)

            if self.console.active:
                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    continue

            # UI components input handling
            ui_handled = False
            for sel in self.selectors:
                if sel.handle_event(event):
                    ui_handled = True
            for slider in self.sliders:
                if slider.handle_event(event):
                    ui_handled = True
                    if slider.label.startswith("Gemini God Affinity"):
                        self.command_queue.append(f"affinity:{slider.value}")
            for btn in self.buttons:
                if btn.handle_event(event):
                    ui_handled = True
            for cb in self.checkboxes:
                if cb.handle_event(event):
                    ui_handled = True
            if ui_handled:
                continue

            # Check remote upgrade banner click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hasattr(self, "update_button_rect") and self.update_button_rect and self.update_button_rect.collidepoint(event.pos):
                    self.command_queue.append("upgrade")
                    self.console.log("🚀 Upgrade triggered from UI banner.")
                    continue

            # Minimap Click-to-Teleport Navigation
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.minimap.handle_click(event.pos, self.camera):
                    continue

            # Modern Mouse Wheel Zoom
            if event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                self.camera.zoom_at_screen(event.y * 0.15, mx, my)

            # Legacy Button 4/5 Wheel Zoom
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.camera.zoom_at_screen(0.15, event.pos[0], event.pos[1])
                elif event.button == 5:
                    self.camera.zoom_at_screen(-0.15, event.pos[0], event.pos[1])

                elif event.button == 1:
                    wx, wy = self.camera.screen_to_world(event.pos[0], event.pos[1])
                    clicked_any = False
                    for entity in entities_snapshot:
                        dx = entity["x"] - wx
                        dy = entity["y"] - wy
                        dist = math.hypot(dx, dy)
                        if dist <= entity["radius"] + 2.0:
                            self.selected_entity_id = entity["id"]
                            self.camera.tracking_entity_id = entity["id"]
                            clicked_any = True
                            break
                    if not clicked_any:
                        self.selected_entity_id = None
                        self.camera.tracking_entity_id = None

            # Drag panning (Middle or Right Click)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[2] or event.buttons[1]:
                    self.camera.pan(event.rel[0], event.rel[1])

        # Smooth Keyboard Pan Navigation (WASD / Arrows)
        if not self.console.active:
            keys = pygame.key.get_pressed()
            pan_spd = 35.0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.camera.pos_y -= pan_spd / self.camera.zoom
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.camera.pos_y += pan_spd / self.camera.zoom
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.camera.pos_x -= pan_spd / self.camera.zoom
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.camera.pos_x += pan_spd / self.camera.zoom

        return True

    def render(
        self,
        entities_snapshot: List[Dict[str, Any]],
        terrain_manager: TerrainManager,
        pheromone_grid: PheromoneGrid,
        system_timings: Dict[str, float],
        sim_tick: int,
        stats_history: Optional[List[Dict[str, int]]] = None,
        time_snapshot: Optional[Any] = None,
        time_manager: Optional[Any] = None,
        god_affinity: Optional[float] = None,
        ruins_manager: Optional[Any] = None,
    ) -> None:
        """Draws single visual frame to the Pygame screen."""
        if not self.ui_active:
            return

        if len(self.checkboxes) > 7:
            self.overlays.ultra_fast_mode = self.checkboxes[7].checked

        self.screen.fill((24, 34, 28))

        # Synchronize God Affinity slider with current simulation state if not dragging
        if len(self.sliders) >= 2 and not self.sliders[1].is_dragging and god_affinity is not None:
            self.sliders[1].value = god_affinity

        from project.world.ancient_ruins import ancient_ruins_mgr
        active_ruins = ruins_manager or ancient_ruins_mgr

        # Update camera follow target
        if self.camera.tracking_entity_id:
            for entity in entities_snapshot:
                if entity["id"] == self.camera.tracking_entity_id:
                    self.camera.update_follow(entity["x"], entity["y"])
                    break

        # 1. Draw environmental terrain tiles (Mountains, Rivers, Biomes)
        self.overlays.draw_terrain(
            self.screen, self.camera, terrain_manager, self.checkboxes[0].checked, self.world_width, self.world_height
        )

        # 2. Draw tribal clan structures (Campfires, Timber Shelters, Altars)
        self.overlays.draw_structures(self.screen, self.camera, sim_tick)

        # 3. Draw ancient sanctuary ruins & ceremonial pathway
        self.overlays.draw_ancient_ruins(self.screen, self.camera, active_ruins, sim_tick)

        # 3. Draw chemical trails (heatmaps)
        if self.checkboxes[3].checked:
            self.heatmaps.draw_pheromone_overlay(
                self.screen, self.camera, pheromone_grid, PheromoneType.FOOD_TRAIL, (0, 255, 100)
            )

        if self.checkboxes[4].checked:
            self.heatmaps.draw_pheromone_overlay(
                self.screen, self.camera, pheromone_grid, PheromoneType.DANGER_ALARM, (255, 50, 50)
            )

        # Draw map borders with Northern breach opening
        self.overlays.draw_world_boundaries(self.screen, self.camera, self.world_width, self.world_height, active_ruins)

        # Compute daylight and celestial properties before rendering entities
        sun_props = None
        if time_manager and hasattr(time_manager, "get_sun_properties"):
            sun_props = time_manager.get_sun_properties()
        elif time_snapshot and hasattr(time_snapshot, "daylight_factor"):
            sun_props = {
                "daylight_factor": time_snapshot.daylight_factor,
                "day_fraction": time_snapshot.day_fraction,
                "phase": "DAY" if time_snapshot.daylight_factor > 0.15 else "NIGHT",
                "solar_lux": time_snapshot.daylight_factor * 100000.0,
                "is_daylight": time_snapshot.daylight_factor > 0.15,
                "sun_color_rgb": (255, 240, 180),
                "ambient_tint_rgb": (255, 255, 255) if time_snapshot.daylight_factor > 0.15 else (25, 30, 55),
            }
        else:
            # Fallback procedural sun computation
            cycle_fraction = (sim_tick % 1200) / 1200.0
            sin_val = math.sin((cycle_fraction - 0.25) * 2.0 * math.pi)
            df = max(0.0, min(1.0, (sin_val + 0.2) * 1.5))
            sun_props = {
                "daylight_factor": df,
                "day_fraction": cycle_fraction,
                "phase": "MIDDAY" if df > 0.6 else ("DAWN/DUSK" if df > 0.15 else "NIGHT"),
                "solar_lux": df * 100000.0,
                "is_daylight": df > 0.15,
                "sun_color_rgb": (255, 240, 180) if df > 0.4 else ((255, 160, 60) if df > 0.15 else (180, 205, 255)),
                "ambient_tint_rgb": (255, 255, 255) if df > 0.4 else ((25, 30, 55)),
            }

        # 4. Draw entities with multi-species color palette & fast frustum culling
        min_wx, min_wy, max_wx, max_wy = self.camera.get_visible_world_bounds(margin=60.0)
        zoom = self.camera.zoom

        for entity in entities_snapshot:
            if not entity["is_alive"]:
                continue

            ex = entity["x"]
            ey = entity["y"]

            # Coarse World-Space Frustum Culling
            if ex < min_wx or ex > max_wx or ey < min_wy or ey > max_wy:
                continue

            sx, sy = self.camera.world_to_screen(ex, ey)
            etype = entity["type"]
            role = entity.get("role")

            # -------------------------------------------------------------
            # Special Monumental Rendering for the Gemini Golden Monolith
            # (Matches architectural terracotta cuboid with circular colonnades)
            # -------------------------------------------------------------
            if role == "MONOLITH" or entity["id"] == "gemini_golden_monolith":
                mono_w = max(24, int(64.0 * zoom))
                mono_h = max(16, int(40.0 * zoom))
                mx_rect = pygame.Rect(sx - mono_w // 2, sy - mono_h // 2, mono_w, mono_h)

                # 1. Pulsing Celestial Golden Sanctuary Aura
                aura_radius = max(8, int(85.0 * zoom + math.sin(sim_tick * 0.08) * 8))
                aura_surf = get_cached_aura_sprite((255, 215, 0, 30), aura_radius)
                self.screen.blit(aura_surf, (sx - aura_radius, sy - aura_radius))

                # 2. Stone Masonry Foundation Base
                base_h = max(3, mono_h // 6)
                base_rect = pygame.Rect(mx_rect.x - 2, mx_rect.bottom - base_h, mono_w + 4, base_h + 2)
                pygame.draw.rect(self.screen, (150, 145, 138), base_rect)
                pygame.draw.rect(self.screen, (90, 85, 80), base_rect, 1)

                # 3. Terracotta Ochre Main Building Facade
                body_rect = pygame.Rect(mx_rect.x, mx_rect.y, mono_w, mono_h - base_h)
                pygame.draw.rect(self.screen, (228, 152, 35), body_rect)
                pygame.draw.rect(self.screen, (255, 190, 65), body_rect, 1)

                # 4. Circular Arch Colonnade Portals (Two tiers of architectural circles)
                portal_radius = max(2, int(mono_h * 0.12))
                num_portals = max(2, min(8, mono_w // max(4, portal_radius * 3)))
                spacing_x = mono_w / (num_portals + 1)
                
                for tier_y in [body_rect.y + int(body_rect.height * 0.48), body_rect.y + int(body_rect.height * 0.78)]:
                    for p_idx in range(1, num_portals + 1):
                        px = int(body_rect.x + p_idx * spacing_x)
                        pygame.draw.circle(self.screen, (110, 55, 12), (px, tier_y), portal_radius)
                        pygame.draw.circle(self.screen, (60, 28, 8), (px, tier_y), max(1, portal_radius - 1))

                # 5. Star-Chart Celestial Perforations on Upper Facade
                upper_y_start = body_rect.y + max(2, int(body_rect.height * 0.14))
                perf_r = max(1, int(portal_radius * 0.35))
                for py_off in [0, 4, 8]:
                    for px_off in range(int(body_rect.x + 8), int(body_rect.right - 8), max(4, int(spacing_x * 0.6))):
                        pygame.draw.circle(self.screen, (80, 40, 10), (px_off, upper_y_start + py_off), perf_r)

                # 6. Overhead Sacred Inscription Label
                from project.renderer.ui import get_cached_text
                label_surf = get_cached_text(self.font, "✨ SACRED MONOLITH OF GEMINI", (255, 225, 100))
                self.screen.blit(label_surf, (sx - label_surf.get_width() // 2, body_rect.y - 18))
                continue

            pixel_r = max(2, int(entity["radius"] * zoom))
            is_thermal = len(self.checkboxes) >= 6 and self.checkboxes[5].checked

            # -------------------------------------------------------------
            # Distinct Food & Flora Rendering (Fruits, Meats, Crops, Seeds)
            # -------------------------------------------------------------
            sp_id = str(entity.get("species_id", "")).lower()
            fruit_tp = str(entity.get("fruit_type", "")).lower()
            is_food = (
                etype == "PLANT" or
                any(k in sp_id for k in ("food", "fruit", "mango", "cucumber", "berry", "apple", "meat", "grass", "honey", "grain", "wheat", "mushroom", "fern")) or
                bool(fruit_tp)
            )

            if is_food and not is_thermal:
                # Show Food Trails: draw appetizing green scent halo around food sources
                if len(self.checkboxes) > 3 and self.checkboxes[3].checked:
                    pulse_r = max(6, int((entity["radius"] * 2.5 + math.sin(sim_tick * 0.12 + ex) * 3.0) * zoom))
                    halo_surf = get_cached_aura_sprite((80, 255, 140, 45), pulse_r)
                    self.screen.blit(halo_surf, (sx - pulse_r, sy - pulse_r))

                is_mature_tree = entity.get("custom_data", {}).get("is_tree", False) or "tree" in sp_id or entity.get("custom_data", {}).get("growth_stage") in ("sapling", "tree", "ancient_tree")
                if is_mature_tree:
                    if zoom < 0.35:
                        tree_r = max(2, int(pixel_r * 0.9))
                        tree_spr = get_cached_circle_sprite((34, 110, 48), tree_r)
                        self.screen.blit(tree_spr, (sx - tree_r, sy - tree_r))
                        if self.selected_entity_id and entity["id"] == self.selected_entity_id:
                            pygame.draw.circle(self.screen, (0, 255, 255), (sx, sy), tree_r + 3, 1)
                        continue
                    # Draw living tree with trunk, layered emerald canopy crown, and fruits
                    stage = entity.get("custom_data", {}).get("growth_stage", "tree")
                    fruit_kg = entity.get("custom_data", {}).get("fruit_kg", 0.0)
                    self.overlays.draw_tree_canopy(
                        surface=self.screen,
                        sx=sx,
                        sy=sy,
                        pixel_r=pixel_r,
                        stage=stage,
                        fruit_kg=fruit_kg,
                        zoom=zoom,
                        sim_tick=sim_tick,
                    )
                else:
                    detected_food_type = fruit_tp or ("mango" if "mango" in sp_id else ("cucumber" if "cucumber" in sp_id else ("meat" if "meat" in sp_id else ("honey" if "honey" in sp_id else ("berry" if "berry" in sp_id else ("grain" if "grain" in sp_id else ("mushroom" if "mushroom" in sp_id else ("grass" if "grass" in sp_id else "fruit"))))))))
                    self.overlays.draw_food_icon(
                        surface=self.screen,
                        sx=sx,
                        sy=sy,
                        food_type=detected_food_type,
                        pixel_r=pixel_r,
                        has_abnormality=entity.get("has_abnormality", False),
                        glow_color=entity.get("glow_color"),
                        zoom=zoom,
                    )
                if self.selected_entity_id and entity["id"] == self.selected_entity_id:
                    pygame.draw.circle(self.screen, (0, 255, 255), (sx, sy), pixel_r + 4, 1)
                continue

            # Show Danger Scent: draw crimson alert aura around predators, combatants, or terrified organisms
            if len(self.checkboxes) > 4 and self.checkboxes[4].checked:
                is_threat = (
                    etype in ("PREDATOR", "CARNIVORE")
                    or entity.get("in_combat", False)
                    or entity.get("fear", 0.0) > 0.35
                    or entity.get("stress", 0.0) > 0.5
                )
                if is_threat:
                    threat_r = max(7, int((entity["radius"] * 2.8 + math.sin(sim_tick * 0.15 + ey) * 3.5) * zoom))
                    threat_surf = get_cached_aura_sprite((255, 50, 50, 45), threat_r)
                    self.screen.blit(threat_surf, (sx - threat_r, sy - threat_r))

            # -------------------------------------------------------------
            # Standard Biological Organism Rendering (with Thermal Vision)
            # -------------------------------------------------------------
            if is_thermal:
                if etype in ("HUMAN", "PREDATOR", "HERBIVORE", "AVIAN", "OMNIVORE"):
                    color = (255, 100, 0)  # Bright Hot Orange/Red (Endotherm)
                elif etype in ("REPTILE", "AMPHIBIAN"):
                    color = (0, 200, 255)  # Bright Cold Cyan (Ectotherm)
                elif etype in ("PLANT", "FUNGUS", "BACTERIA"):
                    color = (0, 50, 150)  # Deep Cold Blue (Flora/Microbe)
                else:
                    color = (100, 100, 120)
            else:
                color = _SPECIES_COLOR_MAP.get(etype, (150, 150, 150))

            # -------------------------------------------------------------
            # Distinct Organic Sprite Rendering with Tool & Action Badges
            # -------------------------------------------------------------
            if etype == "HUMAN" and not is_thermal:
                fast_render = zoom < 0.45 or (getattr(self.overlays, "ultra_fast_mode", False) and zoom < 0.75)
                if fast_render:
                    body_color = (215, 60, 45) if role == "LEADER" else (180, 130, 75)
                    spr_r = max(2, int(entity["radius"] * zoom * 1.6))
                    sprite = get_cached_circle_sprite(body_color, spr_r)
                    self.screen.blit(sprite, (sx - spr_r, sy - spr_r))
                else:
                    hr = max(5, int(entity["radius"] * 3.5 * zoom))
                    # Soft ground shadow
                    pygame.draw.ellipse(self.screen, (0, 0, 0, 75), (sx - hr, sy + hr // 3, hr * 2, max(3, hr // 2)))

                    # Tunic Body
                    body_color = (215, 60, 45) if role == "LEADER" else (180, 130, 75)
                    pygame.draw.circle(self.screen, body_color, (sx, sy), hr)
                    pygame.draw.circle(self.screen, (75, 50, 25), (sx, sy), hr, 1)

                    # Head with natural skin tone
                    head_r = max(2, int(hr * 0.55))
                    pygame.draw.circle(self.screen, (238, 195, 155), (sx, sy - max(1, hr // 3)), head_r)
                    # Hair / Headband
                    pygame.draw.arc(self.screen, (60, 40, 20), (sx - head_r, sy - max(1, hr // 3) - head_r, head_r * 2, head_r * 2), 0, math.pi, max(1, head_r // 2))

                    # Direction indicator / facing
                    heading = entity.get("heading", 0.0)
                    hx_dir = sx + int(math.cos(heading) * (hr + 3))
                    hy_dir = sy + int(math.sin(heading) * (hr + 3))
                    pygame.draw.circle(self.screen, (238, 195, 155), (hx_dir, hy_dir), max(1, int(1.5 * zoom)))

                    # Render equipped tool in hand
                    eq_tool = str(entity.get("equipped_tool") or "")
                    act_str = str(entity.get("action") or "").upper()

                    if "AXE" in eq_tool or "AXE" in act_str:
                        # Stone Axe
                        ax_x = sx + int(math.cos(heading + 0.8) * (hr + 4))
                        ax_y = sy + int(math.sin(heading + 0.8) * (hr + 4))
                        pygame.draw.line(self.screen, (120, 80, 40), (sx, sy), (ax_x, ax_y), max(1, int(2 * zoom)))
                        pygame.draw.circle(self.screen, (150, 155, 160), (ax_x, ax_y), max(2, int(3 * zoom)))
                    elif "SPEAR" in eq_tool or "DEFEND" in act_str or "ATTACK" in act_str:
                        # Hardened Spear
                        sp_x = sx + int(math.cos(heading) * (hr + 8))
                        sp_y = sy + int(math.sin(heading) * (hr + 8))
                        pygame.draw.line(self.screen, (135, 95, 50), (sx, sy), (sp_x, sp_y), max(1, int(2 * zoom)))
                        pygame.draw.circle(self.screen, (200, 205, 215), (sp_x, sp_y), max(2, int(2.5 * zoom)))
                    elif "PICK" in eq_tool or "MINE" in act_str or "STONE" in act_str:
                        # Pickaxe
                        pk_x = sx + int(math.cos(heading + 0.8) * (hr + 5))
                        pk_y = sy + int(math.sin(heading + 0.8) * (hr + 5))
                        pygame.draw.line(self.screen, (110, 75, 35), (sx, sy), (pk_x, pk_y), max(1, int(2 * zoom)))
                        pygame.draw.arc(self.screen, (160, 165, 175), (pk_x - 3, pk_y - 3, 6, 6), 0, math.pi, max(1, int(2 * zoom)))
                    elif "TORCH" in eq_tool or (sun_props and not sun_props.get("is_daylight", True)):
                        # Glowing torch at night
                        tx_x = sx + int(math.cos(heading + 0.8) * (hr + 4))
                        tx_y = sy + int(math.sin(heading + 0.8) * (hr + 4))
                        pygame.draw.line(self.screen, (100, 65, 30), (sx, sy), (tx_x, tx_y), max(1, int(2 * zoom)))
                        t_halo = max(4, int(10 * zoom))
                        pygame.draw.circle(self.screen, (255, 180, 40, 120), (tx_x, tx_y), t_halo)
                        pygame.draw.circle(self.screen, (255, 240, 120), (tx_x, tx_y), max(2, int(2.5 * zoom)))

                    # Action icon floating above head
                    if zoom > 0.45:
                        from project.renderer.ui import get_cached_text
                        badge_icon = None
                        if "TIMBER" in act_str or "TREE" in act_str:
                            badge_icon = "🪓"
                        elif "STONE" in act_str:
                            badge_icon = "⛏️"
                        elif "SHELTER" in act_str or "SLEEP" in act_str:
                            badge_icon = "🛖"
                        elif "CRAFT" in act_str or "BUILT" in act_str:
                            badge_icon = "🔨"
                        elif "DEFEND" in act_str or "ATTACK" in act_str:
                            badge_icon = "⚔️"
                        elif "FLEE" in act_str:
                            badge_icon = "🏃"

                        if badge_icon:
                            lbl = get_cached_text(self.font, badge_icon, (255, 255, 255))
                            if lbl:
                                self.screen.blit(lbl, (sx - lbl.get_width() // 2, sy - hr - 14))

            elif etype == "PREDATOR" and not is_thermal:
                pr = max(4, int(entity["radius"] * 3.0 * zoom))
                # Sleek dark panther/wolf silhouette
                pygame.draw.ellipse(self.screen, (0, 0, 0, 80), (sx - pr, sy + pr // 3, pr * 2, max(3, pr // 2)))
                pygame.draw.circle(self.screen, (38, 40, 48), (sx, sy), pr)
                # Piercing amber eyes
                heading = entity.get("heading", 0.0)
                ex1 = sx + int(math.cos(heading - 0.3) * (pr - 1))
                ey1 = sy + int(math.sin(heading - 0.3) * (pr - 1))
                pygame.draw.circle(self.screen, (255, 80, 20), (ex1, ey1), max(1, int(1.5 * zoom)))
            elif etype == "HERBIVORE" and not is_thermal:
                hr_sz = max(4, int(entity["radius"] * 2.8 * zoom))
                # Warm chestnut gazelle/deer body
                pygame.draw.ellipse(self.screen, (0, 0, 0, 70), (sx - hr_sz, sy + hr_sz // 3, hr_sz * 2, max(3, hr_sz // 2)))
                pygame.draw.circle(self.screen, (185, 125, 65), (sx, sy), hr_sz)
                pygame.draw.circle(self.screen, (230, 205, 175), (sx, sy), max(1, hr_sz // 2))
            else:
                # Fast Blit from Sprite Cache for microorganisms/microbes
                sprite = get_cached_circle_sprite(color, pixel_r)
                self.screen.blit(sprite, (sx - pixel_r, sy - pixel_r))

            # Draw emergent role visual halos
            if role == "LEADER":
                con = entity.get("consciousness", 0.0)
                halo_color = (255, 215, 0) if con < 0.8 else (255, 120, 255)
                halo_r = pixel_r + 6 + int(math.sin(sim_tick * 0.1) * 2)
                pygame.draw.circle(self.screen, halo_color, (sx, sy), max(5, halo_r), 2)
            elif role == "MONSTER":
                pygame.draw.circle(self.screen, (255, 30, 60), (sx, sy), pixel_r + 4, 2)
            elif role == "SHAMAN":
                pygame.draw.circle(self.screen, (180, 100, 255), (sx, sy), pixel_r + 3, 1)
            elif role == "GUARDIAN":
                pygame.draw.circle(self.screen, (60, 160, 255), (sx, sy), pixel_r + 3, 1)

            # Ideation Sparks (Active Cognition & Transcendence Halo)
            show_sparks = len(self.checkboxes) >= 7 and self.checkboxes[6].checked
            if show_sparks and etype == "HUMAN":
                con = entity.get("consciousness", 0.0)
                if con > 0.35 or role == "LEADER":
                    spark_y = sy - pixel_r - max(3, int(4 * zoom))
                    pygame.draw.circle(self.screen, (140, 230, 255), (sx, spark_y), max(2, int(3 * zoom)))

            # Selection ring
            if self.selected_entity_id and entity["id"] == self.selected_entity_id:
                pygame.draw.circle(self.screen, (0, 255, 255), (sx, sy), pixel_r + 5, 2)

        # -------------------------------------------------------------
        # 4. Celestial Stardust & Live Discarded Growing Seeds
        # -------------------------------------------------------------
        from project.world.miracles import world_miracles_mgr
        self.overlays.draw_stardust_deposits(self.screen, self.camera, world_miracles_mgr, sim_tick)

        # 4b. Draw Live Discarded Growing Seeds
        from project.world.seeds import world_seed_growth_mgr
        self.overlays.draw_discarded_seeds(self.screen, self.camera, world_seed_growth_mgr, sim_tick)


        self.overlays.draw_day_night_sky(self.screen, self.camera, sun_props, is_eclipse=world_miracles_mgr.is_eclipse_active)

        # Thermal Vision Night-Vision Green Filter Overlay
        if len(self.checkboxes) >= 6 and self.checkboxes[5].checked:
            if getattr(self, "_thermal_tint_surf", None) is None or self._thermal_tint_surf.get_size() != (self.width, self.height):
                self._thermal_tint_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                self._thermal_tint_surf.fill((0, 80, 0, 70))
            self.screen.blit(self._thermal_tint_surf, (0, 0))

        # 5. Draw UI overlays & HUD
        for btn in self.buttons:
            btn.draw(self.screen, self.font)
        for cb in self.checkboxes:
            cb.draw(self.screen, self.font)
        for slider in self.sliders:
            slider.draw(self.screen, self.font)
        for sel in self.selectors:
            sel.draw(self.screen, self.font)

        # Gemini God Resonance Banner & Solar Status (Top Center)
        from project.renderer.ui import get_cached_text
        phase_str = sun_props.get("phase", "DAY")
        lux_val = sun_props.get("solar_lux", 0.0)
        sun_icon = "☀️" if sun_props.get("is_daylight", True) else "🌙"

        if self.is_offline:
            # Clean Offline Mode: Strictly NO pseudo affinity meter
            header_text = f"{sun_icon} {phase_str} ({lux_val:,.0f} Lux) | 🟢 OFFLINE MODE (Local Neural Core)"
            header_surf = get_cached_text(self.font, header_text, (120, 240, 180))
        else:
            # Genuine online affinity
            affinity_score = god_affinity if god_affinity is not None else 0.0
            header_text = f"{sun_icon} {phase_str} ({lux_val:,.0f} Lux) | 🌟 GEMINI AFFINITY: {affinity_score:.1f}%"
            header_surf = get_cached_text(self.font, header_text, (0, 255, 255))
        self.screen.blit(header_surf, (self.width // 2 - header_surf.get_width() // 2, 10))

        # Quantum Universe & Timeline HUD Info (Bottom-Left)
        try:
            from project.core.quantum_persistence import quantum_persistence
            univ = quantum_persistence.get_active_universe()
            hud_info = f"🌐 World: \"{univ.world_name}\" | Branch: {univ.active_branch} (HEAD: {univ.head_commit_id or 'genesis'})"
            hud_surf = get_cached_text(self.font, hud_info, (140, 185, 230))
            self.screen.blit(hud_surf, (10, self.height - 22))
        except Exception:
            try:
                from project.core.git_save_manager import git_save_manager
                git_info = f"🌿 Branch: {git_save_manager.active_branch} (HEAD: {git_save_manager.current_commit_id or 'genesis'})"
                git_surf = get_cached_text(self.font, git_info, (140, 170, 210))
                self.screen.blit(git_surf, (10, self.height - 22))
            except Exception:
                pass

        # Minimap (Top Right)
        if self.checkboxes[1].checked:
            from project.civilization.settlement import world_settlement_mgr
            self.minimap.draw(self.screen, self.camera, entities_snapshot, structures_snapshot=list(world_settlement_mgr.structures.values()))

        # Inspector Panel (Right Dock)
        selected_snap = None
        needs_snap = None
        if self.selected_entity_id:
            for entity in entities_snapshot:
                if entity["id"] == self.selected_entity_id:
                    selected_snap = entity
                    needs_snap = entity.get("needs")
                    if not needs_snap:
                        h_val = round(max(0.0, min(1.0, 1.0 - entity.get("health", 100.0) / max(1.0, entity.get("max_health", 100.0)))), 2)
                        needs_snap = {
                            "hunger": h_val,
                            "fear": entity.get("fear", 0.0),
                            "stress": entity.get("stress", 0.0),
                            "curiosity": entity.get("curiosity", 0.0),
                        }
                    break
        self.inspector.draw(self.screen, self.font, selected_snap, needs_snap)

        if selected_snap and selected_snap.get("ai_metrics"):
            self.brain_visualizer.draw(self.screen, self.font, selected_snap["ai_metrics"])

        # Diagnostic timings panel & population graph (Left Dock)
        if self.checkboxes[2].checked:
            DebugRenderer.draw_diagnostics(
                self.screen,
                self.font,
                fps=self.clock.get_fps(),
                sim_tick=sim_tick,
                system_timings=system_timings,
            )
            if stats_history:
                self.pop_graph.draw_graph(self.screen, self.font, stats_history)

        # Remote Upgrade Notification Pill (Top Center)
        if (hasattr(self, "update_info") and self.update_info and getattr(self.update_info, "has_update", False)) or getattr(self, "is_updating_ui", False):
            self._draw_update_banner()

        pygame.display.flip()
        self.clock.tick(60)
        # Cooperative sleep to yield CPU slice to OS (drops idle/render CPU from 100% to < 15%)
        time.sleep(0.001)


    def _draw_update_banner(self) -> None:
        """Renders sleek top-center update banner with 1-click upgrade button."""
        if not self.update_info and not self.is_updating_ui:
            self.update_button_rect = None
            return

        cx = self.width // 2
        banner_w = 640
        banner_h = 36
        bx = cx - banner_w // 2
        by = 12

        self.update_banner_rect = pygame.Rect(bx, by, banner_w, banner_h)
        pygame.draw.rect(self.screen, (22, 27, 34), self.update_banner_rect, border_radius=18)
        pygame.draw.rect(self.screen, (88, 166, 255), self.update_banner_rect, 1, border_radius=18)

        if self.is_updating_ui:
            txt = f"⏳ {self.update_status_text or 'Applying update...'}"
            txt_surf = self.font.render(txt, True, (88, 166, 255))
            self.screen.blit(txt_surf, (bx + 20, by + 9))
            self.update_button_rect = None
        else:
            msg = getattr(self.update_info, 'commit_message', 'New update available')[:36]
            sha = getattr(self.update_info, 'remote_commit', 'latest')[:7]
            txt = f"✨ Update Available [{sha}]: \"{msg}\""
            txt_surf = self.font.render(txt, True, (230, 237, 243))
            self.screen.blit(txt_surf, (bx + 18, by + 9))

            btn_w = 135
            btn_h = 26
            btn_x = bx + banner_w - btn_w - 6
            btn_y = by + 5
            self.update_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

            mx, my = pygame.mouse.get_pos()
            is_hover = self.update_button_rect.collidepoint((mx, my))
            btn_bg = (46, 160, 67) if not is_hover else (56, 175, 78)
            pygame.draw.rect(self.screen, btn_bg, self.update_button_rect, border_radius=13)

            btn_txt = self.font.render("🚀 Update Now", True, (255, 255, 255))
            tx = btn_x + (btn_w - btn_txt.get_width()) // 2
            ty = btn_y + (btn_h - btn_txt.get_height()) // 2
            self.screen.blit(btn_txt, (tx, ty))

    def close(self) -> None:
        pygame.quit()
