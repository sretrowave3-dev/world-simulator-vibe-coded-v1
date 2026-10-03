"""
tests/test_persistence.py

Unit tests for simulation saving, loading, compression, and structural recovery.
"""

import os
import unittest
from project.core.persistence import PersistenceManager
from project.world.time import WorldTimeManager
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager, ResourceType, ResourceNode
from project.entities.entity import Entity, EntityType
from project.entities.bacteria import Bacteria
from project.entities.human import Human


class TestPersistenceSubsystem(unittest.TestCase):

    def setUp(self) -> None:
        self.save_filepath = "test_save.dat"
        self.resolved_filepath = PersistenceManager.resolve_save_path(self.save_filepath)

    def tearDown(self) -> None:
        if os.path.exists(self.resolved_filepath):
            os.remove(self.resolved_filepath)
        if os.path.exists(self.save_filepath):
            os.remove(self.save_filepath)

    def test_full_save_load_cycle(self) -> None:
        # 1. Setup managers with initial data
        time_mgr = WorldTimeManager()
        time_mgr.current_tick = 550
        time_mgr.total_seconds = 1100.0

        soil_mgr = SoilManager()
        chunk_soil = soil_mgr.get_or_create_chunk((0, 0))
        chunk_soil.nitrogen[12] = 0.85
        chunk_soil.ph[12] = 6.2

        water_mgr = WaterManager()
        chunk_water = water_mgr.get_or_create_chunk((0, 0))
        chunk_water.depth[12] = 1.45

        veg_mgr = VegetationManager()
        chunk_veg = veg_mgr.get_or_create_chunk((0, 0))
        chunk_veg.biomass[12] = 45.0

        res_mgr = ResourceManager()
        node = res_mgr.spawn_node(ResourceType.STONE, 10.0, 20.0, capacity=500.0, regeneration_rate=0.1, hardness=1.0)
        node.quantity = 250.0

        entities_list: List[Entity] = []
        bac = Bacteria(
            entity_id="bac_1",
            species_id="chem",
            pos_x=12.5,
            pos_y=24.5,
        )
        bac.energy = 75.0
        entities_list.append(bac)
        
        human = Human(
            entity_id="hum_1",
            species_id="sapiens",
            pos_x=100.0,
            pos_y=200.0,
        )
        human.technology_level = 5
        human.add_to_inventory("Wood", 10.0)
        entities_list.append(human)

        # 2. Serialize
        data = PersistenceManager.serialize_state(
            time_mgr=time_mgr,
            soil_mgr=soil_mgr,
            water_mgr=water_mgr,
            veg_mgr=veg_mgr,
            res_mgr=res_mgr,
            entities_list=entities_list,
        )

        # 3. Save to file
        saved_path = PersistenceManager.save_to_file(self.save_filepath, data)
        self.assertTrue(os.path.exists(saved_path))

        # 4. Load from file
        loaded_data = PersistenceManager.load_from_file(self.save_filepath)
        self.assertEqual(loaded_data["time"]["tick"], 550)

        # 5. Instantiate fresh managers to restore into
        new_time_mgr = WorldTimeManager()
        new_soil_mgr = SoilManager()
        new_water_mgr = WaterManager()
        new_veg_mgr = VegetationManager()
        new_res_mgr = ResourceManager()
        new_entities_list: List[Entity] = []

        # 6. Deserialize
        PersistenceManager.deserialize_state(
            state_dict=loaded_data,
            time_mgr=new_time_mgr,
            soil_mgr=new_soil_mgr,
            water_mgr=new_water_mgr,
            veg_mgr=new_veg_mgr,
            res_mgr=new_res_mgr,
            entities_list=new_entities_list,
        )

        # 7. Assertions for recovered state
        self.assertEqual(new_time_mgr.current_tick, 550)
        self.assertAlmostEqual(new_soil_mgr.query_soil(0.0, 0.0).nitrogen, 0.5)  # local index 0
        
        # Check specific index 12 in chunk (0, 0)
        c_soil = new_soil_mgr.get_or_create_chunk((0, 0))
        self.assertAlmostEqual(c_soil.nitrogen[12], 0.85)

        c_water = new_water_mgr.get_or_create_chunk((0, 0))
        self.assertAlmostEqual(c_water.depth[12], 1.45)

        c_veg = new_veg_mgr.get_or_create_chunk((0, 0))
        self.assertAlmostEqual(c_veg.biomass[12], 45.0)

        self.assertEqual(len(new_res_mgr._nodes), 1)
        self.assertEqual(new_res_mgr._nodes[1].quantity, 250.0)

        # Verify recovered entities
        self.assertEqual(len(new_entities_list), 2)
        
        bac = [e for e in new_entities_list if e.entity_id == "bac_1"][0]
        self.assertIsInstance(bac, Bacteria)
        self.assertAlmostEqual(bac.pos_x, 12.5)
        self.assertAlmostEqual(bac.energy, 75.0)

        hum = [e for e in new_entities_list if e.entity_id == "hum_1"][0]
        self.assertIsInstance(hum, Human)
        self.assertEqual(hum.technology_level, 5)
        self.assertIn("Wood", hum.inventory)
        self.assertAlmostEqual(hum.inventory["Wood"], 10.0)


if __name__ == "__main__":
    unittest.main()
