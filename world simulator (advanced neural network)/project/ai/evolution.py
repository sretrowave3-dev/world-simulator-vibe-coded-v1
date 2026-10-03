"""
project/ai/evolution.py

Evolutionary Engine, Fitness Evaluation & Natural Selection Algorithms for the ALife Platform.

Features:
- Multi-objective fitness scoring (longevity, energy harvest, offspring count, biomass accumulation).
- Selection algorithms: Tournament Selection, Roulette Wheel (Fitness Proportionate), Truncation.
- Adaptive evolutionary pressure tuning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, TypeVar
from project.utils.random_utils import DeterministicPRNG

T = TypeVar("T")


@dataclass
class FitnessScore:
    """Multi-objective fitness breakdown for an individual."""
    survival_ticks: int = 0
    energy_harvested: float = 0.0
    offspring_count: int = 0
    food_consumed: float = 0.0
    damage_dealt: float = 0.0
    discovery_points: float = 0.0

    @property
    def composite_score(self) -> float:
        """Calculates normalized aggregate fitness value."""
        return (
            float(self.survival_ticks) * 0.1 +
            self.energy_harvested * 0.5 +
            float(self.offspring_count) * 50.0 +
            self.food_consumed * 0.2 +
            self.damage_dealt * 0.3 +
            self.discovery_points * 10.0
        )


class SelectionEngine:
    """
    Standard evolutionary selection algorithms.
    """

    @staticmethod
    def tournament_selection(
        candidates: List[Tuple[T, float]],
        tournament_size: int = 3,
        prng: Optional[DeterministicPRNG] = None
    ) -> T:
        """Picks the best candidate out of a random sub-sample of size tournament_size."""
        rng = prng or DeterministicPRNG()
        if not candidates:
            raise ValueError("Cannot select from empty candidate pool.")

        sample_size = min(len(candidates), max(1, tournament_size))
        pool = [rng.choice(candidates) for _ in range(sample_size)]
        pool.sort(key=lambda item: item[1], reverse=True)
        return pool[0][0]

    @staticmethod
    def roulette_wheel_selection(
        candidates: List[Tuple[T, float]],
        prng: Optional[DeterministicPRNG] = None
    ) -> T:
        """Selects candidate with probability proportional to positive fitness score."""
        rng = prng or DeterministicPRNG()
        if not candidates:
            raise ValueError("Cannot select from empty candidate pool.")

        # Shift all fitness scores to positive domain
        min_fit = min(c[1] for c in candidates)
        offset = abs(min_fit) + 0.01 if min_fit <= 0 else 0.0
        positive_candidates = [(c[0], c[1] + offset) for c in candidates]

        total_fitness = sum(c[1] for c in positive_candidates)
        if total_fitness <= 0.0:
            return rng.choice(candidates)[0]

        r = rng.uniform(0.0, total_fitness)
        accum = 0.0
        for item, fit in positive_candidates:
            accum += fit
            if r <= accum:
                return item
        return candidates[-1][0]

    @staticmethod
    def truncation_selection(
        candidates: List[Tuple[T, float]],
        top_ratio: float = 0.2
    ) -> List[T]:
        """Returns top percentile of fittest candidates."""
        if not candidates:
            return []
        sorted_candidates = sorted(candidates, key=lambda c: c[1], reverse=True)
        cutoff = max(1, int(len(sorted_candidates) * top_ratio))
        return [c[0] for c in sorted_candidates[:cutoff]]
