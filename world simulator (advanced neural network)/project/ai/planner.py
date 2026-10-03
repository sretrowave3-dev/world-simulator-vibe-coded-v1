"""
project/ai/planner.py

Goal-Oriented Action Planning (GOAP) Engine for Complex ALife Decision Making.

Features:
- State-space A* graph search over action preconditions and effects.
- Dynamic action sequencing for multi-step goals (e.g. Find wood -> Craft axe -> Cut tree -> Build shelter).
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


WorldState = Dict[str, Any]


@dataclass
class GOAPAction:
    name: str
    cost: float = 1.0
    preconditions: WorldState = field(default_factory=dict)
    effects: WorldState = field(default_factory=dict)

    def can_execute(self, current_state: WorldState) -> bool:
        """Checks if current state satisfies all action preconditions."""
        for k, v in self.preconditions.items():
            if current_state.get(k) != v:
                return False
        return True

    def apply_effects(self, current_state: WorldState) -> WorldState:
        """Returns a new state with action effects applied."""
        new_state = dict(current_state)
        new_state.update(self.effects)
        return new_state


class GOAPPlanner:
    """
    A* search planner formulating action chains to transition current state to goal state.
    """

    @staticmethod
    def _state_matches_goal(state: WorldState, goal: WorldState) -> bool:
        for k, v in goal.items():
            if state.get(k) != v:
                return False
        return True

    @staticmethod
    def _heuristic(state: WorldState, goal: WorldState) -> float:
        """Number of unmet goal conditions."""
        unmet = 0
        for k, v in goal.items():
            if state.get(k) != v:
                unmet += 1
        return float(unmet)

    @classmethod
    def plan(
        cls,
        initial_state: WorldState,
        goal_state: WorldState,
        available_actions: List[GOAPAction],
    ) -> Optional[List[GOAPAction]]:
        """
        Formulates an optimal plan (ordered list of GOAPActions) to satisfy goal_state.
        """
        if cls._state_matches_goal(initial_state, goal_state):
            return []

        # Priority Queue: (f_score, counter, current_state_dict, action_chain, g_score)
        pq: List[Tuple[float, int, WorldState, List[GOAPAction], float]] = []
        counter = 0

        h0 = cls._heuristic(initial_state, goal_state)
        heapq.heappush(pq, (h0, counter, initial_state, [], 0.0))

        visited: Set[Tuple[Tuple[str, Any], ...]] = set()

        while pq:
            f, _, current_state, plan_chain, g = heapq.heappop(pq)

            state_key = tuple(sorted(current_state.items()))
            if state_key in visited:
                continue
            visited.add(state_key)

            if cls._state_matches_goal(current_state, goal_state):
                return plan_chain

            for action in available_actions:
                if action.can_execute(current_state):
                    next_state = action.apply_effects(current_state)
                    next_key = tuple(sorted(next_state.items()))
                    if next_key not in visited:
                        next_g = g + action.cost
                        next_h = cls._heuristic(next_state, goal_state)
                        counter += 1
                        heapq.heappush(
                            pq,
                            (next_g + next_h, counter, next_state, plan_chain + [action], next_g)
                        )

        return None
