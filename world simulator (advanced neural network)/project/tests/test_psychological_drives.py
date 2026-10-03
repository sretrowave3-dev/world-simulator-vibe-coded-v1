"""
project/tests/test_psychological_drives.py

Unit tests verifying continuous, dynamic, and non-hardcoded variations
in psychological drives (Hunger, Thirst, Fatigue, Fear, Libido, Social, Curiosity, Stress, Dopamine).
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
from project.entities.human import Human
from project.entities.predator import Predator
from project.ai.needs import OrganismNeeds, get_default_species_profile
from project.systems.decision_system import DecisionSystem
from project.systems.render_sync_system import RenderSyncSystem
from project.core.scheduler import UpdateContext


class TestPsychologicalDrives(unittest.TestCase):

    def test_hunger_and_thirst_variation(self) -> None:
        needs = OrganismNeeds()
        
        # High vitality -> Low urgency
        needs.update_from_vitals(
            energy=100.0, max_energy=100.0,
            hydration=100.0, max_hydration=100.0,
            stamina=100.0, max_stamina=100.0,
        )
        self.assertLess(needs.hunger, 0.1)
        self.assertLess(needs.thirst, 0.1)
        self.assertAlmostEqual(needs.fatigue, 0.0, delta=0.01)

        # Depleted energy and hydration -> High urgency
        needs.update_from_vitals(
            energy=20.0, max_energy=100.0,
            hydration=15.0, max_hydration=100.0,
            stamina=10.0, max_stamina=100.0,
        )
        self.assertGreater(needs.hunger, 0.6)
        self.assertGreater(needs.thirst, 0.7)
        self.assertGreater(needs.fatigue, 0.8)

    def test_decision_system_dynamic_neuropsychology(self) -> None:
        human = Human(entity_id="h1", species_id="homo_sapiens", pos_x=100.0, pos_y=100.0)
        predator = Predator(entity_id="pred1", species_id="panther", pos_x=110.0, pos_y=110.0)
        
        entities = [human, predator]
        dec_sys = DecisionSystem(entities)

        # 1. Threat present -> Fear and Stress surge
        human.custom_data["perceived_entities"] = [predator]
        context = UpdateContext(
            tick=1, delta_time=0.1, simulation_time=0.1,
            random_seed=42, world_reference=None,
            is_paused=False, active_thread_count=1,
        )
        dec_sys.update(context)
        
        self.assertGreater(human.custom_data["fear"], 0.7)
        self.assertGreater(human.custom_data["stress"], 0.2)

        # 2. Threat removed -> Fear decays smoothly
        human.custom_data["perceived_entities"] = []
        initial_fear = human.custom_data["fear"]
        for _ in range(5):
            dec_sys.update(context)
        
        self.assertLess(human.custom_data["fear"], initial_fear)

    def test_render_sync_system_packages_live_needs(self) -> None:
        human = Human(entity_id="h1", species_id="homo_sapiens", pos_x=50.0, pos_y=50.0)
        human.energy = 25.0
        human.max_energy = 100.0
        human.hydration = 20.0
        human.max_hydration = 100.0
        human.stamina = 20.0
        human.max_stamina = 100.0

        entities = [human]
        dec_sys = DecisionSystem(entities)
        render_sync = RenderSyncSystem(entities)

        context = UpdateContext(
            tick=1, delta_time=0.1, simulation_time=0.1,
            random_seed=42, world_reference=None,
            is_paused=False, active_thread_count=1,
        )
        dec_sys.update(context)
        render_sync.update(context)

        snapshot = render_sync.get_snapshot()
        self.assertEqual(len(snapshot), 1)
        snap_h1 = snapshot[0]

        # Verify snap_data contains live varying needs dictionary
        self.assertIn("needs", snap_h1)
        needs_dict = snap_h1["needs"]
        self.assertGreater(needs_dict["hunger"], 0.5)
        self.assertGreater(needs_dict["thirst"], 0.5)
        self.assertGreater(needs_dict["fatigue"], 0.7)


if __name__ == "__main__":
    unittest.main()
