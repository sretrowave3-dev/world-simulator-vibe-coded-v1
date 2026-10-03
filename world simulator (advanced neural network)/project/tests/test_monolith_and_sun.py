"""
project/tests/test_monolith_and_sun.py

Unit tests for the Cosmic Golden Monolith descent at 99+ Affinity,
Sun/Sunlight day-night diurnal simulation, and species ecological reactions.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
from project.entities.monolith import Monolith
from project.entities.human import Human
from project.entities.plant import Plant
from project.entities.predator import Predator
from project.entities.reptile import Reptile
from project.systems.gemini_system import GeminiSystem
from project.world.time import WorldTimeManager, Season
from project.core.scheduler import UpdateContext, SchedulerPhase
from project.world.vegetation import VegetationManager
from project.world.soil import SoilManager
from project.systems.vegetation_system import VegetationSystem
from project.systems.movement_system import MovementSystem
from project.ai.goals import ActiveGoal, GoalType


class TestMonolithAndSun(unittest.TestCase):

    def setUp(self) -> None:
        self.time_mgr = WorldTimeManager(seconds_per_day=120.0)

    def test_monolith_sanctuary_aura(self) -> None:
        monolith = Monolith(
            entity_id="gemini_golden_monolith",
            species_id="monolith",
            pos_x=500.0,
            pos_y=500.0,
        )

        human = Human(entity_id="h1", species_id="homo_sapiens", pos_x=520.0, pos_y=520.0, max_health=100.0, health=50.0)
        human.intelligence_quotient = 120.0
        human.custom_data["stress"] = 0.8

        plant = Plant(entity_id="p1", species_id="fern", pos_x=510.0, pos_y=510.0, max_health=100.0, health=60.0, energy=50.0)
        predator = Predator(entity_id="pred1", species_id="panther", pos_x=530.0, pos_y=530.0)
        predator.custom_data["ambush_mode"] = True

        entities = [monolith, human, plant, predator]
        stats = monolith.apply_sanctuary_aura(entities, current_tick=100)

        self.assertEqual(stats["humans_blessed"], 1)
        self.assertEqual(stats["plants_vitalized"], 1)
        self.assertEqual(stats["threats_calmed"], 1)

        # Human health, stress, and IQ improvements
        self.assertGreater(human.health, 50.0)
        self.assertLess(human.custom_data["stress"], 0.8)
        self.assertGreater(human.intelligence_quotient, 120.0)

        # Plant growth
        self.assertGreater(plant.health, 60.0)
        self.assertGreater(plant.energy, 50.0)

        # Predator pacified
        self.assertFalse(predator.custom_data["ambush_mode"])

    def test_gemini_affinity_monolith_descent(self) -> None:
        leader = Human(entity_id="lead1", species_id="homo_sapiens", pos_x=400.0, pos_y=400.0)
        leader.custom_data["emergent_role"] = "LEADER"

        entities = [leader]
        gemini_sys = GeminiSystem(entities_list=entities, communion_interval_ticks=1)
        gemini_sys.global_god_affinity = 99.5  # Reached 99+

        context = UpdateContext(
            tick=10,
            delta_time=0.1,
            simulation_time=1.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
            time_snapshot=self.time_mgr.get_snapshot(),
        )

        gemini_sys.update(context)

        # Monolith should now be spawned in entities
        self.assertTrue(gemini_sys.monolith_spawned)
        spawned_monoliths = [e for e in entities if isinstance(e, Monolith)]
        self.assertEqual(len(spawned_monoliths), 1)
        self.assertEqual(spawned_monoliths[0].entity_id, "gemini_golden_monolith")

    def test_sun_properties_day_night_phases(self) -> None:
        # Midnight (0.0s)
        self.time_mgr.total_seconds = 0.0
        props = self.time_mgr.get_sun_properties()
        self.assertEqual(props["phase"], "NIGHT")
        self.assertFalse(props["is_daylight"])
        self.assertAlmostEqual(props["solar_lux"], 0.0, delta=100.0)

        # Dawn / Sunrise (30.0s / 120s = 0.25)
        self.time_mgr.total_seconds = 30.0
        props = self.time_mgr.get_sun_properties()
        self.assertEqual(props["phase"], "DAWN")
        self.assertTrue(props["is_daylight"])
        self.assertGreater(props["solar_lux"], 1000.0)

        # Midday Noon (60.0s / 120s = 0.50)
        self.time_mgr.total_seconds = 60.0
        props = self.time_mgr.get_sun_properties()
        self.assertEqual(props["phase"], "MIDDAY")
        self.assertTrue(props["is_daylight"])
        self.assertGreater(props["solar_lux"], 50000.0)

        # Sunset / Dusk (88.0s / 120s = 0.733)
        self.time_mgr.total_seconds = 88.0
        props = self.time_mgr.get_sun_properties()
        self.assertEqual(props["phase"], "DUSK")

    def test_vegetation_sunlight_photosynthesis(self) -> None:
        veg_mgr = VegetationManager()
        soil_mgr = SoilManager()
        plant = Plant(entity_id="p1", species_id="wheat", pos_x=50.0, pos_y=50.0, max_energy=200.0, energy=100.0)
        entities = [plant]

        veg_sys = VegetationSystem(veg_mgr, soil_mgr, entities)

        # Test Daytime Photosynthesis (Noon)
        self.time_mgr.total_seconds = 60.0
        context_day = UpdateContext(
            tick=1,
            delta_time=1.0,
            simulation_time=1.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
            time_snapshot=self.time_mgr.get_snapshot(),
        )
        veg_sys.update(context_day)
        self.assertGreater(plant.energy, 80.0)

    def test_movement_ectotherm_solar_basking(self) -> None:
        reptile = Reptile(entity_id="rep1", species_id="viper", pos_x=100.0, pos_y=100.0)
        entities = [reptile]
        move_sys = MovementSystem(entities)

        # Daytime Midday: Solar Basking
        self.time_mgr.total_seconds = 60.0
        context_day = UpdateContext(
            tick=1,
            delta_time=0.1,
            simulation_time=1.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
            time_snapshot=self.time_mgr.get_snapshot(),
        )
        reptile.body_temperature_c = 25.0
        move_sys.update(context_day)
        self.assertGreater(reptile.body_temperature_c, 25.0)


if __name__ == "__main__":
    unittest.main()
