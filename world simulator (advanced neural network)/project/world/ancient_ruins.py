"""
project/world/ancient_ruins.py

Manages the mysterious boundary wall breach, ancient ceremonial pathway,
and the grand Forbidden Hall of the Primordials.

Civilization has no initial knowledge of this sanctuary; organisms must explore
and stumble upon it near the northern boundary wall to uncover its ancient secrets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from project.entities.entity import Entity, EntityType
from project.entities.human import Human


@dataclass
class AncientPillar:
    """A monumental stone pillar carved with glowing celestial glyphs."""
    pos_x: float
    pos_y: float
    radius: float = 8.0
    glow_color: Tuple[int, int, int] = (0, 230, 255)


@dataclass
class AncientRuinsManager:
    """
    Coordinates the physical structures, discovery fog-of-war, and ancient
    sanctuary blessings for the forbidden boundary hall complex.
    """
    # Breach location along the North boundary (Y = 0)
    breach_min_x: float = 2360.0
    breach_max_x: float = 2540.0
    breach_y: float = 0.0

    # Pathway coordinates
    path_min_x: float = 2420.0
    path_max_x: float = 2480.0
    path_start_y: float = 380.0
    path_end_y: float = 40.0

    # Grand Hall bounds
    hall_min_x: float = 2220.0
    hall_max_x: float = 2680.0
    hall_min_y: float = 30.0
    hall_max_y: float = 360.0

    # Altar & Artifact center
    altar_pos: Tuple[float, float] = (2450.0, 180.0)
    west_archive_pos: Tuple[float, float] = (2270.0, 180.0)
    east_relic_pos: Tuple[float, float] = (2630.0, 180.0)

    # Exploration & Discovery State (Unknown to civilization initially)
    discovered_entity_ids: Set[str] = field(default_factory=set)
    civilization_discovered: bool = False
    first_discoverer_name: Optional[str] = None
    discovery_tick: Optional[int] = None
    discovery_log: List[Dict[str, Any]] = field(default_factory=list)

    # Architectural Pillars
    pillars: List[AncientPillar] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.pillars:
            # 8 Grand Colonnade Pillars lining the sacred pathway
            left_x = 2330.0
            right_x = 2570.0
            for py in [320.0, 240.0, 160.0, 80.0]:
                self.pillars.append(AncientPillar(pos_x=left_x, pos_y=py))
                self.pillars.append(AncientPillar(pos_x=right_x, pos_y=py))

    def is_inside_hall(self, x: float, y: float) -> bool:
        """Returns True if world position falls within the ancient hall complex."""
        return (
            self.hall_min_x <= x <= self.hall_max_x
            and self.hall_min_y <= y <= self.hall_max_y
        )

    def is_near_breach_or_hall(self, x: float, y: float, radius: float = 120.0) -> bool:
        """Returns True if position is within discovery proximity of the ruins."""
        if self.is_inside_hall(x, y):
            return True
        # Check distance to breach center
        breach_center_x = (self.breach_min_x + self.breach_max_x) / 2.0
        dist_to_breach = math.hypot(x - breach_center_x, y - self.breach_y)
        if dist_to_breach <= radius:
            return True
        # Check distance to altar
        dist_to_altar = math.hypot(x - self.altar_pos[0], y - self.altar_pos[1])
        return dist_to_altar <= radius + 150.0

    def update_exploration(self, entities_list: List[Entity], current_tick: int) -> List[str]:
        """
        Scans nearby organisms. If an organism discovers the ancient hall for the first time,
        triggers exploration epiphanies and records discovery thoughts.
        """
        events: List[str] = []

        for entity in entities_list:
            if not entity.is_alive:
                continue

            ex, ey = entity.pos_x, entity.pos_y
            if self.is_near_breach_or_hall(ex, ey):
                eid = entity.entity_id

                # First time this organism discovers the ruins
                if eid not in self.discovered_entity_ids:
                    self.discovered_entity_ids.add(eid)
                    entity_name = getattr(entity, "name", f"Explorer_{eid}")

                    # Bestow Discovery Epiphany
                    entity.custom_data["dopamine"] = 1.0
                    entity.custom_data["stress"] = 0.0
                    entity.custom_data["fear"] = 0.0
                    entity.custom_data["curiosity"] = 1.0
                    entity.gain_energy(40.0)
                    entity.quench_thirst(30.0)

                    if isinstance(entity, Human) or entity.entity_type == EntityType.HUMAN:
                        current_iq = getattr(entity, "intelligence_quotient", 100.0)
                        entity.intelligence_quotient = current_iq + 25.0
                        tech_lvl = getattr(entity, "technology_level", 1)
                        entity.technology_level = tech_lvl + 1

                        # Log philosophical thought in cognitive diary
                        thought_msg = (
                            f"✨ [DISCOVERY EPIPHANY] I ventured near the world boundary and stumbled upon "
                            f"a fractured breach into the ancient Forbidden Sanctuary! Before me stand towering "
                            f"glowing stone pillars and an altar of cosmic energy. We are not the first."
                        )
                        if hasattr(entity, "thought_logger") and entity.thought_logger:
                            entity.thought_logger.log_thought(
                                tick=current_tick,
                                human_id=eid,
                                human_name=entity_name,
                                thought=thought_msg,
                                emotion="AWE_AND_TRANSCENDENCE",
                                iq_at_time=entity.intelligence_quotient,
                                god_affinity=entity.custom_data.get("god_affinity", 50.0),
                            )

                    # First Civilization Discovery
                    if not self.civilization_discovered:
                        self.civilization_discovered = True
                        self.first_discoverer_name = entity_name
                        self.discovery_tick = current_tick
                        msg = (
                            f"🏛️ [ANCIENT RUINS DISCOVERED] {entity_name} has breached the forbidden boundary wall "
                            f"and discovered the Sanctuary of the Primordials at ({ex:.1f}, {ey:.1f})!"
                        )
                        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
                        events.append(msg)

                # Continuous Sanctuary Blessing while inside the Great Hall
                if self.is_inside_hall(ex, ey):
                    entity.heal(0.3)
                    entity.gain_energy(0.4)
                    entity.custom_data["divine_sanctuary_active"] = True
                    entity.custom_data["stress"] = 0.0
                    if getattr(entity, "stamina", 100.0) < getattr(entity, "max_stamina", 100.0):
                        entity.stamina = min(entity.max_stamina, entity.stamina + 0.8)

        return events


# Singleton global instance
ancient_ruins_mgr = AncientRuinsManager()
