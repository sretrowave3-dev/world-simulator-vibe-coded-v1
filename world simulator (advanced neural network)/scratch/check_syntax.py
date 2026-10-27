import re

path = r"world simulator (advanced neural network)\project\renderer\raylib_renderer.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

matches = re.finditer(r'b(["\'])(.*?)\1', text)
bad = []
for m in matches:
    content = m.group(2)
    if any(ord(c) > 127 for c in content):
        bad.append((m.group(0), content))

print(f"Total non-ASCII byte strings found: {len(bad)}")
for full, s in bad:
    print(f"  {ascii(full)}")
