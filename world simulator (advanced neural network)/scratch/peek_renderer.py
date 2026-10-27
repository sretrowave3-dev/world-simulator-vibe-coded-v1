import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('world simulator (advanced neural network)/project/renderer/renderer.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'clock.tick'
idx = text.find(target)
if idx != -1:
    print(text[idx-100:idx+300])
else:
    print("clock.tick not found in renderer.py")
