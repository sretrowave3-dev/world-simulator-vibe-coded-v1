import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('world simulator (advanced neural network)/project/renderer/overlays.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'def draw_terrain_grid('
idx = text.find(target)
target_end = 'def draw_structures('
idx2 = text.find(target_end)
print(text[idx:idx2])
