import pygame
import time
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.renderer.renderer import SimulationRenderer
from project.civilization.settlement import world_settlement_mgr

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
renderer = SimulationRenderer(width=1280, height=720, world_width=14336.0, world_height=14336.0)

t0 = time.perf_counter()
renderer.overlays.draw_structures(renderer.screen, renderer.camera, sim_tick=10)
t1 = time.perf_counter()
print(f"Call 1: {(t1 - t0)*1000.0:.2f} ms")

t2 = time.perf_counter()
renderer.overlays.draw_structures(renderer.screen, renderer.camera, sim_tick=10)
t3 = time.perf_counter()
print(f"Call 2: {(t3 - t2)*1000.0:.2f} ms")

renderer.close()
