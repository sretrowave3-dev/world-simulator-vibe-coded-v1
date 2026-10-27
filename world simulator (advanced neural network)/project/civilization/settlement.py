"""
project/civilization/settlement.py

Minecraft-Inspired Emergent Architecture & Settlement Subsystem.
Implements tiered shelters (Dugouts -> Wooden Plank Cabins -> Cobblestone Fortresses -> Great Halls),
Minecraft block logic (doors, roofs, torches, light levels, furnaces, chests),
occupancy tracking, and nocturnal predator immunity for sheltered inhabitants.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set


class ShelterTier(Enum):
    EMERGENCY_DUGOUT = 1      # Dirt/Branch lean-to (Minecraft Day 1 survival hole)
    WOODEN_CABIN = 2          # Processed wood planks, door, roof, torches (Day 2-3 house)
    COBBLESTONE_HOUSE = 3     # Cobblestone & stone brick masonry, furnace, chimney (Fortress)
    FORTIFIED_HALL = 4        # Great stone clan hall with watchtowers & palisade


@dataclass
class WorldStructure:
    """A physical built structure adhering to Minecraft building and shelter survival rules."""
    structure_id: str
    structure_type: str       # "campfire", "dirt_dugout", "wooden_cabin", "cobblestone_house", "fortified_hall", "sacred_altar"
    pos_x: float
    pos_y: float
    clan_id: str
    built_tick: int
    tier: int = 1
    health: float = 100.0
    max_health: float = 100.0
    capacity: int = 4
    occupants: List[str] = field(default_factory=list)  # Entity IDs currently inside taking shelter
    light_level: int = 0      # 0 to 15 (Minecraft light level rule: >= 8 repels predators/mobs)
    defense_rating: float = 10.0
    comfort_rating: float = 0.5
    has_door: bool = True
    has_roof: bool = True
    is_predator_proof: bool = True
    resources_stored: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True

    def can_enter(self) -> bool:
        """Returns True if the shelter has available room for an inhabitant."""
        return self.is_active and len(self.occupants) < self.capacity

    def add_occupant(self, human_id: str) -> bool:
        """Moves a human inside the shelter, sealing them behind doors."""
        if self.can_enter() and human_id not in self.occupants:
            self.occupants.append(human_id)
            return True
        return False

    def remove_occupant(self, human_id: str) -> bool:
        """Exits the shelter."""
        if human_id in self.occupants:
            self.occupants.remove(human_id)
            return True
        return False

    def is_inside(self, human_id: str) -> bool:
        return human_id in self.occupants

    def repair(self, amount: float) -> None:
        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount: float) -> None:
        self.health = max(0.0, self.health - amount)
        if self.health <= 0.0:
            self.is_active = False


class SettlementManager:
    """Manages all communal hubs, erected shelters, campfires, and tribal fortifications."""

    def __init__(self) -> None:
        self.structures: Dict[str, WorldStructure] = {}
        self._next_id: int = 1
        self._lock = threading.Lock()

    def get_all_structures_snapshot(self) -> List[WorldStructure]:
        with self._lock:
            return list(self.structures.values())

    def spawn_structure(
        self,
        structure_type: str,
        pos_x: float,
        pos_y: float,
        clan_id: str = "genesis_tribe",
        tick: int = 0,
    ) -> WorldStructure:
        sid = f"struct_{structure_type}_{self._next_id}"
        self._next_id += 1

        # Configure Minecraft structure properties based on type & tier
        tier = 1
        max_hp = 100.0
        cap = 4
        light = 4
        def_rating = 10.0
        comfort = 0.4
        pred_proof = True

        if structure_type == "campfire":
            tier = 1
            max_hp = 60.0
            cap = 0  # Outdoor gathering point
            light = 12
            def_rating = 5.0
            comfort = 0.6
            pred_proof = False
        elif structure_type == "dirt_dugout":
            tier = 1
            max_hp = 90.0
            cap = 3
            light = 5
            def_rating = 15.0
            comfort = 0.5
            pred_proof = False  # Can be dug into by strong predators
        elif structure_type in ("wooden_cabin", "tribal_shelter"):
            tier = 2
            max_hp = 250.0
            cap = 6
            light = 11
            def_rating = 45.0
            comfort = 0.8
            pred_proof = True   # Solid wooden door blocks predators
        elif structure_type == "cobblestone_house":
            tier = 3
            max_hp = 650.0
            cap = 12
            light = 14
            def_rating = 120.0
            comfort = 1.0
            pred_proof = True   # Stone masonry fortress walls
        elif structure_type == "fortified_hall":
            tier = 4
            max_hp = 1800.0
            cap = 25
            light = 15
            def_rating = 300.0
            comfort = 1.2
            pred_proof = True   # Impenetrable castle hall
        elif structure_type == "sacred_altar":
            tier = 3
            max_hp = 500.0
            cap = 0
            light = 15
            def_rating = 50.0
            comfort = 1.0
            pred_proof = True

        st = WorldStructure(
            structure_id=sid,
            structure_type=structure_type,
            pos_x=pos_x,
            pos_y=pos_y,
            clan_id=clan_id,
            built_tick=tick,
            tier=tier,
            health=max_hp,
            max_health=max_hp,
            capacity=cap,
            light_level=light,
            defense_rating=def_rating,
            comfort_rating=comfort,
            is_predator_proof=pred_proof,
        )
        with self._lock:
            self.structures[sid] = st
        return st

    def get_nearby_structures(self, x: float, y: float, radius: float = 100.0) -> List[WorldStructure]:
        r2 = radius * radius
        results = []
        for s in self.structures.values():
            if not s.is_active:
                continue
            dx = s.pos_x - x
            dy = s.pos_y - y
            if dx * dx + dy * dy <= r2:
                results.append(s)
        return results

    def find_best_shelter(self, x: float, y: float, max_dist: float = 350.0) -> Optional[WorldStructure]:
        """Finds the best available, highest-tier, uncrowded shelter within reach."""
        candidates = []
        for s in self.structures.values():
            if not s.is_active or s.capacity <= 0 or not s.can_enter():
                continue
            dist = math.hypot(s.pos_x - x, s.pos_y - y)
            if dist <= max_dist:
                candidates.append((dist, s.tier, s))

        if not candidates:
            return None

        # Sort by highest tier first, then shortest distance
        candidates.sort(key=lambda item: (-item[1], item[0]))
        return candidates[0][2]

    def get_clan_shelter_capacity(self, clan_id: str = "genesis_tribe") -> Tuple[int, int]:
        """Returns (total_capacity, currently_occupied)."""
        tot = sum(s.capacity for s in self.structures.values() if s.clan_id == clan_id and s.is_active)
        occ = sum(len(s.occupants) for s in self.structures.values() if s.clan_id == clan_id and s.is_active)
        return (tot, occ)

    def get_clan_highest_tier(self, clan_id: str = "genesis_tribe") -> int:
        """Returns highest shelter tier erected by clan."""
        tiers = [s.tier for s in self.structures.values() if s.clan_id == clan_id and s.is_active and s.capacity > 0]
        return max(tiers) if tiers else 0

    def get_clan_center(self, clan_id: str = "genesis_tribe") -> Optional[Tuple[float, float]]:
        clan_structs = [s for s in self.structures.values() if s.clan_id == clan_id and s.is_active]
        if not clan_structs:
            return None
        avg_x = sum(s.pos_x for s in clan_structs) / len(clan_structs)
        avg_y = sum(s.pos_y for s in clan_structs) / len(clan_structs)
        return (avg_x, avg_y)


# Global settlement singleton
world_settlement_mgr = SettlementManager()
