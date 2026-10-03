"""
project/security/sanitizer.py

Input Sanitization, Buffer Size Enforcement, and JSON Depth Bomb Protection.
Features:
- Recursive JSON depth limit preventing stack-overflow / CPU starvation attacks.
- Strict payload byte size and string length enforcement.
- Control character and null byte stripping.
- Alphanumeric identifier sanitization.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple, Any, Union


class PayloadSanitizer:
    """
    Sanitizes inbound network parameters, JSON objects, and string commands.
    """

    MAX_PAYLOAD_BYTES: int = 512 * 1024       # 512 KB
    MAX_RECURSION_DEPTH: int = 10              # Max nested dict/list depth
    MAX_COLLECTION_ELEMENTS: int = 2000       # Max items in single array/dict
    MAX_STRING_LENGTH: int = 16384            # 16 KB string length

    # Regex matching control characters except standard tabs/newlines
    CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
    IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")

    @classmethod
    def sanitize_text(cls, text: str, max_length: Optional[int] = None) -> str:
        """Strips null bytes and non-printable control characters."""
        if not isinstance(text, str):
            return str(text)
        
        limit = max_length or cls.MAX_STRING_LENGTH
        cleaned = cls.CONTROL_CHAR_REGEX.sub("", text)
        return cleaned[:limit]

    @classmethod
    def is_valid_identifier(cls, identifier: str) -> bool:
        """Validates that a string is a safe alphanumeric identifier."""
        return bool(cls.IDENTIFIER_REGEX.match(identifier))

    @classmethod
    def sanitize_identifier(cls, identifier: str, fallback_prefix: str = "id_") -> str:
        """Cleans and returns a safe identifier string."""
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", identifier.strip())
        if not cleaned:
            return f"{fallback_prefix}safe"
        return cleaned[:64]

    @classmethod
    def _check_depth_and_structure(cls, data: Any, current_depth: int, max_depth: int) -> Tuple[bool, str]:
        """Recursively checks that nested dicts and lists do not exceed depth or size limits."""
        if current_depth > max_depth:
            return False, f"JSON Bomb Protection: Recursion depth exceeded maximum limit ({max_depth})"

        if isinstance(data, dict):
            if len(data) > cls.MAX_COLLECTION_ELEMENTS:
                return False, f"Dictionary element count ({len(data)}) exceeds limit ({cls.MAX_COLLECTION_ELEMENTS})"
            for k, v in data.items():
                if not isinstance(k, str):
                    return False, f"Dictionary keys must be strings, got {type(k).__name__}"
                if len(k) > 256:
                    return False, f"Dictionary key exceeds max length (256 characters)"
                ok, err = cls._check_depth_and_structure(v, current_depth + 1, max_depth)
                if not ok:
                    return False, err

        elif isinstance(data, (list, tuple)):
            if len(data) > cls.MAX_COLLECTION_ELEMENTS:
                return False, f"Array element count ({len(data)}) exceeds limit ({cls.MAX_COLLECTION_ELEMENTS})"
            for item in data:
                ok, err = cls._check_depth_and_structure(item, current_depth + 1, max_depth)
                if not ok:
                    return False, err

        elif isinstance(data, str):
            if len(data) > cls.MAX_STRING_LENGTH:
                return False, f"String value length ({len(data)}) exceeds maximum limit ({cls.MAX_STRING_LENGTH})"

        return True, ""

    @classmethod
    def parse_and_sanitize_json(
        cls,
        json_str: str,
        max_bytes: Optional[int] = None,
        max_depth: Optional[int] = None,
    ) -> Tuple[bool, Optional[Any], str]:
        """
        Parses JSON string safely enforcing byte size, depth limits, and element counts.
        Returns: (is_valid, parsed_object, error_message)
        """
        limit_bytes = max_bytes or cls.MAX_PAYLOAD_BYTES
        depth_limit = max_depth or cls.MAX_RECURSION_DEPTH

        if len(json_str.encode("utf-8")) > limit_bytes:
            return False, None, f"Payload size ({len(json_str)} bytes) exceeds maximum limit ({limit_bytes} bytes)"

        try:
            parsed = json.loads(json_str)
        except Exception as e:
            return False, None, f"Malformed JSON syntax: {str(e)}"

        # Deep structure safety validation
        ok, reason = cls._check_depth_and_structure(parsed, 1, depth_limit)
        if not ok:
            return False, None, reason

        return True, parsed, "Payload structure valid and sanitized"
