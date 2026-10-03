"""
tests/test_simulation.py

Unit and integration tests for Core Scheduler, Simulation Clock, Entities, and Spatial Hash.
"""

import unittest
from project.core.scheduler import (
    Scheduler,
    SchedulerPhase,
    ExecutionPriority,
    UpdateContext,
)
from project.core.simulation import Simulation, SimulationClock, SimulationState
from project.entities.entity import Entity, EntityType
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.herbivore import Herbivore
from project.entities.predator import Predator
from project.entities.human import Human
from project.entities.species import SpeciesRegistry
from project.utils.spatial_hash import SpatialHashGrid
from project.utils.math_utils import vec2_distance, vec2_normalize


class MockSystem:
    def __init__(self, name: str, phase: SchedulerPhase, priority: int, deps: set = None) -> None:
        self._name = name
        self._phase = phase
        self._priority = priority
        self._deps = deps or set()
        self.tick_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def phase(self) -> SchedulerPhase:
        return self._phase

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def dependencies(self) -> set:
        return self._deps

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def update(self, context: UpdateContext) -> None:
        self.tick_count += 1

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass


class TestCoreAndEntities(unittest.TestCase):

    def test_spatial_hash_grid(self):
        grid = SpatialHashGrid[str](cell_size=16.0)
        grid.insert("agent_1", x=10.0, y=10.0)
        grid.insert("agent_2", x=12.0, y=10.0)
        grid.insert("agent_3", x=100.0, y=100.0)

        self.assertEqual(grid.count, 3)

        # Query radius around (10, 10)
        positions = {"agent_1": (10.0, 10.0), "agent_2": (12.0, 10.0), "agent_3": (100.0, 100.0)}
        nearby = grid.query_radius(10.0, 10.0, radius=5.0, position_getter=lambda a: positions[a])
        self.assertEqual(len(nearby), 2)
        self.assertIn("agent_1", nearby)
        self.assertIn("agent_2", nearby)

        # Update position
        grid.update_position("agent_1", x=105.0, y=105.0)
        positions["agent_1"] = (105.0, 105.0)

        nearby_after = grid.query_radius(10.0, 10.0, radius=5.0, position_getter=lambda a: positions[a])
        self.assertEqual(len(nearby_after), 1)
        self.assertIn("agent_2", nearby_after)

    def test_scheduler_pipeline(self):
        scheduler = Scheduler(world_reference=None, target_ups=60)

        sys_weather = MockSystem("WeatherSys", SchedulerPhase.WORLD, ExecutionPriority.WEATHER)
        sys_perception = MockSystem("PerceptionSys", SchedulerPhase.AI, ExecutionPriority.PERCEPTION, deps={"WeatherSys"})

        scheduler.register_system(sys_weather)
        scheduler.register_system(sys_perception)

        scheduler.initialize()
        self.assertEqual(scheduler.state.name, "RUNNING")

        # Execute single tick
        scheduler.update()
        self.assertEqual(sys_weather.tick_count, 1)
        self.assertEqual(sys_perception.tick_count, 1)

        scheduler.shutdown()
        self.assertEqual(scheduler.state.name, "STOPPED")

    def test_entity_hierarchy_and_vitality(self):
        species_reg = SpeciesRegistry()
        spec = species_reg.register_species("Canis lupus", founding_tick=0)

        predator = Predator(
            entity_id="pred_1",
            species_id=spec.species_id,
            pos_x=10.0,
            pos_y=20.0,
        )

        self.assertEqual(predator.entity_type, EntityType.PREDATOR)
        self.assertAlmostEqual(predator.health, 250.0, delta=25.0)
        self.assertTrue(predator.is_alive)

        # Apply damage
        init_health = predator.health
        predator.take_damage(50.0)
        self.assertAlmostEqual(predator.health, init_health - 50.0)

        # Fatal damage
        predator.take_damage(300.0, reason="COMBAT")
        self.assertFalse(predator.is_alive)
        self.assertEqual(predator.cause_of_death, "COMBAT")

    def test_human_inventory(self):
        human = Human(entity_id="h_1", species_id="homo_sapiens")
        self.assertEqual(human.inventory_weight, 0.0)

        added = human.add_to_inventory("Wood", 15.0)
        self.assertTrue(added)
        self.assertEqual(human.inventory_weight, 15.0)

        # Exceed capacity
        failed = human.add_to_inventory("HeavyStone", 100.0)
        self.assertFalse(failed)


if __name__ == "__main__":
    unittest.main()
