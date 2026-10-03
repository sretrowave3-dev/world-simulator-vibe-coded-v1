"""
project/ai/blackboard.py

Blackboard Sensory & State Store for Behavioral AI.

Features:
- Thread-safe key-value blackboard for storing sensory perceptions, navigation targets,
  and behavioral flags.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Blackboard:
    """
    Key-Value shared context blackboard used by Behavior Trees and GOAP planners.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def clear(self) -> None:
        self._data.clear()
