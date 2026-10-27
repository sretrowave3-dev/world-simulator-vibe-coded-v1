"""
project/tests/test_gpu_and_modern_graphics.py

Unit and integration tests for:
- Dedicated GPU Detection & Classification (NVIDIA / AMD / Intel)
- GPU Acceleration Enabler (Windows UserGpuPreferences & OS environment variables)
- GPU Safety Guards (Short-term FPS clamp, cooperative sleep, long-term thermal throttle, VRAM budget)
- Python PATH Verification & Registration
- Modern Graphics Engine (Photorealistic textures, river canyon gorge, whitewater rapids, and directional shadows)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import pygame

# Set dummy video driver for headless test execution
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from project.core.gpu_manager import GPUManager, GPUInfo, GPUSafetyStatus, gpu_mgr
from project.renderer.texture_baker import ensure_baked_textures, make_seamless
from project.renderer.overlays import OverlayRenderer
from project.world.terrain import TerrainManager


class TestGPUAndModernGraphics(unittest.TestCase):

    def setUp(self):
        self.gpu_mgr = GPUManager.get_instance()

    def test_gpu_hardware_scanning_and_classification(self):
        """Verifies that scan_hardware identifies GPUs and correctly classifies dedicated vs integrated."""
        gpus = self.gpu_mgr.scan_hardware(force_refresh=True)
        self.assertIsInstance(gpus, list)
        self.assertGreater(len(gpus), 0, "At least one GPU/display adapter should be detected on host.")

        # Check if dedicated GPU is found
        has_dgpu = self.gpu_mgr.has_dedicated_gpu()
        if has_dgpu:
            dg = self.gpu_mgr.dedicated_gpu
            self.assertIsNotNone(dg)
            self.assertTrue(dg.is_dedicated)
            self.assertIn(dg.vendor, ("NVIDIA", "AMD", "Intel"))
            self.assertGreater(dg.vram_mb, 1024, "Dedicated GPU should have > 1GB VRAM")
            summary = self.gpu_mgr.get_gpu_summary()
            self.assertIn("DEDICATED", summary)

    def test_gpu_enabler_and_windows_preferences(self):
        """Tests that enable_dedicated_gpu sets Windows registry and acceleration environment variables."""
        success, message = self.gpu_mgr.enable_dedicated_gpu()
        if self.gpu_mgr.has_dedicated_gpu():
            self.assertTrue(success)
            self.assertIn("Dedicated GPU Enabled", message)
            self.assertEqual(os.environ.get("SHIM_MCCOMPAT"), "0x800000001")
            self.assertEqual(os.environ.get("__NV_PRIME_RENDER_OFFLOAD"), "1")
            self.assertEqual(os.environ.get("PYGAME_DEDICATED_GPU"), "1")

    def test_python_in_path_verification(self):
        """Verifies that check_python_in_path accurately inspects system PATH."""
        in_path, current_path, py_dir = self.gpu_mgr.check_python_in_path()
        self.assertIsInstance(in_path, bool)
        self.assertIsInstance(py_dir, str)
        self.assertTrue(os.path.exists(py_dir))

    def test_gpu_safety_guards_and_thermal_throttling(self):
        """Verifies frame capping, cooperative yielding, thermal tripwires, and fallback."""
        safety = self.gpu_mgr.safety
        self.assertEqual(safety.target_fps, 60, "Default target FPS should be 60 to prevent coil whine and surges.")
        self.assertEqual(safety.cooperative_sleep_ms, 1.0)
        self.assertFalse(safety.fallback_active)

        # Test frame safety enforcement with mock clock
        mock_clock = MagicMock()
        mock_clock.tick.return_value = 16.6
        dt = self.gpu_mgr.enforce_frame_safety(mock_clock)
        mock_clock.tick.assert_called_with(60)

        # Test thermal tripwires simulation
        with patch("subprocess.run") as mock_sub:
            # Simulate high temperature (88°C critical)
            mock_sub.return_value = MagicMock(returncode=0, stdout="88.0, 35.0")
            status = self.gpu_mgr.check_thermal_health()
            if self.gpu_mgr.dedicated_gpu and self.gpu_mgr.dedicated_gpu.vendor == "NVIDIA":
                self.assertEqual(status.thermal_status, "CRITICAL")
                self.assertEqual(status.target_fps, 30, "Should throttle to 30 FPS under critical temperature.")

            # Simulate recovery (65°C normal)
            mock_sub.return_value = MagicMock(returncode=0, stdout="65.0, 15.0")
            status = self.gpu_mgr.check_thermal_health()
            if self.gpu_mgr.dedicated_gpu and self.gpu_mgr.dedicated_gpu.vendor == "NVIDIA":
                self.assertEqual(status.thermal_status, "NORMAL")
                self.assertEqual(status.target_fps, 60, "Should restore 60 FPS when cooled.")

        # Test VRAM budget tracking
        self.gpu_mgr.update_vram_usage(64.5)
        self.assertAlmostEqual(self.gpu_mgr.safety.vram_estimated_used_mb, 64.5)

        # Test fail-safe software fallback
        self.gpu_mgr.fallback_to_software_renderer("Device context test")
        self.assertTrue(self.gpu_mgr.safety.fallback_active)
        self.assertEqual(self.gpu_mgr.safety.target_fps, 30)

    def test_modern_photorealistic_textures(self):
        """Verifies that high-definition textures matching reference assets are baked and loadable."""
        textures = ensure_baked_textures()
        self.assertIn("grass_photoreal", textures, "Photorealistic grass texture must be baked.")
        self.assertIn("river_water", textures, "Glacial azure river water texture must be baked.")
        self.assertIn("river_rock", textures, "Dark canyon gorge rock texture must be baked.")
        self.assertIn("river_foam", textures, "Rapids foam texture must be baked.")

        # Check dimensions and format
        g_tex = textures["grass_photoreal"]
        self.assertIn(g_tex.get_size(), [(128, 128), (256, 256)])
        r_water = textures["river_water"]
        self.assertIn(r_water.get_size(), [(128, 128), (256, 256)])

    def test_overlay_renderer_modern_terrain_generation(self):
        """Verifies that OverlayRenderer generates seamless chunks with river canyon gorge and rapids."""
        ov = OverlayRenderer()
        tm = TerrainManager(seed=42)

        # Chunk with river at (5, 10)
        chunk_surf = ov._get_chunk_surface(5, 10, tm)
        self.assertIsNotNone(chunk_surf)
        self.assertEqual(chunk_surf.get_size(), (ov.CHUNK_TEX_RES, ov.CHUNK_TEX_RES))
        self.assertIn((5, 10), ov._river_chunks, "River presence must be indexed for dynamic rapids rendering.")

        # Test overview satellite atlas
        overview = ov._get_overview_surface(tm)
        self.assertIsNotNone(overview)
        self.assertEqual(overview.get_size(), (ov._overview_res, ov._overview_res))

        # Test vignette rendering
        test_screen = pygame.Surface((800, 600))
        ov.draw_vignette(test_screen)
        self.assertIsNotNone(ov._vignette_surface)


    def test_full_frame_render_with_shadows_and_vignette(self):
        """Verifies that SimulationRenderer.render() executes completely with entities, shadows, and vignette."""
        from project.renderer.renderer import SimulationRenderer
        from project.ai.pheromone import PheromoneGrid
        from project.world.time import WorldTimeManager

        renderer = SimulationRenderer(width=800, height=600, world_width=4000.0, world_height=4000.0)
        tm = TerrainManager(seed=42)
        grid = PheromoneGrid(width=100, height=100, cell_size=16.0)
        time_mgr = WorldTimeManager()

        sample_entities = [
            {"id": "h1", "type": "HUMAN", "species_id": "homo_sapiens", "x": 400.0, "y": 300.0, "radius": 4.0, "is_alive": True, "role": "LEADER", "heading": 0.5},
            {"id": "p1", "type": "PREDATOR", "species_id": "panther", "x": 450.0, "y": 320.0, "radius": 5.0, "is_alive": True, "heading": 1.2},
            {"id": "b1", "type": "HERBIVORE", "species_id": "gazelle", "x": 380.0, "y": 280.0, "radius": 3.5, "is_alive": True, "heading": -0.8},
        ]

        # Execute render frame with zoom calculation, directional shadows, and vignette
        renderer.render(
            entities_snapshot=sample_entities,
            terrain_manager=tm,
            pheromone_grid=grid,
            system_timings={},
            sim_tick=15,
            stats_history=[],
            time_manager=time_mgr,
            god_affinity=50.0,
        )
        self.assertIsNotNone(renderer.overlays._vignette_surface)
        renderer.close()


if __name__ == "__main__":
    unittest.main()
