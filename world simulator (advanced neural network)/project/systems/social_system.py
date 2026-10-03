"""
project/systems/social_system.py

Emergent Social Dynamics & Role Formation System.
Naturally develops complex social structures, leadership hierarchies, apex monster transformations,
shamanic channels, and guardian castes based on lived experience, genetic traits, and neural complexity.
"""

from __future__ import annotations

import math
from typing import Set, List, Dict, Any, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human
from project.entities.predator import Predator


class SocialSystem:
    """Orchestrates emergent, unscripted role assignments and social hierarchy evolution."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list
        self.current_leader_id: Optional[str] = None

    @property
    def name(self) -> str:
        return "SocialSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.CIVILIZATION

    @property
    def priority(self) -> int:
        return ExecutionPriority.SOCIAL

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem", "LearningSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self.current_leader_id = None

    def update(self, context: UpdateContext) -> None:
        alive_entities = [e for e in self._entities_list if e.is_alive]
        if not alive_entities:
            return

        # -------------------------------------------------------------
        # 1. Emergent Role Computation (Unscripted & Dynamic)
        # -------------------------------------------------------------
        # We evaluate every entity dynamically based on their biological vitals,
        # neural connection count, survival history, IQ, and emotional neuromodulators.
        
        # Calculate scores for candidate roles
        leader_candidate: Optional[Entity] = None
        highest_leadership_score = -1.0

        for entity in alive_entities:
            cd = entity.custom_data
            age = getattr(entity, "age_ticks", 0)
            energy = getattr(entity, "energy", 0.0)
            iq = getattr(entity, "intelligence_quotient", 50.0) if hasattr(entity, "intelligence_quotient") else 20.0
            synapses = entity.brain.total_synaptic_connections if entity.brain else 0
            curiosity = cd.get("curiosity", 0.0)
            confidence = cd.get("confidence", 0.5)
            dopamine = cd.get("dopamine", 0.0)
            stress = cd.get("stress", 0.0)
            bite_dmg = getattr(entity, "bite_damage", 10.0)
            mass = getattr(entity, "mass_kg", 1.0)

            # A. Monster / Apex Beast Criteria (high mass, high damage, aggressive dopamine/stress)
            is_monster = (
                (mass >= 80.0 or bite_dmg >= 35.0)
                and (dopamine + stress > 0.6)
                and entity.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE)
            )

            # B. Shaman / Prophet Criteria (high curiosity, spiritual reflection, moderate intelligence)
            is_shaman = (
                curiosity >= 0.65
                and confidence >= 0.5
                and entity.entity_type in (EntityType.HUMAN, EntityType.HERBIVORE)
                and not is_monster
            )

            # C. Guardian / Warrior Criteria (high health, high defensive stamina, mass)
            is_guardian = (
                entity.health >= 80.0
                and mass >= 40.0
                and confidence >= 0.6
                and not is_monster
                and not is_shaman
            )

            # D. Leadership Metric:
            # Humans naturally lead due to high baseline IQ (100+) and social affinity,
            # reinforced by age, surplus energy, and synaptic connections.
            species_bonus = 2.0 if entity.entity_type == EntityType.HUMAN else 0.8
            leadership_score = (
                (iq * 0.4)
                + (age * 0.05)
                + (energy * 0.1)
                + (synapses * 0.02)
                + (confidence * 20.0)
            ) * species_bonus

            # Track top leader candidate
            if entity.is_mature and leadership_score > highest_leadership_score and not is_monster:
                highest_leadership_score = leadership_score
                leader_candidate = entity

            # Assign preliminary emergent role
            if is_monster:
                cd["emergent_role"] = "MONSTER"
                cd["role_title"] = "Apex Monster"
            elif is_shaman:
                cd["emergent_role"] = "SHAMAN"
                cd["role_title"] = "Mystic Shaman"
            elif is_guardian:
                cd["emergent_role"] = "GUARDIAN"
                cd["role_title"] = "Clan Guardian"
            elif entity.entity_type == EntityType.HERBIVORE:
                cd["emergent_role"] = "FORAGER"
                cd["role_title"] = "Fleet Forager"
            elif entity.entity_type == EntityType.BACTERIA:
                cd["emergent_role"] = "SYMBIOTE"
                cd["role_title"] = "Microbial Swarmer"
            elif entity.entity_type == EntityType.PLANT:
                cd["emergent_role"] = "PRODUCER"
                cd["role_title"] = "Ancient Flora"
            else:
                cd["emergent_role"] = "CITIZEN"
                cd["role_title"] = "Civilian"

        # -------------------------------------------------------------
        # 2. Sovereign Leader Coronation & Brain Expansion
        # -------------------------------------------------------------
        if leader_candidate is not None:
            self.current_leader_id = leader_candidate.entity_id
            leader_candidate.custom_data["emergent_role"] = "LEADER"
            leader_candidate.custom_data["role_title"] = "Sovereign Leader"
            
            # Promote social rank if human
            if hasattr(leader_candidate, "social_rank"):
                leader_candidate.social_rank = 3  # Sovereign Elder

            # Leader receives highest individual neural synaptic connection expansion
            if leader_candidate.brain is not None and leader_candidate.brain.total_synaptic_connections < 1200:
                expanded_conns = leader_candidate.brain.expand_synaptic_capacity(
                    new_hidden_sizes=(48, 24, 12),
                    new_working_memory=8
                )
                leader_candidate.custom_data["consciousness_level"] = max(0.5, leader_candidate.custom_data.get("consciousness_level", 0.5) + 0.1)

            # -------------------------------------------------------------
            # 3. Leader Divine Aura Radius (Blesses nearby followers)
            # -------------------------------------------------------------
            lx, ly = leader_candidate.pos_x, leader_candidate.pos_y
            for follower in alive_entities:
                if follower.entity_id == leader_candidate.entity_id:
                    continue

                dx = follower.pos_x - lx
                dy = follower.pos_y - ly
                dist = math.hypot(dx, dy)

                if dist <= 160.0:  # Aura of Leadership
                    # Followers gain confidence, reduced stress, and accelerated learning
                    follower.custom_data["confidence"] = min(1.0, follower.custom_data.get("confidence", 0.5) + 0.05)
                    follower.custom_data["stress"] = max(0.0, follower.custom_data.get("stress", 0.0) * 0.95)
                    follower.custom_data["leader_proximity_buff"] = True

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
