"""
project/tests/test_lightweight_scanner.py

Comprehensive Unit Test Suite for the Lightweight 3-Phase Scanner Subsystem.
Tests:
- Phase 1: Boot Scan (Saves discovery, new user detection, user rank calculation,
  Owner privileges vs User-based options, Credential Page generation, profile persistence).
- Phase 2: Periodic Runtime Scan (File integrity verification, autosave separation
  detection & Git auto-fix, online security & hacking prevention auto-fix).
- Phase 3: Exit Scan (Overall data integrity validation, data sharing & privacy verification,
  header magic, CRC32/SHA-256 checks, clean exit certificate).
"""

from __future__ import annotations

import os
import sys
import json
import time
import shutil
import tempfile
import unittest

# Ensure UTF-8 output
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from project.core.lightweight_scanner import LightweightScanner, ScanReport, PRIVILEGE_USER_DEFAULT, PRIVILEGE_OWNER_ALL
from project.core.user_profile import UserProfileManager, UserProfile


class TestLightweightScanner(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="alife_scanner_test_")
        self.saves_dir = os.path.join(self.test_dir, "saves")
        self.universes_dir = os.path.join(self.saves_dir, "universes")
        self.logs_dir = os.path.join(self.test_dir, "logs")
        self.project_dir = os.path.join(self.test_dir, "project")
        os.makedirs(self.universes_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.project_dir, exist_ok=True)

        self.profile_path = os.path.join(self.test_dir, "user_profile.json")
        self.user_mgr = UserProfileManager(profile_path=self.profile_path)
        self.scanner = LightweightScanner(workspace_dir=self.test_dir, user_profile_mgr=self.user_mgr)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_boot_scan_new_user_and_rank(self):
        """Tests Boot Scan identifies fresh new user, calculates rank, and saves profile."""
        report = self.scanner.scan_boot(verbose=False)
        self.assertEqual(report.phase, "BOOT")
        self.assertEqual(report.status, "SUCCESS")
        self.assertTrue(report.details["is_new_user"])
        self.assertEqual(report.details["role"], "USER")
        self.assertEqual(report.details["rank"], "NOVICE_EXPLORER")
        self.assertFalse(report.details["is_owner"])

        # Verify privileges are user-based only
        self.assertIn("SIMULATE", report.details["privileges"])
        self.assertIn("SAVE_LOAD", report.details["privileges"])
        self.assertNotIn("PUSH_GITHUB", report.details["privileges"])
        self.assertNotIn("UPDATE_CODE", report.details["privileges"])

        # Verify saved to disk
        self.assertTrue(os.path.exists(self.profile_path))
        loaded = self.user_mgr.load_profile()
        self.assertEqual(loaded.credentials["role"], "USER")
        self.assertEqual(loaded.credentials["rank"], "NOVICE_EXPLORER")

    def test_owner_authentication_and_privileges(self):
        """Tests owner passkey authentication elevates role and grants owner privileges."""
        # Initially standard user
        self.scanner.scan_boot(verbose=False)
        self.assertFalse(self.scanner.has_privilege("PUSH_GITHUB"))

        # Attempt push without owner clearance -> denied
        can_push, msg = self.scanner.push_to_github()
        self.assertFalse(can_push)
        self.assertIn("ACCESS DENIED", msg)

        # Authenticate with owner passkey
        ok, auth_msg = self.scanner.authenticate_owner("sretrowave_root_2026")
        self.assertTrue(ok)
        self.assertIn("Owner privileges granted", auth_msg)
        self.assertTrue(self.scanner.has_privilege("PUSH_GITHUB"))
        self.assertTrue(self.scanner.has_privilege("UPDATE_CODE"))

        prof = self.user_mgr.get_profile()
        self.assertEqual(prof.credentials["role"], "OWNER")
        self.assertEqual(prof.credentials["rank"], "SYSTEM_OWNER")
        self.assertTrue(prof.credentials["is_owner"])

        # Test credential page formatting
        creds_page = self.scanner.render_credentials_page()
        self.assertIn("WORLD SIMULATOR CREDENTIAL PAGE", creds_page)
        self.assertIn("SYSTEM_OWNER", creds_page)
        self.assertIn("PUSH_GITHUB", creds_page)

        # Test logout
        logout_msg = self.scanner.deauthenticate_owner()
        self.assertIn("USER mode", logout_msg)
        self.assertFalse(self.scanner.has_privilege("PUSH_GITHUB"))

    def test_runtime_periodic_file_integrity(self):
        """Tests periodic scan checks project files and reports integrity status."""
        report = self.scanner.scan_runtime_periodic(current_tick=100, verbose=False)
        self.assertEqual(report.phase, "PERIODIC_RUNTIME")
        self.assertIn("file_integrity", report.details)
        self.assertIn("checked_files", report.details["file_integrity"])

    def test_runtime_periodic_autosave_separation_fix(self):
        """
        Tests that when an autosave makes a separate file outside the running world,
        the scanner detects it, reconciles it into the active universe, and registers
        it into the Git DAG.
        """
        # Setup active universe directory
        univ_id = "univ_test_world"
        active_univ_dir = os.path.join(self.universes_dir, univ_id)
        proper_autosaves_dir = os.path.join(active_univ_dir, "autosaves")
        os.makedirs(proper_autosaves_dir, exist_ok=True)

        # Create a separate, orphaned autosave in root saves/
        orphaned_autosave = os.path.join(self.saves_dir, "autosave_slot_1.dat")
        with open(orphaned_autosave, "wb") as f:
            f.write(b"ECHO_SAMPLE_SEPARATE_AUTOSAVE_DATA")

        self.assertTrue(os.path.exists(orphaned_autosave))

        # Run periodic scan
        report = self.scanner.scan_runtime_periodic(current_tick=5000, verbose=False)

        # Confirm separate file was reconciled into active universe
        self.assertFalse(os.path.exists(orphaned_autosave), "Orphaned autosave should be cleaned from root saves/")
        reconciled_files = os.listdir(proper_autosaves_dir)
        self.assertTrue(len(reconciled_files) >= 1, "Autosave should now exist inside active universe autosaves/")
        self.assertTrue(any("reconciled" in f for f in reconciled_files))
        self.assertTrue(any("Reconciled separate autosave" in fix for fix in report.fixes_applied))

    def test_runtime_periodic_security_detection_and_fix(self):
        """Tests that online security threats (e.g. SSRF webhook) are detected and neutralized."""
        # Inject SSRF threat into profile webhook URL
        prof = self.user_mgr.get_profile()
        prof.privacy_and_telemetry["webhook_url"] = "http://169.254.169.254/latest/meta-data/"
        prof.privacy_and_telemetry["telemetry_mode"] = "webhook"
        self.user_mgr.save_profile(prof)

        # Run periodic scan
        report = self.scanner.scan_runtime_periodic(current_tick=12000, verbose=False)

        # Confirm threat was detected and security system neutralized it
        self.assertTrue(any("SSRF attempt detected" in w for w in report.warnings))
        self.assertTrue(any("neutralized SSRF" in f for f in report.fixes_applied))

        # Confirm profile is restored to safe opt_out
        cleaned_prof = self.user_mgr.load_profile()
        self.assertEqual(cleaned_prof.privacy_and_telemetry["webhook_url"], "")
        self.assertEqual(cleaned_prof.privacy_and_telemetry["telemetry_mode"], "opt_out")

    def test_exit_scan_data_integrity_and_data_sharing(self):
        """Tests Exit Scan verifies overall data integrity and data sharing privacy."""
        # Create a mock telemetry log with an accidental raw key
        telemetry_dir = os.path.join(self.logs_dir, "telemetry")
        os.makedirs(telemetry_dir, exist_ok=True)
        telemetry_file = os.path.join(telemetry_dir, "anonymized_telemetry.jsonl")

        prof = self.user_mgr.get_profile()
        secret_key = "AIzaSySecretApiKey1234567890"
        prof.gemini["api_keys"] = [secret_key]
        self.user_mgr.save_profile(prof)

        with open(telemetry_file, "w", encoding="utf-8") as f:
            f.write(f'{{"event": "test", "raw_key": "{secret_key}"}}\n')

        # Also create a stray .tmp file in saves/
        stray_tmp = os.path.join(self.saves_dir, "checkpoint_corrupted.tmp")
        with open(stray_tmp, "w") as f:
            f.write("partial temp data")

        # Run exit scan
        exit_report = self.scanner.scan_exit(verbose=False)
        self.assertEqual(exit_report.phase, "EXIT")
        self.assertIn("data_integrity", exit_report.details)
        self.assertIn("data_sharing_privacy", exit_report.details)

        # Verify stray tmp file was cleaned
        self.assertFalse(os.path.exists(stray_tmp))

        # Verify secret key was scrubbed from telemetry
        with open(telemetry_file, "r", encoding="utf-8") as f:
            cleaned_content = f.read()
        self.assertNotIn(secret_key, cleaned_content)
        self.assertIn("[REDACTED_API_KEY]", cleaned_content)


if __name__ == "__main__":
    unittest.main()
