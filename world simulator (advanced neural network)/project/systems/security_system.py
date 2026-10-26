"""
project/systems/security_system.py

Master Security System running inside the Scheduler execution pipeline.
Features:
- Coordinates Firewall, Rate Limiter, IDS/IPS, RBAC Auth, and Cryptography.
- Periodic cleanup of expired dynamic bans and decaying threat profiles.
- Integrated pipeline entrypoint for evaluating inbound network requests.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Set, Tuple, Any
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.security.firewall import DualZoneFirewall, NetworkZone
from project.security.rate_limiter import MultiTierRateLimiter
from project.security.ids import IntrusionDetectionSystem, ThreatLevel
from project.security.auth import AuthManager, Role, Permission, SecurityToken
from project.security.crypto import CryptoEngine
from project.security.vault import SecureKeyVault
from project.security.sanitizer import PayloadSanitizer
from project.security.audit import SecurityAuditLogger, SecuritySeverity

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SecuritySystem:
    """
    Scheduler-managed security coordinator protecting the simulation against network threats.
    """

    def __init__(
        self,
        firewall: Optional[DualZoneFirewall] = None,
        rate_limiter: Optional[MultiTierRateLimiter] = None,
        ids: Optional[IntrusionDetectionSystem] = None,
        auth_mgr: Optional[AuthManager] = None,
        crypto: Optional[CryptoEngine] = None,
        vault: Optional[SecureKeyVault] = None,
        audit_logger: Optional[SecurityAuditLogger] = None,
        audit_log_path: str = "security_audit.jsonl",
    ) -> None:
        self.firewall = firewall or DualZoneFirewall()
        self.rate_limiter = rate_limiter or MultiTierRateLimiter()
        self.ids = ids or IntrusionDetectionSystem(firewall=self.firewall)
        self.auth_mgr = auth_mgr or AuthManager()
        self.crypto = crypto or CryptoEngine()
        self.vault = vault or SecureKeyVault()
        self.audit_logger = audit_logger or SecurityAuditLogger()
        if audit_log_path and not os.path.isabs(audit_log_path):
            self.audit_log_path = os.path.join(WORKSPACE_DIR, audit_log_path)
        else:
            self.audit_log_path = audit_log_path

    @property
    def name(self) -> str:
        return "SecuritySystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.PRE_UPDATE

    @property
    def priority(self) -> int:
        return ExecutionPriority.SECURITY

    @property
    def dependencies(self) -> Set[str]:
        return set()

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self.audit_logger.log_event(
            severity=SecuritySeverity.INFO,
            event_type="SECURITY_SYSTEM_INIT",
            details="Network security subsystem initialized and active",
        )

    def update(self, context: UpdateContext) -> None:
        try:
            # 1. Clean expired bans & idle rate limiters every 60 ticks (approx 1 sec)
            if context.tick > 0 and context.tick % 60 == 0:
                pruned_bans = self.firewall.clean_expired_bans()
                self.rate_limiter.prune_idle_buckets()
                self.ids.prune_clean_profiles()
                if pruned_bans > 0:
                    self.audit_logger.log_event(
                        severity=SecuritySeverity.INFO,
                        event_type="BANS_PRUNED",
                        details=f"Pruned {pruned_bans} expired dynamic ban(s)",
                    )
        except Exception:
            pass

        # 2. Flush audit logs every 600 ticks (approx 10 sec)
        if context.tick > 0 and context.tick % 600 == 0:
            try:
                if self.audit_log_path and os.path.dirname(self.audit_log_path):
                    os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
                self.audit_logger.flush_to_jsonl(self.audit_log_path)
            except Exception:
                pass

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        # Flush remaining audit logs on shutdown
        try:
            if self.audit_log_path and os.path.dirname(self.audit_log_path):
                os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
            self.audit_logger.flush_to_jsonl(self.audit_log_path)
        except Exception:
            pass

    def process_inbound_request(
        self,
        ip_str: str,
        raw_payload: str,
        token_str: Optional[str] = None,
        required_perm: Permission = Permission.NONE,
        request_cost: float = 1.0,
    ) -> Tuple[bool, Optional[Any], str]:
        """
        Complete end-to-end security pipeline evaluation for incoming requests.
        Returns: (is_allowed, parsed_data_if_valid, reason)
        """
        # Step 1: Firewall Zone & Ban Evaluation
        allowed, zone, fw_reason = self.firewall.is_allowed(ip_str)
        if not allowed:
            self.audit_logger.log_event(
                severity=SecuritySeverity.WARNING,
                event_type="FIREWALL_DROP",
                client_ip=ip_str,
                zone=zone,
                details=fw_reason,
            )
            return False, None, f"Access Denied by Firewall: {fw_reason}"

        # Step 2: Multi-Tier Rate Limiting
        rl_allowed, wait_sec, rl_meta = self.rate_limiter.allow_request(ip_str, zone=zone, cost=request_cost)
        if not rl_allowed:
            self.ids.record_violation(ip_str, "RATE_LIMIT_FLOOD", details=f"Wait required: {wait_sec:.1f}s")
            self.audit_logger.log_event(
                severity=SecuritySeverity.WARNING,
                event_type="RATE_LIMIT_THROTTLED",
                client_ip=ip_str,
                zone=zone,
                details=f"Rate limit exceeded (wait {wait_sec:.1f}s)",
                metadata=rl_meta,
            )
            return False, None, f"Rate Limit Exceeded (Retry after {wait_sec:.1f}s)"

        # Step 3: Payload Sanitization & Depth Bomb Check
        san_ok, parsed_json, san_reason = PayloadSanitizer.parse_and_sanitize_json(raw_payload)
        if not san_ok:
            self.ids.record_violation(ip_str, "MALFORMED_PAYLOAD", details=san_reason)
            self.audit_logger.log_event(
                severity=SecuritySeverity.SECURITY_ALERT,
                event_type="PAYLOAD_SANITIZATION_FAILED",
                client_ip=ip_str,
                zone=zone,
                details=san_reason,
            )
            return False, None, f"Payload Rejected: {san_reason}"

        # Step 4: IDS Exploit & Injection Signature Scan
        ids_ok, threats, _ = self.ids.inspect_payload(ip_str, raw_payload)
        if not ids_ok:
            self.audit_logger.log_event(
                severity=SecuritySeverity.CRITICAL_ATTACK,
                event_type="IDS_EXPLOIT_DETECTED",
                client_ip=ip_str,
                zone=zone,
                details=f"Threat signatures: {', '.join(threats)}",
            )
            return False, None, f"Intrusion Detection: Malicious signature detected ({', '.join(threats)})"

        # Step 5: RBAC Token & Permission Verification (if required)
        if token_str or required_perm != Permission.NONE:
            if not token_str:
                self.audit_logger.log_event(
                    severity=SecuritySeverity.WARNING,
                    event_type="AUTH_REQUIRED",
                    client_ip=ip_str,
                    zone=zone,
                    details="Request requires authentication token",
                )
                return False, None, "Authentication required for this operation"

            auth_ok, token_obj, auth_reason = self.auth_mgr.verify_token(
                token_str=token_str,
                client_ip=ip_str,
                required_permission=required_perm,
            )
            if not auth_ok:
                self.ids.record_violation(ip_str, "AUTH_FAILURE", details=auth_reason)
                self.audit_logger.log_event(
                    severity=SecuritySeverity.WARNING,
                    event_type="AUTH_FAILED",
                    client_ip=ip_str,
                    zone=zone,
                    details=auth_reason,
                )
                return False, None, f"Unauthorized: {auth_reason}"

        # Request Passed all Security Gates
        return True, parsed_json, "Request verified and authorized"
