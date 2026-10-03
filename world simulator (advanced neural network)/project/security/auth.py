"""
project/security/auth.py

Role-Based Access Control (RBAC), Password Hashing, and Cryptographically Signed Token Engine.
Features:
- Permission bitmask hierarchies (ANONYMOUS, OBSERVER, CONTROLLER, ADMIN).
- Cryptographically signed HMAC-SHA256 tokens with expiry and client IP binding.
- PBKDF2-HMAC-SHA256 password hashing with unique salt generation.
- Dynamic token revocation / blacklist management.
"""

from __future__ import annotations

import base64
import enum
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


class Role(enum.Enum):
    ANONYMOUS = "ANONYMOUS"
    OBSERVER = "OBSERVER"
    CONTROLLER = "CONTROLLER"
    ADMIN = "ADMIN"


class Permission(enum.IntFlag):
    NONE = 0
    READ_TELEMETRY = 1 << 0
    READ_ENTITIES = 1 << 1
    CONTROL_SPEED = 1 << 2
    MUTATE_WORLD = 1 << 3
    SPAWN_ENTITIES = 1 << 4
    TRIGGER_DISASTER = 1 << 5
    SAVE_LOAD = 1 << 6
    ADMIN_CONFIG = 1 << 7
    ALL = (1 << 8) - 1


# Default Role Permission Mappings
ROLE_PERMISSIONS: Dict[Role, Permission] = {
    Role.ANONYMOUS: Permission.NONE,
    Role.OBSERVER: Permission.READ_TELEMETRY | Permission.READ_ENTITIES,
    Role.CONTROLLER: (
        Permission.READ_TELEMETRY
        | Permission.READ_ENTITIES
        | Permission.CONTROL_SPEED
    ),
    Role.ADMIN: Permission.ALL,
}


@dataclass
class SecurityToken:
    token_id: str
    user_id: str
    role: Role
    permissions: Permission
    issued_at: float
    expires_at: float
    bound_ip: Optional[str] = None
    signature: str = ""

    def is_expired(self, now: Optional[float] = None) -> bool:
        current = now if now is not None else time.time()
        return current > self.expires_at

    def has_permission(self, perm: Permission) -> bool:
        return (self.permissions & perm) == perm


class AuthManager:
    """
    Manages user credentials, PBKDF2 password authentication, and signed access tokens.
    """

    def __init__(self, secret_key: Optional[str] = None) -> None:
        # Generates strong 256-bit signing key if none provided
        self._secret_key = (secret_key or secrets.token_hex(32)).encode("utf-8")
        self._users: Dict[str, Dict[str, Any]] = {}
        self._revoked_tokens: Set[str] = set()

        # Seed default administrative credentials
        self._setup_default_users()

    def _setup_default_users(self) -> None:
        # Seed default admin user
        salt = secrets.token_hex(16)
        pwd_hash = self.hash_password("admin_alife_secure", salt)
        self._users["admin"] = {
            "user_id": "admin",
            "salt": salt,
            "hash": pwd_hash,
            "role": Role.ADMIN,
            "enabled": True,
        }

        # Seed default observer user
        obs_salt = secrets.token_hex(16)
        obs_hash = self.hash_password("observer_guest", obs_salt)
        self._users["observer"] = {
            "user_id": "observer",
            "salt": obs_salt,
            "hash": obs_hash,
            "role": Role.OBSERVER,
            "enabled": True,
        }

    @staticmethod
    def hash_password(password: str, salt: str, iterations: int = 100_000) -> str:
        """Derives salted key using PBKDF2-HMAC-SHA256."""
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return base64.b64encode(derived).decode("ascii")

    def register_user(self, user_id: str, password: str, role: Role = Role.OBSERVER) -> bool:
        """Registers a new user account."""
        if user_id in self._users:
            return False
        salt = secrets.token_hex(16)
        pwd_hash = self.hash_password(password, salt)
        self._users[user_id] = {
            "user_id": user_id,
            "salt": salt,
            "hash": pwd_hash,
            "role": role,
            "enabled": True,
        }
        return True

    def authenticate_credentials(self, user_id: str, password: str) -> Optional[Role]:
        """Validates username and password. Returns Role if authentic."""
        user = self._users.get(user_id)
        if not user or not user.get("enabled", False):
            return None

        salt = user["salt"]
        expected_hash = user["hash"]
        actual_hash = self.hash_password(password, salt)

        if hmac.compare_digest(expected_hash, actual_hash):
            return user["role"]
        return None

    def create_token(
        self,
        user_id: str,
        role: Role,
        duration_sec: float = 3600.0,
        bound_ip: Optional[str] = None,
        custom_permissions: Optional[Permission] = None,
    ) -> str:
        """
        Creates and signs a base64-encoded HMAC-SHA256 access token.
        Format: <header_b64>.<payload_b64>.<signature_hex>
        """
        now = time.time()
        tid = secrets.token_hex(16)
        perms = custom_permissions if custom_permissions is not None else ROLE_PERMISSIONS.get(role, Permission.NONE)

        payload_dict = {
            "tid": tid,
            "uid": user_id,
            "role": role.value,
            "perms": int(perms),
            "iat": now,
            "exp": now + duration_sec,
            "ip": bound_ip,
        }

        payload_json = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_json).decode("ascii").rstrip("=")

        # Compute HMAC signature over payload
        sig = hmac.new(self._secret_key, payload_b64.encode("ascii"), hashlib.sha256).hexdigest()

        return f"ALIFE.{payload_b64}.{sig}"

    def verify_token(
        self,
        token_str: str,
        client_ip: Optional[str] = None,
        required_permission: Permission = Permission.NONE,
    ) -> Tuple[bool, Optional[SecurityToken], str]:
        """
        Validates token signature, expiration, revocation, IP binding, and permissions.
        Returns: (is_valid, SecurityToken, reason)
        """
        parts = token_str.strip().split(".")
        if len(parts) != 3 or parts[0] != "ALIFE":
            return False, None, "Malformed token format"

        payload_b64 = parts[1]
        received_sig = parts[2]

        # Verify HMAC signature
        expected_sig = hmac.new(self._secret_key, payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, received_sig):
            return False, None, "Invalid cryptographic token signature"

        # Decode payload JSON
        try:
            # Re-pad base64
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            data = json.loads(payload_json)
        except Exception as e:
            return False, None, f"Corrupted token payload: {str(e)}"

        tid = data.get("tid", "")
        uid = data.get("uid", "")
        role_val = data.get("role", "ANONYMOUS")
        perms_int = data.get("perms", 0)
        iat = data.get("iat", 0.0)
        exp = data.get("exp", 0.0)
        bound_ip = data.get("ip")

        # Check Revocation
        if tid in self._revoked_tokens:
            return False, None, "Token has been revoked"

        # Check Expiration
        now = time.time()
        if now > exp:
            return False, None, f"Token expired {int(now - exp)} seconds ago"

        # Check IP Binding (if token was bound to specific IP)
        if bound_ip is not None and client_ip is not None:
            if bound_ip != client_ip:
                return False, None, f"Token IP mismatch (bound to {bound_ip}, request from {client_ip})"

        # Role & Permission parsing
        try:
            role = Role(role_val)
        except ValueError:
            role = Role.ANONYMOUS

        permissions = Permission(perms_int)

        # Check Required Permission
        if required_permission != Permission.NONE:
            if (permissions & required_permission) != required_permission:
                return False, None, f"Insufficient permissions: requires {required_permission.name}"

        token_obj = SecurityToken(
            token_id=tid,
            user_id=uid,
            role=role,
            permissions=permissions,
            issued_at=iat,
            expires_at=exp,
            bound_ip=bound_ip,
            signature=received_sig,
        )

        return True, token_obj, "Token verified successfully"

    def revoke_token(self, token_id: str) -> None:
        """Revokes a specific token ID."""
        self._revoked_tokens.add(token_id)

    def is_revoked(self, token_id: str) -> bool:
        return token_id in self._revoked_tokens
