"""
project/systems/decision_system.py

Decision System executing species-specific psychological need loops, tactical planning,
active appetite/feeding foraging, seed discarding, and neural network sensory-action mediation.
"""

from __future__ import annotations

import math
import random
from typing import Set, List, Optional, Tuple
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.ai.needs import OrganismNeeds, get_default_species_profile, SpeciesPsychologyProfile
from project.ai.goals import GoalSolver, ActiveGoal, GoalType
from project.world.seeds import world_seed_growth_mgr, seed_logger


def is_food_entity(e: Entity) -> bool:
    """Detects whether an entity is a consumable plant, fruit, crop, meat, or forageable biomass."""
    if not e.is_alive:
        return True  # Carcass
    if e.entity_type == EntityType.PLANT:
        return True
    if e.custom_data.get("is_food", False):
        return True
    sp = str(getattr(e, "species_id", "")).lower()
    for kw in ("food", "fruit", "mango", "cucumber", "berry", "apple", "meat", "grass", "honey", "grain", "mushroom", "fern"):
        if kw in sp:
            return True
    return False


def get_food_type_name(e: Entity) -> str:
    """Extracts clean food name like 'Mango', 'Cucumber', 'Meat', 'Grass', etc."""
    if e.custom_data.get("fruit_type"):
        return str(e.custom_data["fruit_type"]).capitalize()
    sp = str(getattr(e, "species_id", "")).lower()
    for kw in ("mango", "cucumber", "berry", "apple", "fruit", "meat", "grass", "honey", "grain", "wheat", "mushroom"):
        if kw in sp:
            return kw.capitalize()
    return "Wild Fruit"


class DecisionSystem:
    """Orchestrates species-specific intentions, survival reflexes, appetite foraging, and psychological goals."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "DecisionSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.AI

    @property
    def priority(self) -> int:
        return ExecutionPriority.DECISION

    @property
    def dependencies(self) -> Set[str]:
        return {"PerceptionSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        dt = context.delta_time
        sim_tick = context.tick
        time_snap = getattr(context, "time_snapshot", None)
        daylight = getattr(time_snap, "daylight_factor", 1.0) if time_snap else 1.0

        # Pre-filter all candidate foods in the world for rapid spatial foraging queries
        available_foods = [e for e in self._entities_list if is_food_entity(e)]
        carcasses_and_meat = [e for e in available_foods if "meat" in str(getattr(e, "species_id", "")).lower() or not e.is_alive]

        for entity in list(self._entities_list):
            if not entity.is_alive or entity.entity_type in (EntityType.PLANT, EntityType.FUNGUS):
                continue

            # -------------------------------------------------------------
            # 1. Psychological Profile & Needs Drive
            # -------------------------------------------------------------
            profile: Optional[SpeciesPsychologyProfile] = entity.custom_data.get("psychology_profile")
            if not profile:
                profile = get_default_species_profile(entity.entity_type.name)
                entity.custom_data["psychology_profile"] = profile

            needs: Optional[OrganismNeeds] = entity.custom_data.get("needs")
            if not needs:
                needs = OrganismNeeds()
                entity.custom_data["needs"] = needs

            perceived = entity.custom_data.get("perceived_entities", [])
            threats = [e for e in perceived if e.is_alive and e.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE)]
            prey = [e for e in perceived if e.is_alive and e.entity_type in (EntityType.HERBIVORE, EntityType.OMNIVORE)]
            allies = [e for e in perceived if e.is_alive and e.entity_type == entity.entity_type and e.entity_id != entity.entity_id]

            # Update drive values based on species traits
            threat_lvl = 1.0 if (threats and entity.entity_type not in (EntityType.PREDATOR, EntityType.CARNIVORE)) else 0.0
            needs.update_from_vitals(
                energy=entity.energy,
                max_energy=entity.max_energy,
                hydration=entity.hydration,
                max_hydration=entity.max_hydration,
                stamina=entity.stamina,
                max_stamina=entity.max_stamina,
                age_ticks=entity.age_ticks,
                maturity_ticks=entity.maturity_age_ticks,
                threat_level=threat_lvl,
                nearby_allies=len(allies),
                profile=profile,
            )

            # Dopamine homeostasis decay toward baseline
            curr_dop = entity.custom_data.get("dopamine", 0.40)
            entity.custom_data["dopamine"] = max(0.05, min(1.0, curr_dop + (0.40 - curr_dop) * 0.03))

            # Fear dynamics
            if threats and entity.entity_type not in (EntityType.PREDATOR, EntityType.CARNIVORE):
                entity.custom_data["fear"] = max(entity.custom_data.get("fear", 0.0), min(1.0, 0.95 * profile.base_fear_sensitivity))
            else:
                entity.custom_data["fear"] = max(0.0, entity.custom_data.get("fear", 0.0) * 0.88)

            # Curiosity tracks boredom drive
            entity.custom_data["curiosity"] = round(needs.boredom, 3)

            # Psychological Stress Calculation
            raw_stress = (
                (needs.hunger * 0.28) +
                (needs.thirst * 0.32) +
                (entity.custom_data.get("fear", 0.0) * 0.45) +
                (needs.fatigue * 0.15)
            )
            if entity.custom_data.get("divine_sanctuary_active", False):
                raw_stress *= 0.40
            entity.custom_data["stress"] = round(max(0.0, min(1.0, raw_stress)), 3)

            # -------------------------------------------------------------
            # 2. Species-Specific Survival & Appetite Foraging Decision Making
            # -------------------------------------------------------------
            goal_type = GoalType.WANDER
            target_pos: Optional[Tuple[float, float]] = None
            priority = 0.5
            is_hungry = (needs.hunger > 0.12 or entity.energy < entity.max_energy * 0.75)

            # ---------------------------------------------------------
            # A. ACTIVE APPETITE & FOOD CONSUMPTION (Herbivores, Humans, Avians, etc.)
            # ---------------------------------------------------------
            if is_hungry and entity.entity_type not in (EntityType.CARNIVORE, EntityType.PREDATOR):
                # Search for closest visible food or flora
                candidate_food = None
                min_f_dist = float("inf")
                for f in available_foods:
                    if f.entity_id == entity.entity_id:
                        continue
                    d_sq = (f.pos_x - entity.pos_x)**2 + (f.pos_y - entity.pos_y)**2
                    if d_sq < min_f_dist:
                        min_f_dist = d_sq
                        candidate_food = f

                if candidate_food and min_f_dist < 40000.0:  # Within 200m sensory range
                    dist = math.sqrt(min_f_dist)
                    target_pos = (candidate_food.pos_x, candidate_food.pos_y)
                    goal_type = GoalType.FORAGE_FOOD
                    priority = 0.88

                    # Within eating proximity (< 6.0m): INITIATE BITE / EAT ACTION!
                    if dist <= 6.0:
                        food_name = get_food_type_name(candidate_food)
                        f_low = food_name.lower()

                        # 1. Nutrition calculation based on food type
                        energy_yield = 65.0
                        hydration_yield = 30.0
                        if "meat" in f_low:
                            energy_yield, hydration_yield = 140.0, 15.0
                        elif "honey" in f_low:
                            energy_yield, hydration_yield = 160.0, 5.0
                        elif "mango" in f_low:
                            energy_yield, hydration_yield = 95.0, 45.0
                        elif "cucumber" in f_low:
                            energy_yield, hydration_yield = 45.0, 75.0
                        elif "berry" in f_low:
                            energy_yield, hydration_yield = 40.0, 30.0

                        entity.gain_energy(energy_yield)
                        entity.quench_thirst(hydration_yield)
                        entity.custom_data["dopamine"] = 0.95  # Satiation euphoria
                        entity.custom_data["stress"] = max(0.0, entity.custom_data.get("stress", 0.0) - 0.40)
                        entity.current_action = f"EATING_{food_name.upper()}"

                        # 2. FRUIT SEED DISCARD & LOGGING (Mango, Cucumber, Fruit, Berry, Grain)
                        if any(k in f_low for k in ("mango", "cucumber", "fruit", "berry", "apple", "grain", "wheat")):
                            world_seed_growth_mgr.generate_fruit_seeds(
                                fruit_type=food_name,
                                pos_x=entity.pos_x,
                                pos_y=entity.pos_y,
                                eater_id=entity.entity_id,
                                eater_species=entity.species_id,
                                sim_tick=sim_tick,
                            )

                        # 3. Reduce food biomass or consume completely
                        if hasattr(candidate_food, "biomass_kg"):
                            candidate_food.biomass_kg = max(0.0, candidate_food.biomass_kg - 0.5)
                            if candidate_food.biomass_kg <= 0.1:
                                candidate_food.is_alive = False
                                if candidate_food in self._entities_list:
                                    self._entities_list.remove(candidate_food)
                        else:
                            # Instant consumable item removal
                            candidate_food.is_alive = False
                            if candidate_food in self._entities_list:
                                self._entities_list.remove(candidate_food)

            # ---------------------------------------------------------
            # B. Herbivore: High-Vigilance Herd Flocking & Panic Flight
            # ---------------------------------------------------------
            if entity.entity_type == EntityType.HERBIVORE:
                if threats:
                    goal_type = GoalType.FLEE
                    closest_threat = min(threats, key=lambda t: (t.pos_x - entity.pos_x)**2 + (t.pos_y - entity.pos_y)**2)
                    target_pos = (closest_threat.pos_x, closest_threat.pos_y)
                    priority = 0.95
                    entity.custom_data["fear"] = 1.0
                elif not is_hungry and allies and needs.loneliness > 0.4:
                    avg_x = sum(a.pos_x for a in allies) / len(allies)
                    avg_y = sum(a.pos_y for a in allies) / len(allies)
                    goal_type = GoalType.SEEK_MATE if needs.reproduction_urge > 0.6 else GoalType.WANDER
                    target_pos = (avg_x, avg_y)
                    priority = 0.70

            # ---------------------------------------------------------
            # C. Predator / Carnivore: Hunting & Carcass Feeding
            # ---------------------------------------------------------
            elif entity.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE):
                # Check for nearby meat carcasses first
                nearest_meat = min(carcasses_and_meat, key=lambda m: (m.pos_x - entity.pos_x)**2 + (m.pos_y - entity.pos_y)**2) if carcasses_and_meat else None
                if nearest_meat and math.hypot(nearest_meat.pos_x - entity.pos_x, nearest_meat.pos_y - entity.pos_y) < 80.0:
                    m_dist = math.hypot(nearest_meat.pos_x - entity.pos_x, nearest_meat.pos_y - entity.pos_y)
                    target_pos = (nearest_meat.pos_x, nearest_meat.pos_y)
                    goal_type = GoalType.FORAGE_FOOD
                    priority = 0.90
                    if m_dist <= 6.0:
                        entity.gain_energy(130.0)
                        entity.custom_data["dopamine"] = 0.95
                        entity.current_action = "FEASTING_MEAT"
                        if nearest_meat in self._entities_list:
                            self._entities_list.remove(nearest_meat)
                elif prey and (needs.predatory_hunger > 0.25 or entity.energy < entity.max_energy * 0.8):
                    target_prey = min(prey, key=lambda p: (p.health, (p.pos_x - entity.pos_x)**2 + (p.pos_y - entity.pos_y)**2))
                    dist = math.hypot(target_prey.pos_x - entity.pos_x, target_prey.pos_y - entity.pos_y)
                    target_pos = (target_prey.pos_x, target_prey.pos_y)

                    if dist <= 25.0:
                        goal_type = GoalType.HUNT_PREY
                        entity.custom_data["ambush_mode"] = True
                        priority = 0.95
                    else:
                        goal_type = GoalType.HUNT_PREY
                        entity.custom_data["ambush_mode"] = False
                        priority = 0.80

            # ---------------------------------------------------------
            # D. Human: Tactical Survival, Tribal Cooperation, Psychological Community & Faith
            # ---------------------------------------------------------
            elif entity.entity_type == EntityType.HUMAN:
                # 0a. Evaluate Minecraft Shelter Need (Cold night darkness & predator attacks)
                entity.evaluate_shelter_need(daylight=daylight, threats_nearby=len(threats), sim_tick=sim_tick)

                # 0b. Nocturnal Shelter Seeking & Resting (Minecraft Rule: Survive the Night)
                if daylight < 0.40 or entity.shelter_importance_score > 0.65:
                    from project.civilization.settlement import world_settlement_mgr
                    if entity.in_shelter_id:
                        # Safely sleeping/resting inside shelter away from nocturnal monsters
                        goal_type = GoalType.REST
                        target_pos = (entity.pos_x, entity.pos_y)
                        priority = 0.99
                        entity.current_action = "SLEEPING_IN_SHELTER"
                        if entity.energy < entity.max_energy:
                            entity.gain_energy(15.0 * dt)
                        if entity.health < entity.max_health:
                            entity.health = min(entity.max_health, entity.health + 2.0 * dt)
                    else:
                        best_shelter = world_settlement_mgr.find_best_shelter(entity.pos_x, entity.pos_y, max_dist=500.0)
                        if best_shelter:
                            dist_to_shelter = math.hypot(best_shelter.pos_x - entity.pos_x, best_shelter.pos_y - entity.pos_y)
                            if dist_to_shelter < 20.0:
                                entity.enter_shelter(best_shelter)
                                goal_type = GoalType.REST
                                target_pos = (best_shelter.pos_x, best_shelter.pos_y)
                                priority = 0.99
                                entity.current_action = "ENTERED_SHELTER"
                            else:
                                target_pos = (best_shelter.pos_x, best_shelter.pos_y)
                                goal_type = GoalType.WANDER
                                priority = 0.95
                                entity.current_action = "SEEKING_SHELTER"
                        elif entity.inventory.get("wood", 0) >= 1.5 or entity.inventory.get("stone", 0) >= 1.5:
                            # Emergency building: create a shelter!
                            crafted_name = entity.attempt_emergent_crafting(sim_tick=sim_tick)
                            if crafted_name:
                                entity.current_action = f"BUILT_{crafted_name.upper().replace(' ', '_')}"
                elif daylight >= 0.45 and entity.in_shelter_id:
                    # Dawn breaks: exit shelter to forage and work
                    entity.exit_shelter()
                    entity.current_action = "EMERGING_AT_DAWN"

                # 0c. Thirst & Hydration: Drink from nearby rivers / water bodies
                if entity.hydration < 140.0:
                    entity.drink_water(80.0)
                    entity.current_action = "DRINKING_WATER"

                # 1. Emergent Crafting: Non-hardcoded discovery based on held materials & IQ
                if sim_tick % 20 == 0 and not threats:
                    crafted_name = entity.attempt_emergent_crafting(sim_tick=sim_tick)
                    if crafted_name:
                        entity.current_action = f"CRAFTED_{crafted_name.upper().replace(' ', '_')}"

                # 2. Resource Foraging: Active Minecraft-style wood harvesting and stone quarrying
                if not is_hungry and not threats and entity.inventory_weight < entity.max_inventory_capacity_kg - 5.0:
                    # Seek out nearby mature trees
                    nearby_trees = [
                        e for e in self._entities_list
                        if e.is_alive and getattr(e, "is_tree", None) and e.is_tree()
                        and math.hypot(e.pos_x - entity.pos_x, e.pos_y - entity.pos_y) < 300.0
                    ]
                    if nearby_trees and entity.inventory.get("wood", 0.0) < 15.0:
                        chosen_tree = min(nearby_trees, key=lambda t: (t.pos_x - entity.pos_x)**2 + (t.pos_y - entity.pos_y)**2)
                        dist = math.hypot(chosen_tree.pos_x - entity.pos_x, chosen_tree.pos_y - entity.pos_y)
                        if dist < 8.0:
                            harvested = entity.harvest_from_tree(chosen_tree)
                            if harvested > 0:
                                entity.current_action = "HARVESTING_TIMBER"
                        else:
                            target_pos = (chosen_tree.pos_x, chosen_tree.pos_y)
                            goal_type = GoalType.FORAGE_FOOD
                            priority = 0.85
                            entity.current_action = "APPROACHING_TREE"

                    # Gather stones if near mountains, rocky quarry boulders, or rivers
                    elif entity.inventory.get("stone", 0.0) < 12.0 and random.random() < 0.35:
                        entity.gather_stone(2.5)
                        entity.current_action = "GATHERING_STONE"

                # 3. Armed Defense against Predators
                if threats and entity.equipped_tool in ("wood_spear", "stone_axe") and (entity.health / max(1.0, entity.max_health)) > 0.4:
                    goal_type = GoalType.ATTACK_ENEMY
                    closest_threat = min(threats, key=lambda t: (t.pos_x - entity.pos_x)**2 + (t.pos_y - entity.pos_y)**2)
                    target_pos = (closest_threat.pos_x, closest_threat.pos_y)
                    priority = 0.98
                    entity.current_action = "DEFENDING_CLAN"

                # 4. Psychological Mobbing & Community Formation
                # Based on shared vulnerability (fear), social affinity, and existential dread (stress).
                # Humans naturally gravitate together when stressed to form a "Mob/Community"
                elif not is_hungry and allies and (entity.custom_data.get("stress", 0.0) * 0.4 + profile.herd_cohesion_weight * 0.6) > 0.35:
                    cluster_x = sum(a.pos_x for a in allies) / len(allies)
                    cluster_y = sum(a.pos_y for a in allies) / len(allies)
                    dist_to_cluster = math.hypot(cluster_x - entity.pos_x, cluster_y - entity.pos_y)
                    
                    if dist_to_cluster > 15.0:
                        target_pos = (cluster_x, cluster_y)
                        goal_type = GoalType.WANDER
                        priority = 0.85
                        entity.current_action = "JOINING_COMMUNITY"
                    else:
                        g_sys = getattr(self, "gemini_sys", None)
                        if g_sys and getattr(g_sys, "global_god_affinity", 0.0) >= 100.0:
                            entity.current_action = "PRAYING"
                            priority = 0.99
                            if getattr(g_sys, "god_incarnated", False) and random.random() < 0.05:
                                entity.custom_data["dopamine"] = 1.0
                        else:
                            entity.current_action = "SOCIALIZING"
                            entity.custom_data["stress"] = max(0.0, entity.custom_data.get("stress", 0.0) - 0.05)
                            entity.custom_data["dopamine"] = min(1.0, entity.custom_data.get("dopamine", 0.0) + 0.01)

                # 5. Tactical Fleeing (Unarmed / Injured)
                elif (entity.health / max(1.0, entity.max_health)) < profile.tactical_retreat_threshold and threats:
                    goal_type = GoalType.FLEE
                    closest_threat = min(threats, key=lambda t: (t.pos_x - entity.pos_x)**2 + (t.pos_y - entity.pos_y)**2)
                    target_pos = (closest_threat.pos_x, closest_threat.pos_y)
                    priority = 0.95
                
                # 6. Altruistic Feeding
                elif not is_hungry and allies and entity.energy > 300.0:
                    starving_ally = next((a for a in allies if a.energy < a.max_energy * 0.3), None)
                    if starving_ally:
                        target_pos = (starving_ally.pos_x, starving_ally.pos_y)
                        goal_type = GoalType.WANDER
                        priority = 0.85
                        if math.hypot(starving_ally.pos_x - entity.pos_x, starving_ally.pos_y - entity.pos_y) < 10.0:
                            entity.energy -= 20.0
                            starving_ally.gain_energy(20.0)
                            entity.custom_data["dopamine"] = 1.0
                
                # 7. Leader Follow
                elif not is_hungry and entity.custom_data.get("emergent_role") != "LEADER":
                    leader = next((a for a in allies if a.custom_data.get("emergent_role") == "LEADER"), None)
                    if leader and math.hypot(leader.pos_x - entity.pos_x, leader.pos_y - entity.pos_y) > 120.0:
                        target_pos = (leader.pos_x, leader.pos_y)
                        goal_type = GoalType.WANDER
                        priority = 0.75

            # ---------------------------------------------------------
            # E. Bacteria: Chemotaxis & Dormancy
            # ---------------------------------------------------------
            elif entity.entity_type == EntityType.BACTERIA:
                if needs.dormancy_urge >= 1.0:
                    goal_type = GoalType.REST
                    entity.custom_data["encysted_dormant"] = True
                    priority = 1.0
                else:
                    entity.custom_data["encysted_dormant"] = False

            # Assign computed active goal
            active_goal = ActiveGoal(goal_type=goal_type, target_pos=target_pos, priority=priority)
            entity.custom_data["active_goal"] = active_goal
            if not entity.current_action or not entity.current_action.startswith("EATING_"):
                entity.current_action = active_goal.goal_type.name

            # -------------------------------------------------------------
            # 3. Neural Network Cognitive Feedforward
            # -------------------------------------------------------------
            if entity.brain and not entity.custom_data.get("encysted_dormant", False):
                norm_energy = min(1.0, entity.energy / max(1.0, entity.max_energy))
                norm_hydra = min(1.0, entity.hydration / max(1.0, entity.max_hydration))
                
                threat_dx, threat_dy = 0.0, 0.0
                if threats:
                    threat_dx = (threats[0].pos_x - entity.pos_x) / 100.0
                    threat_dy = (threats[0].pos_y - entity.pos_y) / 100.0
                    
                target_dx, target_dy = 0.0, 0.0
                if target_pos:
                    target_dx = (target_pos[0] - entity.pos_x) / 100.0
                    target_dy = (target_pos[1] - entity.pos_y) / 100.0
                    
                cd = entity.custom_data
                inputs = [
                    norm_energy,
                    norm_hydra,
                    min(1.0, entity.health / max(1.0, entity.max_health)),
                    threat_dx,
                    threat_dy,
                    target_dx,
                    target_dy,
                    cd.get("dopamine", 0.0),
                    cd.get("serotonin", 0.0),
                    cd.get("stress", 0.0),
                    cd.get("fear", 0.0),
                    cd.get("curiosity", 0.0),
                    cd.get("confidence", 0.0),
                    float(len(allies)) / 10.0,
                    entity.pos_x / 4096.0,
                    entity.pos_y / 4096.0,
                ]

                # Neural forward evaluation
                outputs = entity.brain.forward(inputs)
                if len(outputs) >= 4:
                    steer_x, steer_y, speed_mod, focus = outputs[:4]
                    if target_pos is None:
                        entity.vel_x += steer_x * speed_mod * 0.5
                        entity.vel_y += steer_y * speed_mod * 0.5

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
