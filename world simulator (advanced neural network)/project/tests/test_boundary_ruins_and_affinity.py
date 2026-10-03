"""
project/tests/test_boundary_ruins_and_affinity.py

Unit tests for the mysterious Northern Boundary Breach, Ancient Sanctuary Hall,
unprompted exploration discovery by civilization, and interactive Gemini God Affinity controls.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
from project.world.ancient_ruins import AncientRuinsManager, AncientPillar
from project.entities.human import Human
from project.systems.gemini_system import GeminiSystem


class TestBoundaryRuinsAndAffinity(unittest.TestCase):

    def setUp(self) -> None:
        self.ruins = AncientRuinsManager()

    def test_ancient_ruins_initial_hidden_state(self) -> None:
        # Civilization starts with no prior knowledge
        self.assertFalse(self.ruins.civilization_discovered)
        self.assertEqual(len(self.ruins.discovered_entity_ids), 0)
        self.assertEqual(len(self.ruins.pillars), 8)

        # Structure bounds
        self.assertEqual(self.ruins.breach_min_x, 2360.0)
        self.assertEqual(self.ruins.breach_max_x, 2540.0)
        self.assertEqual(self.ruins.breach_y, 0.0)
        self.assertTrue(self.ruins.is_inside_hall(2450.0, 180.0))
        self.assertFalse(self.ruins.is_inside_hall(100.0, 100.0))

    def test_civilization_unprompted_exploration_discovery(self) -> None:
        human = Human(entity_id="explorer_1", species_id="homo_sapiens", pos_x=2450.0, pos_y=150.0)
        human.intelligence_quotient = 100.0
        human.custom_data["stress"] = 0.5

        entities = [human]

        # Entity explores near the boundary hall
        events = self.ruins.update_exploration(entities, current_tick=50)

        # Discovery triggered
        self.assertTrue(self.ruins.civilization_discovered)
        self.assertIn("explorer_1", self.ruins.discovered_entity_ids)
        self.assertGreater(human.intelligence_quotient, 100.0)
        self.assertEqual(human.custom_data["stress"], 0.0)
        self.assertEqual(human.custom_data["dopamine"], 1.0)
        self.assertTrue(len(events) > 0)

    def test_ruins_sanctuary_aura(self) -> None:
        human = Human(entity_id="h2", species_id="homo_sapiens", pos_x=2450.0, pos_y=180.0)
        human.health = 50.0
        human.energy = 40.0
        human.stamina = 30.0

        entities = [human]
        self.ruins.discovered_entity_ids.add("h2")
        self.ruins.update_exploration(entities, current_tick=60)

        self.assertGreater(human.health, 50.0)
        self.assertGreater(human.energy, 40.0)
        self.assertGreater(human.stamina, 30.0)
        self.assertTrue(human.custom_data.get("divine_sanctuary_active", False))

    def test_gemini_god_affinity_tweaking(self) -> None:
        human = Human(entity_id="h3", species_id="homo_sapiens", pos_x=100.0, pos_y=100.0)
        gemini_sys = GeminiSystem(entities_list=[human])

        # Test tweaking affinity
        gemini_sys.global_god_affinity = 25.0
        self.assertEqual(gemini_sys.global_god_affinity, 25.0)

        # Test slider/hotkey high affinity tweak to 99.5%
        gemini_sys.global_god_affinity = 99.5
        self.assertGreaterEqual(gemini_sys.global_god_affinity, 99.0)


if __name__ == "__main__":
    unittest.main()
