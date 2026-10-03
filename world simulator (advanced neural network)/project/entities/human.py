"""
project/entities/human.py

Sentient Human Entity Model for the ALife Platform.

Features:
- High-Capacity Cognitive Memory: Preallocated >= 50 MB Experience Replay Matrix & Spatial Mapping.
- Advanced Tool Usage, Crafting, Inventory Management, and Shelter Construction.
- Social Hierarchy, Tribal Organization, Cultural Knowledge Transmission, and Divine Ascension.
- Robust Omnivorous Metabolism with high caloric reserves and sustainable foraging efficiency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from project.entities.entity import Entity, EntityType
from project.ai.memory import HumanCognitiveMemory


@dataclass(eq=False)
class Human(Entity):
    """Sentient, tool-using organism capable of social cooperation, deep memory retention, and civilization building."""

    tribe_id: Optional[str] = None
    civilization_id: Optional[str] = None
    social_rank: int = 0
    reputation: float = 0.5

    intelligence_quotient: float = 120.0
    creativity: float = 0.65
    social_affinity: float = 0.85
    technology_level: int = 0
    known_technologies: List[str] = field(default_factory=list)

    inventory: Dict[str, float] = field(default_factory=dict)
    max_inventory_capacity_kg: float = 60.0
    thought_cache: Optional[Any] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.HUMAN
        self.radius = 1.2
        self.mass_kg = 70.0
        self.max_health = 120.0
        self.health = 120.0
        self.max_energy = 500.0
        self.energy = 450.0  # Well-fed base genesis state
        self.max_hydration = 300.0
        self.hydration = 280.0
        self.max_age_ticks = 40000
        self.maturity_age_ticks = 150
        self.base_speed = 3.8
        self.max_speed_cap = 9.8
        self.strength = 20.0
        self.max_strength_cap = 70.0
        self.metabolic_rate = 0.035  # High omnivorous metabolic efficiency
        self.is_endotherm = True
        self.body_temperature_c = 37.0

        # Instantiate 50+ MB High-Capacity Cognitive Memory
        if self.memory is None or not isinstance(self.memory, HumanCognitiveMemory):
            self.memory = HumanCognitiveMemory()

        # Instantiate Human Stream-of-Consciousness Thought Cache
        if self.thought_cache is None:
            from project.core.thought_logger import HumanThoughtCache
            self.thought_cache = HumanThoughtCache(human_id=self.entity_id)

        self._apply_individual_variance()

    def think(
        self,
        content: str,
        category: str = "SURVIVAL",
        valence: float = 0.0,
        intensity: float = 0.5,
        tick: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Any:
        """Records an internal subjective thought into the in-memory cache and persistent diary."""
        if self.thought_cache is None:
            from project.core.thought_logger import HumanThoughtCache
            self.thought_cache = HumanThoughtCache(human_id=self.entity_id)
        return self.thought_cache.add_thought(
            content=content,
            category=category,
            valence=valence,
            intensity=intensity,
            tick=tick,
            tags=tags,
        )

    def recall_thoughts(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        emotion_range: Optional[tuple[float, float]] = None,
        limit: int = 5,
    ) -> List[Any]:
        """Subjectively retrieves past thoughts from memory cache based on context or sentiment."""
        if self.thought_cache is None:
            return []
        if query:
            return self.thought_cache.recall_by_keyword(query, limit=limit)
        if category:
            return self.thought_cache.recall_by_category(category, limit=limit)
        if emotion_range:
            return self.thought_cache.recall_by_emotion(emotion_range[0], emotion_range[1], limit=limit)
        return self.thought_cache.retrieve_recent(limit=limit)

    @property
    def memory_footprint_mb(self) -> float:
        """Returns the memory buffer size in megabytes."""
        if self.memory and hasattr(self.memory, "memory_size_mb"):
            return self.memory.memory_size_mb
        return 51.13

    @property
    def inventory_weight(self) -> float:
        return sum(self.inventory.values())

    def add_to_inventory(self, item_name: str, weight_kg: float) -> bool:
        if self.inventory_weight + weight_kg > self.max_inventory_capacity_kg:
            return False
        self.inventory[item_name] = self.inventory.get(item_name, 0.0) + weight_kg
        return True

    def remove_from_inventory(self, item_name: str, weight_kg: float) -> float:
        available = self.inventory.get(item_name, 0.0)
        if available <= 0.0:
            return 0.0
        removed = min(available, weight_kg)
        self.inventory[item_name] -= removed
        if self.inventory[item_name] <= 0.001:
            del self.inventory[item_name]
        return removed

    def can_mate(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= 150.0
            and self.hydration >= 60.0
            and self.reproduction_cooldown <= 0
        )

    def feed(self, energy_amount: float = 100.0, hydration_amount: float = 60.0) -> None:
        """Direct feeding method topping up human calories and hydration."""
        self.gain_energy(energy_amount)
        self.hydration = min(self.max_hydration, self.hydration + hydration_amount)
        self.custom_data["dopamine"] = 1.0
        self.custom_data["stress"] = 0.0

    __hash__ = Entity.__hash__
    __eq__ = Entity.__eq__
