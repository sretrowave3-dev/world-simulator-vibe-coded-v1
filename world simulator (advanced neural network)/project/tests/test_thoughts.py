"""
project/tests/test_thoughts.py

Unit tests for Human Thought Logging, Adjacent JSON Persistence,
and In-Memory Cache Retrieval Engine.
"""

import os
import json
import unittest
from project.core.thought_logger import (
    HumanThought,
    HumanThoughtCache,
    ThoughtLogger,
    TXT_LOG_PATH,
    JSON_LOG_PATH,
)
from project.entities.human import Human


class TestHumanThoughtSystem(unittest.TestCase):

    def setUp(self) -> None:
        self.human = Human(entity_id="human_test_01", species_id="homo_sap")

    def test_thought_creation_and_serialization(self) -> None:
        """Verifies HumanThought serialization and formatting."""
        thought = HumanThought(
            thought_id="th_001",
            human_id="human_test_01",
            tick=100,
            timestamp=1700000000.0,
            category="SURVIVAL",
            content="We should collect flint before nightfall.",
            valence=0.2,
            intensity=0.7,
            context_tags=["flint", "night", "tools"],
        )

        d = thought.to_dict()
        self.assertEqual(d["thought_id"], "th_001")
        self.assertEqual(d["category"], "SURVIVAL")
        self.assertIn("flint", d["context_tags"])

        restored = HumanThought.from_dict(d)
        self.assertEqual(restored.content, thought.content)
        self.assertEqual(restored.valence, 0.2)

        log_line = thought.format_log_line()
        self.assertIn("[SURVIVAL]", log_line)
        self.assertIn("We should collect flint", log_line)

    def test_dual_file_persistence(self) -> None:
        """Verifies adjacent .log and .json files are created and populated."""
        custom_logger = ThoughtLogger()
        test_thought = HumanThought(
            thought_id="th_persist_test",
            human_id="test_elder",
            tick=42,
            timestamp=1700000000.0,
            category="PHILOSOPHY",
            content="The river flows constantly, yet remains the same river.",
            valence=0.6,
            intensity=0.8,
            context_tags=["river", "wisdom"],
        )

        custom_logger.record_thought(test_thought)

        # Check adjacent .log file
        self.assertTrue(os.path.exists(TXT_LOG_PATH))
        with open(TXT_LOG_PATH, "r", encoding="utf-8") as f:
            txt_content = f.read()
            self.assertIn("The river flows constantly", txt_content)

        # Check adjacent .json file
        self.assertTrue(os.path.exists(JSON_LOG_PATH))
        with open(JSON_LOG_PATH, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            self.assertIsInstance(json_data, list)
            match = any(t.get("thought_id") == "th_persist_test" for t in json_data)
            self.assertTrue(match)

    def test_in_memory_cache_and_retrieval(self) -> None:
        """Verifies fast cognitive retrieval by keyword, emotion, and category."""
        cache = HumanThoughtCache(human_id="philosopher_1", max_capacity=50)

        # Add variety of thoughts
        cache.add_thought("Finding water by the eastern ridge.", category="SURVIVAL", valence=0.5, tags=["water", "ridge"])
        cache.add_thought("A shadow of a predator passed through the tall grass.", category="SURVIVAL", valence=-0.8, tags=["predator", "danger"])
        cache.add_thought("The heavens answered with glowing stars.", category="DEVOTION", valence=0.9, tags=["deity", "stars"])
        cache.add_thought("Can we bind stones with woven fibers?", category="INVENTION", valence=0.4, tags=["craft", "tools"])

        # 1. Retrieve recent
        recent = cache.retrieve_recent(limit=2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[-1].category, "INVENTION")

        # 2. Keyword search
        water_thoughts = cache.recall_by_keyword("water")
        self.assertEqual(len(water_thoughts), 1)
        self.assertIn("eastern ridge", water_thoughts[0].content)

        # 3. Category search
        devotion_thoughts = cache.recall_by_category("DEVOTION")
        self.assertEqual(len(devotion_thoughts), 1)
        self.assertIn("heavens answered", devotion_thoughts[0].content)

        # 4. Emotional valence search (Traumatic / Negative)
        fear_thoughts = cache.recall_by_emotion(min_valence=-1.0, max_valence=-0.2)
        self.assertEqual(len(fear_thoughts), 1)
        self.assertIn("predator", fear_thoughts[0].content)

        # 5. Emotional valence search (Joy / High)
        joy_thoughts = cache.recall_by_emotion(min_valence=0.7, max_valence=1.0)
        self.assertEqual(len(joy_thoughts), 1)
        self.assertEqual(joy_thoughts[0].category, "DEVOTION")

    def test_human_entity_thinking_integration(self) -> None:
        """Verifies Human entity direct thinking and recall methods."""
        h = self.human
        t = h.think("Our clan must shelter under the cavern rock.", category="SURVIVAL", valence=0.1, tick=120, tags=["cave", "shelter"])
        self.assertIsNotNone(t)
        self.assertEqual(h.thought_cache.total_cached, 1)

        recalled = h.recall_thoughts(query="cave")
        self.assertEqual(len(recalled), 1)
        self.assertIn("cavern rock", recalled[0].content)


if __name__ == "__main__":
    unittest.main()
