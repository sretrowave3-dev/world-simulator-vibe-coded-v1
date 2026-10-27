"""
project/tests/test_terminal_mode_and_adv_dev.py

Unit tests for:
- Terminal-based simulation without GUI
- Smart Activity Chronicler (non-spamming activity feed)
- Advanced feature toggle ('adv dev')
- Standard vs Developer command menus
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from project.core.activity_chronicler import ActivityChronicler, activity_chronicler
from project.entities.entity import EntityType
from project.entities.human import Human
from project.entities.predator import Predator
from project.entities.herbivore import Herbivore
from project.world.time import WorldTimeManager, TimeSnapshot, Season


class TestTerminalModeAndAdvDev(unittest.TestCase):

    def setUp(self):
        self.chronicler = ActivityChronicler()
        self.chronicler.set_terminal_mode(True)
        self.chronicler.verbosity = "smart"

    def test_activity_chronicler_records_events(self):
        """Tests that all categories of events are buffered cleanly without error."""
        self.chronicler.record_tech_discovery("Firemaking", "LITHIC", "Genesis Tribe")
        self.assertEqual(len(self.chronicler.buffered_tech), 1)

        self.chronicler.record_construction("campfire", (100.0, 200.0), "Genesis Tribe")
        self.assertEqual(len(self.chronicler.buffered_structures), 1)

        self.chronicler.record_craft("Stone Axe", "tool", "Genesis Tribe")
        self.assertEqual(len(self.chronicler.buffered_civ_events), 1)

        self.chronicler.record_hunt("panther", "gazelle", (300.0, 400.0), counterattack=False)
        self.assertEqual(len(self.chronicler.buffered_hunts), 1)

        self.chronicler.record_hunt("panther", "human", (100.0, 100.0), counterattack=True)
        self.assertEqual(len(self.chronicler.buffered_hunts), 2)

        self.chronicler.record_birth("gazelle", "HERBIVORE")
        self.assertEqual(self.chronicler.buffered_births.get("Gazelle"), 1)

        self.chronicler.record_death("panther", "old_age")
        self.assertEqual(self.chronicler.buffered_deaths.get("Panther"), 1)

        self.chronicler.record_ruins_progress("Discovered ancient ceremonial altar.")
        self.assertEqual(len(self.chronicler.buffered_discoveries), 1)

        self.chronicler.record_miracle("Solar Eclipse", "The sun is eclipsed for 30 seconds.")
        self.assertEqual(len(self.chronicler.buffered_miracles), 1)

        self.chronicler.record_disaster("Wildfire", "Flames ignited in northern forest.")
        self.assertEqual(len(self.chronicler.buffered_disasters), 1)

    def test_activity_chronicler_flush_and_pulse(self):
        """Tests that flush_pulse_digest aggregates events cleanly and clears buffers."""
        self.chronicler.record_tech_discovery("Spear", "LITHIC", "Genesis Tribe")
        self.chronicler.record_hunt("panther", "gazelle", (500.0, 500.0))
        self.chronicler.record_birth("deer", "HERBIVORE")

        captured_messages = []
        self.chronicler.log_to_terminal = lambda msg, force=False: captured_messages.append(msg)

        # Mock time_snap and entities
        time_snap = TimeSnapshot(
            tick=100,
            seconds=100.0,
            day=1,
            day_fraction=0.3,
            season=Season.SPRING,
            year=1,
            daylight_factor=0.8,
            insolation_factor=1.0,
            solar_angle_rad=1.0,
        )

        h = Human(entity_id="test_h", species_id="homo_sapiens", pos_x=100, pos_y=100)
        p = Predator(entity_id="test_p", species_id="panther", pos_x=200, pos_y=200)
        entities = [h, p]

        self.chronicler._flush_pulse_digest(100, time_snap, entities, None)

        # Ensure status pulse bar and event lines were captured
        self.assertTrue(any("Tick 100" in m for m in captured_messages))
        self.assertTrue(any("Discovered 'Spear'" in m for m in captured_messages))
        self.assertTrue(any("Panther" in m for m in captured_messages))

        # Ensure buffers were cleared
        self.assertEqual(len(self.chronicler.buffered_tech), 0)
        self.assertEqual(len(self.chronicler.buffered_hunts), 0)
        self.assertEqual(len(self.chronicler.buffered_births), 0)

    def test_activity_chronicler_diurnal_shift(self):
        """Tests that day/night transitions trigger evocative narrative announcements."""
        captured = []
        self.chronicler.log_to_terminal = lambda msg, force=False: captured.append(msg)

        time_mgr = MagicMock()
        # Simulate DAWN
        time_mgr.get_snapshot.return_value = TimeSnapshot(
            tick=50, seconds=50.0, day=1, day_fraction=0.2, season=Season.SPRING, year=1, daylight_factor=0.3, insolation_factor=1.0, solar_angle_rad=0.5
        )
        self.chronicler.update(50, time_mgr, [], None)
        self.assertTrue(self.chronicler.last_phase == "DAWN")

        # Simulate MIDDAY
        time_mgr.get_snapshot.return_value = TimeSnapshot(
            tick=150, seconds=150.0, day=1, day_fraction=0.4, season=Season.SPRING, year=1, daylight_factor=0.8, insolation_factor=1.0, solar_angle_rad=1.2
        )
        self.chronicler.update(150, time_mgr, [], None)
        self.assertTrue(self.chronicler.last_phase == "MIDDAY")
        self.assertTrue(any("Midday" in m for m in captured))

    def test_standard_and_modern_help_menus(self):
        """Verifies that both standard and modern help menus format and print without errors."""
        from run_gui import print_standard_help_menu, print_modern_help_menu
        # Test printing both menus
        with patch("sys.stdout.write"):
            print_standard_help_menu()
            print_modern_help_menu()

    def test_verbosity_settings(self):
        """Verifies that verbosity mode can be toggled cleanly."""
        res = self.chronicler.set_verbosity("quiet")
        self.assertEqual(self.chronicler.verbosity, "quiet")
        self.assertIn("quiet", res)

        res = self.chronicler.set_verbosity("smart")
        self.assertEqual(self.chronicler.verbosity, "smart")
        self.assertIn("smart", res)

        res = self.chronicler.set_verbosity("all")
        self.assertEqual(self.chronicler.verbosity, "all")
        self.assertIn("all", res)

        res = self.chronicler.set_verbosity("invalid_mode")
        self.assertIn("Unknown", res)


if __name__ == "__main__":
    unittest.main()
