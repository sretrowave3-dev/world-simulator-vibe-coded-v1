"""
project/systems/movement_system.py

Movement System executing species-specific adaptive locomotion, tactical maneuvers,
predator ambush bursts, herbivore panic sprints, and boundary physics.
"""

from __future__ import annotations

import math
from typing import Set, List, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.ai.goals import ActiveGoal, GoalType


class MovementSystem:
    """Calculates species-specific motion kinematics and tactical spatial navigation."""

    def __init__(self, entities_list: List[Entity], world_width: float = 4096.0, world_height: float = 4096.0) -> None:
        self._entities_list = entities_list
        self._world_width = world_width
        self._world_height = world_height

    @property
    def name(self) -> str:
        return "MovementSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.MOVEMENT

    @property
    def dependencies(self) -> Set[str]:
        return {"DecisionSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        for entity in self._entities_list:
            if not entity.is_alive or entity.entity_type == EntityType.PLANT or entity.entity_type == EntityType.FUNGUS:
                continue

            # Encysted dormant bacteria do not move
            if entity.custom_data.get("encysted_dormant", False):
                entity.vel_x = 0.0
                entity.vel_y = 0.0
                continue

            goal: Optional[ActiveGoal] = entity.custom_data.get("active_goal")
            
            # -------------------------------------------------------------
            # 1. Biological Locomotion Speed & Soft-Cap Calculation
            # -------------------------------------------------------------
            from project.core.biology import soft_cap, calculate_locomotion_cost

            indiv_base_speed = getattr(entity, "base_speed", 3.5)
            speed_cap = getattr(entity, "max_speed_cap", 14.0)
            vitality = getattr(entity, "vitality", 1.0)
            stamina_ratio = getattr(entity, "stamina_ratio", 1.0)
            health_ratio = getattr(entity, "health_ratio", 1.0)

            speed_multiplier = 1.0
            is_sprinting = False

            if goal and goal.goal_type == GoalType.FLEE:
                is_sprinting = True
                speed_multiplier = getattr(entity, "flight_speed_multiplier", 1.75)
            elif entity.custom_data.get("ambush_mode", False):
                is_sprinting = True
                speed_multiplier = getattr(entity, "ambush_speed_multiplier", 2.0)
            elif goal and goal.goal_type == GoalType.HUNT_PREY:
                speed_multiplier = 0.65  # Stealth stalk
            elif entity.current_action == "REST":
                speed_multiplier = 0.0

            # Daylight modulation
            time_snap = getattr(context, "time_snapshot", None)
            daylight = getattr(time_snap, "daylight_factor", 1.0) if time_snap else 1.0

            # Ectotherm solar basking (Reptiles / Amphibians)
            if not getattr(entity, "is_endotherm", True):
                if daylight > 0.5:
                    speed_multiplier *= 1.15  # Solar basking agility boost
                    entity.body_temperature_c = min(35.0, entity.body_temperature_c + 0.05)
                elif daylight < 0.15:
                    speed_multiplier *= 0.70  # Cold nocturnal lethargy conservation
                    entity.body_temperature_c = max(14.0, entity.body_temperature_c - 0.05)

            # Diurnal vs Nocturnal behavioral adaptations
            if daylight < 0.15:
                if entity.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE, EntityType.ARTHROPOD):
                    # Nocturnal stealth hunter bonus
                    if goal and goal.goal_type == GoalType.HUNT_PREY:
                        speed_multiplier *= 1.25
                elif entity.entity_type in (EntityType.HUMAN, EntityType.HERBIVORE, EntityType.AVIAN):
                    # Diurnal resting / sleep slowdown to conserve energy
                    if not (goal and goal.goal_type == GoalType.FLEE):
                        speed_multiplier *= 0.45
                        entity.recover_stamina(0.3)

            # Stamina, health, and age-vitality modulation
            stamina_factor = 0.45 + 0.55 * stamina_ratio
            health_factor = 0.35 + 0.65 * health_ratio
            raw_speed = indiv_base_speed * speed_multiplier * stamina_factor * health_factor * vitality

            # Soft-cap effective speed
            effective_speed = soft_cap(raw_speed, soft_limit=speed_cap, hardness=1.2)

            # Manage stamina dynamics
            if is_sprinting:
                entity.drain_stamina(0.35)
                # Additional kinetic energy cost
                kinetic_energy_cost = calculate_locomotion_cost(entity.mass_kg, effective_speed) * context.delta_time
                entity.consume_energy(kinetic_energy_cost, tick=context.tick)
            elif effective_speed > 0.05:
                entity.drain_stamina(0.02)
            else:
                entity.recover_stamina(getattr(entity, "stamina_recovery_rate", 0.6))

            # -------------------------------------------------------------
            # 2. Tactical Steering Vector Computation
            # -------------------------------------------------------------
            target_dx, target_dy = 0.0, 0.0

            if goal and goal.goal_type == GoalType.FLEE:
                # Steering force directly away from threat
                if goal.target_pos is not None:
                    target_dx = entity.pos_x - goal.target_pos[0]
                    target_dy = entity.pos_y - goal.target_pos[1]
                    # Zig-zag evasive perturbation for herbivores
                    if entity.entity_type == EntityType.HERBIVORE:
                        zigzag = math.sin(context.tick * 0.4) * 0.5
                        target_dx += -target_dy * zigzag
                        target_dy += target_dx * zigzag
            elif goal and goal.target_pos is not None:
                # Seek steering toward target pos
                target_dx = goal.target_pos[0] - entity.pos_x
                target_dy = goal.target_pos[1] - entity.pos_y

            # Idle wander if no active directional force
            if abs(target_dx) < 0.001 and abs(target_dy) < 0.001:
                entity.heading_angle += 0.08 * math.sin(context.tick * 0.05 + hash(entity.entity_id) % 10)
                target_dx = math.cos(entity.heading_angle)
                target_dy = math.sin(entity.heading_angle)

            # Neural output integration
            brain_out = entity.custom_data.get("brain_outputs")
            if brain_out and len(brain_out) >= 2 and not (goal and goal.priority >= 0.9):
                target_dx = target_dx * 0.4 + float(brain_out[0]) * 0.6
                target_dy = target_dy * 0.4 + float(brain_out[1]) * 0.6

            # Normalize and apply velocities
            mag = math.hypot(target_dx, target_dy)
            if mag > 1e-9 and effective_speed > 0.0:
                entity.vel_x = (target_dx / mag) * effective_speed
                entity.vel_y = (target_dy / mag) * effective_speed
                entity.heading_angle = math.atan2(entity.vel_y, entity.vel_x)
            else:
                entity.vel_x = 0.0
                entity.vel_y = 0.0

            # -------------------------------------------------------------
            # 3. Position Integration & Soft World Boundaries
            # -------------------------------------------------------------
            dt = context.delta_time
            entity.pos_x += entity.vel_x * (dt * 60.0)
            entity.pos_y += entity.vel_y * (dt * 60.0)

            # Soft boundary clamping
            margin = 15.0
            if entity.pos_x < margin:
                entity.pos_x = margin
                entity.vel_x = abs(entity.vel_x)
            elif entity.pos_x > self._world_width - margin:
                entity.pos_x = self._world_width - margin
                entity.vel_x = -abs(entity.vel_x)

            if entity.pos_y < margin:
                entity.pos_y = margin
                entity.vel_y = abs(entity.vel_y)
            elif entity.pos_y > self._world_height - margin:
                entity.pos_y = self._world_height - margin
                entity.vel_y = -abs(entity.vel_y)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
