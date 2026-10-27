"""
project/main.py

Main launcher redirecting to run_gui.py.
"""
from __future__ import annotations
import os
import sys

# Ensure root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from run_gui import main

if __name__ == "__main__":
    main()
