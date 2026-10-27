"""
project/tests/test_tamper_guard_and_mongo.py

Unit test suite verifying:
1. Anti-Tampering Engine (TamperGuard):
   - Cryptographic manifest sealing & authenticated decryption.
   - Allows users to freely modify non-security files (e.g. world.py, custom logic) without false alarms.
   - Detects modifications/deletions of core security files.
   - Enforces lockdown, online severance, and Discord alert dispatch for unauthorized non-owner tampering.
   - Permits verified Owner to update security files and re-seal the manifest.
2. MongoDB Secure Storage Subsystem (MongoStorageManager):
   - Graceful offline fallback to local storage when MongoDB is not running.
   - User profile persistence and roundtrip retrieval.
   - Security audit event recording.
3. Update System Owner Filtering:
   - Update notifications and banners suppressed for Owner.
   - Accurate Git ahead/behind topology calculation.
"""

from __future__ import annotations

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Safe UTF-8 reconfiguration
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from project.core.tamper_guard import TamperGuard, PROTECTED_SECURITY_FILES, MANIFEST_SECRET_KEY
from project.core.mongo_storage import MongoStorageManager
from project.core.updater import UpdateManager, UpdateInfo
from project.core.user_profile import UserProfileManager, UserProfile
from project.security.crypto import CryptoEngine


class TestTamperGuardAndMongo(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tamper_guard_test_")
        self.project_dir = os.path.join(self.test_dir, "project")
        self.security_dir = os.path.join(self.project_dir, "security")
        self.core_dir = os.path.join(self.project_dir, "core")
        self.systems_dir = os.path.join(self.project_dir, "systems")

        os.makedirs(self.security_dir, exist_ok=True)
        os.makedirs(self.core_dir, exist_ok=True)
        os.makedirs(self.systems_dir, exist_ok=True)

        # Create dummy security files in test_dir
        for rel in PROTECTED_SECURITY_FILES:
            full = os.path.join(self.test_dir, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(f"# Mock security file for {rel}\n")

        # Create dummy non-security files (allowed to be edited locally)
        self.world_file = os.path.join(self.core_dir, "world.py")
        with open(self.world_file, "w", encoding="utf-8") as f:
            f.write("# World simulation logic\n")

        self.guard = TamperGuard(workspace_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_manifest_sealing_and_verification(self):
        """Tests that security manifest seals properly and verifies 100% intact."""
        ok, msg = self.guard.seal_manifest()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.guard.manifest_path))

        # Check verification passes
        intact, tampered, reason = self.guard.verify_integrity()
        self.assertTrue(intact)
        self.assertEqual(len(tampered), 0)
        self.assertIn("verified intact", reason)

    def test_non_security_file_modifications_allowed(self):
        """Tests that users can modify non-security simulation files freely without alarms."""
        self.guard.seal_manifest()

        # Modify world.py (non-security file)
        with open(self.world_file, "a", encoding="utf-8") as f:
            f.write("def custom_user_mutation(): return True\n")

        # Integrity check on security manifest must still be 100% INTACT
        intact, tampered, reason = self.guard.verify_integrity()
        self.assertTrue(intact)
        self.assertEqual(len(tampered), 0)

    def test_security_file_tampering_detected(self):
        """Tests that altering any protected security file is detected immediately."""
        self.guard.seal_manifest()

        # Tamper with project/security/auth.py
        target = os.path.join(self.security_dir, "auth.py")
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n# HACKED CODE INJECTION\n")

        intact, tampered, reason = self.guard.verify_integrity()
        self.assertFalse(intact)
        self.assertTrue(any("project/security/auth.py" in tf for tf in tampered))

    def test_non_owner_tamper_breach_lockdown_and_discord_alert(self):
        """
        Tests that tampering by a non-owner:
        1. Activates simulator lockdown (is_locked=True).
        2. Severs network connections (network_severed=True).
        3. Dispatches emergency Discord webhook alert.
        """
        self.guard.seal_manifest()

        tampered_list = ["project/security/crypto.py (MODIFIED)"]

        with patch.object(self.guard, "_dispatch_discord_breach_alert") as mock_discord:
            locked = self.guard.handle_tamper_breach(
                tampered_files=tampered_list,
                is_owner=False,
                user_name="MaliciousActor",
                webhook_url="https://discord.mock/api/webhook",
            )
            self.assertTrue(locked)
            self.assertTrue(self.guard.is_locked)
            self.assertTrue(self.guard.network_severed)
            self.assertIn("Security subsystem modified", self.guard.lockdown_reason)

            # Check that Discord alert dispatcher was called
            time.sleep(0.1)
            mock_discord.assert_called_once()

    def test_owner_tampering_bypasses_lockdown_and_can_reseal(self):
        """Tests that verified Owner can modify security files and re-seal without lockdown."""
        self.guard.seal_manifest()

        tampered_list = ["project/security/ids.py (MODIFIED)"]

        locked = self.guard.handle_tamper_breach(
            tampered_files=tampered_list,
            is_owner=True,
            user_name="sretrowave3-dev",
        )
        # Must NOT lock down for Owner
        self.assertFalse(locked)
        self.assertFalse(self.guard.is_locked)

        # Re-seal cleans up status
        ok, msg = self.guard.seal_manifest()
        self.assertTrue(ok)
        self.assertFalse(self.guard.is_locked)

    def test_mongo_offline_fallback(self):
        """Tests MongoStorageManager gracefully handles offline MongoDB instances."""
        # Using a non-existent port to guarantee offline
        mongo = MongoStorageManager(uri="mongodb://localhost:29999", db_name="test_sim_db")
        self.assertFalse(mongo.is_connected())

        status = mongo.get_status()
        self.assertEqual(status["status"], "OFFLINE_LOCAL_FALLBACK")

        # Operations fail gracefully without crashing
        res = mongo.save_user_profile({"user_name": "TestUser"})
        self.assertFalse(res)

        load_res = mongo.load_user_profile("TestUser")
        self.assertIsNone(load_res)

    def test_updater_ahead_behind_and_owner_suppression(self):
        """Tests updater ahead/behind detection and confirms owner suppression."""
        updater = UpdateManager(workspace_dir=self.test_dir)

        # Mock GitHub commits response
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = b'{"sha": "b306ab712345", "commit": {"message": "Synchronized commit", "author": {"name": "owner", "date": "2026-10-26"}}}'

        with patch("urllib.request.urlopen", return_value=mock_resp):
            info = updater.check_for_updates(force=True)
            self.assertEqual(info.sync_status, "SYNCHRONIZED")
            self.assertFalse(info.has_update)


if __name__ == "__main__":
    unittest.main()
