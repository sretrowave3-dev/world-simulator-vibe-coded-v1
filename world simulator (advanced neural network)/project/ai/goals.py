"""
project/ai/goals.py

Goal Selection & Intention Prioritization Solver for ALife Organisms.

Features:
- Utility-theory goal evaluation translating biological drives into high-level behavioral goals.
- Goal state tracking (FLEE, FORAGE, DRINK, MATE, REST, ATTACK, EXPLORE, WANDER).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from project.ai.needs import NeedType, OrganismNeeds


class GoalType(enum.Enum):
    IDLE = enum.auto()
    WANDER = enum.auto()
    FLEE = enum.auto()
    FORAGE_FOOD = enum.auto()
    DRINK_WATER = enum.auto()
    SEEK_MATE = enum.auto()
    REST = enum.auto()
    HUNT_PREY = enum.auto()
    ATTACK_ENEMY = enum.auto()
    DEFEND_TERRITORY = enum.auto()
    EXPLORE = enum.auto()
    SOCIALIZE = enum.auto()


@dataclass
class ActiveGoal:
    goal_type: GoalType = GoalType.WANDER
    priority: float = 0.5
    target_pos: Optional[Tuple[float, float]] = None
    target_entity_id: Optional[str] = None
    ticks_active: int = 0
    is_completed: bool = False

    def is_valid(self) -> bool:
        return not self.is_completed and self.ticks_active < 3000


class GoalSolver:
    """
    Evaluates needs, sensory perception, and environmental threats to select active goal.
    """

    @staticmethod
    def evaluate_goal(
        needs: OrganismNeeds,
        threat_detected: bool = False,
        food_visible: bool = False,
        water_visible: bool = False,
        mate_visible: bool = False,
        prey_visible: bool = False,
        is_carnivore: bool = False,
    ) -> ActiveGoal:
        # 1. Immediate Survival: Flight from threats
        if threat_detected or needs.fear > 0.6:
            return ActiveGoal(goal_type=GoalType.FLEE, priority=1.0)

        # 2. Critical Physiological Needs (Thirst > Hunger)
        if needs.thirst > 0.6 or (water_visible and needs.thirst > 0.3):
            return ActiveGoal(goal_type=GoalType.DRINK_WATER, priority=0.85 * needs.thirst)

        if is_carnivore and (needs.hunger > 0.4 or prey_visible):
            return ActiveGoal(goal_type=GoalType.HUNT_PREY, priority=0.80 * needs.hunger)

        if needs.hunger > 0.5 or (food_visible and needs.hunger > 0.25):
            return ActiveGoal(goal_type=GoalType.FORAGE_FOOD, priority=0.75 * needs.hunger)

        # 3. Reproductive urge
        if needs.reproduction_urge > 0.6 or (mate_visible and needs.reproduction_urge > 0.3):
            return ActiveGoal(goal_type=GoalType.SEEK_MATE, priority=0.60 * needs.reproduction_urge)

        # 4. Rest / Fatigue
        if needs.fatigue > 0.7:
            return ActiveGoal(goal_type=GoalType.REST, priority=0.50)

        # 5. Social or Exploration
        if needs.loneliness > 0.5:
            return ActiveGoal(goal_type=GoalType.SOCIALIZE, priority=0.40)

        if needs.boredom > 0.4:
            return ActiveGoal(goal_type=GoalType.EXPLORE, priority=0.30)

        return ActiveGoal(goal_type=GoalType.WANDER, priority=0.10)
