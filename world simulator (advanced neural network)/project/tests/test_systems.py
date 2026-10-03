"""
tests/test_systems.py

Integration and execution tests for the Phase 4 Systems suite.
"""

import unittest
from project.core.scheduler import Scheduler, SchedulerPhase, UpdateContext
from project.world.time import WorldTimeManager
from project.world.weather import WeatherManager, AtmosphericGrid, ChunkData as WeatherChunk
from project.world.disasters import DisasterManager
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager
from project.world.food import FoodManager
from project.utils.spatial_hash import SpatialHashGrid
from project.ai.pheromone import PheromoneGrid
from project.entities.entity import Entity, EntityType
from project.entities.bacteria import Bacteria
from project.entities.herbivore import Herbivore
from project.entities.predator import Predator
from project.entities.human import Human

# Import all systems
from project.systems import (
    TimeSystem,
    WeatherSystem,
    WeatherSyncSystem,
    DisasterSystem,
    SoilSystem,
    WaterSystem,
    VegetationSystem,
    ResourceSystem,
    FoodSystem,
    PerceptionSystem,
    DecisionSystem,
    PheromoneSystem,
    MovementSystem,
    CombatSystem,
    DigestionSystem,
    AgingSystem,
    DeathSystem,
    ReproductionSystem,
    BirthSystem,
    MutationSystem,
    LearningSystem,
    GeminiSystem,
    SocialSystem,
    CivilizationSystem,
    KnowledgeSystem,
    EventSystem,
    StatisticsSystem,
    RenderSyncSystem,
    SaveSystem,
)


class TestSystemsSubsystem(unittest.TestCase):

    def test_systems_scheduling_and_execution(self):
        # 1. Instantiate world coordinators
        time_mgr = WorldTimeManager()
        weather_grid = AtmosphericGrid([WeatherChunk(0, 45.0, -73.0, 10.0)])
        weather_mgr = WeatherManager(weather_grid)
        disaster_mgr = DisasterManager()
        soil_mgr = SoilManager()
        water_mgr = WaterManager()
        veg_mgr = VegetationManager()
        res_mgr = ResourceManager()
        food_mgr = FoodManager()
        spatial_grid = SpatialHashGrid[Entity](cell_size=16.0)
        pheromone_grid = PheromoneGrid()

        # 2. Instantiate entity arrays
        entities_list: List[Entity] = []
        pending_births = []

        # Add initial entities
        entities_list.append(Bacteria(entity_id="b_1", species_id="bac", pos_x=5.0, pos_y=5.0))
        entities_list.append(Herbivore(entity_id="h_1", species_id="herb", pos_x=10.0, pos_y=10.0))
        entities_list.append(Predator(entity_id="p_1", species_id="pred", pos_x=12.0, pos_y=10.0))
        entities_list.append(Human(entity_id="hum_1", species_id="hum", pos_x=15.0, pos_y=15.0))

        # 3. Instantiate Scheduler and Systems
        scheduler = Scheduler(world_reference=None, target_ups=60)

        # Register all 29 systems
        scheduler.register_system(TimeSystem(time_mgr))
        scheduler.register_system(WeatherSystem(weather_mgr))
        scheduler.register_system(WeatherSyncSystem(weather_mgr))
        scheduler.register_system(DisasterSystem(disaster_mgr, entities_list))
        scheduler.register_system(SoilSystem(soil_mgr))
        scheduler.register_system(WaterSystem(water_mgr))
        scheduler.register_system(VegetationSystem(veg_mgr, soil_mgr))
        scheduler.register_system(ResourceSystem(res_mgr))
        scheduler.register_system(FoodSystem(food_mgr))
        scheduler.register_system(PerceptionSystem(spatial_grid, entities_list))
        scheduler.register_system(DecisionSystem(entities_list))
        scheduler.register_system(PheromoneSystem(pheromone_grid, entities_list))
        scheduler.register_system(MovementSystem(entities_list))
        scheduler.register_system(CombatSystem(entities_list))
        scheduler.register_system(DigestionSystem(entities_list, veg_mgr, water_mgr))
        scheduler.register_system(AgingSystem(entities_list))
        scheduler.register_system(DeathSystem(entities_list, soil_mgr))
        scheduler.register_system(ReproductionSystem(entities_list, pending_births))
        scheduler.register_system(BirthSystem(entities_list, pending_births))
        scheduler.register_system(MutationSystem(entities_list, disaster_mgr))
        scheduler.register_system(LearningSystem(entities_list))
        scheduler.register_system(GeminiSystem(entities_list))
        scheduler.register_system(SocialSystem(entities_list))
        scheduler.register_system(CivilizationSystem(entities_list))
        scheduler.register_system(KnowledgeSystem(entities_list))
        scheduler.register_system(EventSystem())
        scheduler.register_system(StatisticsSystem(entities_list))
        scheduler.register_system(RenderSyncSystem(entities_list))
        scheduler.register_system(SaveSystem(entities_list))

        # 4. Initialize and run 5 scheduler updates
        scheduler.initialize()
        self.assertEqual(scheduler.state.name, "RUNNING")

        for _ in range(5):
            scheduler.update()

        # Check ticks progressed
        self.assertEqual(time_mgr.current_tick, 5)

        # Check movement system changed position of entities
        h1 = [e for e in entities_list if e.entity_id == "h_1"][0]
        self.assertNotEqual((h1.pos_x, h1.pos_y), (10.0, 10.0))

        scheduler.shutdown()
        self.assertEqual(scheduler.state.name, "STOPPED")


if __name__ == "__main__":
    unittest.main()
