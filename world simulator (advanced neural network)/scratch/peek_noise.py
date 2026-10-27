import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('world simulator (advanced neural network)/project/world/terrain.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class NoiseGenerator')
if idx == -1:
    idx = text.find('noise = ')
print(text[idx-50:idx+800])
