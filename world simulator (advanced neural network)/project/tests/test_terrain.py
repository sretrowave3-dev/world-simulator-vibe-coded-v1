"""
tests/test_terrain.py

Unit and integration tests for Terrain, Biomes, and Soil/Water/Vegetation subsystems.
"""

import unittest
from project.world.terrain import TerrainManager, BiomeType as TerrainBiomeType
from project.world.biomes import BiomeClassifier, BiomeType, BIOME_CATALOG
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager, ResourceType
from project.world.time import WorldTimeManager


class TestTerrainSubsystems(unittest.TestCase):

    def test_terrain_manager_initialization(self):
        manager = TerrainManager(seed=42)
        tile = manager.get_tile(10, 10)
        self.assertIsNotNone(tile)
        self.assertTrue(0.0 <= tile.height <= 1.0)
        self.assertIsInstance(tile.biome, TerrainBiomeType)

    def test_biome_classification(self):
        # Ocean elevation
        biome = BiomeClassifier.classify(elevation=0.1, temperature_c=15.0, moisture=0.8)
        self.assertEqual(biome, BiomeType.DEEP_OCEAN)

        # Desert
        biome_desert = BiomeClassifier.classify(elevation=0.5, temperature_c=35.0, moisture=0.1)
        self.assertEqual(biome_desert, BiomeType.DESERT)

        # Rainforest
        biome_rainforest = BiomeClassifier.classify(elevation=0.5, temperature_c=25.0, moisture=0.85)
        self.assertEqual(biome_rainforest, BiomeType.RAINFOREST)

    def test_soil_nutrients_and_mineralization(self):
        soil_mgr = SoilManager()
        profile = soil_mgr.query_soil(5.0, 5.0)
        self.assertAlmostEqual(profile.nitrogen, 0.5)

        # Deposit organic matter and tick
        chunk = soil_mgr.get_or_create_chunk((0, 0))
        chunk.deposit_organic_matter(5, 5, mass_kg=10.0)
        chunk.tick_decomposition(dt=1.0, temperature_c=25.0)

        updated_profile = soil_mgr.query_soil(5.0, 5.0)
        self.assertGreater(updated_profile.nitrogen, 0.5)

    def test_water_hydrology_and_thirst(self):
        water_mgr = WaterManager()
        chunk = water_mgr.get_or_create_chunk((0, 0))
        idx = 5 * 16 + 5
        chunk.depth[idx] = 1.0
        chunk.salinity[idx] = 0.0
        chunk.purity[idx] = 1.0

        state = water_mgr.query_water(5.0, 5.0)
        self.assertTrue(state.is_drinkable)

        # Drink water
        liters_drank, toxicity = chunk.drink(5, 5, volume_liters=50.0)
        self.assertAlmostEqual(liters_drank, 50.0)
        self.assertEqual(toxicity, 0.0)

    def test_resource_spawning_and_harvest(self):
        res_mgr = ResourceManager(seed=1337)
        node = res_mgr.spawn_node(ResourceType.WOOD, x=20.0, y=20.0, capacity=500.0)
        self.assertEqual(node.quantity, 500.0)

        harvested = node.harvest(50.0)
        self.assertEqual(harvested, 50.0)
        self.assertEqual(node.quantity, 450.0)

        nearest = res_mgr.find_nearest_resource(x=21.0, y=20.0, resource_type=ResourceType.WOOD)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest[0].node_id, node.node_id)


if __name__ == "__main__":
    unittest.main()
