"""
project/security/__init__.py

Advanced Local and Public Network Security Subsystem for the Echo Evolution Simulator.
"""

from project.security.firewall import DualZoneFirewall, NetworkZone, BanRecord
from project.security.rate_limiter import MultiTierRateLimiter, ZoneRatePolicy, RateBucket
from project.security.ids import IntrusionDetectionSystem, ThreatLevel, ThreatProfile
from project.security.auth import (
    AuthManager,
    Role,
    Permission,
    SecurityToken,
    ROLE_PERMISSIONS,
)
from project.security.crypto import CryptoEngine
from project.security.vault import SecureKeyVault
from project.security.sanitizer import PayloadSanitizer
from project.security.audit import (
    SecurityAuditLogger,
    SecurityAuditEvent,
    SecuritySeverity,
)

__all__ = [
    # Firewall
    "DualZoneFirewall",
    "NetworkZone",
    "BanRecord",
    # Rate Limiter
    "MultiTierRateLimiter",
    "ZoneRatePolicy",
    "RateBucket",
    # IDS / IPS
    "IntrusionDetectionSystem",
    "ThreatLevel",
    "ThreatProfile",
    # Auth & RBAC
    "AuthManager",
    "Role",
    "Permission",
    "SecurityToken",
    "ROLE_PERMISSIONS",
    # Cryptography
    "CryptoEngine",
    # Vault & SSRF
    "SecureKeyVault",
    # Sanitization
    "PayloadSanitizer",
    # Audit Logger
    "SecurityAuditLogger",
    "SecurityAuditEvent",
    "SecuritySeverity",
]
