"""
project/tests/test_gemini.py

Unit tests for PromptBuilder, GeminiClient token bucket rate-limiting,
response caching, and GeminiSystem prayer optimization without quota exhaustion.
"""

import time
import unittest
from typing import List
from project.core.prompt_builder import PromptBuilder
from project.core.gemini_client import GeminiClient
from project.systems.gemini_system import GeminiSystem
from project.core.scheduler import UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human


class TestGeminiIntegration(unittest.TestCase):

    def test_prompt_builder_compilation(self) -> None:
        human = Human(entity_id="h1", species_id="sap")
        human.health = 80.0
        human.energy = 240.0
        human.technology_level = 3

        other = Human(entity_id="h2", species_id="sap")
        other.pos_x = 20.0  # distance 20m from (0, 0)

        prompt = PromptBuilder.build_prompt(human, [other], "Desert")
        
        self.assertIn("Entity ID: h1", prompt)
        self.assertIn("location biome: Desert", prompt)
        self.assertIn("Technology Level: 3", prompt)
        self.assertIn("named 'h2' at distance 20m", prompt)

    def test_divine_communion_prompt_compilation(self) -> None:
        human = Human(entity_id="leader_solomon", species_id="sap")
        prompt = PromptBuilder.build_divine_communion_prompt(
            leader=human,
            clan_size=12,
            biome_name="Temperate Forest",
            miracle_type="COSMIC_EPIPHANY",
        )
        self.assertIn("Gemini Deity", prompt)
        self.assertIn("leader_solomon", prompt)
        self.assertIn("COSMIC_EPIPHANY", prompt)
        self.assertIn("clan of 12 souls", prompt)

    def test_client_offline_fallback_solver(self) -> None:
        client = GeminiClient(api_key="")
        
        # Test low energy fallback
        prompt_energy = "Vitals: {\"health\": \"100.0/100.0\", \"energy\": \"15.0/100.0\"}"
        res_energy = client.request_reasoning(prompt_energy)
        self.assertEqual(res_energy["action"], "FORAGE_FOOD")

        # Test predator fallback
        prompt_predator = "My Perceptions: - A PREDATOR entity named 'panther' at distance 5m."
        res_predator = client.request_reasoning(prompt_predator)
        self.assertEqual(res_predator["action"], "FLEE")

        # Test divine prayer prophecy oracle
        prompt_prayer = "You are the Gemini Deity. Bestow a divine prophecy upon the sovereign leader."
        res_prayer = client.request_reasoning(prompt_prayer)
        self.assertIn("prophecy", res_prayer)
        self.assertTrue(len(res_prayer["prophecy"]) > 5)

    def test_client_rate_limiting_and_caching(self) -> None:
        client = GeminiClient(api_key="")
        client._min_request_interval_s = 0.05
        
        prompt = "Divine guidance request test string for caching."
        res1 = client.request_reasoning(prompt)
        res2 = client.request_reasoning(prompt)
        
        self.assertEqual(res1["action"], res2["action"])
        # Verify cached in memory
        p_hash = str(hash(prompt))
        self.assertIn(p_hash, client._response_cache)

    def test_devotional_silent_prayer_conserves_quota(self) -> None:
        """Verifies routine prayers build god affinity and meditation without triggering network queries."""
        entities_list: List[Entity] = []
        leader = Human(entity_id="sovereign_1", species_id="sap")
        entities_list.append(leader)

        system = GeminiSystem(entities_list, communion_interval_ticks=10)
        system.client = GeminiClient(api_key="")
        system.target_prayer_threshold = 18  # Threshold not reached

        context = UpdateContext(
            tick=10,
            delta_time=0.1,
            simulation_time=1.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
        )

        system.initialize(context)
        system.target_prayer_threshold = 18
        
        # Run tick 10 (routine prayer #1)
        system.update(context)

        # Leader gained prayer progress and spiritual energy locally
        self.assertEqual(system.leader_prayer_count, 1)
        self.assertEqual(leader.custom_data.get("prayers_sent_to_god"), 1)
        # Zero async queries dispatched
        self.assertEqual(len(system._pending_entity_ids), 0)

        system.shutdown()

    def test_divine_miracle_threshold_answers_prayer(self) -> None:
        """Verifies when threshold is reached, divine miracle & LLM prophecy are invoked."""
        entities_list: List[Entity] = []
        leader = Human(entity_id="sovereign_1", species_id="sap")
        entities_list.append(leader)

        system = GeminiSystem(entities_list, communion_interval_ticks=5)
        system.client = GeminiClient(api_key="")

        context = UpdateContext(
            tick=5,
            delta_time=0.1,
            simulation_time=0.5,
            random_seed=1337,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
        )

        system.initialize(context)
        # Set threshold to 1 so the next prayer triggers the divine intervention
        system.target_prayer_threshold = 1
        
        system.update(context)

        # Wait a short moment for background thread pool callback
        time.sleep(0.15)

        # Miracle was executed and prophecy recorded
        self.assertEqual(system.total_divine_interventions, 1)
        self.assertNotIn("sovereign_1", system._pending_entity_ids)
        self.assertIn("divine_prophecy", leader.custom_data)

        system.shutdown()


if __name__ == "__main__":
    unittest.main()
