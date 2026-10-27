"""
run.py

World Simulator Root Runner.
Launches the simulator directly from the workspace root.
"""
import os
import sys

# Ensure 'world simulator (advanced neural network)' is in sys.path
sim_dir = os.path.join(os.path.dirname(__file__), "world simulator (advanced neural network)")
if os.path.exists(sim_dir):
    sys.path.insert(0, os.path.abspath(sim_dir))
    os.chdir(sim_dir)

from run_gui import main

if __name__ == "__main__":
    main()
