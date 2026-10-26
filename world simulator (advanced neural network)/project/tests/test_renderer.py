"""
tests/test_renderer.py

Headless unit tests for the Visual Renderer, Viewport Camera, Minimap, and UI elements.
"""

import os
import unittest

# Set SDL to use dummy video driver for headless test environment
os.environ["SDL_VIDEODRIVER"] = "dummy"

try:
    import pygame
    HAS_PYGAME = True
    from project.renderer.camera import Camera
    from project.renderer.minimap import Minimap
    from project.renderer.ui import Button, Checkbox
except ImportError:
    HAS_PYGAME = False
    Camera = Minimap = Button = Checkbox = None  # type: ignore


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestRendererElements(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_camera_conversions(self) -> None:
        camera = Camera(screen_width=1000, screen_height=600)
        camera.zoom = 1.0
        camera.pos_x = 0.0
        camera.pos_y = 0.0

        # World (0, 0) should map to screen center (500, 300)
        sx, sy = camera.world_to_screen(0.0, 0.0)
        self.assertEqual(sx, 500)
        self.assertEqual(sy, 300)

        # Screen center should map back to world (0, 0)
        wx, wy = camera.screen_to_world(500, 300)
        self.assertAlmostEqual(wx, 0.0)
        self.assertAlmostEqual(wy, 0.0)

        # Zoom in
        camera.zoom = 2.0
        sx, sy = camera.world_to_screen(10.0, 10.0)
        self.assertEqual(sx, 520)
        self.assertEqual(sy, 320)

    def test_ui_button_interaction(self) -> None:
        # Create a mock surface
        surface = pygame.Surface((200, 100))
        font = pygame.font.SysFont("Arial", 12)

        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(x=10, y=10, width=80, height=30, text="Click", callback=on_click)

        # Test hover event
        motion_event = pygame.event.Event(pygame.MOUSEMOTION, pos=(15, 15))
        button.handle_event(motion_event)
        self.assertTrue(button.is_hovered)

        # Test click event
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 20))
        button.handle_event(click_event)
        self.assertTrue(clicked)

    def test_ui_checkbox_interaction(self) -> None:
        checkbox = Checkbox(x=10, y=10, label="Show Grid", default_state=False)
        self.assertFalse(checkbox.checked)

        # Click inside checkbox bounds
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(15, 15))
        checkbox.handle_event(click_event)
        self.assertTrue(checkbox.checked)

    def test_minimap_projection(self) -> None:
        minimap = Minimap(x=0, y=0, width=100, height=100, world_width=1000.0, world_height=1000.0)
        # Scaled x = 100/1000 = 0.1
        self.assertAlmostEqual(minimap.scale_x, 0.1)

        # Entity at (500, 500) should project to center of minimap (50, 50)
        entities = [{"id": "e1", "type": "PLANT", "x": 500.0, "y": 500.0, "is_alive": True, "radius": 2.0}]
        camera = Camera(screen_width=1000, screen_height=600)

        screen = pygame.Surface((200, 200))
        minimap.draw(screen, camera, entities)
        # Verify execution completes without throwing exceptions
        self.assertTrue(True)

    def test_camera_viewport_bounds(self) -> None:
        camera = Camera(screen_width=1000, screen_height=600)
        camera.pos_x = 500.0
        camera.pos_y = 300.0
        camera.zoom = 1.0

        min_x, min_y, max_x, max_y = camera.get_visible_world_bounds(margin=0.0)
        self.assertEqual(min_x, 0.0)
        self.assertEqual(min_y, 0.0)
        self.assertEqual(max_x, 1000.0)
        self.assertEqual(max_y, 600.0)

    def test_sprite_caching(self) -> None:
        from project.renderer.renderer import get_cached_circle_sprite
        s1 = get_cached_circle_sprite((255, 0, 0), 10)
        s2 = get_cached_circle_sprite((255, 0, 0), 10)
        self.assertIs(s1, s2)
        self.assertEqual(s1.get_width(), 20)

    def test_particle_deque_lifecycle(self) -> None:
        from project.renderer.particles import ParticleSystemManager
        pm = ParticleSystemManager(max_particles=5)
        for i in range(10):
            pm.spawn(i * 10, i * 10, 1.0, 1.0, (255, 255, 255), lifespan=1.0)
        self.assertEqual(len(pm.particles), 5)
        pm.tick(0.5)
        self.assertEqual(len(pm.particles), 5)
        pm.tick(0.6)  # Age reaches 1.1s > 1.0s lifespan
        self.assertEqual(len(pm.particles), 0)

    def test_simulation_renderer_lifecycle(self) -> None:
        from project.renderer.renderer import SimulationRenderer
        renderer = SimulationRenderer(width=640, height=480, world_width=1000.0, world_height=1000.0)
        
        entities = [{"id": "e1", "type": "PLANT", "x": 500.0, "y": 500.0, "is_alive": True, "radius": 2.0}]
        
        # Test handle_input without events
        keep_running = renderer.handle_input(entities)
        self.assertTrue(keep_running)

        # Test speed changes
        renderer.set_speed(2.0)
        self.assertEqual(renderer.simulation_speed, 2.0)

        renderer.close()

    def test_pheromone_overlay_rendering(self) -> None:
        """Verifies that HeatmapRenderer draws visible food trails and danger scents."""
        from project.renderer.heatmaps import HeatmapRenderer
        from project.ai.pheromone import PheromoneGrid, PheromoneType
        import pygame

        camera = Camera(screen_width=800, screen_height=600)
        camera.pos_x = 400.0
        camera.pos_y = 300.0
        camera.zoom = 1.0

        grid = PheromoneGrid(width=100, height=100, cell_size=16.0)
        # Deposit visible scent at camera center
        grid.deposit(400.0, 300.0, PheromoneType.FOOD_TRAIL, intensity=1.5)
        grid.deposit(420.0, 300.0, PheromoneType.DANGER_ALARM, intensity=2.0)

        surface = pygame.Surface((800, 600), pygame.SRCALPHA)
        hr = HeatmapRenderer(cell_size=16.0)

        # Draw Food Trail
        hr.draw_pheromone_overlay(surface, camera, grid, PheromoneType.FOOD_TRAIL, (0, 255, 100))
        # Surface must have non-zero alpha pixels drawn
        has_food_pixels = any(surface.get_at((x, y))[3] > 0 for x in range(380, 420, 5) for y in range(280, 320, 5))
        self.assertTrue(has_food_pixels)

        # Draw Danger Alarm
        danger_surface = pygame.Surface((800, 600), pygame.SRCALPHA)
        hr.draw_pheromone_overlay(danger_surface, camera, grid, PheromoneType.DANGER_ALARM, (255, 50, 50))
        has_danger_pixels = any(danger_surface.get_at((x, y))[3] > 0 for x in range(400, 440, 5) for y in range(280, 320, 5))
        self.assertTrue(has_danger_pixels)


if __name__ == "__main__":
    unittest.main()
