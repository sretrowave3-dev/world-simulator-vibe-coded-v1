import json
from typing import Any, Dict
import threading

class JSONRAMCache:
    """
    Acts as an in-memory 'RAM' utilizing fast JSON stringification for deep copies
    and thread-safe state synchronization across simulation boundaries.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(JSONRAMCache, cls).__new__(cls)
                cls._instance._cache = {}
        return cls._instance

    def store(self, key: str, data: Any) -> None:
        """Stores object by dumping to a JSON string buffer (fast RAM snap)."""
        with self._lock:
            try:
                # Store as json string to ensure decoupling (acts like a RAM page)
                self._cache[key] = json.dumps(data)
            except Exception as e:
                pass # Silent fail for un-serializable objects

    def retrieve(self, key: str) -> Any:
        """Retrieves and parses the object from the JSON RAM buffer."""
        with self._lock:
            raw = self._cache.get(key)
            if raw is not None:
                try:
                    return json.loads(raw)
                except Exception:
                    return None
            return None

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

ram_cache = JSONRAMCache()
