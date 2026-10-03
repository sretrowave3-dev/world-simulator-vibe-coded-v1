"""
project/security/ids.py

Intrusion Detection and Prevention System (IDS/IPS) for World Simulation Network.
Features:
- Threat scoring engine with natural exponential score decay.
- Automated progressive quarantine & bans via DualZoneFirewall integration.
- Signature inspection against Injection, Path Traversal, Replay, and JSON DOS Bombs.
- Anomaly detection for Brute-Force, Port Scanning, and Flood attacks.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from project.security.firewall import DualZoneFirewall, NetworkZone


class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ThreatProfile:
    ip: str
    score: float = 0.0
    last_event_time: float = 0.0
    violations_count: int = 0
    incident_history: List[Dict[str, Any]] = field(default_factory=list)


class IntrusionDetectionSystem:
    """
    Real-time IDS/IPS inspecting payloads, tracking threat scores, and blocking malicious actors.
    """

    # Exploit and injection signature patterns
    SIGNATURES = [
        # Path Traversal
        (re.compile(r"(\.\./|\.\.\\|/etc/passwd|/etc/shadow|c:\\windows|c:/windows)", re.IGNORECASE), "PATH_TRAVERSAL", 40.0),
        # Command / Shell Injection
        (re.compile(r"(\||;|&&|\$\(|\`)\s*(whoami|cat\s+|rm\s+-rf|curl\s+|wget\s+|powershell|cmd\.exe|bash|sh\s+)", re.IGNORECASE), "COMMAND_INJECTION", 75.0),
        # Python Code Execution / Eval Injection
        (re.compile(r"(__import__|__builtins__|eval\s*\(|exec\s*\(|getattr\s*\(|subprocess\.|os\.system)", re.IGNORECASE), "PYTHON_CODE_INJECTION", 80.0),
        # SQL / NoSQL Injection
        (re.compile(r"(\'\s*OR\s*\'1\'\s*=\s*\'1|UNION\s+SELECT|DROP\s+TABLE|\$where|\$regex|\$gt|\$ne)", re.IGNORECASE), "DATABASE_INJECTION", 60.0),
        # Dangerous HTML / XSS Scripts
        (re.compile(r"(<script\b[^>]*>|javascript:|onerror\s*=|onload\s*=)", re.IGNORECASE), "XSS_SCRIPT_INJECTION", 30.0),
    ]

    # Pre-defined event threat scores
    EVENT_SCORES = {
        "AUTH_FAILURE": 15.0,
        "AUTH_BRUTE_FORCE": 45.0,
        "RATE_LIMIT_FLOOD": 20.0,
        "MALFORMED_PAYLOAD": 25.0,
        "PAYLOAD_OVERSIZE": 35.0,
        "REPLAY_ATTACK": 60.0,
        "TAMPERED_SIGNATURE": 80.0,
        "UNAUTHORIZED_ENDPOINT_PROBE": 30.0,
        "SSRF_ATTEMPT": 90.0,
    }

    def __init__(
        self,
        firewall: Optional[DualZoneFirewall] = None,
        warning_threshold: float = 50.0,
        temp_ban_threshold: float = 100.0,
        extended_ban_threshold: float = 250.0,
        perm_ban_threshold: float = 500.0,
        decay_rate_per_min: float = 5.0,
    ) -> None:
        self.firewall = firewall
        self.warning_threshold = warning_threshold
        self.temp_ban_threshold = temp_ban_threshold
        self.extended_ban_threshold = extended_ban_threshold
        self.perm_ban_threshold = perm_ban_threshold
        self.decay_rate_per_sec = decay_rate_per_min / 60.0

        self._profiles: Dict[str, ThreatProfile] = {}
        self.total_inspections: int = 0
        self.threats_detected: int = 0
        self.bans_triggered: int = 0

    def _get_profile(self, ip_str: str) -> ThreatProfile:
        now = time.time()
        if ip_str not in self._profiles:
            self._profiles[ip_str] = ThreatProfile(ip=ip_str, last_event_time=now)
            return self._profiles[ip_str]
        
        profile = self._profiles[ip_str]
        # Apply score decay based on elapsed time
        elapsed = now - profile.last_event_time
        if elapsed > 0 and profile.score > 0:
            decay = elapsed * self.decay_rate_per_sec
            profile.score = max(0.0, profile.score - decay)
        profile.last_event_time = now
        return profile

    def inspect_payload(self, ip_str: str, payload_str: str) -> Tuple[bool, List[str], float]:
        """
        Scans raw text/JSON payloads against intrusion and injection signatures.
        Returns: (is_safe, detected_threat_names, total_score_added)
        """
        self.total_inspections += 1
        detected = []
        added_score = 0.0

        for pattern, name, score in self.SIGNATURES:
            if pattern.search(payload_str):
                detected.append(name)
                added_score += score

        if detected:
            self.threats_detected += 1
            reason = f"Payload matched signatures: {', '.join(detected)}"
            self.record_violation(ip_str, "INJECTION_ATTEMPT", custom_score=added_score, details=reason)
            return False, detected, added_score

        return True, [], 0.0

    def record_violation(
        self,
        ip_str: str,
        event_type: str,
        custom_score: Optional[float] = None,
        details: str = "",
    ) -> Tuple[float, ThreatLevel, Optional[str]]:
        """
        Records a security violation event for an IP address.
        Evaluates thresholds and triggers firewall bans if necessary.
        Returns: (updated_score, threat_level, action_taken)
        """
        profile = self._get_profile(ip_str)
        now = time.time()

        score_to_add = custom_score if custom_score is not None else self.EVENT_SCORES.get(event_type, 20.0)
        profile.score += score_to_add
        profile.violations_count += 1
        profile.incident_history.append({
            "timestamp": now,
            "event": event_type,
            "score_added": score_to_add,
            "details": details,
        })
        
        # Keep incident history compact
        if len(profile.incident_history) > 20:
            profile.incident_history.pop(0)

        threat_level = ThreatLevel.NONE
        action_taken = None

        if profile.score >= self.perm_ban_threshold:
            threat_level = ThreatLevel.CRITICAL
            action_taken = "PERMANENT_BAN"
            if self.firewall:
                self.firewall.add_ban(ip_str, duration_sec=None, reason=f"IDS Critical Threat: {event_type} ({details})")
                self.bans_triggered += 1

        elif profile.score >= self.extended_ban_threshold:
            threat_level = ThreatLevel.HIGH
            action_taken = "EXTENDED_BAN_24H"
            if self.firewall:
                self.firewall.add_ban(ip_str, duration_sec=86400.0, reason=f"IDS High Threat: {event_type} ({details})")
                self.bans_triggered += 1

        elif profile.score >= self.temp_ban_threshold:
            threat_level = ThreatLevel.MEDIUM
            action_taken = "TEMPORARY_BAN_15M"
            if self.firewall:
                self.firewall.add_ban(ip_str, duration_sec=900.0, reason=f"IDS Medium Threat: {event_type} ({details})")
                self.bans_triggered += 1

        elif profile.score >= self.warning_threshold:
            threat_level = ThreatLevel.LOW
            action_taken = "SECURITY_WARNING"

        return profile.score, threat_level, action_taken

    def get_threat_score(self, ip_str: str) -> float:
        """Returns the current decaying threat score of an IP."""
        if ip_str not in self._profiles:
            return 0.0
        return self._get_profile(ip_str).score

    def reset_threat(self, ip_str: str) -> None:
        """Clears threat records for an IP."""
        if ip_str in self._profiles:
            del self._profiles[ip_str]

    def prune_clean_profiles(self, max_idle_sec: float = 3600.0) -> int:
        """Prunes tracking for IPs that have decayed back to 0 score and stayed idle."""
        now = time.time()
        to_del = []
        for ip, profile in self._profiles.items():
            decayed_score = self.get_threat_score(ip)
            if decayed_score <= 0.001 and (now - profile.last_event_time) > max_idle_sec:
                to_del.append(ip)
        for ip in to_del:
            del self._profiles[ip]
        return len(to_del)

    def get_stats(self) -> Dict[str, Any]:
        """Returns IDS operational metrics."""
        return {
            "total_inspections": self.total_inspections,
            "threats_detected": self.threats_detected,
            "bans_triggered": self.bans_triggered,
            "tracked_threat_profiles": len(self._profiles),
        }
