"""
project/entities/human.py

Sentient Human Entity Model for the ALife Platform.

Features:
- High-Capacity Cognitive Memory: Preallocated >= 50 MB Experience Replay Matrix & Spatial Mapping.
- Non-Hardcoded Emergent Tool Usage, Crafting, Inventory Management, and Shelter Construction.
- Social Hierarchy, Tribal Organization, Cultural Knowledge Transmission, and Divine Ascension.
- Robust Omnivorous Metabolism with high caloric reserves and sustainable foraging efficiency.
- Tree and Forest Harvesting: Gathers wood/fruit from mature trees and stones from mountain quarries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from project.entities.entity import Entity, EntityType
from project.ai.memory import HumanCognitiveMemory


@dataclass(eq=False)
class Human(Entity):
    """Sentient, tool-using organism capable of social cooperation, deep memory retention, and civilization building."""

    tribe_id: Optional[str] = None
    civilization_id: Optional[str] = None
    social_rank: int = 0
    reputation: float = 0.5

    intelligence_quotient: float = 120.0
    creativity: float = 0.65
    social_affinity: float = 0.85
    technology_level: int = 0
    known_technologies: List[str] = field(default_factory=list)

    inventory: Dict[str, float] = field(default_factory=dict)
    max_inventory_capacity_kg: float = 60.0
    equipped_tool: Optional[str] = None  # "stone_axe", "wood_spear", "stone_pickaxe", etc.
    shelter_importance_score: float = 0.3
    desired_shelter_tier: int = 1
    in_shelter_id: Optional[str] = None
    night_exposure_ticks: int = 0
    predator_attacks_survived: int = 0
    thought_cache: Optional[Any] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.entity_type = EntityType.HUMAN
        self.radius = 1.2
        self.mass_kg = 70.0
        self.max_health = 120.0
        self.health = 120.0
        self.max_energy = 500.0
        self.energy = 450.0  # Well-fed base genesis state
        self.max_hydration = 300.0
        self.hydration = 280.0
        self.max_age_ticks = 40000
        self.maturity_age_ticks = 150
        self.base_speed = 3.8
        self.max_speed_cap = 9.8
        self.strength = 20.0
        self.max_strength_cap = 70.0
        self.metabolic_rate = 0.035  # High omnivorous metabolic efficiency
        self.is_endotherm = True
        self.body_temperature_c = 37.0

        # Instantiate 50+ MB High-Capacity Cognitive Memory
        if self.memory is None or not isinstance(self.memory, HumanCognitiveMemory):
            self.memory = HumanCognitiveMemory()

        # Instantiate Human Stream-of-Consciousness Thought Cache
        if self.thought_cache is None:
            from project.core.thought_logger import HumanThoughtCache
            self.thought_cache = HumanThoughtCache(human_id=self.entity_id)

        self._apply_individual_variance()

    def think(
        self,
        content: str,
        category: str = "SURVIVAL",
        valence: float = 0.0,
        intensity: float = 0.5,
        tick: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Any:
        """Records an internal subjective thought into the in-memory cache and persistent diary."""
        if self.thought_cache is None:
            from project.core.thought_logger import HumanThoughtCache
            self.thought_cache = HumanThoughtCache(human_id=self.entity_id)
        return self.thought_cache.add_thought(
            content=content,
            category=category,
            valence=valence,
            intensity=intensity,
            tick=tick,
            tags=tags or [],
        )

    def recall_thoughts(self, query: str = "", category: Optional[str] = None, limit: int = 5) -> List[Any]:
        """Recalls subjective thoughts from the thought cache matching keywords or category."""
        if self.thought_cache is None:
            return []
        if category:
            return self.thought_cache.recall_by_category(category, limit=limit)
        if query:
            return self.thought_cache.recall_by_keyword(query, limit=limit)
        with self.thought_cache._lock:
            return list(self.thought_cache._thoughts[-limit:])

    def _apply_individual_variance(self) -> None:
        import random
        self.intelligence_quotient += random.gauss(0.0, 10.0)
        self.creativity = max(0.1, min(1.0, self.creativity + random.uniform(-0.15, 0.15)))
        self.social_affinity = max(0.2, min(1.0, self.social_affinity + random.uniform(-0.1, 0.1)))

    @property
    def inventory_weight(self) -> float:
        return sum(self.inventory.values())

    def add_to_inventory(self, item_name: str, weight_kg: float) -> bool:
        if self.inventory_weight + weight_kg > self.max_inventory_capacity_kg:
            return False
        self.inventory[item_name] = self.inventory.get(item_name, 0.0) + weight_kg
        return True

    def remove_from_inventory(self, item_name: str, weight_kg: float) -> float:
        available = self.inventory.get(item_name, 0.0)
        if available <= 0.0:
            return 0.0
        removed = min(available, weight_kg)
        self.inventory[item_name] -= removed
        if self.inventory[item_name] <= 0.001:
            del self.inventory[item_name]
        return removed

    def harvest_from_tree(self, plant_entity: Any) -> float:
        """
        Emergent wood and fruit gathering from trees and flora.
        Equipped stone axe doubles woodcutting efficiency.
        """
        tool_mult = 2.2 if self.equipped_tool == "stone_axe" else 1.0
        wood_harvested = plant_entity.harvest_wood(requested_kg=2.5, tool_multiplier=tool_mult)
        if wood_harvested > 0:
            self.add_to_inventory("wood", wood_harvested)
            self.energy = max(10.0, self.energy - 3.0)

        fruit_harvested = plant_entity.harvest_fruit(requested_kg=1.5)
        if fruit_harvested > 0:
            self.add_to_inventory("food", fruit_harvested)
            self.gain_energy(fruit_harvested * 20.0)  # Immediate snack

        return wood_harvested + fruit_harvested

    def gather_stone(self, amount_kg: float = 2.0) -> float:
        """Gathers stone from boulders, quarries, or mountain foothills."""
        tool_mult = 2.5 if self.equipped_tool == "stone_pickaxe" else 1.0
        effective = amount_kg * (1.2 if tool_mult > 1.0 else 1.0)
        if self.add_to_inventory("stone", effective):
            self.energy = max(10.0, self.energy - 4.0)
            return effective
        return 0.0

    def drink_water(self, hydration_amount: float = 80.0) -> None:
        """Quenches thirst at rivers and fresh water bodies."""
        pottery_bonus = 40.0 if self.inventory.get("clay_pottery", 0.0) > 0 else 0.0
        self.hydration = min(self.max_hydration, self.hydration + hydration_amount + pottery_bonus)
        self.custom_data["stress"] = max(0.0, self.custom_data.get("stress", 0.0) - 0.1)

    def evaluate_shelter_need(self, daylight: float, threats_nearby: int, sim_tick: int) -> None:
        """
        Minecraft Survival Instinct:
        Humans experience vulnerability from cold nights, thunderstorms, and nocturnal predator ambushes.
        As threats or night exposure increase, they realize shelter is vital and desire higher architectural tiers.
        """
        if self.in_shelter_id is not None:
            self.night_exposure_ticks = 0
            self.custom_data["stress"] = max(0.0, self.custom_data.get("stress", 0.0) - 0.05)
            self.custom_data["fear"] = 0.0
            return

        is_night = daylight < 0.38
        if is_night:
            self.night_exposure_ticks += 1
            if self.night_exposure_ticks % 40 == 0:
                self.shelter_importance_score = min(1.0, self.shelter_importance_score + 0.12)
                self.custom_data["stress"] = min(1.0, self.custom_data.get("stress", 0.0) + 0.05)
                if self.shelter_importance_score > 0.55 and sim_tick % 100 == 0:
                    self.think(
                        "The nocturnal darkness is freezing and dangerous. We must erect a sturdy shelter with walls!",
                        category="SURVIVAL",
                        valence=-0.4,
                        intensity=0.8,
                        tick=sim_tick,
                    )

        if threats_nearby > 0:
            self.shelter_importance_score = min(1.0, self.shelter_importance_score + 0.20)
            if self.predator_attacks_survived > 0 and self.desired_shelter_tier < 3:
                self.desired_shelter_tier = 3
                if sim_tick % 80 == 0:
                    self.think(
                        "Predators can claw through simple branches! We must quarry cobblestone and construct an impenetrable fortress!",
                        category="SURVIVAL",
                        valence=-0.2,
                        intensity=0.9,
                        tick=sim_tick,
                    )
            elif self.desired_shelter_tier < 2:
                self.desired_shelter_tier = 2

    def enter_shelter(self, structure: Any) -> bool:
        """Enters a built shelter structure, closing the door against predators and elements."""
        if structure.add_occupant(self.entity_id):
            self.in_shelter_id = structure.structure_id
            self.custom_data["is_sheltered"] = True
            self.custom_data["stress"] = 0.0
            self.custom_data["fear"] = 0.0
            self.custom_data["dopamine"] = 1.0
            return True
        return False

    def exit_shelter(self, structure: Optional[Any] = None) -> None:
        """Exits the shelter into the outside world."""
        if structure and self.in_shelter_id == structure.structure_id:
            structure.remove_occupant(self.entity_id)
        self.in_shelter_id = None
        self.custom_data["is_sheltered"] = False

    def attempt_emergent_crafting(self, sim_tick: int = 0, force_shelter: bool = False) -> Optional[str]:
        """
        Non-hardcoded emergent crafting and construction:
        Checks held raw materials against the technology tree.
        Discovers new innovations AND repeatedly builds structures or crafts tools when needed.
        """
        from project.civilization.technology import world_tech_tree
        need_shelter = force_shelter or (self.in_shelter_id is None and (self.shelter_importance_score > 0.45 or self.night_exposure_ticks > 0))
        recipe = world_tech_tree.get_best_craftable_recipe(
            inventory=self.inventory,
            iq=self.intelligence_quotient,
            creativity=self.creativity,
            known_techs=self.known_technologies,
            desired_tier=self.desired_shelter_tier,
            need_shelter=need_shelter,
            equipped_tool=self.equipped_tool,
        )

        if recipe:
            # Consume required materials
            for mat, amount in recipe.required_materials.items():
                self.remove_from_inventory(mat, amount)

            # Discover technology if new
            is_new_discovery = recipe.name not in self.known_technologies
            if is_new_discovery:
                self.known_technologies.append(recipe.name)
            if recipe.name not in world_tech_tree.discovered_recipes:
                world_tech_tree.discovered_recipes.add(recipe.name)

            # Equip, inventory, or spawn structure
            if recipe.output_type in ("tool", "weapon"):
                self.equipped_tool = recipe.output_item
                self.add_to_inventory(recipe.output_item, recipe.output_weight_kg)
                if "combat_bonus" in recipe.bonus_effects:
                    self.strength = min(self.max_strength_cap, self.strength + recipe.bonus_effects["combat_bonus"])
            elif recipe.output_type == "material":
                self.add_to_inventory(recipe.output_item, recipe.output_weight_kg)
            elif recipe.output_type == "structure":
                from project.civilization.settlement import world_settlement_mgr
                clan_id = self.tribe_id or "genesis_tribe"
                st = world_settlement_mgr.spawn_structure(
                    structure_type=recipe.output_item,
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    clan_id=clan_id,
                    tick=sim_tick,
                )
                if st.capacity > 0:
                    self.enter_shelter(st)

            # Boost morale and record thought
            self.custom_data["dopamine"] = 1.0
            self.custom_data["stress"] = 0.0
            thought_prefix = "Eureka! Discovered" if is_new_discovery else "Constructed"
            try:
                from project.core.activity_chronicler import activity_chronicler
                clan_name = (self.tribe_id or "Genesis Tribe").replace("_", " ").title()
                if is_new_discovery:
                    activity_chronicler.record_tech_discovery(recipe.name, recipe.tier.name, clan_name)
                if recipe.output_type == "structure":
                    activity_chronicler.record_construction(recipe.output_item, (self.pos_x, self.pos_y), self.tribe_id or "genesis_tribe")
                else:
                    activity_chronicler.record_craft(recipe.name, recipe.output_type, clan_name)
            except Exception:
                pass
            self.think(
                f"{thought_prefix} a {recipe.name}! {recipe.description}",
                category="CREATION",
                valence=1.0,
                intensity=0.9,
                tick=sim_tick,
            )
            return recipe.name

        return None

    def can_mate(self) -> bool:
        return (
            self.is_alive
            and self.is_mature
            and self.energy >= 150.0
            and self.hydration >= 60.0
            and self.reproduction_cooldown <= 0
        )

    def feed(self, energy_amount: float = 100.0, hydration_amount: float = 60.0) -> None:
        """Direct feeding method topping up human calories and hydration."""
        self.gain_energy(energy_amount)
        self.hydration = min(self.max_hydration, self.hydration + hydration_amount)
        self.custom_data["dopamine"] = 1.0
        self.custom_data["stress"] = 0.0

    __hash__ = Entity.__hash__
    __eq__ = Entity.__eq__
