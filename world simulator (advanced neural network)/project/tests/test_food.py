"""
tests/test_food.py

Unit tests for Planetary Food Ecology subsystem.
"""

import unittest
from project.world.food import (
    FoodManager,
    FoodChunkStore,
    LifecycleStage,
    ChunkEnvironmentContext,
)


class TestFoodSubsystem(unittest.TestCase):

    def test_food_spawning_and_lifecycle(self):
        food_mgr = FoodManager(world_seed=1337)

        # Spawn plant organism
        plant = food_mgr.spawn_organism(
            species_id=101,  # Apple Tree
            position=(10.0, 10.0, 0.0),
            stage=LifecycleStage.VEGETATIVE,
            biomass_kg=1.0,
        )

        self.assertEqual(plant.stage, LifecycleStage.VEGETATIVE)
        self.assertAlmostEqual(plant.biomass_kg, 1.0)

        # Nearest search
        found = food_mgr.find_nearest_food(x=12.0, y=10.0, max_radius=20.0)
        self.assertIsNotNone(found)
        self.assertEqual(found.food_id, plant.food_id)

    def test_food_consumption(self):
        food_mgr = FoodManager(world_seed=1337)

        fruit = food_mgr.spawn_organism(
            species_id=100,  # Apple fruit
            position=(5.0, 5.0, 0.0),
            stage=LifecycleStage.HARVESTABLE,
            biomass_kg=0.5,
        )

        initial_biomass = fruit.biomass_kg
        energy_acquired = food_mgr.consume_food(fruit.food_id, amount_kg=0.2)
        self.assertGreater(energy_acquired, 0.0)

        # Remaining biomass
        self.assertAlmostEqual(fruit.biomass_kg, initial_biomass - 0.2, places=3)


if __name__ == "__main__":
    unittest.main()
