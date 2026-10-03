"""
project/ai/genome.py

Genetics Engine & Chromosomal Representation for the ALife Platform.

Features:
- Normalized floating-point gene vector encoding $[-1.0, 1.0]$.
- Crossover operators: Uniform, Single-Point, Two-Point, and Arithmetic Blending.
- Adaptive Gaussian & Creep mutation operators.
- Phenotype Expression Decoder: Translates raw genetic alleles into concrete organism physical traits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from project.utils.random_utils import DeterministicPRNG


@dataclass
class PhenotypeTraits:
    """Decoded physical and behavioral attributes expressed from a Genome."""
    size_modifier: float = 1.0          # 0.5 to 2.0
    speed_modifier: float = 1.0         # 0.5 to 2.0
    vision_range_modifier: float = 1.0  # 0.5 to 2.0
    metabolism_modifier: float = 1.0    # 0.5 to 2.0
    aggression: float = 0.5             # 0.0 to 1.0
    fear_sensitivity: float = 0.5       # 0.0 to 1.0
    mating_drive: float = 0.5           # 0.0 to 1.0
    social_cooperation: float = 0.5     # 0.0 to 1.0
    cold_resistance: float = 0.5        # 0.0 to 1.0
    heat_resistance: float = 0.5        # 0.0 to 1.0
    color_hue: float = 0.5              # 0.0 to 1.0 (for procedural rendering)


@dataclass
class Genome:
    """
    Chromosomal representation containing array of continuous floating-point alleles.
    """

    genes: List[float] = field(default_factory=lambda: [0.0] * 32)

    @classmethod
    def create_random(cls, length: int = 32, prng: Optional[DeterministicPRNG] = None) -> Genome:
        rng = prng or DeterministicPRNG()
        return cls(genes=[rng.uniform(-1.0, 1.0) for _ in range(length)])

    def clone(self) -> Genome:
        return Genome(genes=list(self.genes))

    def mutate(
        self,
        mutation_rate: float = 0.05,
        mutation_magnitude: float = 0.15,
        prng: Optional[DeterministicPRNG] = None
    ) -> Genome:
        """Applies Gaussian creep mutations to alleles with probability mutation_rate."""
        rng = prng or DeterministicPRNG()
        new_genes = list(self.genes)

        for i in range(len(new_genes)):
            if rng.bernoulli(mutation_rate):
                delta = rng.gaussian(0.0, mutation_magnitude)
                new_genes[i] = max(-1.0, min(1.0, new_genes[i] + delta))

        return Genome(genes=new_genes)

    @classmethod
    def crossover_uniform(
        cls,
        parent_a: Genome,
        parent_b: Genome,
        blend_factor: float = 0.5,
        prng: Optional[DeterministicPRNG] = None
    ) -> Genome:
        """Uniform crossover with arithmetic gene blending."""
        rng = prng or DeterministicPRNG()
        length = min(len(parent_a.genes), len(parent_b.genes))
        child_genes: List[float] = [0.0] * length

        for i in range(length):
            ga = parent_a.genes[i]
            gb = parent_b.genes[i]
            if rng.bernoulli(0.5):
                # Inherit from parent A with slight blend
                child_genes[i] = ga * (1.0 - blend_factor * 0.2) + gb * (blend_factor * 0.2)
            else:
                # Inherit from parent B with slight blend
                child_genes[i] = gb * (1.0 - blend_factor * 0.2) + ga * (blend_factor * 0.2)

        return cls(genes=child_genes)

    @classmethod
    def crossover_twopoint(
        cls,
        parent_a: Genome,
        parent_b: Genome,
        prng: Optional[DeterministicPRNG] = None
    ) -> Genome:
        """Two-point chromosome crossover."""
        rng = prng or DeterministicPRNG()
        length = min(len(parent_a.genes), len(parent_b.genes))
        if length <= 2:
            return parent_a.clone()

        pt1 = rng.randint(1, length - 2)
        pt2 = rng.randint(pt1 + 1, length - 1)

        child_genes = (
            parent_a.genes[:pt1] +
            parent_b.genes[pt1:pt2] +
            parent_a.genes[pt2:]
        )
        return cls(genes=child_genes)

    def express_phenotype(self) -> PhenotypeTraits:
        """
        Decodes normalized genes into concrete PhenotypeTraits.
        Gene mapping:
          G0: Size, G1: Speed, G2: Vision, G3: Metabolism,
          G4: Aggression, G5: Fear, G6: Mating, G7: Social,
          G8: Cold, G9: Heat, G10: Color Hue
        """
        def to_unit(g_val: float) -> float:
            return (g_val + 1.0) * 0.5

        def to_scale(g_val: float, min_s: float = 0.5, max_s: float = 2.0) -> float:
            return min_s + to_unit(g_val) * (max_s - min_s)

        g = self.genes
        # Pad with 0.0 if genes length is shorter
        def get_g(idx: int) -> float:
            return g[idx] if idx < len(g) else 0.0

        return PhenotypeTraits(
            size_modifier=to_scale(get_g(0), 0.6, 1.8),
            speed_modifier=to_scale(get_g(1), 0.6, 1.8),
            vision_range_modifier=to_scale(get_g(2), 0.5, 2.0),
            metabolism_modifier=to_scale(get_g(3), 0.7, 1.5),
            aggression=to_unit(get_g(4)),
            fear_sensitivity=to_unit(get_g(5)),
            mating_drive=to_unit(get_g(6)),
            social_cooperation=to_unit(get_g(7)),
            cold_resistance=to_unit(get_g(8)),
            heat_resistance=to_unit(get_g(9)),
            color_hue=to_unit(get_g(10)),
        )
