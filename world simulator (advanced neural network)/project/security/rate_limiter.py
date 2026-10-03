"""
project/security/rate_limiter.py

Multi-Tier Token Bucket Rate Limiter with Zone-Aware Adaptive Throttling.
Features:
- Separate rate limits & burst allowances for LOCAL vs. PUBLIC zones.
- Variable operation cost (e.g. telemetry ping = 1, state sync = 5, LLM trigger = 10).
- Leaky bucket smoothing & burst tokens.
- Violation counter for rapid DDoS mitigation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Any
from project.security.firewall import NetworkZone


@dataclass
class RateBucket:
    tokens: float
    capacity: float
    refill_rate: float        # Tokens replenished per second
    last_refill: float
    violations: int = 0
    penalty_until: float = 0.0


@dataclass
class ZoneRatePolicy:
    capacity: float           # Max burst
    refill_rate: float        # Sustained requests per second
    max_violations_before_penalty: int = 5
    penalty_duration_sec: float = 30.0


class MultiTierRateLimiter:
    """
    Token-bucket rate limiter enforcing different policies for Local vs. Public connections.
    """

    def __init__(
        self,
        local_policy: Optional[ZoneRatePolicy] = None,
        public_policy: Optional[ZoneRatePolicy] = None,
    ) -> None:
        # Default local policy: 500 burst, 200 req/sec
        self.local_policy = local_policy or ZoneRatePolicy(
            capacity=500.0,
            refill_rate=200.0,
            max_violations_before_penalty=20,
            penalty_duration_sec=10.0,
        )
        
        # Default public policy: 30 burst, 10 req/sec
        self.public_policy = public_policy or ZoneRatePolicy(
            capacity=30.0,
            refill_rate=10.0,
            max_violations_before_penalty=5,
            penalty_duration_sec=60.0,
        )

        self._buckets: Dict[str, RateBucket] = {}
        self.total_checked: int = 0
        self.total_throttled: int = 0

    def _get_policy_for_zone(self, zone: NetworkZone) -> ZoneRatePolicy:
        if zone == NetworkZone.LOCAL:
            return self.local_policy
        return self.public_policy

    def _get_or_create_bucket(self, ip_str: str, zone: NetworkZone, now: float) -> RateBucket:
        if ip_str in self._buckets:
            return self._buckets[ip_str]

        policy = self._get_policy_for_zone(zone)
        bucket = RateBucket(
            tokens=policy.capacity,
            capacity=policy.capacity,
            refill_rate=policy.refill_rate,
            last_refill=now,
            violations=0,
            penalty_until=0.0,
        )
        self._buckets[ip_str] = bucket
        return bucket

    def _refill(self, bucket: RateBucket, now: float) -> None:
        elapsed = now - bucket.last_refill
        if elapsed > 0:
            bucket.tokens = min(bucket.capacity, bucket.tokens + elapsed * bucket.refill_rate)
            bucket.last_refill = now

    def allow_request(
        self,
        ip_str: str,
        zone: NetworkZone = NetworkZone.PUBLIC,
        cost: float = 1.0,
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluates whether a request from ip_str is allowed under its zone rate policy.
        Returns: (is_allowed, wait_seconds, metadata)
        """
        self.total_checked += 1
        now = time.time()
        policy = self._get_policy_for_zone(zone)
        bucket = self._get_or_create_bucket(ip_str, zone, now)

        # Check if under active penalty
        if now < bucket.penalty_until:
            self.total_throttled += 1
            wait_time = bucket.penalty_until - now
            return False, wait_time, {
                "remaining_tokens": 0.0,
                "in_penalty": True,
                "violations": bucket.violations,
            }

        # Refill tokens based on elapsed time
        self._refill(bucket, now)

        # Check token availability
        if bucket.tokens >= cost:
            bucket.tokens -= cost
            return True, 0.0, {
                "remaining_tokens": bucket.tokens,
                "in_penalty": False,
                "violations": bucket.violations,
            }

        # Rate limit exceeded
        self.total_throttled += 1
        bucket.violations += 1
        
        # Apply penalty if violation threshold reached
        if bucket.violations >= policy.max_violations_before_penalty:
            bucket.penalty_until = now + policy.penalty_duration_sec
            wait_time = policy.penalty_duration_sec
        else:
            needed = cost - bucket.tokens
            wait_time = needed / bucket.refill_rate if bucket.refill_rate > 0 else 1.0

        return False, wait_time, {
            "remaining_tokens": bucket.tokens,
            "in_penalty": now < bucket.penalty_until,
            "violations": bucket.violations,
        }

    def reset_ip(self, ip_str: str) -> None:
        """Resets rate limit bucket for specific IP."""
        if ip_str in self._buckets:
            del self._buckets[ip_str]

    def prune_idle_buckets(self, max_idle_sec: float = 300.0) -> int:
        """Prunes buckets that have been full and inactive for max_idle_sec."""
        now = time.time()
        to_delete = []
        for ip, bucket in self._buckets.items():
            if bucket.tokens >= bucket.capacity and (now - bucket.last_refill) > max_idle_sec:
                to_delete.append(ip)
        for ip in to_delete:
            del self._buckets[ip]
        return len(to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """Returns rate limiter summary statistics."""
        return {
            "total_checked": self.total_checked,
            "total_throttled": self.total_throttled,
            "active_tracked_ips": len(self._buckets),
        }
