"""
project/tests/test_seeds_and_appetite.py

Unit tests for Appetite Foraging, Multi-Food Seeds, Live Growth, Abnormalities, and Discard Logging.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
import tempfile
import json

from project.entities.human import Human
from project.entities.herbivore import Herbivore
from project.entities.plant import Plant
from project.entities.predator import Predator
from project.systems.decision_system import DecisionSystem
from project.world.seeds import (
    world_seed_growth_mgr,
    seed_logger,
    SeedAbnormality,
    SeedGrowthManager,
    SeedLogManager,
)
from project.core.scheduler import UpdateContext


class TestSeedsAndAppetite(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp_log = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_log.close()
        self.custom_logger = SeedLogManager(log_path=self.tmp_log.name)
        self.growth_mgr = SeedGrowthManager()

    def tearDown(self) -> None:
        if os.path.exists(self.tmp_log.name):
            os.remove(self.tmp_log.name)

    def test_fruit_seed_generation_and_abnormalities(self) -> None:
        # Test Mango seed generation (1 large stone pit seed)
        mango_seeds = self.growth_mgr.generate_fruit_seeds(
            fruit_type="Mango",
            pos_x=100.0,
            pos_y=200.0,
            eater_id="human_1",
            eater_species="homo_sapiens",
            sim_tick=500,
        )
        self.assertEqual(len(mango_seeds), 1)
        self.assertEqual(mango_seeds[0].parent_fruit, "Mango")
        self.assertEqual(mango_seeds[0].dropped_by_entity_id, "human_1")

        # Test Cucumber seed generation (multiple seeds)
        cuc_seeds = self.growth_mgr.generate_fruit_seeds(
            fruit_type="Cucumber",
            pos_x=50.0,
            pos_y=50.0,
            eater_id="herbivore_1",
            eater_species="deer",
            sim_tick=501,
        )
        self.assertGreaterEqual(len(cuc_seeds), 8)
        self.assertEqual(cuc_seeds[0].parent_fruit, "Cucumber")

    def test_live_seed_growth_and_plant_spawning(self) -> None:
        entities = []
        seeds = self.growth_mgr.generate_fruit_seeds(
            fruit_type="Mango",
            pos_x=150.0,
            pos_y=150.0,
            eater_id="human_1",
            eater_species="homo_sapiens",
            sim_tick=100,
        )
        seed = seeds[0]
        seed.germination_speed = 1.0  # Fast test speed

        # Advance growth through Sprout -> Sapling (growth_delta = 1.0 * 1.0 * 0.8 * 0.5 = 0.40 >= 0.25 -> SPROUT)
        self.growth_mgr.update(dt=0.8, sim_tick=101, entities_list=entities)
        self.assertIn(seed.stage, ("SPROUT", "SAPLING"))

        # Complete growth to 100%
        self.growth_mgr.update(dt=3.0, sim_tick=102, entities_list=entities)
        self.assertTrue(seed.is_mature)
        self.assertEqual(seed.stage, "MATURE_PLANT")
        self.assertEqual(len(entities), 1)
        self.assertIsInstance(entities[0], Plant)
        self.assertEqual(entities[0].custom_data.get("parent_fruit"), "Mango")

    def test_appetite_and_active_foraging(self) -> None:
        # Create hungry human and mango food item nearby
        human = Human(entity_id="h1", species_id="homo_sapiens", pos_x=10.0, pos_y=10.0)
        human.energy = 40.0  # Acute hunger

        food = Plant(entity_id="f_mango", species_id="food_mango", pos_x=12.0, pos_y=10.0)
        food.custom_data["is_food"] = True
        food.custom_data["fruit_type"] = "mango"

        entities = [human, food]
        dec_sys = DecisionSystem(entities_list=entities)

        ctx = UpdateContext(
            tick=1000,
            delta_time=0.1,
            simulation_time=100.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
        )

        initial_seeds_count = len(world_seed_growth_mgr.active_seeds)
        dec_sys.update(ctx)

        # Human should have eaten the mango within 2m distance
        self.assertGreater(human.energy, 40.0)
        self.assertGreater(human.custom_data.get("dopamine", 0.0), 0.8)
        self.assertIn("EATING_", human.current_action)

        # Mango seeds discarded in world
        self.assertGreater(len(world_seed_growth_mgr.active_seeds), initial_seeds_count)

    def test_seed_log_manager_persistence(self) -> None:
        seeds = self.growth_mgr.generate_fruit_seeds(
            fruit_type="Cucumber",
            pos_x=300.0,
            pos_y=400.0,
            eater_id="h_tester",
            eater_species="homo_sapiens",
            sim_tick=1234,
        )
        self.custom_logger.log_seed_drop(
            eater_id="h_tester",
            eater_species="homo_sapiens",
            fruit_name="Cucumber",
            pos_x=300.0,
            pos_y=400.0,
            sim_tick=1234,
            seeds=seeds,
        )

        # Read back from log file
        with open(self.tmp_log.name, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[-1]["eater_id"], "h_tester")
        self.assertEqual(data[-1]["fruit_consumed"], "Cucumber")
        self.assertIn("seeds_detail", data[-1])


if __name__ == "__main__":
    unittest.main()
