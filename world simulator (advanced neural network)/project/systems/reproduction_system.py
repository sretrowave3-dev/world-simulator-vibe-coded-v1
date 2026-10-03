"""
project/systems/reproduction_system.py

Comprehensive Multi-Species Reproduction System coordinating true biological Bacteria Cell Division,
plant seed dispersal, sexual pair mating, and emergent leader/founder lineage propagation.
"""

from __future__ import annotations

import random
import math
from typing import Set, List, Tuple, Any, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.herbivore import Herbivore
from project.entities.carnivore import Carnivore
from project.entities.predator import Predator
from project.entities.human import Human
from project.entities.omnivore import Omnivore
from project.entities.decomposer import Decomposer


class ReproductionSystem:
    """Manages organism mating selection, cell division, seed dispersal, and chaotic evolutionary branching."""

    def __init__(
        self,
        entities_list: List[Entity],
        pending_births: List[Tuple[EntityType, Tuple[float, float], Tuple[str, ...], Any]],
    ) -> None:
        self._entities_list = entities_list
        self._pending_births = pending_births
        self.division_event_count: int = 0

    @property
    def name(self) -> str:
        return "ReproductionSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.REPRODUCTION

    @property
    def dependencies(self) -> Set[str]:
        return {"DigestionSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        self._pending_births.clear()
        self.division_event_count = 0

    def update(self, context: UpdateContext) -> None:
        # Cap max active population to prevent exponential explosive lag
        MAX_POPULATION = 350
        if len(self._entities_list) >= MAX_POPULATION:
            return

        for entity in list(self._entities_list):
            if not entity.is_alive:
                continue

            # Update reproduction cooldowns
            if entity.reproduction_cooldown > 0:
                entity.reproduction_cooldown -= 1
                continue

            # -------------------------------------------------------------
            # 1. Biological Bacteria Cell Division (True Binary Fission)
            # -------------------------------------------------------------
            if entity.entity_type == EntityType.BACTERIA:
                fiss_thresh = getattr(entity, "fission_energy_threshold", 60.0)
                if entity.is_mature and entity.energy >= fiss_thresh:
                    self.division_event_count += 1
                    
                    # Split energy and mass symmetrically between parent and daughter
                    half_energy = entity.energy * 0.50
                    entity.energy = half_energy
                    entity.reproduction_cooldown = 120  # cooldown before next fission

                    # Opposing flagella propulsion impulse
                    split_angle = random.uniform(0.0, 2.0 * math.pi)
                    impulse_speed = 3.5
                    entity.vel_x = math.cos(split_angle) * impulse_speed
                    entity.vel_y = math.sin(split_angle) * impulse_speed
                    entity.pos_x += entity.vel_x * 0.5
                    entity.pos_y += entity.vel_y * 0.5

                    # Daughter spawn coordinates in exact opposing vector
                    daughter_x = entity.pos_x - (math.cos(split_angle) * 3.0)
                    daughter_y = entity.pos_y - (math.sin(split_angle) * 3.0)

                    # Plasmid mutation & genetic drift
                    child_genome = entity.genome
                    if child_genome and hasattr(child_genome, "mutate_point"):
                        try:
                            child_genome = child_genome.clone()
                            child_genome.mutate_point(rate=0.15, magnitude=0.2)
                        except Exception:
                            pass

                    self._pending_births.append((
                        EntityType.BACTERIA,
                        (daughter_x, daughter_y),
                        (entity.entity_id,),
                        child_genome,
                    ))

            # -------------------------------------------------------------
            # 2. Plant Seed Dispersal & Flowering Germination
            # -------------------------------------------------------------
            elif entity.entity_type == EntityType.PLANT:
                seed_cost = getattr(entity, "seed_production_cost", 35.0)
                if entity.is_mature and entity.energy >= seed_cost:
                    entity.energy -= seed_cost
                    entity.reproduction_cooldown = 250  # ticks
                    if isinstance(entity, Plant):
                        entity.is_pollinated = False
                        spread = entity.seed_spread_radius
                    else:
                        spread = 20.0
                        
                    # Chaotic wind dispersal
                    wind_angle = random.uniform(0.0, 2.0 * math.pi)
                    dist = random.uniform(5.0, spread)
                    spawn_pos = (
                        entity.pos_x + math.cos(wind_angle) * dist,
                        entity.pos_y + math.sin(wind_angle) * dist,
                    )
                    self._pending_births.append((
                        EntityType.PLANT,
                        spawn_pos,
                        (entity.entity_id,),
                        entity.genome,
                    ))

            # -------------------------------------------------------------
            # 3. Animal & Sentient Reproduction (Sexual Pair Mating or Founder Budding)
            # -------------------------------------------------------------
            elif entity.is_mature:
                perceived = entity.custom_data.get("perceived_entities", [])
                
                # Check for compatible mature mates of the same species in proximity
                compatible_mates = [
                    other for other in perceived
                    if other.is_alive
                    and other.entity_type == entity.entity_type
                    and other.is_mature
                    and other.reproduction_cooldown <= 0
                    and other.entity_id != entity.entity_id
                ]

                # A. Sexual Pair Mating
                if compatible_mates and entity.energy >= (entity.max_energy * 0.40):
                    partner = compatible_mates[0]
                    energy_cost = entity.max_energy * 0.22
                    entity.energy -= energy_cost
                    partner.energy -= energy_cost
                    entity.reproduction_cooldown = 320
                    partner.reproduction_cooldown = 320

                    # Recombine genomes if available
                    child_genome = None
                    if entity.genome and partner.genome:
                        try:
                            from project.ai.genome import Genome
                            child_genome = Genome.crossover_uniform(entity.genome, partner.genome)
                        except Exception:
                            child_genome = entity.genome
                    else:
                        child_genome = entity.genome or partner.genome

                    spawn_pos = (
                        (entity.pos_x + partner.pos_x) / 2.0 + random.uniform(-4.0, 4.0),
                        (entity.pos_y + partner.pos_y) / 2.0 + random.uniform(-4.0, 4.0),
                    )
                    self._pending_births.append((
                        entity.entity_type,
                        spawn_pos,
                        (entity.entity_id, partner.entity_id),
                        child_genome,
                    ))

                # B. Lone Founder Parthenogenesis / Clan Propagation
                # If an organism has huge surplus energy and is mature, allow it to seed a lineage
                elif entity.energy >= (entity.max_energy * 0.70):
                    entity.energy -= (entity.max_energy * 0.30)
                    entity.reproduction_cooldown = 400
                    spawn_pos = (
                        entity.pos_x + random.uniform(-8.0, 8.0),
                        entity.pos_y + random.uniform(-8.0, 8.0),
                    )
                    self._pending_births.append((
                        entity.entity_type,
                        spawn_pos,
                        (entity.entity_id,),
                        entity.genome,
                    ))

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
