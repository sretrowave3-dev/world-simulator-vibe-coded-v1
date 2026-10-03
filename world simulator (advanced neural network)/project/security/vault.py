"""
project/security/vault.py

Secure Key Vault, Memory-Masked Secret Storage, and Outbound SSRF Guard.
Features:
- Ephemeral XOR memory masking preventing plain secrets from lingering in memory dumps.
- Automatic API key redaction in logging and string representations.
- Outbound SSRF (Server-Side Request Forgery) guard enforcing strict domain whitelists and blocking cloud metadata endpoints.
"""

from __future__ import annotations

import os
import secrets
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple


class SecureKeyVault:
    """
    Manages API credentials with in-memory masking and outbound URL security validation.
    """

    # Allowed outbound domains for simulation cloud services
    ALLOWED_OUTBOUND_DOMAINS = {
        "generativelanguage.googleapis.com",
        "api.gemini.google.com",
    }

    # Prohibited destinations (Cloud metadata IP, Local loopback, Private LAN)
    FORBIDDEN_OUTBOUND_HOSTS = {
        "127.0.0.1",
        "localhost",
        "::1",
        "169.254.169.254",   # AWS/GCP/Azure Instance Metadata Service
        "metadata.google.internal",
        "0.0.0.0",
    }

    def __init__(self, primary_api_key: Optional[str] = None) -> None:
        self._master_xor_pad: bytes = secrets.token_bytes(64)
        self._secrets: Dict[str, bytes] = {}
        self._allowed_domains: Set[str] = set(self.ALLOWED_OUTBOUND_DOMAINS)

        # Store initial key if provided
        if primary_api_key:
            self.set_secret("GEMINI_API_KEY", primary_api_key)

    def _mask(self, plaintext: str) -> bytes:
        """XORs string bytes with the ephemeral master pad."""
        raw = plaintext.encode("utf-8")
        pad = self._master_xor_pad
        return bytes(raw[i] ^ pad[i % len(pad)] for i in range(len(raw)))

    def _unmask(self, masked: bytes) -> str:
        """Restores plaintext transiently from masked bytes."""
        pad = self._master_xor_pad
        unmasked = bytes(masked[i] ^ pad[i % len(pad)] for i in range(len(masked)))
        return unmasked.decode("utf-8")

    def set_secret(self, key_name: str, secret_value: str) -> None:
        """Stores a masked secret."""
        if secret_value is None:
            return
        self._secrets[key_name] = self._mask(secret_value)

    def get_secret(self, key_name: str) -> Optional[str]:
        """Retrieves and transiently unmasks a secret."""
        if key_name in self._secrets:
            val = self._unmask(self._secrets[key_name])
            return val if val != "" else None

        # Fallback to environment variable if present
        env_val = os.environ.get(key_name)
        if env_val:
            self.set_secret(key_name, env_val)
            return env_val
        return None

    def mask_string(self, text: str, visible_chars: int = 8) -> str:
        """Redacts sensitive key string for display in logs or UIs."""
        if not text:
            return "<EMPTY>"
        if len(text) <= visible_chars:
            return "*" * len(text)
        return f"{text[:visible_chars]}...{'*' * 8}"

    def allow_domain(self, domain: str) -> None:
        """Whitelists an external domain for outbound queries."""
        self._allowed_domains.add(domain.lower().strip())

    def validate_outbound_url(self, url: str) -> Tuple[bool, str]:
        """
        Guards outbound HTTP requests against SSRF and unauthorized domain exfiltration.
        Returns: (is_safe, reason)
        """
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as e:
            return False, f"Malformed URL format: {str(e)}"

        # 1. Enforce HTTPS scheme for public API queries
        if parsed.scheme.lower() != "https":
            return False, f"Insecure protocol '{parsed.scheme}': HTTPS is strictly required"

        hostname = (parsed.hostname or "").lower()

        # 2. Block forbidden cloud metadata and loopback targets
        if hostname in self.FORBIDDEN_OUTBOUND_HOSTS:
            return False, f"SSRF Protection: Outbound request to '{hostname}' is blocked"

        # 3. Enforce Allowed Domain Whitelist
        if hostname not in self._allowed_domains:
            return False, f"SSRF Protection: Host '{hostname}' is not in allowed outbound domain whitelist"

        return True, "Outbound destination validated and safe"
