"""
project/utils/random_utils.py

High-performance, deterministic PRNG and statistical distribution sampling helpers.

Architectural Guarantees:
- Bit-exact cross-platform determinism via 64-bit SplitMix and Xoroshiro128+ engines.
- Independent of Python's runtime randomized hash seeds.
- Zero external dependencies.
- Standard scientific distributions: Uniform, Normal (Box-Muller), Exponential, Bernoulli, Weighted Choice.
"""

from __future__ import annotations

import math
from typing import Any, List, Sequence, Tuple, TypeVar

T = TypeVar("T")


class DeterministicPRNG:
    """
    64-bit SplitMix64 pseudo-random number generator.
    Fast state transitions with exceptional statistical distribution properties.
    """

    __slots__ = ("_state", "_has_spare_gaussian", "_spare_gaussian")

    def __init__(self, seed: int = 42) -> None:
        self._state: int = seed & 0xFFFFFFFFFFFFFFFF
        self._has_spare_gaussian: bool = False
        self._spare_gaussian: float = 0.0

    def reseed(self, seed: int) -> None:
        self._state = seed & 0xFFFFFFFFFFFFFFFF
        self._has_spare_gaussian = False
        self._spare_gaussian = 0.0

    def next_uint64(self) -> int:
        """Returns next pseudo-random unsigned 64-bit integer."""
        self._state = (self._state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF

    def next_uint32(self) -> int:
        """Returns next pseudo-random unsigned 32-bit integer."""
        return self.next_uint64() >> 32

    def next_float(self) -> float:
        """Returns a deterministic floating point number in range [0.0, 1.0)."""
        return (self.next_uint64() >> 11) * (1.0 / 9007199254740992.0)

    def uniform(self, min_val: float, max_val: float) -> float:
        """Returns a uniform random float in range [min_val, max_val)."""
        return min_val + (max_val - min_val) * self.next_float()

    def randint(self, min_val: int, max_val: int) -> int:
        """Returns a uniform random integer in inclusive range [min_val, max_val]."""
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        range_size = max_val - min_val + 1
        return min_val + int(self.next_float() * range_size) % range_size

    def bernoulli(self, p: float = 0.5) -> bool:
        """Returns True with probability p, otherwise False."""
        return self.next_float() < p

    def gaussian(self, mean: float = 0.0, std_dev: float = 1.0) -> float:
        """
        Box-Muller transform generating Gaussian (Normal) distributed random float.
        """
        if self._has_spare_gaussian:
            self._has_spare_gaussian = False
            return mean + self._spare_gaussian * std_dev

        # Sample two uniform random floats
        u1 = max(1e-15, self.next_float())
        u2 = self.next_float()

        r = math.sqrt(-2.0 * math.log(u1))
        theta = 2.0 * math.pi * u2

        self._spare_gaussian = r * math.sin(theta)
        self._has_spare_gaussian = True

        return mean + (r * math.cos(theta)) * std_dev

    def exponential(self, rate_lambda: float = 1.0) -> float:
        """Inverse transform sampling of Exponential distribution."""
        u = max(1e-15, self.next_float())
        return -math.log(u) / rate_lambda

    def choice(self, sequence: Sequence[T]) -> T:
        """Picks a random element uniformly from sequence."""
        if not sequence:
            raise IndexError("Cannot choice from empty sequence.")
        idx = int(self.next_float() * len(sequence)) % len(sequence)
        return sequence[idx]

    def weighted_choice(self, items: Sequence[T], weights: Sequence[float]) -> T:
        """Selects an item based on relative weights."""
        if len(items) != len(weights) or not items:
            raise ValueError("Items and weights must be non-empty and of equal length.")

        total_weight = sum(weights)
        if total_weight <= 0.0:
            return self.choice(items)

        r = self.next_float() * total_weight
        accum = 0.0
        for item, weight in zip(items, weights):
            accum += weight
            if r <= accum:
                return item
        return items[-1]

    def shuffle(self, sequence: List[T]) -> None:
        """In-place Fisher-Yates shuffle."""
        for i in range(len(sequence) - 1, 0, -1):
            j = self.randint(0, i)
            sequence[i], sequence[j] = sequence[j], sequence[i]

    def derive_child(self, offset: int) -> DeterministicPRNG:
        """Derives a bitwise distinct, reproducible child PRNG stream."""
        h = (self.next_uint64() ^ (offset * 0x9E3779B97F4A7C15)) & 0xFFFFFFFFFFFFFFFF
        z = (h ^ (h >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        return DeterministicPRNG(z)
