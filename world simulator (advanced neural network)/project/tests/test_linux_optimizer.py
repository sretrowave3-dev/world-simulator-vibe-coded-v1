"""
project/tests/test_linux_optimizer.py

Unit tests for LinuxPlatformOptimizer, /dev/shm shared memory cache,
GLIBC malloc trimming, CPU core affinity, and vectorized pheromone diffusion.
"""

import os
import sys
import tempfile
import unittest
from project.core.linux_optimizer import LinuxPlatformOptimizer, linux_optimizer
from project.core.cache_bridge import bridge_hub
from project.ai.pheromone import PheromoneGrid, PheromoneType


class TestLinuxOptimizer(unittest.TestCase):

    def test_optimizer_singleton_and_detection(self) -> None:
        opt = LinuxPlatformOptimizer()
        self.assertIs(opt, linux_optimizer)
        self.assertGreaterEqual(opt.total_cores, 1)
        self.assertIsInstance(opt.is_linux, bool)
        self.assertEqual(opt.is_linux, sys.platform.startswith("linux"))

    def test_thread_naming(self) -> None:
        res = linux_optimizer.set_thread_name("test-engine")
        if linux_optimizer.is_linux:
            self.assertTrue(res)

    def test_cpu_affinity(self) -> None:
        affinity = linux_optimizer.get_affinity()
        self.assertIsInstance(affinity, list)
        self.assertGreater(len(affinity), 0)
        
        # Test setting affinity to current cores
        if linux_optimizer.is_linux:
            success = linux_optimizer.set_thread_affinity([affinity[0]])
            self.assertTrue(success)
            # Restore all available cores
            linux_optimizer.set_thread_affinity(affinity)

    def test_malloc_trim(self) -> None:
        trim_res = linux_optimizer.malloc_trim(0)
        if linux_optimizer.is_linux:
            self.assertTrue(trim_res)
            self.assertGreater(linux_optimizer.trim_count, 0)
            self.assertGreater(linux_optimizer.last_trim_timestamp, 0.0)

    def test_optimized_cache_dir(self) -> None:
        cache_dir = linux_optimizer.get_optimized_cache_dir("test_echo_sim")
        self.assertTrue(os.path.exists(cache_dir))
        self.assertTrue(os.path.isdir(cache_dir))
        if linux_optimizer.is_linux and os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK):
            self.assertTrue(cache_dir.startswith("/dev/shm"))

    def test_posix_fadvise(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"0" * 1024)
            f.flush()
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                # Should execute without error
                linux_optimizer.posix_advise_sequential(f.fileno())
                linux_optimizer.posix_advise_willneed(f.fileno())
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_memory_telemetry(self) -> None:
        metrics = linux_optimizer.get_memory_telemetry()
        self.assertIn("platform", metrics)
        self.assertIn("total_cores", metrics)
        self.assertIn("active_cores", metrics)
        self.assertIn("vm_rss_kb", metrics)
        if linux_optimizer.is_linux:
            self.assertGreaterEqual(metrics["vm_rss_kb"], 0)

    def test_vectorized_pheromone_diffusion(self) -> None:
        grid = PheromoneGrid(width=32, height=32, cell_size=8.0, diffusion_rate=0.2)
        # Deposit at center (x=128, y=128) -> cell (16, 16)
        grid.deposit(128.0, 128.0, PheromoneType.FOOD_TRAIL, 50.0)
        
        initial_val = grid.sample(128.0, 128.0, PheromoneType.FOOD_TRAIL)
        self.assertAlmostEqual(initial_val, 50.0, delta=0.01)
        
        neighbor_initial = grid.sample(128.0 + 8.0, 128.0, PheromoneType.FOOD_TRAIL)
        self.assertEqual(neighbor_initial, 0.0)
        
        # Step diffusion
        grid.tick(dt=0.1)
        
        # Scent should have diffused to neighbor cell
        neighbor_after = grid.sample(128.0 + 8.0, 128.0, PheromoneType.FOOD_TRAIL)
        self.assertGreater(neighbor_after, 0.0)
        
        # Center should have decreased due to diffusion and decay
        center_after = grid.sample(128.0, 128.0, PheromoneType.FOOD_TRAIL)
        self.assertLess(center_after, initial_val)


if __name__ == "__main__":
    unittest.main()
