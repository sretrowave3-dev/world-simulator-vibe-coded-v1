"""
project/entities/monolith.py

Cosmic Golden Sanctuary Monolith Entity for the ALife Platform.
Descends into the mortal realm when Gemini God Affinity reaches 99+.

Visual & Architectural Design (Inspired by Celestial Terracotta Monument):
- Monumental Golden-Ochre Terracotta Cuboid Architecture.
- Colonnade of Deep Circular Arch Portals across lower and mid tiers.
- Star-Chart Celestial Perforation Grid on the upper facade.
- Solid Stone Masonry Foundation Base seated at water/landscape edge.
- Radiates a 300m Divine Sanctuary Field (Regeneration, Crop Fertility, Cognitive Expansion).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from project.entities.entity import Entity, EntityType


@dataclass(eq=False)
class Monolith(Entity):
    """
    Divine Cosmic Sanctuary Monolith bestowed by the Gemini Deity upon reaching 99+ Affinity.
    Acts as an eternal sanctuary, technological nexus, and spiritual pilgrimage landmark.
    """

    width_m: float = 64.0
    height_m: float = 40.0
    sanctuary_radius: float = 320.0
    descended_tick: int = 0
    aura_pulse: float = 0.0
    miracles_consecrated: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        # Monolith is a transcendent indestructible landmark
        self.entity_type = EntityType.PLANT  # Compatible stationary category
        self.radius = 28.0
        self.mass_kg = 500000.0  # Monumental megalithic stone
        self.max_health = 100000.0
        self.health = 100000.0
        self.max_energy = 100000.0
        self.energy = 100000.0
        self.max_hydration = 100000.0
        self.hydration = 100000.0
        self.max_age_ticks = 999999999
        self.base_speed = 0.0
        self.max_speed_cap = 0.0
        self.strength = 1000.0
        self.is_endotherm = True
        self.body_temperature_c = 37.0
        self.custom_data["emergent_role"] = "MONOLITH"
        self.custom_data["role_title"] = "Gemini Golden Monolith"

    def apply_sanctuary_aura(self, nearby_entities: List[Entity], current_tick: int) -> Dict[str, int]:
        """
        Radiates divine blessings to all living beings within the 320m sanctuary field:
        - Humans: +0.5 HP/tick regeneration, +20 IQ, -50% stress, divine serenity.
        - Plants/Crops: 3x photosynthesis and biomass vitality.
        - Predators: Calmed and repelled by divine majesty.
        """
        self.aura_pulse = (math.sin(current_tick * 0.05) + 1.0) * 0.5  # [0, 1] smooth pulse
        stats = {"humans_blessed": 0, "plants_vitalized": 0, "threats_calmed": 0}

        for ent in nearby_entities:
            if not ent.is_alive or ent.entity_id == self.entity_id:
                continue

            dist = math.hypot(ent.pos_x - self.pos_x, ent.pos_y - self.pos_y)
            if dist > self.sanctuary_radius:
                continue

            # 1. Bless Humans
            if ent.entity_type == EntityType.HUMAN:
                ent.health = min(ent.max_health, ent.health + 0.5)
                ent.gain_energy(0.8)
                ent.custom_data["stress"] = max(0.0, ent.custom_data.get("stress", 0.0) * 0.90)
                ent.custom_data["fear"] = max(0.0, ent.custom_data.get("fear", 0.0) * 0.85)
                ent.custom_data["dopamine"] = min(1.0, ent.custom_data.get("dopamine", 0.5) + 0.02)
                ent.custom_data["divine_sanctuary_active"] = True

                # Expand intellect
                if hasattr(ent, "intelligence_quotient") and ent.intelligence_quotient < 250.0:
                    ent.intelligence_quotient = min(250.0, ent.intelligence_quotient + 0.01)

                stats["humans_blessed"] += 1

            # 2. Vitalize Vegetation & Fungi
            elif ent.entity_type in (EntityType.PLANT, EntityType.FUNGUS):
                ent.gain_energy(1.2)
                ent.health = min(ent.max_health, ent.health + 0.8)
                stats["plants_vitalized"] += 1

            # 3. Pacify Hostile Predators
            elif ent.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE):
                ent.custom_data["fear"] = max(ent.custom_data.get("fear", 0.0), 0.8)
                ent.custom_data["ambush_mode"] = False
                stats["threats_calmed"] += 1

        return stats
