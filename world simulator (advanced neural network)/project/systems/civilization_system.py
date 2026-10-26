"""
project/systems/civilization_system.py

Civilization System managing technological advancements, cultural knowledge transmission,
emergent settlements, and tribal prosperity across human clans.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human
from project.civilization.technology import world_tech_tree
from project.civilization.settlement import world_settlement_mgr


class CivilizationSystem:
    """Manages technology progression, cultural sharing, and tribal development."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "CivilizationSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.CIVILIZATION

    @property
    def priority(self) -> int:
        return ExecutionPriority.CIVILIZATION

    @property
    def dependencies(self) -> Set[str]:
        return {"SocialSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        sim_tick = context.tick
        humans = [e for e in self._entities_list if e.is_alive and e.entity_type == EntityType.HUMAN]
        if not humans:
            return

        # 1. Cultural Knowledge Transmission: Clan members share discovered technologies
        if sim_tick % 25 == 0:
            for i in range(len(humans)):
                h1 = humans[i]
                for j in range(i + 1, min(len(humans), i + 8)):
                    h2 = humans[j]
                    dist = math.hypot(h1.pos_x - h2.pos_x, h1.pos_y - h2.pos_y)
                    if dist < 45.0:  # Proximity for oral communication and imitation
                        # Transmit tech from h1 to h2
                        for t in h1.known_technologies:
                            if t not in h2.known_technologies:
                                h2.known_technologies.append(t)
                        # Transmit tech from h2 to h1
                        for t in h2.known_technologies:
                            if t not in h1.known_technologies:
                                h1.known_technologies.append(t)

        # 2. Technology Tier Calibration based on clan knowledge
        all_known = set()
        for h in humans:
            all_known.update(h.known_technologies)

        clan_tier = 0
        if any("Stone" in t or "Spear" in t for t in all_known):
            clan_tier = max(clan_tier, 1)
        if any("Shelter" in t or "Pottery" in t or "Bow" in t for t in all_known):
            clan_tier = max(clan_tier, 2)
        if any("Altar" in t or "Monument" in t for t in all_known):
            clan_tier = max(clan_tier, 3)

        for h in humans:
            h.technology_level = max(h.technology_level, clan_tier)

        # 3. Settlement Aura: Campfires and shelters provide comfort and health regen
        if sim_tick % 30 == 0:
            for s in list(world_settlement_mgr.structures.values()):
                if not s.is_active:
                    continue
                for h in humans:
                    dist = math.hypot(h.pos_x - s.pos_x, h.pos_y - s.pos_y)
                    if dist < 50.0:
                        # Warmth / shelter relief
                        h.custom_data["stress"] = max(0.0, h.custom_data.get("stress", 0.0) - 0.08)
                        h.custom_data["dopamine"] = min(1.0, h.custom_data.get("dopamine", 0.0) + 0.05)
                        if h.health < h.max_health:
                            h.health = min(h.max_health, h.health + 0.5)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
