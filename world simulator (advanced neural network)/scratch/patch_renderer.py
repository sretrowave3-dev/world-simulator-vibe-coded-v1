import os

target_file = r"C:\Users\hp\Documents\codes\world sim\world-simulator-vibe-coded-v1\world simulator (advanced neural network)\project\renderer\renderer.py"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update draw_terrain call to pass sim_tick
old_terrain_call = "self.overlays.draw_terrain(\n            self.screen, self.camera, terrain_manager, self.checkboxes[0].checked, self.world_width, self.world_height\n        )"
new_terrain_call = "self.overlays.draw_terrain(\n            self.screen, self.camera, terrain_manager, self.checkboxes[0].checked, self.world_width, self.world_height, sim_tick\n        )"

if old_terrain_call in content:
    content = content.replace(old_terrain_call, new_terrain_call)
    print("Updated draw_terrain call!")
else:
    # Try CRLF
    old_terrain_call_crlf = old_terrain_call.replace("\n", "\r\n")
    new_terrain_call_crlf = new_terrain_call.replace("\n", "\r\n")
    if old_terrain_call_crlf in content:
        content = content.replace(old_terrain_call_crlf, new_terrain_call_crlf)
        print("Updated draw_terrain call (CRLF)!")
    else:
        print("Could not find draw_terrain call")

# 2. Add directional shadow computation right before entity loop
old_entity_head = "# 4. Draw entities with multi-species color palette & fast frustum culling"
new_entity_head = """# 4. Compute directional sunlight shadow projection vectors for entities and structures
        sun_frac = sun_props.get("day_fraction", 0.5) if sun_props else 0.5
        sun_df = sun_props.get("daylight_factor", 1.0) if sun_props else 1.0
        sun_angle = (sun_frac - 0.5) * math.pi
        sun_shadow_dx = int(math.sin(sun_angle) * (1.2 - sun_df * 0.4) * 6.0 * zoom)
        sun_shadow_dy = int(math.cos(sun_angle) * 3.0 * zoom + 3.0 * zoom)

        # Draw entities with multi-species color palette & fast frustum culling"""

if old_entity_head in content:
    content = content.replace(old_entity_head, new_entity_head)
    print("Added directional shadow vector computation!")
else:
    print("Could not find entity loop header")

# 3. Update shadow ellipses for Human, Predator, and Herbivore
content = content.replace(
    "pygame.draw.ellipse(self.screen, (0, 0, 0, 75), (sx - hr, sy + hr // 3, hr * 2, max(3, hr // 2)))",
    "pygame.draw.ellipse(self.screen, (0, 0, 0, 75), (sx - hr + sun_shadow_dx, sy + hr // 3 + sun_shadow_dy, hr * 2, max(3, hr // 2)))"
)
content = content.replace(
    "pygame.draw.ellipse(self.screen, (0, 0, 0, 80), (sx - pr, sy + pr // 3, pr * 2, max(3, pr // 2)))",
    "pygame.draw.ellipse(self.screen, (0, 0, 0, 80), (sx - pr + sun_shadow_dx, sy + pr // 3 + sun_shadow_dy, pr * 2, max(3, pr // 2)))"
)
content = content.replace(
    "pygame.draw.ellipse(self.screen, (0, 0, 0, 70), (sx - hr_sz, sy + hr_sz // 3, hr_sz * 2, max(3, hr_sz // 2)))",
    "pygame.draw.ellipse(self.screen, (0, 0, 0, 70), (sx - hr_sz + sun_shadow_dx, sy + hr_sz // 3 + sun_shadow_dy, hr_sz * 2, max(3, hr_sz // 2)))"
)

# 4. Update display.flip and GPU safety enforcement at end of render()
old_flip = """        pygame.display.flip()
        self.clock.tick(60)
        # Cooperative sleep to yield CPU slice to OS (drops idle/render CPU from 100% to < 15%)
        time.sleep(0.001)"""

new_flip = """        # Cinematic Atmospheric Vignette
        self.overlays.draw_vignette(self.screen)

        pygame.display.flip()
        # Enforce Dedicated GPU & CPU safety (60 FPS clamp, thermal throttling, OS cooperative yield)
        from project.core.gpu_manager import gpu_mgr
        gpu_mgr.enforce_frame_safety(self.clock)
        vram_est = (len(self.overlays._chunk_cache) * 32 * 32 * 4 + len(self.overlays._scaled_chunk_cache) * 128 * 128 * 4) / (1024 * 1024)
        gpu_mgr.update_vram_usage(vram_est)"""

if old_flip in content:
    content = content.replace(old_flip, new_flip)
    print("Updated flip and gpu safety!")
else:
    old_flip_crlf = old_flip.replace("\n", "\r\n")
    new_flip_crlf = new_flip.replace("\n", "\r\n")
    if old_flip_crlf in content:
        content = content.replace(old_flip_crlf, new_flip_crlf)
        print("Updated flip and gpu safety (CRLF)!")
    else:
        print("Could not find old_flip")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Saved updated renderer.py!")
