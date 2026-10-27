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
from project.renderer.camera import Camera

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
screen = pygame.display.set_mode((1280, 720))

tm = TerrainManager(seed=42)
textures = ensure_baked_textures()
camera = Camera(screen_width=1280, screen_height=720)
camera.pos_x = 7168.0
camera.pos_y = 7168.0

print("Initialized test environment successfully.")
