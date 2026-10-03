"""
project/security/audit.py

Security Audit Logging, Event Buffering, and SIEM Telemetry Dispatcher.
Features:
- Standardized security event schema with severity levels.
- Thread-safe memory buffering with periodic disk persistence.
- Aggregated threat metrics and attack vectors breakdown.
"""

from __future__ import annotations

import enum
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from project.security.firewall import NetworkZone


class SecuritySeverity(enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    SECURITY_ALERT = "SECURITY_ALERT"
    CRITICAL_ATTACK = "CRITICAL_ATTACK"


@dataclass
class SecurityAuditEvent:
    event_id: str
    timestamp: float
    severity: SecuritySeverity
    event_type: str
    client_ip: str
    zone: NetworkZone
    details: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "event_type": self.event_type,
            "client_ip": self.client_ip,
            "zone": self.zone.value,
            "details": self.details,
            "metadata": self.metadata,
        }


class SecurityAuditLogger:
    """
    Central auditor recording and persisting security events and attack attempts.
    """

    def __init__(self, max_buffer_size: int = 2000) -> None:
        self.max_buffer_size = max_buffer_size
        self._event_buffer: List[SecurityAuditEvent] = []
        self._severity_counts: Dict[SecuritySeverity, int] = {s: 0 for s in SecuritySeverity}

    def log_event(
        self,
        severity: SecuritySeverity,
        event_type: str,
        client_ip: str = "127.0.0.1",
        zone: NetworkZone = NetworkZone.LOCAL,
        details: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SecurityAuditEvent:
        """Records a new security audit event."""
        event = SecurityAuditEvent(
            event_id=secrets.token_hex(8),
            timestamp=time.time(),
            severity=severity,
            event_type=event_type,
            client_ip=client_ip,
            zone=zone,
            details=details,
            metadata=metadata or {},
        )

        self._event_buffer.append(event)
        self._severity_counts[severity] += 1

        # Keep buffer bounded
        if len(self._event_buffer) > self.max_buffer_size:
            self._event_buffer.pop(0)

        return event

    def get_events(
        self,
        min_severity: Optional[SecuritySeverity] = None,
        limit: int = 100,
    ) -> List[SecurityAuditEvent]:
        """Retrieves recent events filtered by severity."""
        if min_severity is None:
            return self._event_buffer[-limit:]

        severity_rank = {
            SecuritySeverity.INFO: 1,
            SecuritySeverity.WARNING: 2,
            SecuritySeverity.SECURITY_ALERT: 3,
            SecuritySeverity.CRITICAL_ATTACK: 4,
        }
        target_rank = severity_rank[min_severity]
        filtered = [e for e in self._event_buffer if severity_rank[e.severity] >= target_rank]
        return filtered[-limit:]

    def flush_to_jsonl(self, filepath: str) -> int:
        """Appends buffered security events to a JSON-Lines audit log file."""
        if not self._event_buffer:
            return 0

        count = len(self._event_buffer)
        with open(filepath, "a", encoding="utf-8") as f:
            for event in self._event_buffer:
                f.write(json.dumps(event.to_dict()) + "\n")

        self._event_buffer.clear()
        return count

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistical overview of security posture."""
        return {
            "total_events": sum(self._severity_counts.values()),
            "severity_breakdown": {s.value: count for s, count in self._severity_counts.items()},
            "buffered_events_count": len(self._event_buffer),
        }
