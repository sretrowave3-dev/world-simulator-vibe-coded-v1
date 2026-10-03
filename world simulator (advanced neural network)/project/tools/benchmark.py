import cProfile
import pstats
import io
import time

from project.core.scheduler import Scheduler
from project.entities.bacteria import Bacteria
from project.world.terrain import TerrainManager
from project.world.weather import WeatherManager, AtmosphericGrid
from project.world.disasters import DisasterManager
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager
from project.world.food import FoodManager
from project.utils.spatial_hash import SpatialHashGrid

from project.systems import (
    MovementSystem,
    PerceptionSystem,
    DecisionSystem,
    CombatSystem,
    DigestionSystem,
    AgingSystem,
)

def run_benchmark():
    entities = [Bacteria(f"bac_{i}", "chemophile", 1000, 1000) for i in range(1000)]
    
    spatial_grid = SpatialHashGrid(cell_size=16.0)
    veg_mgr = VegetationManager()
    water_mgr = WaterManager()
    
    scheduler = Scheduler(None)
    scheduler.register_system(PerceptionSystem(spatial_grid, entities))
    scheduler.register_system(DecisionSystem(entities))
    scheduler.register_system(MovementSystem(entities, 2048, 2048))
    scheduler.register_system(CombatSystem(entities))
    scheduler.register_system(DigestionSystem(entities, veg_mgr, water_mgr))
    scheduler.register_system(AgingSystem(entities))
    
    scheduler.initialize()
    
    print("Starting benchmark of 100 ticks for 1000 entities...")
    start_time = time.perf_counter()
    
    pr = cProfile.Profile()
    pr.enable()
    
    for _ in range(100):
        scheduler.update()
        
    pr.disable()
    end_time = time.perf_counter()
    
    print(f"Completed 100 ticks in {end_time - start_time:.4f} seconds.")
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
    ps.print_stats(20)
    print(s.getvalue())

if __name__ == "__main__":
    run_benchmark()
