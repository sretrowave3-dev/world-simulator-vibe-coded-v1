"""
project/systems/birth_system.py

Birth System instantiating queued offspring records into active simulation entity pools,
preserving neural network brain weights, genetic traits, and multi-species taxonomy.
"""

from __future__ import annotations

import random
from typing import Set, List, Tuple, Any, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.herbivore import Herbivore
from project.entities.carnivore import Carnivore
from project.entities.predator import Predator
from project.entities.omnivore import Omnivore
from project.entities.decomposer import Decomposer
from project.entities.human import Human
from project.entities.avian import Avian
from project.entities.amphibian import Amphibian
from project.entities.arthropod import Arthropod
from project.entities.reptile import Reptile
from project.entities.fungus import Fungus
from project.ai.brain import Brain


class BirthSystem:
    """Orchestrates entity spawns and inserts them into the loop with inherited neural brains."""

    def __init__(
        self,
        entities_list: List[Entity],
        pending_births: List[Tuple[EntityType, Tuple[float, float], Tuple[str, ...], Any]],
    ) -> None:
        self._entities_list = entities_list
        self._pending_births = pending_births
        self._next_id: int = 10000

    @property
    def name(self) -> str:
        return "BirthSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.REPRODUCTION + 1

    @property
    def dependencies(self) -> Set[str]:
        return {"ReproductionSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        # Create map for quick parent brain lookup
        parent_map = {e.entity_id: e for e in self._entities_list}

        for ent_type, pos, parents, genome in list(self._pending_births):
            eid = f"birth_{self._next_id}"
            self._next_id += 1

            x, y = pos
            child: Optional[Entity] = None

            # Calculate generation
            parent_gens = [parent_map[pid].generation for pid in parents if pid in parent_map]
            child_gen = (max(parent_gens) + 1) if parent_gens else 1

            # Inherit and mutate Neural Brain
            inherited_brain: Optional[Brain] = None
            for pid in parents:
                if pid in parent_map and parent_map[pid].brain is not None:
                    try:
                        p_brain = parent_map[pid].brain
                        inherited_brain = Brain(
                            input_size=p_brain.input_size,
                            hidden_sizes=p_brain.hidden_sizes,
                            output_size=p_brain.output_size,
                            activation=p_brain.activation,
                            working_memory_size=p_brain.working_memory_size,
                            learning_rate=p_brain.learning_rate,
                        )
                        weights_vec = p_brain.export_weights_to_vector()
                        mutated_vec = [w + random.gauss(0.0, 0.05) if random.random() < 0.1 else w for w in weights_vec]
                        inherited_brain.load_weights_from_vector(mutated_vec)
                        break
                    except Exception:
                        inherited_brain = Brain()

            # Spawn corresponding entity subclass
            if ent_type == EntityType.BACTERIA:
                child = Bacteria(entity_id=eid, species_id="bacteria", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.HERBIVORE:
                child = Herbivore(entity_id=eid, species_id="herbivore", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.CARNIVORE:
                child = Carnivore(entity_id=eid, species_id="carnivore", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.PREDATOR:
                child = Predator(entity_id=eid, species_id="predator", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.PLANT:
                child = Plant(entity_id=eid, species_id="plant", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, generation=child_gen)
            elif ent_type == EntityType.HUMAN:
                child = Human(entity_id=eid, species_id="human", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.OMNIVORE:
                child = Omnivore(entity_id=eid, species_id="omnivore", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.DECOMPOSER:
                child = Decomposer(entity_id=eid, species_id="decomposer", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.AVIAN:
                child = Avian(entity_id=eid, species_id="avian", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.AMPHIBIAN:
                child = Amphibian(entity_id=eid, species_id="amphibian", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.ARTHROPOD:
                child = Arthropod(entity_id=eid, species_id="arthropod", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.REPTILE:
                child = Reptile(entity_id=eid, species_id="reptile", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=inherited_brain, generation=child_gen)
            elif ent_type == EntityType.FUNGUS:
                child = Fungus(entity_id=eid, species_id="fungus", pos_x=x, pos_y=y, parent_ids=parents, genome=genome, generation=child_gen)

            if child is not None:
                child.birth_tick = context.tick
                self._entities_list.append(child)

        self._pending_births.clear()

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
