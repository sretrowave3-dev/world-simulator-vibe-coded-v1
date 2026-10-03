"""
tests/test_weather.py

Unit tests for Weather and Disasters subsystems.
"""

import unittest
from project.world.weather import WeatherManager, AtmosphericGrid, ChunkData, ThermalConfig
from project.world.disasters import DisasterManager, DisasterConfig, HazardType


class TestWeatherAndDisasters(unittest.TestCase):

    def test_weather_pipeline_execution(self):
        chunks = [
            ChunkData(chunk_id=0, latitude=45.0, longitude=-73.0, elevation=100.0),
            ChunkData(chunk_id=1, latitude=10.0, longitude=-73.0, elevation=10.0),
        ]
        grid = AtmosphericGrid(chunks)
        manager = WeatherManager(grid)

        # Run 5 ticks
        for _ in range(5):
            manager.update(dt=0.1)

        temp_c = grid.sample_temperature_bilinear(2.0, 2.0, chunk_id=0)
        self.assertIsInstance(temp_c, float)
        self.assertGreater(manager.stats.mean_pressure, 900.0)

    def test_disaster_manager_lifecycle(self):
        config = DisasterConfig(master_seed=42)
        disaster_mgr = DisasterManager(config)

        # Load chunk
        disaster_mgr.load_chunk((0, 0))
        self.assertIn((0, 0), disaster_mgr.domain.active_chunks)

        # Tick disaster simulation
        disaster_mgr.tick(dt=0.05)

        # Query hazards
        buf = [0] * 256
        count = disaster_mgr.query_hazards((0, 0), buf)
        self.assertEqual(count, 256)

        # Snapshot
        snapshot = disaster_mgr.create_snapshot()
        self.assertIsNotNone(snapshot)
        self.assertEqual(len(snapshot.active_chunk_coords), 1)

        # Unload chunk
        disaster_mgr.unload_chunk((0, 0))
        self.assertNotIn((0, 0), disaster_mgr.domain.active_chunks)


if __name__ == "__main__":
    unittest.main()
