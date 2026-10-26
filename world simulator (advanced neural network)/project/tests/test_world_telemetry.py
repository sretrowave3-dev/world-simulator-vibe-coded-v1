"""
project/tests/test_world_telemetry.py

Unit tests for World State Telemetry Extraction and Active User Heartbeat Analytics.
- Validates Active User Heartbeat generation and session tracking.
- Validates Summary, Deep, and Full State ("literally everything") extraction.
- Validates zlib+base64 compression for high-dimensional simulation dumps.
- Validates strict Opt-In gatekeeping (zero data dispatched without user consent).
"""

from __future__ import annotations

import base64
import json
import time
import unittest
import zlib
from unittest.mock import patch, MagicMock

from project.core.world_telemetry import WorldTelemetryCollector
from project.core.user_profile import UserProfile, user_profile_manager


class MockEntity:
    def __init__(self, eid: str, species: str, health: float, energy: float, age: float, gen: int = 1):
        self.entity_id = eid
        self.species_id = species
        self.health = health
        self.energy = energy
        self.age = age
        self.generation = gen
        self.is_alive = True
        self.speed = 2.5
        self.metabolism_rate = 1.0
        self.brain = MagicMock()


class TestWorldTelemetry(unittest.TestCase):
    """Test suite for world state and active user telemetry extraction."""

    def setUp(self) -> None:
        self.collector = WorldTelemetryCollector()
        self.entities = [
            MockEntity("e1", "gazelle", 90.0, 80.0, 15.0, gen=2),
            MockEntity("e2", "gazelle", 85.0, 75.0, 20.0, gen=2),
            MockEntity("e3", "panther", 100.0, 95.0, 35.0, gen=3),
            MockEntity("e4", "plant", 50.0, 40.0, 50.0, gen=1),
        ]

    def test_active_user_heartbeat_opt_in_gatekeeping(self) -> None:
        """Confirms heartbeat is strictly dropped if consent is not granted."""
        mock_prof = UserProfile()
        mock_prof.privacy_and_telemetry["consent_given"] = False

        with patch.object(user_profile_manager, "get_profile", return_value=mock_prof):
            with patch("project.core.telemetry_dispatcher.telemetry_dispatcher.record_event") as mock_record:
                self.collector.dispatch_heartbeat(tick=100, entities_count=4)
                mock_record.assert_not_called()

    def test_active_user_heartbeat_dispatches_when_consented(self) -> None:
        """Confirms heartbeat dispatches complete telemetry when user consented."""
        mock_prof = UserProfile()
        mock_prof.privacy_and_telemetry["consent_given"] = True
        mock_prof.privacy_and_telemetry["anonymized_client_id"] = "anon_test_user_123"

        with patch.object(user_profile_manager, "get_profile", return_value=mock_prof):
            with patch("project.core.telemetry_dispatcher.telemetry_dispatcher.record_event") as mock_record:
                self.collector.dispatch_heartbeat(tick=1200, entities_count=4, fps=59.5, ups=60.0, status="active")
                mock_record.assert_called_once()
                call_args = mock_record.call_args[1]
                self.assertEqual(call_args["event_type"], "ACTIVE_USER_HEARTBEAT")
                details = call_args["details"]
                self.assertEqual(details["client_id"], "anon_test_user_123")
                self.assertEqual(details["sim_tick"], 1200)
                self.assertEqual(details["entities_alive"], 4)
                self.assertIn("uptime_seconds", details)
                self.assertIn("environment", details)

    def test_build_summary_state(self) -> None:
        """Verifies Tier 1 Summary telemetry extraction."""
        summary = self.collector.build_summary_state(self.entities)
        self.assertEqual(summary["tier"], "SUMMARY")
        pop = summary["population"]
        self.assertEqual(pop["total_alive"], 4)
        self.assertEqual(pop["species_breakdown"]["gazelle"], 2)
        self.assertEqual(pop["species_breakdown"]["panther"], 1)
        self.assertEqual(pop["species_breakdown"]["plant"], 1)
        self.assertEqual(pop["max_generation"], 3)
        self.assertEqual(pop["species_diversity_count"], 3)

    def test_build_deep_state(self) -> None:
        """Verifies Tier 2 Deep Ecosystem state extraction."""
        deep = self.collector.build_deep_state(self.entities)
        self.assertEqual(deep["tier"], "DEEP")
        eco = deep["ecosystem_details"]
        self.assertEqual(eco["neural_agents_count"], 4)
        oldest = eco["oldest_organisms"]
        # Entity e4 is oldest with age 50.0
        self.assertEqual(oldest[0]["id"], "e4")
        self.assertEqual(oldest[0]["age"], 50.0)

    def test_build_full_state_compression(self) -> None:
        """Verifies Tier 3 Full World Dump serializes and compresses large states cleanly."""
        mock_large_state = {
            "entities": [{"id": f"ent_{i}", "weights": [0.123] * 50} for i in range(200)],
            "grid": [[0.5] * 50 for _ in range(50)],
        }
        with patch("project.core.persistence.PersistenceManager.serialize_state", return_value=mock_large_state):
            full_dump = self.collector.build_full_state(self.entities)
            # Should be compressed because payload > MAX_UNCOMPRESSED_PAYLOAD_BYTES
            self.assertEqual(full_dump["tier"], "FULL_DUMP_COMPRESSED")
            self.assertEqual(full_dump["compression"], "zlib+base64")
            self.assertIn("payload_b64", full_dump)

            # Test decompressibility
            compressed_bytes = base64.b64decode(full_dump["payload_b64"])
            decompressed_json = zlib.decompress(compressed_bytes).decode("utf-8")
            recovered_state = json.loads(decompressed_json)
            self.assertEqual(len(recovered_state["entities"]), 200)

    def test_owner_dashboard_processing(self) -> None:
        """Verifies owner dashboard event processing and active user calculation."""
        import owner_telemetry_dashboard as dashboard
        dashboard.active_sessions.clear()
        dashboard.world_snapshots.clear()

        # Ingest active user heartbeat
        mock_heartbeat = {
            "client_id": "anon_unit_test",
            "event_type": "ACTIVE_USER_HEARTBEAT",
            "timestamp": time.time(),
            "data": {
                "session_id": "test_sess_1",
                "status": "active",
                "uptime_seconds": 120,
                "sim_tick": 400,
                "entities_alive": 12,
                "performance": {"fps": 60, "ups": 60},
                "environment": {"os": "TestOS", "python": "3.15"},
            }
        }
        dashboard.process_telemetry_event(mock_heartbeat, relay_to_discord=False)
        self.assertEqual(dashboard.get_live_active_users_count(), 1)
        self.assertIn("test_sess_1", dashboard.active_sessions)

        # Ingest world state
        mock_world = {
            "client_id": "anon_unit_test",
            "event_type": "WORLD_STATE_SUMMARY",
            "timestamp": time.time(),
            "data": {
                "tier": "SUMMARY",
                "tick": 400,
                "population": {"total_alive": 12},
            }
        }
        dashboard.process_telemetry_event(mock_world, relay_to_discord=False)
        self.assertEqual(len(dashboard.world_snapshots), 1)
        self.assertEqual(dashboard.world_snapshots[0]["tier"], "SUMMARY")


if __name__ == "__main__":
    unittest.main()
