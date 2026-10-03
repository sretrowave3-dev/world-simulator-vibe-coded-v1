"""
project/security/firewall.py

Advanced Dual-Zone Network Firewall for Local (LAN) and Public (WAN) Traffic.
Features:
- Dual-zone classification (LOCAL vs. PUBLIC vs. BLOCKED).
- RFC1918, Loopback, Link-Local and IPv6 private subnet resolution.
- Bogon / reserved IP filtering for public interfaces.
- Static and dynamic CIDR whitelisting/blacklisting.
- Automatic expiration of temporary ban rules.
"""

from __future__ import annotations

import enum
import ipaddress
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union


class NetworkZone(enum.Enum):
    LOCAL = "LOCAL"       # LAN, Loopback, Private Subnets (High trust / High throughput)
    PUBLIC = "PUBLIC"     # WAN Internet (Strict scrutiny / Strict rate limits)
    DMZ = "DMZ"           # Demilitarized / Isolated Gateway
    BLOCKED = "BLOCKED"   # Banned, Bogon, or Blacklisted


@dataclass
class BanRecord:
    ip: str
    reason: str
    banned_at: float
    expires_at: Optional[float]  # None = permanent ban
    violation_count: int = 1


class DualZoneFirewall:
    """
    Intelligent Firewall separating Local Network (LAN) and Public Internet (WAN) interfaces.
    Enforces strict access controls, CIDR matching, and anti-spoofing bogon filters.
    """

    # RFC 1918 & Local Private Networks
    LOCAL_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),       # Loopback
        ipaddress.ip_network("10.0.0.0/8"),        # Class A Private
        ipaddress.ip_network("172.16.0.0/12"),     # Class B Private
        ipaddress.ip_network("192.168.0.0/16"),    # Class C Private
        ipaddress.ip_network("169.254.0.0/16"),    # Link-Local
        ipaddress.ip_network("::1/128"),           # IPv6 Loopback
        ipaddress.ip_network("fc00::/7"),          # IPv6 Unique Local
        ipaddress.ip_network("fe80::/10"),         # IPv6 Link-Local
    ]

    # Bogon / Invalid Public Routing Networks (Should never appear as source IPs on public WAN)
    BOGON_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("100.64.0.0/10"),     # Carrier-grade NAT
        ipaddress.ip_network("192.0.0.0/24"),      # IANA IPv4 Special Purpose
        ipaddress.ip_network("192.0.2.0/24"),      # TEST-NET-1
        ipaddress.ip_network("198.18.0.0/15"),     # Network Benchmark Testing
        ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
        ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
        ipaddress.ip_network("224.0.0.0/4"),       # Multicast
        ipaddress.ip_network("240.0.0.0/4"),       # Reserved for Future Use
        ipaddress.ip_network("255.255.255.255/32"),# Broadcast
    ]

    def __init__(
        self,
        allow_public_traffic: bool = True,
        strict_bogon_filtering: bool = True,
    ) -> None:
        self.allow_public_traffic = allow_public_traffic
        self.strict_bogon_filtering = strict_bogon_filtering
        
        self._whitelist_networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
        self._blacklist_networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
        self._dynamic_bans: Dict[str, BanRecord] = {}
        
        # Statistics
        self.total_evaluated: int = 0
        self.total_allowed: int = 0
        self.total_blocked: int = 0

    def parse_ip(self, ip_str: str) -> Optional[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
        """Safely parses string to IP address object."""
        try:
            # Handle possible hostname 'localhost'
            if ip_str.lower() in ("localhost", "127.0.0.1"):
                return ipaddress.ip_address("127.0.0.1")
            if ip_str.lower() == "::1":
                return ipaddress.ip_address("::1")
            return ipaddress.ip_address(ip_str.strip())
        except ValueError:
            return None

    def classify_zone(self, ip_str: str) -> NetworkZone:
        """Classifies an IP address into LOCAL, PUBLIC, or BLOCKED zone."""
        ip_obj = self.parse_ip(ip_str)
        if ip_obj is None:
            return NetworkZone.BLOCKED

        # Check explicit bans
        if self.is_banned(ip_str):
            return NetworkZone.BLOCKED

        # Check Blacklist Networks
        for net in self._blacklist_networks:
            if ip_obj in net:
                return NetworkZone.BLOCKED

        # Check Local Networks
        for net in self.LOCAL_NETWORKS:
            if ip_obj in net:
                return NetworkZone.LOCAL

        # Check Bogons if public
        if self.strict_bogon_filtering:
            for net in self.BOGON_NETWORKS:
                if ip_obj in net:
                    return NetworkZone.BLOCKED

        # Otherwise it is a routable Public WAN IP
        return NetworkZone.PUBLIC if self.allow_public_traffic else NetworkZone.BLOCKED

    def is_allowed(self, ip_str: str) -> Tuple[bool, NetworkZone, str]:
        """
        Evaluates whether an IP address is permitted to connect.
        Returns: (is_allowed, zone, reason)
        """
        self.total_evaluated += 1
        ip_obj = self.parse_ip(ip_str)

        if ip_obj is None:
            self.total_blocked += 1
            return False, NetworkZone.BLOCKED, f"Invalid IP address format: '{ip_str}'"

        # 1. Check Dynamic / Permanent Bans
        if self.is_banned(ip_str):
            self.total_blocked += 1
            ban = self._dynamic_bans[ip_str]
            return False, NetworkZone.BLOCKED, f"IP is banned: {ban.reason}"

        # 2. Check Static Blacklist
        for net in self._blacklist_networks:
            if ip_obj in net:
                self.total_blocked += 1
                return False, NetworkZone.BLOCKED, f"Matched static blacklist CIDR {net}"

        # 3. Check Static Whitelist (Highest Priority Bypass)
        for net in self._whitelist_networks:
            if ip_obj in net:
                self.total_allowed += 1
                zone = NetworkZone.LOCAL if any(ip_obj in lnet for lnet in self.LOCAL_NETWORKS) else NetworkZone.PUBLIC
                return True, zone, f"Matched static whitelist CIDR {net}"

        # 4. Classify Zone & Check Bogons
        zone = self.classify_zone(ip_str)

        if zone == NetworkZone.BLOCKED:
            self.total_blocked += 1
            return False, NetworkZone.BLOCKED, "Blocked by bogon filter or public traffic disabled"

        if zone == NetworkZone.LOCAL:
            self.total_allowed += 1
            return True, NetworkZone.LOCAL, "Local LAN/Loopback trusted interface"

        if zone == NetworkZone.PUBLIC:
            if not self.allow_public_traffic:
                self.total_blocked += 1
                return False, NetworkZone.BLOCKED, "Public WAN traffic disabled by firewall policy"
            self.total_allowed += 1
            return True, NetworkZone.PUBLIC, "Public WAN interface allowed"

        self.total_blocked += 1
        return False, NetworkZone.BLOCKED, "Default policy drop"

    def is_banned(self, ip_str: str) -> bool:
        """Checks if an IP is currently banned (cleans expired bans)."""
        ban = self._dynamic_bans.get(ip_str)
        if ban is None:
            return False
        
        if ban.expires_at is not None and time.time() > ban.expires_at:
            # Expired ban
            del self._dynamic_bans[ip_str]
            return False
        return True

    def add_ban(self, ip_str: str, duration_sec: Optional[float] = 3600.0, reason: str = "Security violation") -> None:
        """Dynamically bans an IP address for duration_sec (None for permanent)."""
        now = time.time()
        expires = now + duration_sec if duration_sec is not None else None
        
        if ip_str in self._dynamic_bans:
            self._dynamic_bans[ip_str].violation_count += 1
            self._dynamic_bans[ip_str].expires_at = expires
            self._dynamic_bans[ip_str].reason = reason
        else:
            self._dynamic_bans[ip_str] = BanRecord(
                ip=ip_str,
                reason=reason,
                banned_at=now,
                expires_at=expires,
                violation_count=1,
            )

    def remove_ban(self, ip_str: str) -> bool:
        """Removes a dynamic ban on an IP."""
        if ip_str in self._dynamic_bans:
            del self._dynamic_bans[ip_str]
            return True
        return False

    def add_whitelist(self, cidr_str: str) -> None:
        """Adds CIDR network or single IP to whitelist."""
        net = ipaddress.ip_network(cidr_str.strip(), strict=False)
        if net not in self._whitelist_networks:
            self._whitelist_networks.append(net)

    def add_blacklist(self, cidr_str: str) -> None:
        """Adds CIDR network or single IP to blacklist."""
        net = ipaddress.ip_network(cidr_str.strip(), strict=False)
        if net not in self._blacklist_networks:
            self._blacklist_networks.append(net)

    def clean_expired_bans(self) -> int:
        """Prunes expired dynamic bans. Returns count of pruned bans."""
        now = time.time()
        expired = [ip for ip, ban in self._dynamic_bans.items() if ban.expires_at is not None and now > ban.expires_at]
        for ip in expired:
            del self._dynamic_bans[ip]
        return len(expired)

    def get_stats(self) -> Dict[str, Union[int, float, List[str]]]:
        """Returns firewall runtime statistics."""
        return {
            "total_evaluated": self.total_evaluated,
            "total_allowed": self.total_allowed,
            "total_blocked": self.total_blocked,
            "active_bans_count": len(self._dynamic_bans),
            "banned_ips": list(self._dynamic_bans.keys()),
            "whitelist_rules": [str(n) for n in self._whitelist_networks],
            "blacklist_rules": [str(n) for n in self._blacklist_networks],
        }
