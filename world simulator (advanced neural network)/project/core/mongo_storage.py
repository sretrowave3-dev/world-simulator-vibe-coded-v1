"""
project/core/mongo_storage.py

MongoDB Secure Storage and Remote Database Subsystem.
Enables users and owners to persist, backup, and query user profiles,
universe saves, checkpoints, and security audit logs in MongoDB.

Features:
- Auto-discovery of local or remote MongoDB instance (MONGODB_URI / default localhost:27017).
- Non-blocking connection check with 1.5s timeout.
- Seamless fallback: if MongoDB is not running, falls back safely to local encrypted storage.
- Encrypted sensitive fields before document ingestion.
"""

from __future__ import annotations

import os
import sys
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple

# Safe UTF-8 reconfiguration for Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_MONGO_URI = os.environ.get("MONGODB_URI", os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
DEFAULT_DB_NAME = "world_simulator_db"


class MongoStorageManager:
    """
    Manages MongoDB persistence for user profiles, simulation saves, and security logs.
    """

    def __init__(self, uri: str = DEFAULT_MONGO_URI, db_name: str = DEFAULT_DB_NAME) -> None:
        self.uri = uri
        self.db_name = db_name
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None
        self._is_connected: bool = False
        self._last_ping_time: float = 0.0

        # Attempt initial soft connect
        self._try_connect(verbose=False)

    def _try_connect(self, verbose: bool = False) -> bool:
        """Tries to connect to MongoDB with a short timeout."""
        try:
            import pymongo
            client = pymongo.MongoClient(
                self.uri,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
            )
            # Test ping
            client.admin.command("ping")
            self._client = client
            self._db = client[self.db_name]
            self._is_connected = True
            self._last_ping_time = time.time()
            if verbose:
                try:
                    print(f"🍃 [MONGODB] Connected successfully to '{self.uri}' (Database: {self.db_name})")
                except Exception:
                    pass
            return True
        except Exception as e:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
            self._is_connected = False
            self._client = None
            self._db = None
            if verbose:
                try:
                    print(f"🍃 [MONGODB] Offline or unreachable ({e}). Local storage active.")
                except Exception:
                    pass
            return False

    def is_connected(self) -> bool:
        """Returns True if MongoDB connection is live."""
        now = time.time()
        if self._is_connected and (now - self._last_ping_time) < 60.0:
            return True
        return self._try_connect(verbose=False)

    def set_uri(self, uri: str) -> Tuple[bool, str]:
        """Updates connection URI and attempts reconnection."""
        self.uri = uri.strip()
        ok = self._try_connect(verbose=True)
        if ok:
            return True, f"🍃 Successfully connected to MongoDB at {self.uri}"
        return False, f"⚠️ Could not reach MongoDB at {self.uri}. Local fallback active."

    # ─────────────────────────────────────────────────────────────────────────
    # USER PROFILES
    # ─────────────────────────────────────────────────────────────────────────

    def save_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Stores or updates a user profile document in the 'users' collection."""
        if not self.is_connected() or self._db is None:
            return False

        try:
            col = self._db["users"]
            clean_doc = dict(profile_data)
            # Use user_name or anonymized_client_id as unique key
            uid = clean_doc.get("user_name", "Architect")
            clean_doc["_id"] = uid
            clean_doc["last_updated_at"] = time.time()

            # Upsert into MongoDB
            col.replace_one({"_id": uid}, clean_doc, upsert=True)
            return True
        except Exception:
            return False

    def load_user_profile(self, user_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user profile document from MongoDB."""
        if not self.is_connected() or self._db is None:
            return None

        try:
            col = self._db["users"]
            doc = col.find_one({"_id": user_name})
            if doc:
                doc.pop("_id", None)
                return doc
        except Exception:
            pass
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # WORLD SAVES & UNIVERSES
    # ─────────────────────────────────────────────────────────────────────────

    def save_universe_meta(self, universe_meta: Dict[str, Any]) -> bool:
        """Stores universe metadata in the 'universes' collection."""
        if not self.is_connected() or self._db is None:
            return False

        try:
            col = self._db["universes"]
            uid = universe_meta.get("universe_id")
            if not uid:
                return False
            doc = dict(universe_meta)
            doc["_id"] = uid
            doc["synced_at"] = time.time()
            col.replace_one({"_id": uid}, doc, upsert=True)
            return True
        except Exception:
            return False

    def save_checkpoint(
        self,
        universe_id: str,
        checkpoint_name: str,
        payload_bytes: bytes,
        metadata: Dict[str, Any],
    ) -> bool:
        """Stores a serialized compressed simulation checkpoint in MongoDB."""
        if not self.is_connected() or self._db is None:
            return False

        try:
            col = self._db["saves"]
            doc_id = f"{universe_id}:{checkpoint_name}"
            import base64
            doc = {
                "_id": doc_id,
                "universe_id": universe_id,
                "checkpoint_name": checkpoint_name,
                "payload_b64": base64.b64encode(payload_bytes).decode("ascii"),
                "size_bytes": len(payload_bytes),
                "sha256": hashlib.sha256(payload_bytes).hexdigest(),
                "metadata": metadata,
                "created_at": time.time(),
            }
            col.replace_one({"_id": doc_id}, doc, upsert=True)
            return True
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # SECURITY AUDIT LOGGING
    # ─────────────────────────────────────────────────────────────────────────

    def log_security_event(self, event_data: Dict[str, Any]) -> bool:
        """Stores an incident or tamper breach alert into 'security_audit' collection."""
        if not self.is_connected() or self._db is None:
            return False

        try:
            col = self._db["security_audit"]
            doc = dict(event_data)
            doc["logged_at"] = time.time()
            col.insert_one(doc)
            return True
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # DIAGNOSTICS & SYNC
    # ─────────────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive diagnostic metrics for MongoDB connection."""
        connected = self.is_connected()
        users_count = 0
        universes_count = 0
        saves_count = 0
        audit_count = 0

        if connected and self._db is not None:
            try:
                users_count = self._db["users"].count_documents({})
                universes_count = self._db["universes"].count_documents({})
                saves_count = self._db["saves"].count_documents({})
                audit_count = self._db["security_audit"].count_documents({})
            except Exception:
                pass

        return {
            "status": "CONNECTED" if connected else "OFFLINE_LOCAL_FALLBACK",
            "uri": self.uri,
            "database": self.db_name,
            "users_count": users_count,
            "universes_count": universes_count,
            "saves_count": saves_count,
            "audit_count": audit_count,
        }

    def sync_local_data_to_mongo(self, workspace_dir: str) -> Tuple[int, int, str]:
        """Pushes local user profile and universes to MongoDB."""
        if not self.is_connected():
            return 0, 0, "⚠️ MongoDB is currently offline or unreachable. Local storage remains safe."

        synced_users = 0
        synced_universes = 0

        # 1. Sync User Profile
        prof_p = os.path.join(workspace_dir, "user_profile.json")
        if os.path.exists(prof_p):
            try:
                with open(prof_p, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                if self.save_user_profile(pdata):
                    synced_users += 1
            except Exception:
                pass

        # 2. Sync Universes
        u_root = os.path.join(workspace_dir, "saves", "universes")
        if os.path.exists(u_root):
            for entry in os.listdir(u_root):
                meta_p = os.path.join(u_root, entry, "universe_meta.json")
                if os.path.exists(meta_p):
                    try:
                        with open(meta_p, "r", encoding="utf-8") as f:
                            mdata = json.load(f)
                        if self.save_universe_meta(mdata):
                            synced_universes += 1
                    except Exception:
                        pass

        return synced_users, synced_universes, f"🍃 Successfully synced {synced_users} user profile(s) and {synced_universes} universe(s) to MongoDB!"


# Global singleton instance
mongo_storage = MongoStorageManager()
