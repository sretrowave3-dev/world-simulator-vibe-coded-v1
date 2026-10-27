target_file = r"C:\Users\hp\Documents\codes\world sim\world-simulator-vibe-coded-v1\world simulator (advanced neural network)\project\renderer\renderer.py"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

old_close = "def close(self) -> None:\n        pygame.quit()"
new_close = "def close(self) -> None:\n        if hasattr(self, \"overlays\") and hasattr(self.overlays, \"close\"):\n            self.overlays.close()\n        pygame.quit()"

if old_close in content:
    content = content.replace(old_close, new_close)
    print("Updated close() (LF)")
else:
    old_close_crlf = old_close.replace("\n", "\r\n")
    new_close_crlf = new_close.replace("\n", "\r\n")
    if old_close_crlf in content:
        content = content.replace(old_close_crlf, new_close_crlf)
        print("Updated close() (CRLF)")
    else:
        print("Could not find old_close")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Saved renderer.py")
