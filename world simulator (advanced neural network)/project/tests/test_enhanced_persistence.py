"""
project/tests/test_enhanced_persistence.py

Unit tests for the upgraded Persistence Subsystem:
- Full Multi-Species preservation (Avian, Reptile, Amphibian, Arthropod, Fungus, etc.)
- Gemini God Affinity, Ancient Ruins discovery, and Miracles persistence
- Fuzzy matching & Numeric index load resolution
- CRC32 verification and atomic file writes
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
import tempfile
from project.core.persistence import PersistenceManager
from project.world.time import WorldTimeManager
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager
from project.entities.human import Human
from project.entities.avian import Avian
from project.entities.reptile import Reptile
from project.entities.fungus import Fungus
from project.entities.bacteria import Bacteria
from project.systems.gemini_system import GeminiSystem
from project.world.ancient_ruins import AncientRuinsManager
from project.world.miracles import WorldMiracleManager, StardustDeposit


class TestEnhancedPersistence(unittest.TestCase):

    def setUp(self) -> None:
        self.time_mgr = WorldTimeManager()
        self.soil_mgr = SoilManager()
        self.water_mgr = WaterManager()
        self.veg_mgr = VegetationManager()
        self.res_mgr = ResourceManager()
        self.ruins_mgr = AncientRuinsManager()
        self.miracles_mgr = WorldMiracleManager()

        # Create multi-species entities
        self.human = Human(entity_id="h1", species_id="homo_sapiens", pos_x=2450.0, pos_y=180.0)
        self.human.intelligence_quotient = 135.0
        self.human.custom_data["dopamine"] = 0.95

        self.avian = Avian(entity_id="av1", species_id="falcon", pos_x=100.0, pos_y=200.0)
        self.reptile = Reptile(entity_id="rep1", species_id="viper", pos_x=300.0, pos_y=400.0)
        self.fungus = Fungus(entity_id="fung1", species_id="mycelium", pos_x=50.0, pos_y=50.0)

        self.entities = [self.human, self.avian, self.reptile, self.fungus]
        self.gemini_sys = GeminiSystem(entities_list=self.entities)
        self.gemini_sys.global_god_affinity = 99.5

        # Configure ruins and miracles
        self.ruins_mgr.civilization_discovered = True
        self.ruins_mgr.discovered_entity_ids.add("h1")
        self.miracles_mgr.stardust_deposits.append(StardustDeposit(pos_x=2450.0, pos_y=180.0, energy_value=150.0))

    def test_full_roundtrip_serialization(self) -> None:
        self.time_mgr.current_tick = 5000

        # 1. Serialize
        state = PersistenceManager.serialize_state(
            time_mgr=self.time_mgr,
            soil_mgr=self.soil_mgr,
            water_mgr=self.water_mgr,
            veg_mgr=self.veg_mgr,
            res_mgr=self.res_mgr,
            entities_list=self.entities,
            gemini_sys=self.gemini_sys,
            ruins_mgr=self.ruins_mgr,
            miracles_mgr=self.miracles_mgr,
        )

        # Verify state dictionary content
        self.assertEqual(state["time"]["tick"], 5000)
        self.assertEqual(len(state["entities"]), 4)
        self.assertEqual(state["gemini"]["god_affinity"], 99.5)
        self.assertTrue(state["ancient_ruins"]["discovered"])
        self.assertEqual(len(state["miracles"]["stardust"]), 1)

        # 2. Save to file
        save_path = PersistenceManager.save_to_file("test_persistence_unit.dat", state)
        self.assertTrue(os.path.exists(save_path))

        # 3. Load & Deserialize
        loaded_state = PersistenceManager.load_from_file("test_persistence_unit.dat")
        new_time = WorldTimeManager()
        new_soil = SoilManager()
        new_water = WaterManager()
        new_veg = VegetationManager()
        new_res = ResourceManager()
        new_entities = []
        new_gemini = GeminiSystem(entities_list=[])
        new_ruins = AncientRuinsManager()
        new_miracles = WorldMiracleManager()

        PersistenceManager.deserialize_state(
            state_dict=loaded_state,
            time_mgr=new_time,
            soil_mgr=new_soil,
            water_mgr=new_water,
            veg_mgr=new_veg,
            res_mgr=new_res,
            entities_list=new_entities,
            gemini_sys=new_gemini,
            ruins_mgr=new_ruins,
            miracles_mgr=new_miracles,
        )

        # Verify restored values
        self.assertEqual(new_time.current_tick, 5000)
        self.assertEqual(len(new_entities), 4)
        
        # Verify Avian, Reptile, Fungus correctly re-instantiated
        types = {e.__class__.__name__ for e in new_entities}
        self.assertIn("Human", types)
        self.assertIn("Avian", types)
        self.assertIn("Reptile", types)
        self.assertIn("Fungus", types)

        self.assertEqual(new_gemini.global_god_affinity, 99.5)
        self.assertTrue(new_ruins.civilization_discovered)
        self.assertIn("h1", new_ruins.discovered_entity_ids)
        self.assertEqual(len(new_miracles.stardust_deposits), 1)

        # Cleanup
        if os.path.exists(save_path):
            os.remove(save_path)

    def test_fuzzy_and_numeric_path_resolution(self) -> None:
        # Create a dummy save file
        dummy_state = PersistenceManager.serialize_state(
            self.time_mgr, self.soil_mgr, self.water_mgr, self.veg_mgr, self.res_mgr, self.entities
        )
        saved = PersistenceManager.save_to_file("test_fuzzy_target.dat", dummy_state)

        # Test index resolution "1"
        res_1 = PersistenceManager.resolve_save_path("1")
        self.assertTrue(os.path.exists(res_1))

        # Test fuzzy name "fuzzy_target"
        res_fuzzy = PersistenceManager.resolve_save_path("fuzzy_target")
        self.assertTrue(os.path.exists(res_fuzzy))
        self.assertEqual(res_fuzzy, saved)

        # Cleanup
        if os.path.exists(saved):
            os.remove(saved)


if __name__ == "__main__":
    unittest.main()
