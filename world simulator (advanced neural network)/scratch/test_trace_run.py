import subprocess
import sys

cmd = [sys.executable, "-u", "run_gui.py"]
p = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd="world simulator (advanced neural network)",
    text=True,
    encoding="utf-8",
    errors="replace"
)

try:
    stdout, _ = p.communicate(input="2\nexit\n", timeout=12)
    with open(r"world simulator (advanced neural network)\scratch\run_gui_output.txt", "w", encoding="utf-8") as f:
        f.write(stdout)
    print("Communication finished successfully! Output length:", len(stdout))
except subprocess.TimeoutExpired:
    p.kill()
    stdout, _ = p.communicate()
    with open(r"world simulator (advanced neural network)\scratch\run_gui_output.txt", "w", encoding="utf-8") as f:
        f.write(stdout)
    print("Communication timed out! Output length:", len(stdout))
