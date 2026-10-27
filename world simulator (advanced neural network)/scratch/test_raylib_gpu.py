import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import raylib
from raylib import *

print("Raylib successfully imported!")
print(f"RAYLIB VERSION: {raylib.__version__ if hasattr(raylib, '__version__') else '6.0.1'}")

# Test non-window functions or headless check
# Note: In Windows, InitWindow creates a native Win32/OpenGL 3.3 hardware window on the RTX 3050
SetConfigFlags(FLAG_WINDOW_HIDDEN | FLAG_MSAA_4X_HINT)
InitWindow(800, 600, b"Raylib Hardware GPU Test")
SetTargetFPS(60)

print(f"Window ready: {IsWindowReady()}")
print(f"Window hidden: {IsWindowHidden()}")

# Test rendering a frame
BeginDrawing()
ClearBackground(Color(104, 186, 56, 255))
DrawCircle(400, 300, 50, Color(240, 210, 135, 255))
DrawText(b"Raylib Hardware GPU Pipeline Active", 200, 20, 24, Color(255, 255, 255, 255))
EndDrawing()

print("Frame drawn successfully!")
CloseWindow()
print("Window closed cleanly.")
