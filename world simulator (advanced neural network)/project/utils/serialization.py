"""
project/utils/serialization.py

Fast serialization, compression, and checksum verification utilities.

Architectural Guarantees:
- Handles Enums, Dataclasses, Tuples, Sets, and numpy-like nested structures.
- Optional zlib binary compression.
- CRC32 checksum generation for integrity verification.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import zlib
from typing import Any, Dict, List, Optional, Union


class EngineJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder handling engine data types (Enums, dataclasses, sets)."""

    def default(self, o: Any) -> Any:
        if isinstance(o, enum.Enum):
            return {"__enum__": f"{o.__class__.__name__}.{o.name}", "value": o.value}
        if dataclasses.is_dataclass(o):
            return {"__dataclass__": o.__class__.__name__, "data": dataclasses.asdict(o)}
        if isinstance(o, set):
            return {"__set__": list(o)}
        if isinstance(o, tuple):
            return {"__tuple__": list(o)}
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return super().default(o)


def serialize_json(data: Any, indent: Optional[int] = None) -> str:
    """Serializes data structure to JSON string."""
    return json.dumps(data, cls=EngineJSONEncoder, indent=indent)


def deserialize_json(json_str: str) -> Any:
    """Deserializes JSON string back into standard python dictionaries/lists."""
    return json.loads(json_str)


def compress_bytes(raw_bytes: bytes, compression_level: int = 6) -> bytes:
    """Compresses raw bytes using zlib."""
    return zlib.compress(raw_bytes, level=compression_level)


def decompress_bytes(compressed_bytes: bytes) -> bytes:
    """Decompresses zlib compressed bytes."""
    return zlib.decompress(compressed_bytes)


def compute_crc32(data_bytes: bytes) -> int:
    """Computes 32-bit CRC checksum for integrity validation."""
    return zlib.crc32(data_bytes) & 0xFFFFFFFF


def serialize_compressed_payload(data: Any) -> Tuple[bytes, int]:
    """
    Serializes data to compressed JSON binary with CRC32 checksum.
    Returns: (compressed_bytes, checksum_crc32)
    """
    json_text = serialize_json(data)
    raw_bytes = json_text.encode("utf-8")
    compressed = compress_bytes(raw_bytes)
    checksum = compute_crc32(compressed)
    return compressed, checksum


def deserialize_compressed_payload(compressed_bytes: bytes, expected_checksum: Optional[int] = None) -> Any:
    """
    Validates checksum and decompresses payload back into Python object.
    """
    if expected_checksum is not None:
        calc_checksum = compute_crc32(compressed_bytes)
        if calc_checksum != expected_checksum:
            raise ValueError(
                f"Payload checksum mismatch: expected {expected_checksum:#010x}, calculated {calc_checksum:#010x}"
            )

    raw_bytes = decompress_bytes(compressed_bytes)
    json_text = raw_bytes.decode("utf-8")
    return deserialize_json(json_text)
