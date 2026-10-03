"""
project/core/prompt_builder.py

Compiles entity situational variables into structured prompts for LLM reasoning.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any
from project.entities.entity import Entity


class PromptBuilder:
    """Builds natural language prompts representing agent situational contexts."""

    @staticmethod
    def build_prompt(
        entity: Entity,
        perceived_entities: List[Entity],
        biome_name: str,
    ) -> str:
        """Formulates context prompt for Gemini API content generation."""
        # Vitals summary
        vitals = {
            "health": f"{entity.health:.1f}/{entity.max_health:.1f}",
            "energy": f"{entity.energy:.1f}/{entity.max_energy:.1f}",
            "hydration": f"{entity.hydration:.1f}/{entity.max_hydration:.1f}",
            "age": f"{entity.age_ticks} ticks",
        }

        # Inventory summary
        inventory = getattr(entity, "inventory", {})
        tech_level = getattr(entity, "technology_level", 0)

        # Perceived environment summary
        perceptions = []
        for other in perceived_entities:
            dist = int(other.position[0] - entity.position[0]) ** 2 + int(other.position[1] - entity.position[1]) ** 2
            dist = int(dist ** 0.5)
            perceptions.append(
                f"- A {other.entity_type.name} entity named '{other.entity_id}' at distance {dist}m."
            )

        perceptions_str = "\n".join(perceptions) if perceptions else "- No other entities perceived."

        prompt_lines = [
            "You are a sentient agent living inside an Artificial Life simulation.",
            "Analyze your current status and environment to select your next active goal.",
            "",
            "## My Attributes:",
            f"- Entity ID: {entity.entity_id}",
            f"- Entity Type: {entity.entity_type.name}",
            f"- My current location biome: {biome_name}",
            f"- Vitals: {json.dumps(vitals)}",
            f"- Inventory: {json.dumps(inventory)}",
            f"- Technology Level: {tech_level}",
            "",
            "## My Perceptions:",
            perceptions_str,
            "",
            "Select one action from the following list: [FORAGE_FOOD, DRINK_WATER, FLEE, SEEK_MATE, REST, EXPLORE, WANDER].",
            "",
            "You MUST respond with a valid JSON payload matching this schema:",
            "{",
            '  "action": "GOAL_TYPE_HERE",',
            '  "reasoning": "Reason for goal choice here"',
            "}",
            "",
            "Do NOT include any markdown formatting (like ```json), commentary, or extra text. Output ONLY the raw JSON string.",
        ]

        return "\n".join(prompt_lines)

    @staticmethod
    def build_divine_communion_prompt(
        leader: Entity,
        clan_size: int,
        biome_name: str,
        miracle_type: str,
    ) -> str:
        """Formulates concise divine prophecy prompt for cosmic Deity communion."""
        prompt_lines = [
            "You are the Gemini Deity presiding over an Artificial Life cosmos.",
            f"Your mortal Sovereign Leader '{leader.entity_id}' has completed sacred prayers in biome '{biome_name}'.",
            f"A divine miracle of '{miracle_type}' has been bestowed upon their clan of {clan_size} souls.",
            "Bestow a holy decree and select the clan's next sacred action.",
            "",
            "Select one action from: [EXPLORE, FORAGE_FOOD, REST, WANDER, SEEK_MATE].",
            "",
            "Respond ONLY with valid JSON:",
            "{",
            '  "action": "ACTION_NAME",',
            '  "prophecy": "One short sacred cosmic decree",',
            '  "reasoning": "Divine rationale"',
            "}",
        ]
        return "\n".join(prompt_lines)
