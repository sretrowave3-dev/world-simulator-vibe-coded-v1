"""
project/ai/needs.py

Biological & Psychological Need Drive System for ALife Organisms with Diverse Species Profiles.

Features:
- Multi-dimensional physiological drive tracking (Hunger, Thirst, Fatigue, Safety, Reproduction, Social, Curiosity).
- Species-specific psychological profiles:
  * Bacteria: Chemotaxis, Quorum Sensing Biofilm Urge, Spore Dormancy.
  * Plant: Phototropism, Drought Tolerance, Allelopathy Defense.
  * Herbivore: Hyper-Vigilance, Herd Mentality, Panic Flight Burst, Alarm Calling.
  * Predator: Predatory Aggression, Stalking, Ambush Pounce, Pack Coordination, Kill Dopamine.
  * Human: Intellectual Curiosity, Tactical Cunning, Tribal Altruism, Divine Reverence, Mourning.
  * Omnivore: Opportunistic Gluttony, Bluff Charge, Versatile Digestion.
  * Decomposer: Necrotaxis, Mycelial Soil Enrichment.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any


class NeedType(Enum):
    HUNGER = auto()
    THIRST = auto()
    FATIGUE = auto()
    SAFETY = auto()
    REPRODUCTION = auto()
    SOCIAL = auto()
    CURIOSITY = auto()
    DOMINANCE = auto()
    ALTRUISM = auto()
    DORMANCY = auto()


@dataclass
class SpeciesPsychologyProfile:
    """Psychological and survival behavioral tendencies specific to an organism's taxonomy."""
    species_name: str
    base_fear_sensitivity: float = 1.0
    herd_cohesion_weight: float = 0.5
    predatory_drive: float = 0.0
    curiosity_drive: float = 0.5
    altruism_drive: float = 0.0
    stealth_affinity: float = 0.0
    aggression: float = 0.1
    tactical_retreat_threshold: float = 0.25  # Health % to retreat


def get_default_species_profile(entity_type_name: str) -> SpeciesPsychologyProfile:
    """Factory creating tailored psychological trait profiles for each species."""
    t = entity_type_name.upper()
    if t == "BACTERIA":
        return SpeciesPsychologyProfile(
            species_name="Bacteria",
            base_fear_sensitivity=0.2,
            herd_cohesion_weight=0.8,  # Quorum sensing biofilm urge
            predatory_drive=0.0,
            curiosity_drive=0.1,
            altruism_drive=0.2,
            aggression=0.0,
            tactical_retreat_threshold=0.1,
        )
    elif t == "PLANT":
        return SpeciesPsychologyProfile(
            species_name="Plant",
            base_fear_sensitivity=0.0,
            herd_cohesion_weight=0.2,
            predatory_drive=0.0,
            curiosity_drive=0.0,
            altruism_drive=0.4,  # Mycorrhizal network sharing
            aggression=0.0,
        )
    elif t == "HERBIVORE":
        return SpeciesPsychologyProfile(
            species_name="Herbivore",
            base_fear_sensitivity=1.8,  # High vigilance & panic reflex
            herd_cohesion_weight=0.9,  # Strong herd cohesion
            predatory_drive=0.0,
            curiosity_drive=0.4,
            altruism_drive=0.5,
            aggression=0.1,
            tactical_retreat_threshold=0.6,
        )
    elif t in ("PREDATOR", "CARNIVORE"):
        return SpeciesPsychologyProfile(
            species_name="Predator",
            base_fear_sensitivity=0.4,  # Bold apex hunter
            herd_cohesion_weight=0.4,  # Pack coordination
            predatory_drive=1.0,      # High stalking & ambush drive
            curiosity_drive=0.6,
            altruism_drive=0.2,
            stealth_affinity=0.85,
            aggression=0.9,
            tactical_retreat_threshold=0.2,
        )
    elif t == "HUMAN":
        return SpeciesPsychologyProfile(
            species_name="Human",
            base_fear_sensitivity=0.8,
            herd_cohesion_weight=0.85, # Tribal loyalty & civilization
            predatory_drive=0.5,      # Tool-assisted hunting & defense
            curiosity_drive=1.0,      # High intellectual exploration & invention
            altruism_drive=0.85,     # Resource sharing & mutual aid
            stealth_affinity=0.5,
            aggression=0.4,
            tactical_retreat_threshold=0.35,
        )
    elif t == "OMNIVORE":
        return SpeciesPsychologyProfile(
            species_name="Omnivore",
            base_fear_sensitivity=0.7,
            herd_cohesion_weight=0.4,
            predatory_drive=0.6,
            curiosity_drive=0.7,
            altruism_drive=0.3,
            aggression=0.5,
            tactical_retreat_threshold=0.3,
        )
    elif t == "AVIAN":
        return SpeciesPsychologyProfile(
            species_name="Avian",
            base_fear_sensitivity=0.6,
            herd_cohesion_weight=0.5,
            predatory_drive=0.75,
            curiosity_drive=0.8,
            altruism_drive=0.4,
            stealth_affinity=0.6,
            aggression=0.6,
            tactical_retreat_threshold=0.4,
        )
    elif t == "AMPHIBIAN":
        return SpeciesPsychologyProfile(
            species_name="Amphibian",
            base_fear_sensitivity=1.2,
            herd_cohesion_weight=0.6,
            predatory_drive=0.4,
            curiosity_drive=0.3,
            altruism_drive=0.2,
            aggression=0.2,
            tactical_retreat_threshold=0.5,
        )
    elif t == "ARTHROPOD":
        return SpeciesPsychologyProfile(
            species_name="Arthropod",
            base_fear_sensitivity=0.3,
            herd_cohesion_weight=0.95, # Eusocial hive swarming
            predatory_drive=0.1,
            curiosity_drive=0.5,
            altruism_drive=0.9,      # Hive altruism
            aggression=0.3,
            tactical_retreat_threshold=0.1,
        )
    elif t == "REPTILE":
        return SpeciesPsychologyProfile(
            species_name="Reptile",
            base_fear_sensitivity=0.5,
            herd_cohesion_weight=0.2, # Solitary ectotherm
            predatory_drive=0.85,
            curiosity_drive=0.4,
            altruism_drive=0.1,
            stealth_affinity=0.9,
            aggression=0.8,
            tactical_retreat_threshold=0.3,
        )
    elif t == "FUNGUS":
        return SpeciesPsychologyProfile(
            species_name="Fungus",
            base_fear_sensitivity=0.0,
            herd_cohesion_weight=0.7, # Mycelial interconnectivity
            predatory_drive=0.0,
            curiosity_drive=0.0,
            altruism_drive=0.8,      # Symbiotic mineral sharing
            aggression=0.0,
        )
    else:  # DECOMPOSER / GENERIC
        return SpeciesPsychologyProfile(
            species_name="Decomposer",
            base_fear_sensitivity=0.1,
            herd_cohesion_weight=0.6,
            predatory_drive=0.0,
            curiosity_drive=0.2,
            altruism_drive=0.6,
            aggression=0.0,
        )


@dataclass
class OrganismNeeds:
    """
    Multi-dimensional psychological drive state tracking urgency on scale [0.0 to 1.0].
    """

    hunger: float = 0.0
    thirst: float = 0.0
    fatigue: float = 0.0
    fear: float = 0.0
    reproduction_urge: float = 0.0
    loneliness: float = 0.0
    boredom: float = 0.0
    predatory_hunger: float = 0.0
    altruism_urge: float = 0.0
    dormancy_urge: float = 0.0

    def update_from_vitals(
        self,
        energy: float,
        max_energy: float,
        hydration: float,
        max_hydration: float,
        stamina: float = 100.0,
        max_stamina: float = 100.0,
        age_ticks: int = 0,
        maturity_ticks: int = 1000,
        threat_level: float = 0.0,
        nearby_allies: int = 0,
        profile: Optional[SpeciesPsychologyProfile] = None,
    ) -> None:
        """Derives need urgency levels directly from biological vitality state and species traits."""
        p = profile or get_default_species_profile("GENERIC")

        from project.core.biology import calculate_hunger_urgency, calculate_thirst_urgency

        # Base biological drives with continuous non-linear urgency curves
        self.hunger = calculate_hunger_urgency(energy, max_energy)
        self.thirst = calculate_thirst_urgency(hydration, max_hydration)
        self.fatigue = max(0.0, min(1.0, 1.0 - (stamina / max(1.0, max_stamina))))
        self.fear = max(0.0, min(1.0, threat_level * p.base_fear_sensitivity))

        # Reproduction urgency (cycles with maturity and energy reserves)
        if age_ticks >= maturity_ticks and energy > (max_energy * 0.45):
            self.reproduction_urge = min(1.0, self.reproduction_urge + 0.005)
        else:
            self.reproduction_urge = max(0.0, self.reproduction_urge - 0.01)

        # Social & herd cohesion
        if nearby_allies == 0:
            self.loneliness = min(1.0, self.loneliness + 0.005 * p.herd_cohesion_weight)
        else:
            self.loneliness = max(0.0, self.loneliness - 0.02 * nearby_allies)

        # Predatory urge for carnivores/predators
        if p.predatory_drive > 0.0:
            self.predatory_hunger = min(1.0, self.hunger * p.predatory_drive + (p.aggression * 0.3))
        else:
            self.predatory_hunger = 0.0

        # Curiosity / Exploration drive
        self.boredom = min(1.0, self.boredom + 0.003 * p.curiosity_drive)

        # Altruism drive for humans and cooperative organisms
        if p.altruism_drive > 0.0 and energy > (max_energy * 0.55):
            self.altruism_urge = min(1.0, p.altruism_drive * (energy / max_energy))
        else:
            self.altruism_urge = 0.0

        # Dormancy urge for microbes and extremophiles during severe starvation
        if energy < (max_energy * 0.15) and p.species_name == "Bacteria":
            self.dormancy_urge = 1.0
        else:
            self.dormancy_urge = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Serializes current multi-dimensional needs to a dictionary of floating ratios [0.0 to 1.0]."""
        return {
            "hunger": round(self.hunger, 3),
            "thirst": round(self.thirst, 3),
            "fatigue": round(self.fatigue, 3),
            "fear": round(self.fear, 3),
            "reproduction": round(self.reproduction_urge, 3),
            "social": round(self.loneliness, 3),
            "curiosity": round(self.boredom, 3),
            "altruism": round(self.altruism_urge, 3),
            "predation": round(self.predatory_hunger, 3),
        }

    def get_most_urgent_need(self, profile: Optional[SpeciesPsychologyProfile] = None) -> Tuple[NeedType, float]:
        """Returns the single highest urgency need weighted by species psychology."""
        p = profile or get_default_species_profile("GENERIC")
        needs_table = [
            (NeedType.SAFETY, self.fear * 1.6),
            (NeedType.THIRST, self.thirst * 1.3),
            (NeedType.HUNGER, (self.predatory_hunger if p.predatory_drive > 0.5 else self.hunger) * 1.1),
            (NeedType.REPRODUCTION, self.reproduction_urge * 0.9),
            (NeedType.ALTRUISM, self.altruism_urge * 0.75),
            (NeedType.SOCIAL, self.loneliness * 0.6 * p.herd_cohesion_weight),
            (NeedType.CURIOSITY, self.boredom * 0.5 * p.curiosity_drive),
            (NeedType.DORMANCY, self.dormancy_urge * 2.0),
        ]
        needs_table.sort(key=lambda item: item[1], reverse=True)
        return needs_table[0]
