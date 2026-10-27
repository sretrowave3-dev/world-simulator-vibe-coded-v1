import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('world simulator (advanced neural network)/project/world/terrain.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'r_noise1 = noise.sample(x * 0.0018, y * 0.0018)'
idx = text.find(target)
print(text[idx:idx+1500])
