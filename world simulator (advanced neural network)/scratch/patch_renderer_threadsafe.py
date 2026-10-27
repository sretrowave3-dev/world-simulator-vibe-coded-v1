import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base_dir, "project", "renderer", "renderer.py")

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

target = "structures_snapshot=list(world_settlement_mgr.structures.values())"
replacement = "structures_snapshot=world_settlement_mgr.get_all_structures_snapshot() if hasattr(world_settlement_mgr, 'get_all_structures_snapshot') else list(world_settlement_mgr.structures.values())"

if target in text:
    text = text.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated renderer.py with thread safety!")
else:
    print("Target not found in renderer.py")
