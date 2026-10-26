"""
project/core/auto_debugger.py

Parallel Auto-Debugger and Watchdog Thread with safe UTF-8 output encoding.
"""

import sys
import threading
import time
import traceback
import json
from typing import Any, Dict

# Safe UTF-8 reconfiguration for Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class AutoDebugger:
    """
    Parallel Auto-Debugger and Watchdog Thread.
    Monitors global exceptions and system health, automatically dumping crash logs.
    """
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.crash_logs = []
        self._lock = threading.Lock()

    def start(self):
        # Override global exception hook
        sys.excepthook = self.global_exception_handler
        self.thread.start()
        try:
            print("[AUTO-DEBUGGER] Parallel Watchdog & Crash Handler ACTIVE.")
        except Exception:
            pass

    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        with self._lock:
            crash_info = {
                "timestamp": time.time(),
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
            }
            self.crash_logs.append(crash_info)
            try:
                print(f"\n[AUTO-DEBUGGER] Intercepted Critical Crash: {exc_type.__name__} - {exc_value}")
            except Exception:
                pass
            self.dump_logs()
            try:
                from project.core.telemetry_dispatcher import telemetry_dispatcher
                telemetry_dispatcher.record_crash(
                    exc_type=exc_type.__name__,
                    exc_message=str(exc_value),
                    stack_trace="".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                )
            except Exception:
                pass

    def _watchdog_loop(self):
        while self.running:
            time.sleep(10.0)

    def dump_logs(self):
        try:
            with open("auto_debugger_crash_dump.json", "w", encoding="utf-8") as f:
                json.dump(self.crash_logs, f, indent=4)
            print("[AUTO-DEBUGGER] Crash state exported to auto_debugger_crash_dump.json")
        except Exception:
            pass

    def stop(self):
        self.running = False


debugger = AutoDebugger()
