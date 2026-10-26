"""
project/tests/test_updater.py

Unit and Integration Tests for Autonomous In-App Upgrades & 3-Step Verification Pipeline:
- Step 1: Security Verification (Origin, Path breakout, AST static screening, protected user files).
- Step 2: Code Reliability Pre-flight (Bytecode compilation, dry-run syntax screening, automatic rollback).
- Step 3: File Integrity & Manifest Tree Matching (Module presence, non-corruption, atomic commit stamping).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from project.core.updater import (
    UpdateChecker,
    UpdateManager,
    UpdateVerifier,
    UpdateInfo,
    SecurityVerificationError,
    CodeReliabilityError,
    IntegrityVerificationError,
    ASTSecurityScanner,
)


class TestUpdateSystem(unittest.TestCase):
    """Test suite for update verification, screening, and rollback mechanisms."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp(prefix="updater_test_")
        self.staged_dir = os.path.join(self.test_dir, "staged")
        os.makedirs(self.staged_dir, exist_ok=True)

        # Create valid mock simulation structure
        os.makedirs(os.path.join(self.staged_dir, "project", "core"), exist_ok=True)
        os.makedirs(os.path.join(self.staged_dir, "project", "systems"), exist_ok=True)

        with open(os.path.join(self.staged_dir, "run_gui.py"), "w", encoding="utf-8") as f:
            f.write("# Valid entrypoint\nprint('Simulation Running')\n")

        with open(os.path.join(self.staged_dir, "project", "core", "scheduler.py"), "w", encoding="utf-8") as f:
            f.write("class Scheduler:\n    pass\n")

        with open(os.path.join(self.staged_dir, "project", "core", "simulation.py"), "w", encoding="utf-8") as f:
            f.write("class SimulationEngine:\n    pass\n")

        with open(os.path.join(self.staged_dir, "project", "core", "persistence.py"), "w", encoding="utf-8") as f:
            f.write("class PersistenceManager:\n    pass\n")

        with open(os.path.join(self.staged_dir, "project", "systems", "security_system.py"), "w", encoding="utf-8") as f:
            f.write("class SecuritySystem:\n    pass\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Step 1: Security Verification Tests
    # -------------------------------------------------------------------------
    def test_step_1_security_valid_code_passes(self) -> None:
        """Valid simulation code passes Step 1 security screening."""
        UpdateVerifier.verify_step_1_security(self.staged_dir)

    def test_step_1_security_blocks_malicious_exec_eval(self) -> None:
        """Step 1 rejects obfuscated dynamic execution payloads."""
        malicious_file = os.path.join(self.staged_dir, "project", "core", "bad_script.py")
        with open(malicious_file, "w", encoding="utf-8") as f:
            f.write("import base64\neval(base64.b64decode('cHJpbnQoMSk='))\n")

        with self.assertRaises(SecurityVerificationError) as ctx:
            UpdateVerifier.verify_step_1_security(self.staged_dir)
        self.assertIn("Dangerous obfuscated dynamic code execution", str(ctx.exception))

    def test_step_1_security_blocks_unauthorized_binaries(self) -> None:
        """Step 1 rejects executable binary additions."""
        bad_bin = os.path.join(self.staged_dir, "malicious.exe")
        with open(bad_bin, "wb") as f:
            f.write(b"MZ\x90\x00")

        with self.assertRaises(SecurityVerificationError) as ctx:
            UpdateVerifier.verify_step_1_security(self.staged_dir)
        self.assertIn("Disallowed executable file", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 2. Step 2: Code Reliability Tests
    # -------------------------------------------------------------------------
    def test_step_2_reliability_valid_code_passes(self) -> None:
        """Clean Python files pass bytecode compilation dry-run."""
        UpdateVerifier.verify_step_2_reliability(self.staged_dir)

    def test_step_2_reliability_catches_syntax_errors(self) -> None:
        """Step 2 catches broken syntax before deployment."""
        broken_file = os.path.join(self.staged_dir, "project", "broken.py")
        with open(broken_file, "w", encoding="utf-8") as f:
            f.write("def invalid_syntax(\n")

        with self.assertRaises(CodeReliabilityError) as ctx:
            UpdateVerifier.verify_step_2_reliability(self.staged_dir)
        self.assertIn("Syntax or compilation error", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 3. Step 3: File Integrity & Tree Matching Tests
    # -------------------------------------------------------------------------
    def test_step_3_integrity_valid_tree_passes(self) -> None:
        """Complete file structure passes integrity check."""
        UpdateVerifier.verify_step_3_integrity(self.staged_dir, "mock_sha")

    def test_step_3_integrity_detects_missing_core_file(self) -> None:
        """Step 3 flags missing essential simulation files."""
        os.remove(os.path.join(self.staged_dir, "run_gui.py"))
        with self.assertRaises(IntegrityVerificationError) as ctx:
            UpdateVerifier.verify_step_3_integrity(self.staged_dir, "mock_sha")
        self.assertIn("missing from update", str(ctx.exception))

    def test_step_3_integrity_detects_empty_file(self) -> None:
        """Step 3 flags corrupt 0-byte core files."""
        sched_path = os.path.join(self.staged_dir, "project", "core", "scheduler.py")
        with open(sched_path, "w", encoding="utf-8") as f:
            f.write("")

        with self.assertRaises(IntegrityVerificationError) as ctx:
            UpdateVerifier.verify_step_3_integrity(self.staged_dir, "mock_sha")
        self.assertIn("is empty", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 4. End-to-End Manager & Protected User Data Shield Tests
    # -------------------------------------------------------------------------
    def test_update_manager_shields_protected_files(self) -> None:
        """Confirms user_profile.json, saves, and .env are never overwritten by update."""
        manager = UpdateManager(workspace_dir=self.test_dir)

        # Create user profile and save file in workspace
        profile_path = os.path.join(self.test_dir, "user_profile.json")
        with open(profile_path, "w", encoding="utf-8") as f:
            f.write('{"user_name": "OriginalArchitect"}')

        save_dir = os.path.join(self.test_dir, "saves")
        os.makedirs(save_dir, exist_ok=True)
        save_file = os.path.join(save_dir, "my_save.dat")
        with open(save_file, "w", encoding="utf-8") as f:
            f.write("User Save Data")

        # Staged update contains an attempt to overwrite user_profile.json
        staged_profile = os.path.join(self.staged_dir, "user_profile.json")
        with open(staged_profile, "w", encoding="utf-8") as f:
            f.write('{"user_name": "Overwritten"}')

        # Deploy
        manager._deploy_from_staging(self.staged_dir)

        # Verify user_profile.json was NOT overwritten
        with open(profile_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("OriginalArchitect", content)
        self.assertNotIn("Overwritten", content)

        # Verify saves are untouched
        self.assertTrue(os.path.exists(save_file))

    def test_update_checker_github_mock(self) -> None:
        """Tests GitHub remote check parsing."""
        manager = UpdateManager(workspace_dir=self.test_dir)
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b'{"sha": "abcdef123456", "commit": {"message": "New mechanics", "author": {"name": "owner", "date": "2026-10-25"}}}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            info = manager.check_for_updates(force=True)
            self.assertEqual(info.remote_commit, "abcdef1")
            self.assertEqual(info.commit_message, "New mechanics")
            self.assertTrue(info.has_update)


if __name__ == "__main__":
    unittest.main()
