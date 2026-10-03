import os, sys
sys.path.append(os.path.abspath(os.getcwd()))
from project.renderer.renderer import SimulationRenderer

# Create renderer
renderer = SimulationRenderer(width=800, height=600, world_width=2048, world_height=2048)

# Mock data
snapshot = []
class MockTerrain:
    def get_tile(self, x, y):
        class Tile:
            pass
        t = Tile()
        t.height = 0.5
        t.biome = 'FOREST'
        return t
mock_terrain = MockTerrain()
class MockPheromoneGrid:
    pass
pheromone_grid = MockPheromoneGrid()
renderer.render(entities_snapshot=snapshot, terrain_manager=mock_terrain, pheromone_grid=pheromone_grid, system_timings={}, sim_tick=0, stats_history=None)
print('Render called successfully')
