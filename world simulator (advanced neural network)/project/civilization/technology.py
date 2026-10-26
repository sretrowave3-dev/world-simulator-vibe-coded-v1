"""
project/civilization/technology.py

Minecraft-Inspired Emergent Crafting, Lithic Technology Tree, and Architecture Engine.
Humans discover tools, block transformations, and architectural tiers emergently based on
materials in their possession, individual IQ/creativity, and survival imperatives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class TechTier(Enum):
    PRIMAL = 0       # Paleolithic foraging
    LITHIC = 1       # Emergency dirt dugouts, stone tools, spears, fire
    WOOD_AGE = 2     # Processed wood planks, crafting tables, wooden cabins, torches
    STONE_AGE = 3    # Cobblestone masonry houses, furnaces, stone pickaxes, fortified halls
    MONUMENTAL = 4   # Sacred monolithic shrines, watchtowers, grand civilization


@dataclass
class CraftRecipe:
    """Recipe discovered emergently through cognitive experimentation and survival need."""
    name: str
    tier: TechTier
    required_materials: Dict[str, float]  # e.g. {"wood": 2.0, "stone": 1.0}
    output_item: str
    output_weight_kg: float
    output_type: str                      # "material", "tool", "weapon", "structure", "vessel"
    iq_threshold: float
    creativity_threshold: float
    description: str
    bonus_effects: Dict[str, float] = field(default_factory=dict)


# Emerging catalog of discoverable crafts across tiers (incorporating Minecraft survival progression)
CRAFT_CATALOG: Dict[str, CraftRecipe] = {
    # ── Tier 1: Emergency Survival & Lithic Tools ──
    "stone_handaxe": CraftRecipe(
        name="Stone Handaxe",
        tier=TechTier.LITHIC,
        required_materials={"wood": 1.5, "stone": 2.0},
        output_item="stone_axe",
        output_weight_kg=2.5,
        output_type="tool",
        iq_threshold=100.0,
        creativity_threshold=0.35,
        description="A knapped flint or stone lashed to a wooden handle. Greatly boosts wood harvest yield from trees.",
        bonus_effects={"woodcutting_multiplier": 2.2, "combat_bonus": 4.0},
    ),
    "wood_spear": CraftRecipe(
        name="Hardened Spear",
        tier=TechTier.LITHIC,
        required_materials={"wood": 2.5, "stone": 1.0},
        output_item="wood_spear",
        output_weight_kg=2.0,
        output_type="weapon",
        iq_threshold=105.0,
        creativity_threshold=0.40,
        description="A fire-hardened wooden shaft tipped with sharp stone. Provides lethal defensive and hunting reach against predators.",
        bonus_effects={"combat_bonus": 16.0, "reach": 1.8},
    ),
    "campfire": CraftRecipe(
        name="Campfire Hearth",
        tier=TechTier.LITHIC,
        required_materials={"wood": 3.0, "stone": 2.0},
        output_item="campfire",
        output_weight_kg=5.0,
        output_type="structure",
        iq_threshold=108.0,
        creativity_threshold=0.42,
        description="Controlled fire enclosed in a stone ring. Dispels darkness (light level 12), repels predators, and warms resting humans.",
        bonus_effects={"warmth_radius": 15.0, "predator_repel": 25.0, "light_level": 12.0},
    ),
    "dirt_dugout": CraftRecipe(
        name="Emergency Dugout",
        tier=TechTier.LITHIC,
        required_materials={"stone": 2.0, "wood": 1.5},
        output_item="dirt_dugout",
        output_weight_kg=4.0,
        output_type="structure",
        iq_threshold=102.0,
        creativity_threshold=0.30,
        description="A hasty dirt and branch lean-to dugout (Minecraft Day 1 survival shelter). Shields 2-3 humans from the nocturnal cold.",
        bonus_effects={"shelter_capacity": 3.0, "defense_rating": 15.0, "tier": 1.0},
    ),
    "stone_pickaxe": CraftRecipe(
        name="Stone Pickaxe",
        tier=TechTier.LITHIC,
        required_materials={"wood": 2.0, "stone": 3.0},
        output_item="stone_pickaxe",
        output_weight_kg=3.5,
        output_type="tool",
        iq_threshold=110.0,
        creativity_threshold=0.40,
        description="A heavy pick forged from dense mountain granite. Enables quarrying stone boulders and mining mineral veins.",
        bonus_effects={"mining_multiplier": 2.5, "stone_harvest": 2.0},
    ),

    # ── Tier 2: Minecraft Wood Age (Planks, Cabins, Torches) ──
    "wood_planks": CraftRecipe(
        name="Refined Wood Planks",
        tier=TechTier.WOOD_AGE,
        required_materials={"wood": 2.0},
        output_item="wood_planks",
        output_weight_kg=3.0,
        output_type="material",
        iq_threshold=112.0,
        creativity_threshold=0.45,
        description="Square sawn timber planks (Minecraft 1 log -> 4 planks). The foundational building block for sturdy wooden houses.",
        bonus_effects={"building_efficiency": 2.0},
    ),
    "torch": CraftRecipe(
        name="Resin Torch",
        tier=TechTier.WOOD_AGE,
        required_materials={"wood": 1.0, "stone": 0.5},
        output_item="torch",
        output_weight_kg=0.8,
        output_type="tool",
        iq_threshold=110.0,
        creativity_threshold=0.40,
        description="A long-burning wooden torch (Minecraft light level 14). Illumines dark nights and deters dangerous beast spawns.",
        bonus_effects={"light_level": 14.0, "mob_deterrent": 30.0},
    ),
    "wooden_cabin": CraftRecipe(
        name="Wooden Plank Cabin",
        tier=TechTier.WOOD_AGE,
        required_materials={"wood": 5.0, "stone": 2.0},
        output_item="wooden_cabin",
        output_weight_kg=12.0,
        output_type="structure",
        iq_threshold=116.0,
        creativity_threshold=0.50,
        description="A complete wooden house with timber frame, solid wooden door, and roof (Minecraft Tier 2). Totally blocks nocturnal predators.",
        bonus_effects={"shelter_capacity": 6.0, "defense_rating": 45.0, "tier": 2.0, "comfort_rating": 0.8},
    ),
    "clay_pottery": CraftRecipe(
        name="Water Pottery",
        tier=TechTier.WOOD_AGE,
        required_materials={"stone": 1.0, "wood": 1.0},
        output_item="clay_pottery",
        output_weight_kg=1.5,
        output_type="vessel",
        iq_threshold=114.0,
        creativity_threshold=0.52,
        description="Baked clay and stone jug for transporting water from distant rivers, sustaining long-range explorations.",
        bonus_effects={"water_capacity": 150.0},
    ),

    # ── Tier 3: Minecraft Stone Masonry (Cobblestone Houses, Furnaces) ──
    "furnace": CraftRecipe(
        name="Stone Furnace",
        tier=TechTier.STONE_AGE,
        required_materials={"stone": 5.0},
        output_item="furnace",
        output_weight_kg=8.0,
        output_type="structure",
        iq_threshold=120.0,
        creativity_threshold=0.55,
        description="A stone hearth and flue for smelting ores and firing durable bricks (Minecraft 8 cobblestone = furnace).",
        bonus_effects={"smelting_power": 1.5},
    ),
    "cobblestone_house": CraftRecipe(
        name="Cobblestone Fortress House",
        tier=TechTier.STONE_AGE,
        required_materials={"stone": 8.0, "wood": 4.0},
        output_item="cobblestone_house",
        output_weight_kg=22.0,
        output_type="structure",
        iq_threshold=122.0,
        creativity_threshold=0.60,
        description="A formidable fortified stone masonry house with chimney and furnace (Minecraft Tier 3). 100% predator-proof fortress walls.",
        bonus_effects={"shelter_capacity": 12.0, "defense_rating": 120.0, "tier": 3.0, "comfort_rating": 1.0},
    ),
    "fortified_hall": CraftRecipe(
        name="Great Stone Clan Hall",
        tier=TechTier.STONE_AGE,
        required_materials={"stone": 16.0, "wood": 8.0},
        output_item="fortified_hall",
        output_weight_kg=45.0,
        output_type="structure",
        iq_threshold=126.0,
        creativity_threshold=0.68,
        description="A monumental castle keep with stone battlements, torch arrays, and master hearth. Shelters the entire tribe.",
        bonus_effects={"shelter_capacity": 25.0, "defense_rating": 300.0, "tier": 4.0, "comfort_rating": 1.2},
    ),

    # ── Tier 4: Monumental & Sacred Architecture ──
    "sacred_altar": CraftRecipe(
        name="Stone Altar of the Monolith",
        tier=TechTier.MONUMENTAL,
        required_materials={"wood": 4.0, "stone": 8.0},
        output_item="sacred_altar",
        output_weight_kg=15.0,
        output_type="structure",
        iq_threshold=125.0,
        creativity_threshold=0.70,
        description="A consecrated stone monument erected to venerate the Gemini Deity and channel divine miracles.",
        bonus_effects={"divine_affinity_boost": 0.05, "piety_radius": 30.0, "light_level": 15.0},
    ),
}


class TechnologyTree:
    """Manages discoverable technologies, civilization knowledge pools, and emergent crafting."""

    def __init__(self) -> None:
        self.recipes = CRAFT_CATALOG
        self.discovered_recipes: Set[str] = set()

    def check_emergent_discovery(
        self,
        inventory: Dict[str, float],
        iq: float,
        creativity: float,
        known_techs: List[str],
        desired_tier: int = 1,
    ) -> Optional[CraftRecipe]:
        """
        Evaluates whether a human's current materials, intelligence, and shelter urgency spark a discovery.
        Prioritizes desired shelter tier when safety/shelter is urgent!
        """
        candidate_recipes = []

        for recipe_id, recipe in self.recipes.items():
            if recipe_id in known_techs or recipe.name in known_techs:
                continue

            # Check IQ and creativity requirements
            if iq < recipe.iq_threshold or creativity < recipe.creativity_threshold:
                continue

            # Check if inventory has required raw materials
            has_mats = True
            for mat, req_amount in recipe.required_materials.items():
                if inventory.get(mat, 0.0) < req_amount:
                    has_mats = False
                    break

            if has_mats:
                # Calculate priority score: boost structures if desired tier matches
                rec_tier_val = recipe.tier.value
                prio = 1.0
                if recipe.output_type == "structure":
                    prio += 2.0
                    if rec_tier_val >= desired_tier:
                        prio += 3.0
                candidate_recipes.append((prio, recipe))

        if candidate_recipes:
            candidate_recipes.sort(key=lambda x: -x[0])
            return candidate_recipes[0][1]

        return None



    def get_best_craftable_recipe(
        self,
        inventory: Dict[str, float],
        iq: float,
        creativity: float,
        known_techs: List[str],
        desired_tier: int = 1,
        need_shelter: bool = False,
        equipped_tool: Optional[str] = None,
    ) -> Optional[CraftRecipe]:
        """
        Returns the best craftable recipe for an entity holding raw materials.
        Supports both novel emergent discoveries AND repeated construction/crafting
        of known recipes (e.g. building multiple cabins/fortresses, replacement tools, torches, wood planks).
        """
        # If shelter is urgent, prioritize any craftable shelter structure (new or known) matching desired tier
        if need_shelter:
            shelter_candidates = []
            for recipe_id, recipe in self.recipes.items():
                if recipe.bonus_effects.get("shelter_capacity", 0) <= 0:
                    continue
                # Check materials
                has_mats = all(inventory.get(mat, 0.0) >= req for mat, req in recipe.required_materials.items())
                if not has_mats:
                    continue
                # If undiscovered, must also meet IQ/creativity
                is_known = (recipe_id in known_techs or recipe.name in known_techs or recipe.name in self.discovered_recipes)
                if not is_known:
                    if iq < recipe.iq_threshold or creativity < recipe.creativity_threshold:
                        continue
                # Score based on how closely it matches desired_tier
                tier_diff = abs(recipe.tier.value - desired_tier)
                prio = 100.0 - (tier_diff * 10.0) + recipe.tier.value
                shelter_candidates.append((prio, recipe))

            if shelter_candidates:
                shelter_candidates.sort(key=lambda x: -x[0])
                return shelter_candidates[0][1]

        # 1. Standard priority: Emergent discovery of brand-new innovations
        discovery = self.check_emergent_discovery(inventory, iq, creativity, known_techs, desired_tier)
        if discovery:
            return discovery

        # 2. Crafting known or globally discovered technologies
        candidate_recipes = []
        for recipe_id, recipe in self.recipes.items():
            is_known = (recipe_id in known_techs or recipe.name in known_techs or recipe.name in self.discovered_recipes)
            if not is_known:
                continue

            has_mats = all(inventory.get(mat, 0.0) >= req for mat, req in recipe.required_materials.items())
            if not has_mats:
                continue

            prio = 1.0
            if recipe.output_type == "structure":
                prio += 0.5
            elif recipe.output_type in ("tool", "weapon"):
                if equipped_tool is None:
                    prio += 8.0
                elif recipe.output_item == "stone_axe" and inventory.get("wood", 0.0) < 6.0:
                    prio += 5.0
                elif recipe.output_item == "stone_pickaxe" and inventory.get("stone", 0.0) < 6.0:
                    prio += 5.0
            elif recipe.output_type == "material" and recipe_id == "wood_planks":
                if inventory.get("wood", 0.0) >= 6.0:
                    prio += 4.0
            elif recipe_id == "torch":
                prio += 3.0

            candidate_recipes.append((prio, recipe))

        if candidate_recipes:
            candidate_recipes.sort(key=lambda x: -x[0])
            return candidate_recipes[0][1]

        return None


# Global singleton technology tree
world_tech_tree = TechnologyTree()
