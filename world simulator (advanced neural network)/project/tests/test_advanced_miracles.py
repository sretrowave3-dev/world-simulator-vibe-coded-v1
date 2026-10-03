"""
project/tests/test_advanced_miracles.py

Unit tests for advanced celestial miracles: Solar Eclipse, Meteor Stardust Shower,
Divine Rainstorms, Bountiful Harvests, and Epiphany Waves.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
from project.world.miracles import WorldMiracleManager, StardustDeposit
from project.entities.human import Human
from project.entities.plant import Plant
from project.entities.predator import Predator


class TestAdvancedMiracles(unittest.TestCase):

    def setUp(self) -> None:
        self.miracles = WorldMiracleManager()

    def test_solar_eclipse_and_rainstorm(self) -> None:
        # Solar Eclipse
        self.assertFalse(self.miracles.is_eclipse_active)
        self.miracles.trigger_solar_eclipse(20.0)
        self.assertTrue(self.miracles.is_eclipse_active)
        self.assertEqual(self.miracles.eclipse_remaining_seconds, 20.0)

        # Divine Rainstorm
        self.assertFalse(self.miracles.is_rainstorm_active)
        self.miracles.trigger_divine_rainstorm(30.0)
        self.assertTrue(self.miracles.is_rainstorm_active)

        # Update pass reduces timers
        self.miracles.update(dt=5.0, entities_list=[])
        self.assertEqual(self.miracles.eclipse_remaining_seconds, 15.0)
        self.assertEqual(self.miracles.rainstorm_remaining_seconds, 25.0)

    def test_meteor_stardust_shower_and_pickup(self) -> None:
        self.miracles.stardust_deposits = [
            StardustDeposit(pos_x=100.0, pos_y=100.0),
            StardustDeposit(pos_x=500.0, pos_y=500.0),
            StardustDeposit(pos_x=800.0, pos_y=800.0),
        ]
        self.assertEqual(len(self.miracles.stardust_deposits), 3)

        # Human near the first meteorite fragment picks it up
        human = Human(entity_id="h1", species_id="homo_sapiens", pos_x=100.0, pos_y=100.0)
        human.intelligence_quotient = 100.0
        human.energy = 50.0

        self.miracles.update(dt=0.1, entities_list=[human])

        # Exactly 1 deposit collected & human gained IQ and energy
        self.assertEqual(len(self.miracles.stardust_deposits), 2)
        self.assertGreater(human.intelligence_quotient, 100.0)
        self.assertGreater(human.energy, 50.0)

    def test_bountiful_harvest_and_epiphany_wave(self) -> None:
        human = Human(entity_id="h2", species_id="homo_sapiens", pos_x=200.0, pos_y=200.0)
        human.intelligence_quotient = 105.0
        plant = Plant(entity_id="p1", species_id="wheat", pos_x=210.0, pos_y=210.0, energy=40.0)

        entities = [human, plant]

        # Bountiful harvest feeds human and vitalizes plant
        self.miracles.trigger_bountiful_harvest(entities, center_x=200.0, center_y=200.0, radius=50.0)
        self.assertGreater(plant.energy, 40.0)
        self.assertEqual(human.custom_data["dopamine"], 1.0)

        # Epiphany wave boosts human intellect
        self.miracles.trigger_epiphany_wave(entities, tick=100)
        self.assertGreater(human.intelligence_quotient, 105.0)

    def test_purge_threats(self) -> None:
        predator = Predator(entity_id="pred1", species_id="panther", pos_x=300.0, pos_y=300.0)
        predator.custom_data["ambush_mode"] = True
        entities = [predator]

        self.miracles.trigger_purge_threats(entities, center_x=300.0, center_y=300.0, radius=50.0)
        self.assertEqual(predator.custom_data["fear"], 1.0)
        self.assertFalse(predator.custom_data["ambush_mode"])


if __name__ == "__main__":
    unittest.main()
