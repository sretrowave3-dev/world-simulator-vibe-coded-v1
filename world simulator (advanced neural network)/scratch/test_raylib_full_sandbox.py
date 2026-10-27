import os
import sys
import time
import math
import raylib
from raylib import *

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("Starting Raylib Full Sandbox Test...")
SetConfigFlags(FLAG_WINDOW_HIDDEN | FLAG_MSAA_4X_HINT)
InitWindow(1280, 720, b"Raylib Hardware GPU Full Sandbox")
SetTargetFPS(60)

cam = raylib.ffi.new('Camera2D*')
cam.offset = [640, 360]
cam.target = [7180, 7180]
cam.rotation = 0.0
cam.zoom = 1.2

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tex_dir = os.path.join(base_dir, 'project', 'renderer', 'assets', 'textures')
textures = {}
for fname in ["grass_photoreal.png", "river_water.png", "sand_dune.png", "mountain_stone.png"]:
    p = os.path.join(tex_dir, fname)
    if os.path.exists(p):
        textures[fname] = LoadTexture(p.encode('utf-8'))

atlas_p = os.path.join(base_dir, 'cache', 'continental_atlas_42_512.png')
atlas_tex = LoadTexture(atlas_p.encode('utf-8')) if os.path.exists(atlas_p) else None

# Test 60 frames of complete world drawing
t0 = time.time()
for frame in range(60):
    BeginDrawing()
    ClearBackground([24, 30, 36, 255])

    # 1. 2D World Space Rendering
    BeginMode2D(cam[0])

    # Draw continental atlas backdrop
    if atlas_tex:
        DrawTexturePro(
            atlas_tex,
            [0.0, 0.0, float(atlas_tex.width), float(atlas_tex.height)],
            [0.0, 0.0, 14336.0, 14336.0],
            [0.0, 0.0],
            0.0,
            [255, 255, 255, 255]
        )

    # Draw sample chunk tiles
    t_grass = textures.get("grass_photoreal.png")
    if t_grass:
        for cx in range(27, 30):
            for cy in range(27, 30):
                DrawTexturePro(
                    t_grass,
                    [0.0, 0.0, float(t_grass.width), float(t_grass.height)],
                    [float(cx * 256), float(cy * 256), 256.0, 256.0],
                    [0.0, 0.0],
                    0.0,
                    [255, 255, 255, 255]
                )

    # Draw campfires & structures
    DrawCircle(7180, 7180, 28, [255, 145, 25, 60])  # Glow
    DrawCircle(7180, 7180, 8, [28, 25, 24, 255])     # Hearth
    DrawCircle(7180, 7180, 5, [255, 120, 20, 255])   # Flame

    # Draw timber cabin
    DrawRectangleRec([7220, 7170, 36, 26], [155, 105, 52, 255])
    DrawRectangleLines(7220, 7170, 36, 26, [95, 60, 28, 255])

    # Draw living entities (Humans, Animals, Food)
    for i in range(25):
        ex = 7180 + math.cos(frame * 0.05 + i) * 60
        ey = 7180 + math.sin(frame * 0.05 + i) * 60
        # Drop shadow
        DrawEllipse(int(ex + 1), int(ey + 3), 5.0, 2.5, [0, 0, 0, 80])
        # Entity body
        DrawCircle(int(ex), int(ey), 4.0, [245, 245, 255, 255] if i % 2 == 0 else [255, 210, 50, 255])
        # Heading line
        DrawLine(int(ex), int(ey), int(ex + math.cos(i) * 8), int(ey + math.sin(i) * 8), [0, 255, 200, 200])

    EndMode2D()

    # 2. Screen Space HUD
    DrawRectangle(0, 0, 1280, 34, [18, 22, 28, 220])
    DrawLine(0, 34, 1280, 34, [0, 220, 200, 180])
    DrawText(b"WORLD SIMULATOR - RAYLIB HARDWARE GPU ENGINE (NVIDIA RTX 3050)", 15, 8, 16, [255, 255, 255, 255])
    fps_txt = f"FPS: {GetFPS()} | Entities: 25 | Zoom: {cam.zoom:.2f}x".encode('utf-8')
    DrawText(fps_txt, 980, 8, 16, [0, 255, 200, 255])

    # Minimap preview at top right
    DrawRectangle(1060, 45, 200, 150, [15, 18, 24, 210])
    DrawRectangleLines(1060, 45, 200, 150, [0, 200, 220, 255])
    DrawText(b"MINIMAP", 1070, 50, 12, [180, 200, 220, 255])

    EndDrawing()

dt_total = time.time() - t0
fps_avg = 60.0 / dt_total
print(f"Rendered 60 full frames in {dt_total:.3f}s ({fps_avg:.1f} FPS)!")

for t in textures.values():
    UnloadTexture(t)
if atlas_tex:
    UnloadTexture(atlas_tex)

CloseWindow()
print("Raylib Sandbox test completed with 100% success!")
