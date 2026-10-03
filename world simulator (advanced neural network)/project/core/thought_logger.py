"""
project/core/thought_logger.py

Human Stream of Consciousness Thought Logging, Dual File Persistence (.log and .json),
and In-Memory Cache Retrieval Engine for the ALife Platform.

Features:
- HumanThought Data Model: Captures subjective thoughts, reflections, categories,
  emotional valence (-1.0 to 1.0), intensity, context tags, and simulation tick.
- Dual Adjacent Storage:
  * project/logs/thoughts/human_thoughts.log (Chronological human-readable diary format)
  * project/logs/thoughts/human_thoughts.json (Structured JSON record database)
- HumanThoughtCache: In-memory LRU/ring cache on Human entities enabling fast cognitive
  retrieval by keyword, emotion, category, or recency when organisms recall memories.
"""

from __future__ import annotations

import os
import json
import time
import threading
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "thoughts")
TXT_LOG_PATH = os.path.join(LOG_DIR, "human_thoughts.log")
JSON_LOG_PATH = os.path.join(LOG_DIR, "human_thoughts.json")


@dataclass
class HumanThought:
    """Individual human subjective thought record."""
    thought_id: str
    human_id: str
    tick: int
    timestamp: float
    category: str  # SURVIVAL, PHILOSOPHY, DEVOTION, SOCIAL, INVENTION, EMOTION
    content: str
    valence: float = 0.0      # -1.0 (grief/terror) to +1.0 (joy/epiphany)
    intensity: float = 0.5    # 0.0 (fleeting) to 1.0 (core conviction)
    context_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HumanThought:
        return cls(
            thought_id=data.get("thought_id", f"th_{int(time.time()*1000)}"),
            human_id=data.get("human_id", "unknown"),
            tick=data.get("tick", 0),
            timestamp=data.get("timestamp", time.time()),
            category=data.get("category", "SURVIVAL"),
            content=data.get("content", ""),
            valence=float(data.get("valence", 0.0)),
            intensity=float(data.get("intensity", 0.5)),
            context_tags=list(data.get("context_tags", [])),
        )

    def format_log_line(self) -> str:
        """Formats thought into human-readable diary string."""
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))
        valence_icon = "😊" if self.valence > 0.3 else ("😨" if self.valence < -0.3 else "😐")
        return (
            f"[{time_str} | Tick #{self.tick:06d}] [{self.human_id}] [{self.category.upper()}] {valence_icon} "
            f"(Valence: {self.valence:+.2f}, Intensity: {self.intensity:.2f})\n"
            f"   Thought: \"{self.content}\"\n"
            f"   Tags: {', '.join(self.context_tags) if self.context_tags else 'None'}\n"
        )


class ThoughtLogger:
    """Thread-safe persistent thought logger managing adjacent .log and .json files."""

    def __init__(self, log_dir: str = LOG_DIR) -> None:
        self.log_dir = log_dir
        self.txt_path = os.path.join(self.log_dir, "human_thoughts.log")
        self.json_path = os.path.join(self.log_dir, "human_thoughts.json")
        self._lock = threading.Lock()
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Creates directory and initial files if they do not exist."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            if not os.path.exists(self.txt_path):
                with open(self.txt_path, "w", encoding="utf-8") as f:
                    f.write("=== HUMAN CONSCIOUSNESS THOUGHT LOG STREAM ===\n\n")
            if not os.path.exists(self.json_path):
                with open(self.json_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
        except Exception:
            pass

    def record_thought(self, thought: HumanThought) -> None:
        """Appends thought to both human-readable log and structured JSON database."""
        with self._lock:
            try:
                # 1. Append to human-readable .log file
                with open(self.txt_path, "a", encoding="utf-8") as f:
                    f.write(thought.format_log_line() + "\n")
                    f.flush()

                # 2. Append to structured .json file
                records: List[Dict[str, Any]] = []
                if os.path.exists(self.json_path) and os.path.getsize(self.json_path) > 2:
                    try:
                        with open(self.json_path, "r", encoding="utf-8") as f:
                            records = json.load(f)
                            if not isinstance(records, list):
                                records = []
                    except Exception:
                        records = []

                records.append(thought.to_dict())
                # Cap persistent JSON file at last 2000 thoughts to prevent unbounded disk bloat
                if len(records) > 2000:
                    records = records[-2000:]

                with open(self.json_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2)
                    f.flush()
            except Exception:
                pass


    def __getstate__(self) -> Dict[str, Any]:
        with self._lock:
            state = self.__dict__.copy()
            state["_lock"] = None
            return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self._lock = threading.Lock()


# Global singleton thought logger
global_thought_logger = ThoughtLogger()


class HumanThoughtCache:
    """
    In-memory cognitive thought cache enabling fast subjective recall for Humans.
    Allows humans to search and retrieve past musings by keyword, emotion, category, or time.
    """

    def __init__(self, human_id: str, max_capacity: int = 150) -> None:
        self.human_id = human_id
        self.max_capacity = max_capacity
        self._thoughts: List[HumanThought] = []
        self._lock = threading.Lock()

    def __getstate__(self) -> Dict[str, Any]:
        with self._lock:
            state = self.__dict__.copy()
            state["_lock"] = None
            return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self._lock = threading.Lock()

    @property
    def total_cached(self) -> int:
        with self._lock:
            return len(self._thoughts)

    def add_thought(
        self,
        content: str,
        category: str = "SURVIVAL",
        valence: float = 0.0,
        intensity: float = 0.5,
        tick: int = 0,
        tags: Optional[List[str]] = None,
        persist: bool = True,
    ) -> HumanThought:
        """Constructs, caches, and persists a new human thought."""
        thought = HumanThought(
            thought_id=f"th_{self.human_id}_{tick}_{int(time.time()*1000) % 100000}",
            human_id=self.human_id,
            tick=tick,
            timestamp=time.time(),
            category=category.upper(),
            content=content.strip(),
            valence=max(-1.0, min(1.0, valence)),
            intensity=max(0.0, min(1.0, intensity)),
            context_tags=tags or [],
        )

        with self._lock:
            self._thoughts.append(thought)
            if len(self._thoughts) > self.max_capacity:
                self._thoughts.pop(0)

        if persist:
            global_thought_logger.record_thought(thought)

        return thought

    def retrieve_recent(self, limit: int = 10) -> List[HumanThought]:
        """Retrieves the most recent thoughts in chronological order."""
        with self._lock:
            return list(self._thoughts[-limit:])

    def recall_by_keyword(self, keyword: str, limit: int = 5) -> List[HumanThought]:
        """Searches memory cache for thoughts containing query keywords."""
        kw_lower = keyword.strip().lower()
        if not kw_lower:
            return self.retrieve_recent(limit)

        with self._lock:
            matches = [
                t for t in self._thoughts
                if kw_lower in t.content.lower() or any(kw_lower in tag.lower() for tag in t.context_tags)
            ]
            return matches[-limit:]

    def recall_by_category(self, category: str, limit: int = 5) -> List[HumanThought]:
        """Recalls thoughts matching a specific category (e.g. DEVOTION, PHILOSOPHY)."""
        cat_upper = category.strip().upper()
        with self._lock:
            matches = [t for t in self._thoughts if t.category == cat_upper]
            return matches[-limit:]

    def recall_by_emotion(self, min_valence: float = 0.0, max_valence: float = 1.0, limit: int = 5) -> List[HumanThought]:
        """Recalls thoughts within an emotional valence window."""
        with self._lock:
            matches = [
                t for t in self._thoughts
                if min_valence <= t.valence <= max_valence
            ]
            return matches[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._thoughts.clear()
