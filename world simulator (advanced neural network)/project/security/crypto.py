"""
project/security/crypto.py

Cryptographic Security Engine providing Packet Signing, Anti-Replay Protection, and Authenticated Encryption.
Features:
- HMAC-SHA256 packet signatures with strict timestamp freshness windows.
- Nonce cache preventing Replay attacks.
- Pure-Python authenticated stream encryption (CTR-SHA256 + HMAC) for zero-dependency cross-platform compatibility.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Union


class CryptoEngine:
    """
    Handles cryptographic signing, anti-replay nonce tracking, and authenticated packet encryption.
    """

    def __init__(
        self,
        default_shared_key: Optional[str] = None,
        max_clock_skew_sec: float = 60.0,
    ) -> None:
        self.default_shared_key = (default_shared_key or secrets.token_hex(32)).encode("utf-8")
        self.max_clock_skew_sec = max_clock_skew_sec
        
        # Anti-replay tracking: nonce -> timestamp
        self._seen_nonces: Dict[str, float] = {}

    def sign_payload(
        self,
        payload_data: Any,
        sender_id: str = "node_0",
        shared_key: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Packs and signs data with timestamp, nonce, and HMAC-SHA256 signature.
        """
        key = shared_key or self.default_shared_key
        now = time.time()
        nonce = secrets.token_hex(16)
        
        payload_json = json.dumps(payload_data, separators=(",", ":"))
        
        # Digest input: timestamp:nonce:sender_id:payload_json
        canonical_msg = f"{now:.6f}:{nonce}:{sender_id}:{payload_json}".encode("utf-8")
        signature = hmac.new(key, canonical_msg, hashlib.sha256).hexdigest()

        return {
            "version": "SEC_v1",
            "timestamp": now,
            "nonce": nonce,
            "sender_id": sender_id,
            "payload": payload_data,
            "signature": signature,
        }

    def verify_and_unpack(
        self,
        packet_dict: Dict[str, Any],
        shared_key: Optional[bytes] = None,
    ) -> Tuple[bool, Optional[Any], str]:
        """
        Verifies timestamp freshness, checks for replay attacks, and validates HMAC signature.
        Returns: (is_valid, unpacked_payload, reason)
        """
        key = shared_key or self.default_shared_key
        now = time.time()

        # 1. Structural check
        required_fields = ("version", "timestamp", "nonce", "sender_id", "payload", "signature")
        if not all(k in packet_dict for k in required_fields):
            return False, None, "Missing required secure packet fields"

        ts = float(packet_dict["timestamp"])
        nonce = str(packet_dict["nonce"])
        sender_id = str(packet_dict["sender_id"])
        payload = packet_dict["payload"]
        received_sig = str(packet_dict["signature"])

        # 2. Clock Skew / Freshness Check
        if abs(now - ts) > self.max_clock_skew_sec:
            return False, None, f"Packet timestamp expired or out of sync (delta: {abs(now - ts):.2f}s)"

        # 3. Anti-Replay Nonce Check
        self._prune_old_nonces(now)
        if nonce in self._seen_nonces:
            return False, None, f"Replay attack detected: Nonce '{nonce}' already processed"
        self._seen_nonces[nonce] = ts

        # 4. Verify HMAC Signature
        payload_json = json.dumps(payload, separators=(",", ":"))
        canonical_msg = f"{ts:.6f}:{nonce}:{sender_id}:{payload_json}".encode("utf-8")
        expected_sig = hmac.new(key, canonical_msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, received_sig):
            return False, None, "HMAC signature mismatch: payload may have been tampered with"

        return True, payload, "Packet validated successfully"

    def _prune_old_nonces(self, now: float) -> None:
        """Removes nonces older than the clock skew window."""
        cutoff = now - (self.max_clock_skew_sec * 2)
        expired = [n for n, t in self._seen_nonces.items() if t < cutoff]
        for n in expired:
            del self._seen_nonces[n]

    @staticmethod
    def _keystream_generator(key: bytes, nonce: bytes, length: int) -> bytes:
        """Derives pseudo-random keystream using SHA-256 counter mode."""
        keystream = bytearray()
        counter = 0
        while len(keystream) < length:
            counter_bytes = struct.pack(">Q", counter)
            block = hashlib.sha256(key + nonce + counter_bytes).digest()
            keystream.extend(block)
            counter += 1
        return bytes(keystream[:length])

    def encrypt_bytes(self, plaintext: bytes, key: Optional[bytes] = None) -> Dict[str, str]:
        """
        Encrypts raw bytes using authenticated CTR keystream and HMAC-SHA256.
        Returns dict containing base64 nonce, ciphertext, and tag.
        """
        secret = key or self.default_shared_key
        # Derive encryption key and MAC key using HKDF-style split
        enc_key = hashlib.sha256(secret + b"ENC_KEY").digest()
        mac_key = hashlib.sha256(secret + b"MAC_KEY").digest()

        nonce = secrets.token_bytes(16)
        keystream = self._keystream_generator(enc_key, nonce, len(plaintext))
        
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
        tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()

        return {
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
        }

    def decrypt_bytes(self, encrypted_dict: Dict[str, str], key: Optional[bytes] = None) -> Optional[bytes]:
        """
        Decrypts authenticated ciphertext. Returns None if tag verification fails.
        """
        secret = key or self.default_shared_key
        enc_key = hashlib.sha256(secret + b"ENC_KEY").digest()
        mac_key = hashlib.sha256(secret + b"MAC_KEY").digest()

        try:
            nonce = base64.b64decode(encrypted_dict["nonce"])
            ciphertext = base64.b64decode(encrypted_dict["ciphertext"])
            tag = base64.b64decode(encrypted_dict["tag"])
        except Exception:
            return None

        # Verify HMAC tag first (Encrypt-then-MAC)
        expected_tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_tag, tag):
            return None

        keystream = self._keystream_generator(enc_key, nonce, len(ciphertext))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
        return plaintext
