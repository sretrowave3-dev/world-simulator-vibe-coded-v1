"""
project/systems/combat_system.py

Combat System resolving predator attacks, herd defensive shielding, stealth ambush critical hits,
and tribal counter-offensives between organisms.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType


class CombatSystem:
    """Manages species-specific attack events, herd defense mitigation, and combat resolutions."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "CombatSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.COMBAT

    @property
    def dependencies(self) -> Set[str]:
        return {"MovementSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        predators = [e for e in self._entities_list if e.is_alive and e.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE)]
        prey_and_humans = [e for e in self._entities_list if e.is_alive and e.entity_type not in (EntityType.PREDATOR, EntityType.CARNIVORE, EntityType.PLANT)]

        for predator in predators:
            cooldown = predator.custom_data.get("attack_cooldown_ticks", 0)
            if cooldown > 0:
                predator.custom_data["attack_cooldown_ticks"] = cooldown - 1
                continue

            for target in prey_and_humans:
                if target.entity_id == predator.entity_id:
                    continue

                dx = target.pos_x - predator.pos_x
                dy = target.pos_y - predator.pos_y
                dist = math.hypot(dx, dy)

                attack_range = predator.radius + target.radius + 2.0
                if dist <= attack_range:
                    # Dynamic striking power derived from allometric mass, strength, vitality, and stamina
                    strike_damage = getattr(predator, "combat_power", 30.0) * 1.25

                    # 1. Ambush Critical Strike Bonus
                    if predator.custom_data.get("ambush_mode", False):
                        strike_damage *= 1.45  # 45% ambush critical strike
                        predator.custom_data["ambush_mode"] = False

                    # 2. Herd Defense Shielding Mitigation
                    if target.entity_type == EntityType.HERBIVORE:
                        nearby_herd = sum(
                            1 for e in prey_and_humans
                            if e.is_alive and e.entity_type == EntityType.HERBIVORE and e.entity_id != target.entity_id
                            and math.hypot(e.pos_x - target.pos_x, e.pos_y - target.pos_y) < 60.0
                        )
                        damage_reduction = min(0.60, nearby_herd * 0.12)
                        strike_damage *= (1.0 - damage_reduction)

                    # 3. Human Tribal Defense & Divine Shield
                    elif target.entity_type == EntityType.HUMAN:
                        if target.custom_data.get("divine_blessing_active", False):
                            strike_damage *= 0.50  # Divine protection shield
                        # Counter-attack predator using human combat strength
                        human_counter = getattr(target, "combat_power", 20.0) * 0.9
                        predator.take_damage(human_counter, reason="HUMAN_COUNTERATTACK", tick=context.tick)
                        predator.drain_stamina(10.0)

                    # Drain combat stamina
                    predator.drain_stamina(12.0)
                    target.drain_stamina(8.0)

                    # Inflict damage
                    target.take_damage(strike_damage, reason="COMBAT_PREDATION", tick=context.tick)

                    # Feast on prey carcass upon kill
                    if not target.is_alive:
                        meat_calories = min(150.0, target.mass_kg * 6.5)
                        predator.gain_energy(meat_calories)
                        predator.quench_thirst(15.0)
                    else:
                        predator.gain_energy(10.0)

                    # Psychological responses
                    predator.custom_data["dopamine"] = 1.0
                    predator.custom_data["confidence"] = 1.0
                    target.custom_data["fear"] = 1.0
                    target.custom_data["stress"] = 1.0

                    predator.custom_data["attack_cooldown_ticks"] = 35
                    break

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
