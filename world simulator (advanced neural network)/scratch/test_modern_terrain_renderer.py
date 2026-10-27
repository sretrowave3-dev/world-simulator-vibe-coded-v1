import pygame
import time
import math
import queue
import threading
import os
import sys

sys.path.insert(0, 'world simulator (advanced neural network)')
from project.world.terrain import TerrainManager
from project.renderer.texture_baker import ensure_baked_textures

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
tm = TerrainManager(seed=42)
textures = ensure_baked_textures()

print("Loaded textures:", list(textures.keys()))
