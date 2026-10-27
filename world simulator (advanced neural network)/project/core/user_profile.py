"""
project/core/user_profile.py

User Profile, Local Preferences, and First-Time Setup State Manager.
Persists user preferences, telemetry consent, display options, and Gemini API keys
cleanly to user_profile.json.
"""

from __future__ import annotations

import os
import sys
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

# Safe UTF-8 reconfiguration for Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROFILE_FILE_NAME = "user_profile.json"
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROFILE_PATH = os.path.join(WORKSPACE_DIR, PROFILE_FILE_NAME)
SAVES_DIR = os.path.join(WORKSPACE_DIR, "saves")


@dataclass
class UserProfile:
    """Dataclass holding all user preferences and initial setup choices."""
    profile_version: str = "2.0"
    first_time_setup_completed: bool = False
    user_name: str = "Architect"
    created_at: float = field(default_factory=time.time)

    # Display & Visuals
    display: Dict[str, Any] = field(default_factory=lambda: {
        "width": 1280,
        "height": 720,
        "fullscreen": False,
        "theme": "minimalist_dark",
        "target_fps": 60,
    })

    # Telemetry & Consent
    privacy_and_telemetry: Dict[str, Any] = field(default_factory=lambda: {
        "consent_given": False,
        "telemetry_mode": "opt_out",  # "opt_out", "webhook", "local_only"
        "webhook_url": "",
        "world_data_level": "full",   # "summary", "deep", "full" (literally everything)
        "anonymized_client_id": f"anon_{uuid.uuid4().hex[:12]}",
    })

    # Gemini Cognition & Offline Mode
    gemini: Dict[str, Any] = field(default_factory=lambda: {
        "is_offline": False,
        "api_keys": [],
        "routing_strategy": "best_health",  # "best_health", "lowest_latency", "round_robin"
    })

    # Git-like Save Management
    git_save: Dict[str, Any] = field(default_factory=lambda: {
        "active_branch": "main",
        "auto_stash_conflict": True,
        "max_history": 50,
    })

    # Auto-Update Notifications
    updates: Dict[str, Any] = field(default_factory=lambda: {
        "auto_check": True,
        "last_checked": 0.0,
        "ignored_commit": "",
    })

    # Scanner & Security Credentials
    credentials: Dict[str, Any] = field(default_factory=lambda: {
        "role": "USER",
        "rank": "NOVICE_EXPLORER",
        "is_owner": False,
        "privileges": ["SIMULATE", "SAVE_LOAD", "REWIND", "VIEW_STATS", "SWITCH_WORLD"],
        "auth_token": "",
        "session_id": "",
        "last_boot_scan": 0.0,
        "last_periodic_scan": 0.0,
        "last_exit_scan": 0.0,
        "total_scans_performed": 0,
        "integrity_status": "SECURE",
    })


class UserProfileManager:
    """Manages reading, writing, and validating user_profile.json."""

    def __init__(self, profile_path: Optional[str] = None) -> None:
        self.profile_path = profile_path or PROFILE_PATH
        self._profile: Optional[UserProfile] = None

    def is_first_run(self) -> bool:
        """
        Determines whether the first-time setup wizard should be triggered.
        Returns True if:
        1. user_profile.json does not exist, OR
        2. first_time_setup_completed is False.
        """
        if not os.path.exists(self.profile_path):
            return True
        prof = self.get_profile()
        return not prof.first_time_setup_completed

    def get_profile(self) -> UserProfile:
        """Retrieves currently cached profile or loads it from disk."""
        if self._profile is None:
            self._profile = self.load_profile()
        return self._profile

    def load_profile(self) -> UserProfile:
        """Reads user_profile.json from disk, or initializes default if missing."""
        if not os.path.exists(self.profile_path):
            prof = UserProfile()
            # If no saves exist either, setup flag remains False
            return prof

        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            prof = UserProfile(
                profile_version=raw_data.get("profile_version", "2.0"),
                first_time_setup_completed=raw_data.get("first_time_setup_completed", False),
                user_name=raw_data.get("user_name", "Architect"),
                created_at=raw_data.get("created_at", time.time()),
                display=raw_data.get("display", {}),
                privacy_and_telemetry=raw_data.get("privacy_and_telemetry", {}),
                gemini=raw_data.get("gemini", {}),
                git_save=raw_data.get("git_save", {}),
                updates=raw_data.get("updates", {}),
                credentials=raw_data.get("credentials", {}),
            )
            # Ensure defaults for missing sub-keys
            if "anonymized_client_id" not in prof.privacy_and_telemetry:
                prof.privacy_and_telemetry["anonymized_client_id"] = f"anon_{uuid.uuid4().hex[:12]}"
            if not prof.credentials:
                prof.credentials = {
                    "role": "USER",
                    "rank": "NOVICE_EXPLORER",
                    "is_owner": False,
                    "privileges": ["SIMULATE", "SAVE_LOAD", "REWIND", "VIEW_STATS", "SWITCH_WORLD"],
                    "auth_token": "",
                    "session_id": "",
                    "last_boot_scan": 0.0,
                    "last_periodic_scan": 0.0,
                    "last_exit_scan": 0.0,
                    "total_scans_performed": 0,
                    "integrity_status": "SECURE",
                }
            self._profile = prof
            return prof
        except Exception as e:
            try:
                print(f"[USER PROFILE] Warning loading {self.profile_path}: {e}. Initializing clean defaults.")
            except Exception:
                pass
            return UserProfile()

    def save_profile(self, profile: Optional[UserProfile] = None) -> str:
        """Persists profile to disk cleanly."""
        if profile is not None:
            self._profile = profile
        elif self._profile is None:
            self._profile = UserProfile()

        data = asdict(self._profile)
        os.makedirs(os.path.dirname(os.path.abspath(self.profile_path)), exist_ok=True)
        temp_path = f"{self.profile_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        os.replace(temp_path, self.profile_path)
        return self.profile_path

    def complete_setup(self, setup_data: Dict[str, Any]) -> UserProfile:
        """Applies values collected during the first-time setup wizard and saves."""
        prof = self.get_profile()
        prof.first_time_setup_completed = True
        prof.user_name = setup_data.get("user_name", prof.user_name)

        if "display" in setup_data:
            prof.display.update(setup_data["display"])

        if "privacy_and_telemetry" in setup_data:
            prof.privacy_and_telemetry.update(setup_data["privacy_and_telemetry"])

        if "gemini" in setup_data:
            prof.gemini.update(setup_data["gemini"])

        if "git_save" in setup_data:
            prof.git_save.update(setup_data["git_save"])

        if "credentials" in setup_data:
            prof.credentials.update(setup_data["credentials"])

        self.save_profile(prof)
        try:
            print(f"✅ [FIRST-TIME SETUP] Profile configured successfully for '{prof.user_name}'. Saved to {self.profile_path}")
        except Exception:
            print(f"[FIRST-TIME SETUP] Profile configured successfully for '{prof.user_name}'. Saved to {self.profile_path}")
        return prof

    def add_gemini_key(self, key: str) -> None:
        """Registers a new Gemini API key into the user profile."""
        clean = key.strip()
        if not clean:
            return
        prof = self.get_profile()
        keys: List[str] = prof.gemini.setdefault("api_keys", [])
        if clean not in keys:
            keys.append(clean)
            prof.gemini["is_offline"] = False
            self.save_profile()

    def remove_gemini_key(self, index_or_key: Any) -> bool:
        """Removes a Gemini API key by index or value."""
        prof = self.get_profile()
        keys: List[str] = prof.gemini.setdefault("api_keys", [])
        removed = False
        if isinstance(index_or_key, int) and 0 <= index_or_key < len(keys):
            keys.pop(index_or_key)
            removed = True
        elif isinstance(index_or_key, str) and index_or_key in keys:
            keys.remove(index_or_key)
            removed = True

        if len(keys) == 0:
            prof.gemini["is_offline"] = True

        if removed:
            self.save_profile()
        return removed

    def set_offline_mode(self, is_offline: bool) -> None:
        """Sets offline mode status."""
        prof = self.get_profile()
        prof.gemini["is_offline"] = is_offline
        self.save_profile()

    def is_owner(self) -> bool:
        """Returns True if the current user profile has Owner credentials."""
        prof = self.get_profile()
        return bool(prof.credentials.get("is_owner", False))

    def get_rank(self) -> str:
        """Returns the current user rank."""
        prof = self.get_profile()
        return str(prof.credentials.get("rank", "NOVICE_EXPLORER"))

    def get_privileges(self) -> List[str]:
        """Returns list of privileges granted to the current user."""
        prof = self.get_profile()
        return list(prof.credentials.get("privileges", []))


# Singleton instance
user_profile_manager = UserProfileManager()
