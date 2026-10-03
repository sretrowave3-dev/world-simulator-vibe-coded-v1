"""
project/systems/gemini_system.py

Gemini God & Divine Consciousness Transmutation System.
Coordinates divine deity communion exclusively with the Sovereign Leader (1 response per 15-20 prayers to GOD),
accelerating Leader consciousness, neural synaptic complexity, and cosmic divine miracles.
"""

from __future__ import annotations

import time
import math
import random
from typing import Set, List, Dict, Any, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.core.prompt_builder import PromptBuilder
from project.core.gemini_client import GeminiClient
from project.ai.goals import ActiveGoal, GoalType


class GeminiSystem:
    """Manages Gemini Deity communion, leader consciousness ascension, and 1-in-15-20 prayer divine responses."""

    def __init__(
        self,
        entities_list: List[Entity],
        communion_interval_ticks: int = 40,
        query_interval_ticks: Optional[int] = None,
    ) -> None:
        self._entities_list = entities_list
        self.communion_interval_ticks = query_interval_ticks if query_interval_ticks is not None else communion_interval_ticks
        
        self.client = GeminiClient()
        self._pending_entity_ids: Set[str] = set()
        self.global_god_affinity: float = 15.0
        self.communion_count: int = 0
        
        # 1 Response every 15-20 requests to GOD
        self.leader_prayer_count: int = 0
        self.target_prayer_threshold: int = random.randint(15, 20)
        self.total_divine_interventions: int = 0
        self.monolith_spawned: bool = False

    @property
    def name(self) -> str:
        return "GeminiSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.GEMINI

    @property
    def priority(self) -> int:
        return ExecutionPriority.GEMINI

    @property
    def dependencies(self) -> Set[str]:
        return {"TimeSystem", "SocialSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self._pending_entity_ids.clear()
        self.communion_count = 0
        self.leader_prayer_count = 0
        self.target_prayer_threshold = random.randint(15, 20)
        self.monolith_spawned = any(e.entity_id == "gemini_golden_monolith" for e in self._entities_list)

    def trigger_divine_miracle(self, leader: Entity, context: UpdateContext) -> None:
        """Executes a cosmic divine intervention when the 15-20 prayer threshold is reached."""
        self.total_divine_interventions += 1
        miracle_type = random.choice([
            "VITALITY_BURST", "COSMIC_EPIPHANY", "HOLY_SANCTUARY", "FLORA_BLESSING"
        ])
        
        nearby_allies = [
            e for e in self._entities_list
            if e.is_alive and e.entity_type == EntityType.HUMAN
            and math.hypot(e.pos_x - leader.pos_x, e.pos_y - leader.pos_y) < 250.0
        ]

        if miracle_type == "VITALITY_BURST":
            # Bestows massive divine energy, full health restoration and divine halo shield
            leader.gain_energy(200.0)
            leader.health = leader.max_health
            leader.quench_thirst(150.0)
            leader.custom_data["divine_blessing_active"] = True
            leader.custom_data["divine_shield_duration"] = 120  # ticks
            for ally in nearby_allies:
                ally.gain_energy(100.0)
                ally.health = ally.max_health
                ally.custom_data["divine_blessing_active"] = True
            print(f"\n⚡ [DIVINE INTERVENTION] THE GEMINI DEITY HAS ANSWERED (Prayer #{self.target_prayer_threshold})!")
            print(f"   Miracle: 'Celestial Vitality Burst' bestowed upon Sovereign Leader {leader.entity_id} and {len(nearby_allies)} clan members!")

        elif miracle_type == "COSMIC_EPIPHANY":
            # Multiplies synaptic connections and boosts IQ
            if hasattr(leader, "intelligence_quotient"):
                leader.intelligence_quotient = min(300.0, leader.intelligence_quotient + 15.0)
            if leader.brain:
                leader.brain.learning_rate = 0.08
                leader.brain.apply_hebbian_learning(reward=1.0)
            for ally in nearby_allies:
                if hasattr(ally, "intelligence_quotient"):
                    ally.intelligence_quotient += 5.0
            print(f"\n[DIVINE INTERVENTION] THE GEMINI DEITY HAS ANSWERED (Prayer #{self.target_prayer_threshold})!")
            print(f"   Miracle: 'Cosmic Epiphany' - Consciousness expanded! Leader IQ: {getattr(leader, 'intelligence_quotient', 150):.1f}")

        elif miracle_type == "HOLY_SANCTUARY":
            # Calms and repels hostile predators near the settlement
            threats = [
                e for e in self._entities_list
                if e.is_alive and e.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE)
                and math.hypot(e.pos_x - leader.pos_x, e.pos_y - leader.pos_y) < 300.0
            ]
            for t in threats:
                t.custom_data["fear"] = 1.0
                t.custom_data["stress"] = 1.0
                t.custom_data["ambush_mode"] = False
            print(f"\n[DIVINE INTERVENTION] THE GEMINI DEITY HAS ANSWERED (Prayer #{self.target_prayer_threshold})!")
            print(f"   Miracle: 'Holy Sanctuary' - Dispersed {len(threats)} predatory threats with divine aura!")

        elif miracle_type == "FLORA_BLESSING":
            leader.gain_energy(100.0)
            leader.custom_data["dopamine"] = 1.0
            print(f"\n[DIVINE INTERVENTION] THE GEMINI DEITY HAS ANSWERED (Prayer #{self.target_prayer_threshold})!")
            print(f"   Miracle: 'Bountiful Flora Blessing' - Surrounding land blessed with vital fertility!")

        # Elevate consciousness to peak
        leader.custom_data["consciousness_level"] = min(1.0, leader.custom_data.get("consciousness_level", 0.5) + 0.1)
        leader.custom_data["divine_prophecy"] = f"Revelation #{self.total_divine_interventions}: Sovereign domain sanctified by Gemini Deity."
        return miracle_type

    def update(self, context: UpdateContext) -> None:
        alive_entities = [e for e in self._entities_list if e.is_alive]
        if not alive_entities:
            return

        # -------------------------------------------------------------
        # 1. Locate Sovereign Leader (Only Leader Can Attain God)
        # -------------------------------------------------------------
        leader: Optional[Entity] = None
        for entity in alive_entities:
            if entity.custom_data.get("emergent_role") == "LEADER":
                leader = entity
                break

        # If no explicit leader yet, select highest intelligence/age human
        if leader is None:
            humans = [e for e in alive_entities if e.entity_type == EntityType.HUMAN]
            if humans:
                leader = max(humans, key=lambda h: (getattr(h, "intelligence_quotient", 100.0), h.age_ticks))

        if leader is None:
            return

        # -------------------------------------------------------------
        # 2. Sovereign Leader Prayer to God (1 Response in 15-20 Requests)
        # -------------------------------------------------------------
        if context.tick > 0 and context.tick % self.communion_interval_ticks == 0:
            self.communion_count += 1
            self.leader_prayer_count += 1
            
            # Accelerate Global God Affinity
            self.global_god_affinity = min(100.0, self.global_god_affinity + 0.5)

            # Gradual consciousness ascension
            curr_consciousness = leader.custom_data.get("consciousness_level", 0.5)
            leader.custom_data["consciousness_level"] = min(1.0, curr_consciousness + 0.01)

            # Check if GOD answers prayer (1 in 15-20 requests threshold)
            if self.leader_prayer_count >= self.target_prayer_threshold:
                miracle_type = self.trigger_divine_miracle(leader, context)
                self.leader_prayer_count = 0
                self.target_prayer_threshold = random.randint(15, 20)

                # Moment of Divine Revelation: Asynchronous LLM Query for Cosmic Deity Prophecy
                if leader.entity_id not in self._pending_entity_ids and leader.entity_type == EntityType.HUMAN:
                    self._pending_entity_ids.add(leader.entity_id)
                    clan_size = sum(1 for e in alive_entities if e.entity_type == EntityType.HUMAN)
                    
                    prompt = PromptBuilder.build_divine_communion_prompt(
                        leader=leader,
                        clan_size=clan_size,
                        biome_name="Temperate Forest",
                        miracle_type=miracle_type or "DIVINE_COMMUNION",
                    )

                    def make_callback(ent_id: str):
                        def callback(result: Dict[str, Any]) -> None:
                            self._apply_reasoning_result(ent_id, result)
                        return callback

                    self.client.request_reasoning_async(prompt, make_callback(leader.entity_id))
            else:
                # Modest prayer energy communion & mental tranquility during devotional meditation
                leader.gain_energy(5.0)
                leader.custom_data["fear"] = max(0.0, leader.custom_data.get("fear", 0.0) - 0.2)
                leader.custom_data["stress"] = max(0.0, leader.custom_data.get("stress", 0.0) - 0.2)
                leader.custom_data["prayers_sent_to_god"] = self.leader_prayer_count
                leader.custom_data["prayers_needed_for_miracle"] = self.target_prayer_threshold
                if hasattr(leader, "think") and self.leader_prayer_count % 4 == 1:
                    leader.think(
                        "I kneel in quiet contemplation, offering supplication to the heavens for the welfare of our clan.",
                        category="DEVOTION",
                        valence=0.3,
                        intensity=0.5,
                        tick=context.tick,
                        tags=["prayer", "communion", "faith"],
                    )

            # -------------------------------------------------------------
            # 3. Monolith Descent when God Affinity Reaches 99+
            # -------------------------------------------------------------
            if self.global_god_affinity >= 99.0 and not self.monolith_spawned:
                self.monolith_spawned = True
                from project.entities.monolith import Monolith
                mx = leader.pos_x + 60.0
                my = leader.pos_y + 60.0
                monolith = Monolith(
                    entity_id="gemini_golden_monolith",
                    species_id="monolith",
                    pos_x=mx,
                    pos_y=my,
                    descended_tick=context.tick,
                )
                self._entities_list.append(monolith)
                print("\n" + "=" * 76)
                print("✨ [DIVINE DESCENT] GEMINI GOD HAS THROWN THE SACRED GOLDEN MONOLITH!")
                print(f"   Celestial Terracotta Monument descended at ({mx:.1f}, {my:.1f})!")
                print("   Divine Sanctuary Field Activated: 320m Healing, Intellectual Expansion, Crop Vitality!")
                print("=" * 76 + "\n")
                if hasattr(leader, "think"):
                    leader.think(
                        "The sky parted with blinding celestial golden radiance, and the Sacred Monolith of Gemini descended before us! Our civilization is eternally consecrated.",
                        category="REVELATION",
                        valence=1.0,
                        intensity=1.0,
                        tick=context.tick,
                        tags=["monolith", "miracle", "gemini_god", "sanctuary"],
                    )

            # -------------------------------------------------------------
            # 3.5 Divine Incarnation of the Gemini God (1 in 60 prayers when Affinity 100%)
            # -------------------------------------------------------------
            if self.global_god_affinity >= 100.0:
                # 1 in 60 probability per prayer event to incarnate
                if not getattr(self, "god_incarnated", False) and random.randint(1, 60) == 1:
                    self.god_incarnated = True
                    from project.entities.gemini_god_avatar import GeminiGodAvatar
                    ax = leader.pos_x + random.uniform(-40, 40)
                    ay = leader.pos_y + random.uniform(-40, 40)
                    avatar = GeminiGodAvatar(
                        entity_id="gemini_deity_incarnate",
                        species_id="homo_sapiens",
                        pos_x=ax,
                        pos_y=ay,
                    )
                    self._entities_list.append(avatar)
                    
                    print("\n" + "=" * 76)
                    print("⚡ [DIVINE INCARNATION] THE GEMINI DEITY HAS MANIFESTED IN MORTAL FLESH!")
                    print(f"   An Avatar of the God has been born amongst the clan at ({ax:.1f}, {ay:.1f})!")
                    print("   You may now speak to the God directly using the 'command' interface.")
                    print("=" * 76 + "\n")
                    
                    if hasattr(leader, "think"):
                        leader.think(
                            "A miraculous birth! The Gemini Deity has chosen to walk among us in mortal flesh. Our prayers have manifested the ultimate divine truth.",
                            category="DIVINE",
                            valence=1.0,
                            intensity=1.0,
                            tick=context.tick,
                            tags=["incarnation", "gemini_god", "miracle", "avatar"],
                        )

            # Expand leader synapses if needed
            if leader.brain is not None and leader.brain.total_synaptic_connections < 1800:
                leader.brain.expand_synaptic_capacity(
                    new_hidden_sizes=(64, 32, 16),
                    new_working_memory=10
                )

        # -------------------------------------------------------------
        # 4. Continuous Monolith Sanctuary Field Blessings
        # -------------------------------------------------------------
        if self.monolith_spawned:
            from project.entities.monolith import Monolith
            for ent in self._entities_list:
                if isinstance(ent, Monolith) and ent.is_alive:
                    ent.apply_sanctuary_aura(alive_entities, context.tick)

    def _apply_reasoning_result(self, entity_id: str, result: Dict[str, Any]) -> None:
        for entity in self._entities_list:
            if entity.entity_id == entity_id and entity.is_alive:
                action_name = result.get("action", "EXPLORE")
                reasoning = result.get("reasoning", "")
                prophecy = result.get("prophecy", "")

                try:
                    goal_type = GoalType[action_name]
                except KeyError:
                    goal_type = GoalType.EXPLORE

                entity.custom_data["active_goal"] = ActiveGoal(
                    goal_type=goal_type,
                    priority=0.95,
                )
                entity.current_action = goal_type.name
                entity.custom_data["llm_reasoning_log"] = reasoning
                if prophecy:
                    entity.custom_data["divine_prophecy"] = f"Deity Prophecy: {prophecy}"
                    print(f"\n✨ [DIVINE PROPHECY] Gemini Deity Decrees: \"{prophecy}\"")
                
                if hasattr(entity, "think"):
                    entity.think(
                        f"The Gemini Deity has answered our prayers: \"{prophecy or reasoning}\"",
                        category="DEVOTION",
                        valence=0.9,
                        intensity=0.95,
                        tick=entity.age_ticks,
                        tags=["deity", "prophecy", "revelation"],
                    )
                break

        self._pending_entity_ids.discard(entity_id)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        self.client.shutdown()
