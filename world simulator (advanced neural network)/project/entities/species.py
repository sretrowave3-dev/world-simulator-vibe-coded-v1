"""
project/entities/species.py

Species Taxonomy, Speciation Dynamics & Phylogenetic Tree Tracking for the ALife Platform.

Features:
- Phylogenetic lineage tree recording speciation branching and extinctions.
- Genetic divergence distance calculation for adaptive speciation thresholds.
- Population dynamics (current population, birth count, death count, peak census).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Species:
    species_id: str
    name: str
    founding_tick: int
    parent_species_id: Optional[str] = None
    generation: int = 1
    color_rgb: Tuple[int, int, int] = (150, 150, 150)
    
    # Population Demographics
    current_population: int = 0
    total_births: int = 0
    total_deaths: int = 0
    peak_population: int = 0
    is_extinct: bool = False
    extinction_tick: Optional[int] = None

    # Representative Baseline Traits
    baseline_genome_vector: List[float] = field(default_factory=list)

    def record_birth(self) -> None:
        self.current_population += 1
        self.total_births += 1
        if self.current_population > self.peak_population:
            self.peak_population = self.current_population

    def record_death(self, current_tick: int) -> None:
        self.current_population = max(0, self.current_population - 1)
        self.total_deaths += 1
        if self.current_population == 0 and not self.is_extinct:
            self.is_extinct = True
            self.extinction_tick = current_tick


class SpeciesRegistry:
    """
    Registry tracking all living and extinct species lineages across evolutionary time.
    """

    def __init__(self, speciation_threshold: float = 0.25) -> None:
        self.speciation_threshold = speciation_threshold
        self._species_map: Dict[str, Species] = {}
        self._lineage_tree: Dict[str, List[str]] = {}  # parent_id -> list of child_ids
        self._next_species_index: int = 1

    def register_species(
        self,
        name: str,
        founding_tick: int,
        parent_id: Optional[str] = None,
        color_rgb: Tuple[int, int, int] = (150, 150, 150),
        genome_vector: Optional[List[float]] = None,
    ) -> Species:
        species_id = f"species_{self._next_species_index:04d}"
        self._next_species_index += 1

        generation = 1
        if parent_id and parent_id in self._species_map:
            generation = self._species_map[parent_id].generation + 1

        spec = Species(
            species_id=species_id,
            name=name,
            founding_tick=founding_tick,
            parent_species_id=parent_id,
            generation=generation,
            color_rgb=color_rgb,
            baseline_genome_vector=genome_vector or [],
        )

        self._species_map[species_id] = spec
        if parent_id:
            if parent_id not in self._lineage_tree:
                self._lineage_tree[parent_id] = []
            self._lineage_tree[parent_id].append(species_id)

        return spec

    def get(self, species_id: str) -> Optional[Species]:
        return self._species_map.get(species_id)

    def get_all_active(self) -> List[Species]:
        return [s for s in self._species_map.values() if not s.is_extinct]

    def get_all_extinct(self) -> List[Species]:
        return [s for s in self._species_map.values() if s.is_extinct]

    @staticmethod
    def calculate_genetic_distance(genome_a: List[float], genome_b: List[float]) -> float:
        """Normalized Euclidean genetic distance between two allele vectors."""
        if not genome_a or not genome_b or len(genome_a) != len(genome_b):
            return 1.0

        sq_sum = sum((a - b) ** 2 for a, b in zip(genome_a, genome_b))
        return math.sqrt(sq_sum / len(genome_a))

    def should_speciate(self, individual_genome: List[float], species_id: str) -> bool:
        """Determines if an individual has diverged far enough to trigger speciation."""
        spec = self.get(species_id)
        if spec is None or not spec.baseline_genome_vector:
            return False

        dist = self.calculate_genetic_distance(individual_genome, spec.baseline_genome_vector)
        return dist >= self.speciation_threshold
