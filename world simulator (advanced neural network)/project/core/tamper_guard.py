"""
project/core/tamper_guard.py

Anti-Tampering Engine and Cryptographic Security Manifest Subsystem.
Enforces security file integrity, prevents unauthorized local tampering with security files,
dispatches emergency breach telemetry alerts to Discord, cuts down online connectivity,
and locks down tampered non-owner simulator instances.

Core Policy:
- Standard users may modify world logic, biology, simulation parameters, terrain, and scenarios.
- Security files (project/security/*, scanner, tamper guard, telemetry config, security system)
  are strictly protected by an authenticated encrypted manifest (.security_manifest.enc).
- If non-owner tampers with security files:
  1. Dispatches immediate Discord webhook alert to DEFAULT_OWNER_WEBHOOK.
  2. Immediately severs online connection (offline mode, GitHub push cutoff, API severance).
  3. Activates program lockdown (halts simulation, locks interface).
- Verified Owner on the authorized workstation may edit security files and re-seal the manifest.
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import urllib.request
import urllib.error
import threading
import hashlib
import platform
import getpass
from typing import Dict, Any, List, Optional, Tuple, Set

# Safe UTF-8 reconfiguration for Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from project.security.crypto import CryptoEngine
from project.core.telemetry_config import DEFAULT_OWNER_WEBHOOK

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SECURITY_DIR = os.path.join(WORKSPACE_DIR, "project", "security")
MANIFEST_FILE_NAME = ".security_manifest.enc"
PRIMARY_MANIFEST_PATH = os.path.join(SECURITY_DIR, MANIFEST_FILE_NAME)
FALLBACK_MANIFEST_PATH = os.path.join(WORKSPACE_DIR, MANIFEST_FILE_NAME)
OWNER_MACHINE_FILE = os.path.join(WORKSPACE_DIR, ".owner_machine.json")

# Master cryptographic signing key for the manifest
MANIFEST_SECRET_KEY = b"ECHO_WORLD_SIMULATOR_SOVEREIGN_MANIFEST_SECRET_2026_V1"

# Explicit list of protected security files (normalized relative paths with forward slashes)
PROTECTED_SECURITY_FILES: List[str] = [
    "project/security/__init__.py",
    "project/security/audit.py",
    "project/security/auth.py",
    "project/security/crypto.py",
    "project/security/firewall.py",
    "project/security/ids.py",
    "project/security/rate_limiter.py",
    "project/security/sanitizer.py",
    "project/security/spec_protector.py",
    "project/security/vault.py",
    "project/core/lightweight_scanner.py",
    "project/core/tamper_guard.py",
    "project/core/user_profile.py",
    "project/core/telemetry_config.py",
    "project/systems/security_system.py",
]


class TamperGuard:
    """
    Guards core security files against unauthorized tampering using authenticated encryption.
    """

    def __init__(self, workspace_dir: Optional[str] = None) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir or WORKSPACE_DIR)
        self.manifest_path = os.path.join(self.workspace_dir, "project", "security", MANIFEST_FILE_NAME)
        self.crypto = CryptoEngine(default_shared_key=MANIFEST_SECRET_KEY.decode("latin1"))

        # Lockdown and network severance flags
        self.is_locked: bool = False
        self.network_severed: bool = False
        self.lockdown_reason: str = ""
        self.tampered_files_detected: List[str] = []
        self._last_verification_time: float = 0.0

        # Auto-seal manifest on initialization if missing and on owner workstation
        if not os.path.exists(self.manifest_path) and self.is_owner_workstation():
            self.seal_manifest()

    def is_owner_workstation(self) -> bool:
        """
        Determines if current host PC is the permanently authorized Owner workstation.
        Checks machine hostname and Windows username against .owner_machine.json.
        """
        # 1. Check environment overrides
        if os.environ.get("SIMULATOR_ROLE", "").upper() == "OWNER" or os.environ.get("SIMULATOR_OWNER") in ("1", "true", "True"):
            return True

        current_machine = os.environ.get("COMPUTERNAME") or platform.node() or ""
        try:
            current_user = os.environ.get("USERNAME") or getpass.getuser() or ""
        except Exception:
            current_user = ""

        # Check owner machine file in workspace or parent
        candidate_paths = [
            os.path.join(self.workspace_dir, ".owner_machine.json"),
            os.path.join(self.workspace_dir, "..", ".owner_machine.json"),
            OWNER_MACHINE_FILE,
        ]

        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    auth_machine = data.get("machine_name", "")
                    auth_user = data.get("user_account", "")
                    perm = data.get("permanent_clearance", False)

                    if perm and auth_machine and current_machine.upper() == auth_machine.upper():
                        if not auth_user or current_user.lower() == auth_user.lower():
                            return True
                except Exception:
                    pass

        # Recognized permanent fallback host
        if current_machine.upper() == "LAPTOP-M93BDH5R" and current_user.lower() == "hp":
            return True

        return False

    def _compute_file_sha256(self, rel_path: str) -> Optional[str]:
        """Calculates SHA-256 digest of a protected file."""
        norm_path = rel_path.replace("/", os.sep).replace("\\", os.sep)
        full_path = os.path.join(self.workspace_dir, norm_path)
        if not os.path.isfile(full_path):
            return None
        try:
            with open(full_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

    def seal_manifest(self) -> Tuple[bool, str]:
        """
        Recomputes cryptographic SHA-256 signatures of all protected security files,
        encrypts the manifest using CryptoEngine (HMAC-authenticated CTR mode),
        and persists it to .security_manifest.enc.
        """
        signatures: Dict[str, str] = {}
        for rel_file in PROTECTED_SECURITY_FILES:
            h = self._compute_file_sha256(rel_file)
            if h is not None:
                signatures[rel_file] = h

        payload = {
            "version": "2.0-SOVEREIGN",
            "sealed_by": "sretrowave3-dev",
            "timestamp": time.time(),
            "machine": os.environ.get("COMPUTERNAME", platform.node()),
            "protected_files_count": len(signatures),
            "signatures": signatures,
        }

        try:
            raw_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            enc_dict = self.crypto.encrypt_bytes(raw_bytes, key=MANIFEST_SECRET_KEY)
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(enc_dict, f, indent=2)

            # Also write fallback in root
            try:
                root_fallback = os.path.join(self.workspace_dir, MANIFEST_FILE_NAME)
                with open(root_fallback, "w", encoding="utf-8") as rf:
                    json.dump(enc_dict, rf, indent=2)
            except Exception:
                pass

            # Clear lockdown if owner re-seals
            self.is_locked = False
            self.tampered_files_detected.clear()
            self.lockdown_reason = ""

            return True, f"🔒 [TAMPER GUARD] Sealed {len(signatures)} security files into encrypted manifest ({self.manifest_path})"
        except Exception as e:
            return False, f"❌ [TAMPER GUARD] Failed to seal manifest: {e}"

    def verify_integrity(self) -> Tuple[bool, List[str], str]:
        """
        Decrypts .security_manifest.enc and verifies the cryptographic hash
        of each protected security file against its stored signature.
        Returns: (is_intact, list_of_tampered_files, reason)
        """
        self._last_verification_time = time.time()

        target_manifest = self.manifest_path
        if not os.path.exists(target_manifest):
            # Check fallback in root
            root_fallback = os.path.join(self.workspace_dir, MANIFEST_FILE_NAME)
            if os.path.exists(root_fallback):
                target_manifest = root_fallback
            else:
                if self.is_owner_workstation():
                    self.seal_manifest()
                    return True, [], "Manifest initialized and sealed on Owner workstation"
                return False, ["MANIFEST_MISSING"], "Security manifest (.security_manifest.enc) is missing"

        # Load and decrypt
        try:
            with open(target_manifest, "r", encoding="utf-8") as f:
                enc_dict = json.load(f)
            decrypted_bytes = self.crypto.decrypt_bytes(enc_dict, key=MANIFEST_SECRET_KEY)
            if decrypted_bytes is None:
                return False, ["MANIFEST_AUTHENTICATION_FAILED"], "Encrypted manifest HMAC authentication failed (tampering detected)"
            manifest_data = json.loads(decrypted_bytes.decode("utf-8"))
        except Exception as e:
            return False, ["MANIFEST_CORRUPT"], f"Failed to decrypt or parse security manifest: {e}"

        stored_signatures: Dict[str, str] = manifest_data.get("signatures", {})
        tampered_files: List[str] = []

        for rel_file, expected_hash in stored_signatures.items():
            current_hash = self._compute_file_sha256(rel_file)
            if current_hash is None:
                tampered_files.append(f"{rel_file} (DELETED/UNREADABLE)")
            elif current_hash != expected_hash:
                tampered_files.append(f"{rel_file} (MODIFIED)")

        if tampered_files:
            return False, tampered_files, f"Unauthorized changes detected in {len(tampered_files)} security file(s)"

        return True, [], "All protected security files verified intact"

    def handle_tamper_breach(
        self,
        tampered_files: List[str],
        is_owner: Optional[bool] = None,
        user_name: str = "UnknownUser",
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Executes immediate breach enforcement when security files are modified.
        - If Owner: alerts in console without locking down; prompts to re-seal.
        - If Non-Owner:
          1. Alerts Discord webhook immediately with intruder telemetry.
          2. Cuts down online connectivity (offline mode + severing push/updates).
          3. Activates permanent program lockdown.
        Returns True if lockdown was engaged, False if owner or bypassed.
        """
        self.tampered_files_detected = list(tampered_files)

        # 1. Owner development bypass
        effective_owner = self.is_owner_workstation() if is_owner is None else is_owner
        if effective_owner:
            try:
                print(f"\n⚠️  [TAMPER GUARD NOTICE] Security file modification detected on Owner workstation:")
                for tf in tampered_files[:5]:
                    print(f"   - {tf}")
                print("   👑 Development Mode: System lockdown bypassed for Owner.")
                print("   👉 Run 'sec seal' in terminal to update the encrypted manifest with your changes.\n")
            except Exception:
                pass
            return False

        # 2. NON-OWNER: ENGAGE IMMEDIATE LOCKDOWN & SEVERANCE
        self.is_locked = True
        self.network_severed = True
        self.lockdown_reason = f"Security subsystem modified without authorization ({len(tampered_files)} file(s))"

        machine_name = os.environ.get("COMPUTERNAME", platform.node())
        try:
            user_account = os.environ.get("USERNAME", getpass.getuser())
        except Exception:
            user_account = "unknown"

        # Sever online connection via user_profile
        try:
            from project.core.user_profile import user_profile_manager
            prof = user_profile_manager.get_profile()
            prof.gemini["is_offline"] = True
            prof.credentials["integrity_status"] = "BREACH_LOCKDOWN"
            prof.credentials["privileges"] = []
            prof.credentials["role"] = "UNAUTHORIZED_MODIFIER"
            user_profile_manager.save_profile(prof)
        except Exception:
            pass

        # Log to security audit
        audit_event = {
            "event": "CRITICAL_SECURITY_BREACH",
            "type": "SECURITY_FILES_TAMPERED",
            "timestamp": time.time(),
            "user_name": user_name,
            "machine": machine_name,
            "user_account": user_account,
            "tampered_files": tampered_files,
            "action": "LOCKDOWN_ENGAGED_NETWORK_SEVERED",
        }
        try:
            audit_log_p = os.path.join(self.workspace_dir, "security_audit.jsonl")
            with open(audit_log_p, "a", encoding="utf-8") as af:
                af.write(json.dumps(audit_event) + "\n")
        except Exception:
            pass

        # Log to MongoDB if accessible
        try:
            from project.core.mongo_storage import mongo_storage
            mongo_storage.log_security_event(audit_event)
        except Exception:
            pass

        # 3. Emergency Discord Webhook Dispatch (Async Thread)
        hook = webhook_url or DEFAULT_OWNER_WEBHOOK
        if hook:
            threading.Thread(
                target=self._dispatch_discord_breach_alert,
                args=(hook, user_name, machine_name, user_account, tampered_files),
                daemon=True,
                name="breach-alert-dispatcher",
            ).start()

        # 4. Print prominent terminal lockdown banner
        self._print_terminal_lockdown_screen(tampered_files)

        return True

    def _dispatch_discord_breach_alert(
        self,
        webhook_url: str,
        user_name: str,
        machine_name: str,
        user_account: str,
        tampered_files: List[str],
    ) -> None:
        """Transmits emergency Discord webhook alert with intrusion telemetry."""
        files_text = "\n".join(f"• `{f}`" for f in tampered_files[:8])
        if len(tampered_files) > 8:
            files_text += f"\n• ... and {len(tampered_files) - 8} more"

        payload = {
            "username": "ECHO Security Guard",
            "avatar_url": "https://raw.githubusercontent.com/sretrowave3-dev/world-simulator-vibe-coded-v1/main/assets/security_shield.png",
            "embeds": [
                {
                    "title": "🚨 CRITICAL SECURITY ALERT: Security Subsystem Tampered!",
                    "description": (
                        "An unauthorized client has modified core security subsystem files.\n"
                        "Immediate defensive countermeasures have been executed."
                    ),
                    "color": 0xED4245,  # Discord Red
                    "fields": [
                        {
                            "name": "👤 Client Identity",
                            "value": f"**Username**: `{user_name}`\n**Machine**: `{machine_name}`\n**OS User**: `{user_account}`",
                            "inline": True,
                        },
                        {
                            "name": "🛡️ Countermeasures Executed",
                            "value": "⛔ **Network Connections Severed**\n🔒 **Simulator Execution Locked**\n🚫 **GitHub Push Access Terminated**",
                            "inline": True,
                        },
                        {
                            "name": "📂 Tampered Security Files",
                            "value": files_text or "Manifest integrity check failed",
                            "inline": False,
                        },
                        {
                            "name": "🕒 Timestamp",
                            "value": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                            "inline": False,
                        },
                    ],
                    "footer": {
                        "text": "World Simulator Sovereign Anti-Tamper Engine v2.2",
                    },
                }
            ],
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WorldSimulator-TamperGuard/2.2",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                _ = resp.read()
        except Exception:
            pass

    def _print_terminal_lockdown_screen(self, tampered_files: List[str]) -> None:
        """Renders ASCII terminal lockdown banner."""
        try:
            print("\n" + "═" * 80)
            print("🚨 CRITICAL SECURITY ALERT: SIMULATOR EXECUTION LOCKED DOWN 🚨")
            print("═" * 80)
            print("❌ Unauthorized modification of protected security files detected!")
            print("   Non-owner users are strictly forbidden from modifying security subsystems.")
            print("\nTampered File(s):")
            for f in tampered_files[:6]:
                print(f"   • {f}")
            print("\nDefensive Countermeasures Activated:")
            print("   ⛔ Online connection to GitHub and server: SEVERED (Offline Mode Active)")
            print("   🔒 Program instance: LOCKED DOWN (Simulation frozen)")
            print("   📡 Incident telemetry dispatched to repository Owner.")
            print("═" * 80)
            print("Contact the project owner (sretrowave3-dev) to restore clearance.")
            print("═" * 80 + "\n")
        except Exception:
            pass

    def render_gui_lockdown_message(self) -> Dict[str, Any]:
        """Provides status dict for GUI overlay rendering."""
        return {
            "is_locked": self.is_locked,
            "reason": self.lockdown_reason,
            "tampered_files": list(self.tampered_files_detected),
            "network_severed": self.network_severed,
        }


# Global singleton instance
tamper_guard = TamperGuard()
