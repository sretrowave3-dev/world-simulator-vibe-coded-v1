import subprocess
import sys
import time

cmd = [sys.executable, "run_gui.py"]
p = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="world simulator (advanced neural network)",
    text=True,
    encoding="utf-8",
    errors="replace",
    bufsize=1
)

# Send option 2
p.stdin.write("2\n")
p.stdin.flush()

time.sleep(3)

# Send 'adv dev'
p.stdin.write("adv dev\n")
p.stdin.flush()

time.sleep(2)

# Send 'exit'
p.stdin.write("exit\n")
p.stdin.flush()

try:
    stdout, stderr = p.communicate(timeout=10)
    print("STDOUT:")
    print(stdout[-1500:] if len(stdout) > 1500 else stdout)
    if stderr:
        print("STDERR:")
        print(stderr[-1000:] if len(stderr) > 1000 else stderr)
except subprocess.TimeoutExpired:
    p.kill()
    stdout, stderr = p.communicate()
    print("Timed out, killed. STDOUT:")
    print(stdout[-1500:] if len(stdout) > 1500 else stdout)
    if stderr:
        print("STDERR:")
        print(stderr[-1000:] if len(stderr) > 1000 else stderr)
