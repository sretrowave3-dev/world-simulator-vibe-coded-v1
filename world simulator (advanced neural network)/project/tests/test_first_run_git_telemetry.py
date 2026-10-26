"""
project/tests/test_first_run_git_telemetry.py

Unit tests for:
1. First-time setup detection and UserProfile persistence
2. Free, open-source safe telemetry and secret scrubbing
3. Gemini multi-key intelligent health-routing and offline mode
4. Complete removal of pseudo affinity meter in offline mode
5. Git-like save/load system and accidental overwrite conflict protection
"""

import os
import shutil
import tempfile
import unittest
import time
import json
from unittest.mock import patch, MagicMock

from project.core.user_profile import UserProfileManager, UserProfile
from project.core.telemetry_dispatcher import TelemetrySanitizer, TelemetryDispatcher
from project.core.gemini_client import GeminiClient, KeyHealth
from project.core.git_save_manager import GitSaveManager, GitCommit
from project.core.persistence import PersistenceManager


class TestFirstRunAndUserProfile(unittest.TestCase):
    """Verifies first-time setup detection and profile lifecycle."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.profile_path = os.path.join(self.test_dir, "user_profile.json")
        self.mgr = UserProfileManager(profile_path=self.profile_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_first_run_detection(self):
        # File doesn't exist yet -> first run should be True
        self.assertTrue(self.mgr.is_first_run())

        # Complete setup
        self.mgr.complete_setup({
            "user_name": "TestObserver",
            "display": {"width": 1600, "height": 900},
            "gemini": {"is_offline": True, "api_keys": []},
            "privacy_and_telemetry": {"consent_given": False},
        })

        # File exists and completed -> first run should now be False
        self.assertFalse(self.mgr.is_first_run())

        # Reload from disk
        new_mgr = UserProfileManager(profile_path=self.profile_path)
        prof = new_mgr.get_profile()
        self.assertEqual(prof.user_name, "TestObserver")
        self.assertEqual(prof.display["width"], 1600)
        self.assertTrue(prof.gemini["is_offline"])

    def test_key_management(self):
        self.mgr.add_gemini_key("AIzaSyFakeKey123456789012345678901234")
        prof = self.mgr.get_profile()
        self.assertEqual(len(prof.gemini["api_keys"]), 1)
        self.assertFalse(prof.gemini["is_offline"])

        # Remove key
        removed = self.mgr.remove_gemini_key(0)
        self.assertTrue(removed)
        prof = self.mgr.get_profile()
        self.assertEqual(len(prof.gemini["api_keys"]), 0)
        self.assertTrue(prof.gemini["is_offline"])


class TestSafeTelemetry(unittest.TestCase):
    """Verifies zero secret leakage, PII redaction, and consent gatekeeping."""

    def test_secret_scrubbing(self):
        raw_text = "Error in C:\\Users\\Administrator\\world\\app.py with key AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6 and email dev@example.com"
        sanitized = TelemetrySanitizer.sanitize_string(raw_text)

        self.assertNotIn("Administrator", sanitized)
        self.assertNotIn("AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6", sanitized)
        self.assertNotIn("dev@example.com", sanitized)
        self.assertIn("[USER_HOME]", sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)

    def test_consent_gatekeeping(self):
        # Create dispatcher with consent=False in profile
        mock_mgr = MagicMock()
        mock_prof = UserProfile()
        mock_prof.privacy_and_telemetry["consent_given"] = False
        mock_mgr.get_profile.return_value = mock_prof

        with patch("project.core.telemetry_dispatcher.user_profile_manager", mock_mgr):
            dispatcher = TelemetryDispatcher()
            # Send event
            dispatcher.record_event("TEST_EVENT", {"secret": "data"})
            # Queue should remain empty because consent is False!
            self.assertEqual(dispatcher._queue.qsize(), 0)

            # Now grant consent
            mock_prof.privacy_and_telemetry["consent_given"] = True
            dispatcher.record_event("TEST_EVENT", {"info": "allowed"})
            self.assertEqual(dispatcher._queue.qsize(), 1)
            item = dispatcher._queue.get_nowait()
            self.assertEqual(item["event_type"], "TEST_EVENT")
            dispatcher._running = False


class TestGeminiMultiKeyRouting(unittest.TestCase):
    """Verifies multi-key health routing and offline mode."""

    def test_offline_mode_immediate_response(self):
        client = GeminiClient(api_key="", use_default_pool=False)
        client.is_offline = True
        res = client.request_reasoning("Entity with health 20/100 needs action")
        self.assertIn("action", res)
        # Offline heuristic solver responds immediately
        self.assertEqual(res["action"], "FORAGE_FOOD")

    def test_best_key_routing(self):
        client = GeminiClient(api_key="", use_default_pool=False)
        client.is_offline = False
        client.add_api_key("KEY_A_12345678")
        client.add_api_key("KEY_B_12345678")

        # Simulate KEY_A has errors and high latency
        client._key_stats["KEY_A_12345678"].consecutive_errors = 3
        client._key_stats["KEY_A_12345678"].avg_latency_ms = 850.0

        # Simulate KEY_B is healthy and fast
        client._key_stats["KEY_B_12345678"].consecutive_errors = 0
        client._key_stats["KEY_B_12345678"].avg_latency_ms = 120.0

        best = client.get_best_key()
        self.assertEqual(best, "KEY_B_12345678")

    def test_429_failover(self):
        client = GeminiClient(api_key="", use_default_pool=False)
        client.is_offline = False
        client.add_api_key("KEY_1_12345678")
        client.add_api_key("KEY_2_12345678")

        # Trigger 429 quota error on KEY_1
        client.record_key_error("KEY_1_12345678", is_429=True)
        self.assertEqual(client._key_stats["KEY_1_12345678"].status, "COOLDOWN_429")
        self.assertFalse(client._key_stats["KEY_1_12345678"].is_available)

        # Router should automatically failover to KEY_2
        best = client.get_best_key()
        self.assertEqual(best, "KEY_2_12345678")


class TestGitLikeSaveSystem(unittest.TestCase):
    """Verifies Git DAG, overwrite protection, and auto-stash on divergence."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.git_mgr = GitSaveManager(saves_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_linear_commit_progression(self):
        dummy_save = os.path.join(self.test_dir, "manual_save.dat")
        with open(dummy_save, "wb") as f:
            f.write(b"checkpoint_1")

        c1 = self.git_mgr.record_commit(dummy_save, tick=1000, alive_count=45, message="First settlement")
        self.assertEqual(self.git_mgr.current_commit_id, c1.commit_id)
        self.assertEqual(self.git_mgr.active_branch, "main")

        # Second commit
        c2 = self.git_mgr.record_commit(dummy_save, tick=2000, alive_count=60, message="Second stage")
        self.assertEqual(c2.parent_id, c1.commit_id)
        self.assertEqual(self.git_mgr.current_commit_id, c2.commit_id)

    def test_accidental_overwrite_protection(self):
        # Scenario: User has a save on disk with Tick 10,000
        save_file = os.path.join(self.test_dir, "progressed_world.dat")
        with open(save_file, "wb") as f:
            f.write(b"big_civilization_at_tick_10000")

        # Write sidecar with Tick 10,000
        meta_file = f"{save_file}.meta.json"
        with open(meta_file, "w") as mf:
            json.dump({"tick": 10000, "alive": 150, "commit_id": "c10000"}, mf)

        # Now simulate user accidentally starting a fresh simulation at Tick 25
        # and trying to save over "progressed_world.dat"!
        conflict_detected, msg = self.git_mgr.check_and_protect_overwrite(
            target_file_path=save_file,
            current_tick=25,
            current_alive=20,
        )

        self.assertTrue(conflict_detected)
        self.assertIn("Prevented accidental data loss", msg)

        # Verify that an auto-stash branch was created in branches/!
        branches = os.listdir(self.git_mgr.branches_dir)
        self.assertGreater(len(branches), 0)
        self.assertTrue(any("stash" in b and "tick10000" in b for b in branches))

        # Check that the original 10,000 tick content is preserved in the branch stash
        stash_file = [b for b in branches if "stash" in b and b.endswith(".dat")][0]
        stash_path = os.path.join(self.git_mgr.branches_dir, stash_file)
        with open(stash_path, "rb") as sf:
            self.assertEqual(sf.read(), b"big_civilization_at_tick_10000")

    def test_branching_and_ascii_log(self):
        dummy_save = os.path.join(self.test_dir, "world.dat")
        with open(dummy_save, "wb") as f:
            f.write(b"data")

        c1 = self.git_mgr.record_commit(dummy_save, tick=500, alive_count=30, message="Genesis")
        self.git_mgr.create_branch("experiment/ice-age")
        self.assertEqual(self.git_mgr.active_branch, "experiment/ice-age")

        c2 = self.git_mgr.record_commit(dummy_save, tick=1200, alive_count=15, message="Deep freeze")
        self.assertEqual(c2.branch, "experiment/ice-age")

        log = self.git_mgr.generate_ascii_log()
        self.assertIn("experiment/ice-age", log)
        self.assertIn("Deep freeze", log)
        self.assertIn("Genesis", log)


class TestRendererAndSetupWizard(unittest.TestCase):
    """Verifies that pseudo affinity meter is removed and setup wizard operates correctly."""

    @classmethod
    def setUpClass(cls):
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    def test_renderer_offline_removes_pseudo_affinity(self):
        import pygame
        pygame.init()
        from project.renderer.renderer import SimulationRenderer

        # Mock user profile as offline
        mock_mgr = MagicMock()
        mock_prof = UserProfile()
        mock_prof.gemini["is_offline"] = True
        mock_prof.gemini["api_keys"] = []
        mock_mgr.get_profile.return_value = mock_prof

        with patch("project.core.user_profile.user_profile_manager", mock_mgr):
            renderer = SimulationRenderer(width=800, height=600, world_width=1000, world_height=1000)
            self.assertTrue(renderer.is_offline)
            # Slider 1 (Gemini God Affinity) must NOT be present
            self.assertEqual(len(renderer.sliders), 1)
            self.assertEqual(renderer.sliders[0].label, "Food Size")
            renderer.close()

    def test_renderer_online_has_affinity_slider(self):
        import pygame
        pygame.init()
        from project.renderer.renderer import SimulationRenderer

        mock_mgr = MagicMock()
        mock_prof = UserProfile()
        mock_prof.gemini["is_offline"] = False
        mock_prof.gemini["api_keys"] = ["AIzaSyValidKeyExample12345"]
        mock_mgr.get_profile.return_value = mock_prof

        with patch("project.core.user_profile.user_profile_manager", mock_mgr):
            renderer = SimulationRenderer(width=800, height=600, world_width=1000, world_height=1000)
            self.assertFalse(renderer.is_offline)
            # Gemini God Affinity slider should be present
            self.assertEqual(len(renderer.sliders), 2)
            self.assertEqual(renderer.sliders[1].label, "Gemini God Affinity (%)")
            renderer.close()

    def test_setup_wizard_flow(self):
        import pygame
        pygame.init()
        from project.renderer.setup_wizard import FirstTimeSetupWizard

        wiz = FirstTimeSetupWizard(screen_w=900, screen_h=600)
        self.assertEqual(wiz.current_step, 1)

        # Advance to Step 2
        wiz._next_step()
        self.assertEqual(wiz.current_step, 2)

        # Advance to Step 3
        wiz._next_step()
        self.assertEqual(wiz.current_step, 3)

        # Test Skip / Offline button on Step 3
        wiz._skip_offline_clicked()
        self.assertTrue(wiz.is_offline_selected)
        self.assertEqual(len(wiz.api_keys), 0)
        self.assertEqual(wiz.current_step, 4)

        # Complete wizard
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_prof_path = os.path.join(tmp_dir, "wizard_test_profile.json")
            test_mgr = UserProfileManager(profile_path=test_prof_path)
            with patch("project.renderer.setup_wizard.user_profile_manager", test_mgr):
                wiz._complete_wizard()
                self.assertTrue(wiz.finished)
                saved_prof = test_mgr.get_profile()
                self.assertTrue(saved_prof.gemini["is_offline"])
                self.assertTrue(saved_prof.first_time_setup_completed)


if __name__ == "__main__":
    unittest.main()
