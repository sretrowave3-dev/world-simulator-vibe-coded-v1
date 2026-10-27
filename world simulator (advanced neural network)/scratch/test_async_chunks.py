import pygame
import time
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

class AsyncChunkManager:
    def __init__(self, tm, textures):
        self.tm = tm
        self.textures = textures
        self.cache = {}
        self.queue = queue.Queue()
        self.in_progress = set()
        self.lock = threading.Lock()
        self.running = True
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def _worker_loop(self):
        while self.running:
            try:
                cx, cy = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            surf, has_r = self._generate_chunk(cx, cy)
            with self.lock:
                self.cache[(cx, cy)] = surf
                self.in_progress.discard((cx, cy))
            self.queue.task_done()

    def _generate_chunk(self, cx, cy, res=16):
        surf = pygame.Surface((res, res))
        surf.blit(pygame.transform.smoothscale(self.textures["grass_photoreal"], (res, res)), (0, 0))
        m_step = 256.0 / res
        has_river = False
        river_mask = pygame.Surface((res, res), pygame.SRCALPHA)
        for px in range(res):
            wx = cx * 256.0 + px * m_step
            for py in range(res):
                wy = cy * 256.0 + py * m_step
                h, w_str, b_type = self.tm.sample_surface_point(wx, wy)
                if "RIVER" in w_str:
                    has_river = True
                    river_mask.set_at((px, py), (255, 255, 255, 255))
        if has_river:
            water_layer = pygame.transform.smoothscale(self.textures["river_water"], (res, res)).copy()
            water_layer.blit(river_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(water_layer, (0, 0))
        return surf, has_river

    def get_chunk(self, cx, cy):
        with self.lock:
            if (cx, cy) in self.cache:
                return self.cache[(cx, cy)]
            if (cx, cy) not in self.in_progress:
                self.in_progress.add((cx, cy))
                self.queue.put((cx, cy))
            return None

acm = AsyncChunkManager(tm, textures)
print("AsyncChunkManager initialized.")
# Request 50 chunks
for i in range(50):
    c = acm.get_chunk(10 + i % 10, 10 + i // 10)
print("Submitted 50 chunks without stalling main thread!")
time.sleep(0.3)
with acm.lock:
    print(f"Chunks completed in background in 300ms: {len(acm.cache)} / 50")
acm.running = False
