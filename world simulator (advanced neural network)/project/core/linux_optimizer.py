"""
project/core/linux_optimizer.py

Linux Platform Optimization and Hardware Telemetry Subsystem.
Provides deep Linux-native capabilities:
- CPU core pinning and thread affinity (os.sched_setaffinity).
- POSIX thread naming (prctl PR_SET_NAME) for profiling with htop/perf/sysprof.
- GLIBC heap compaction and arena release (libc.malloc_trim).
- High-speed RAM cache bridge (/dev/shm tmpfs).
- POSIX kernel page cache advising (os.posix_fadvise).
- High-resolution process memory metrics via /proc/self/status.
"""

from __future__ import annotations

import os
import sys
import time
import ctypes
import ctypes.util
from typing import Any, Dict, List, Optional, Set, Tuple


# PR_SET_NAME constant for prctl on Linux
PR_SET_NAME = 15


class LinuxPlatformOptimizer:
    """
    Singleton controller managing Linux-specific kernel optimizations,
    thread affinities, memory trimming, and hardware telemetry.
    """

    _instance: Optional[LinuxPlatformOptimizer] = None
    _libc: Optional[ctypes.CDLL] = None
    _libc_loaded: bool = False

    def __new__(cls) -> LinuxPlatformOptimizer:
        if cls._instance is None:
            cls._instance = super(LinuxPlatformOptimizer, cls).__new__(cls)
            cls._instance._init_optimizer()
        return cls._instance

    def _init_optimizer(self) -> None:
        self.is_linux: bool = sys.platform.startswith("linux")
        self.total_cores: int = os.cpu_count() or 1
        self.allocated_cores: List[int] = list(range(self.total_cores))
        self.last_trim_timestamp: float = 0.0
        self.trim_count: int = 0
        self.trimmed_bytes_est: int = 0
        
        # Load libc for Linux-native system calls
        self._load_libc()

        if self.is_linux and hasattr(os, "sched_getaffinity"):
            try:
                self.allocated_cores = sorted(list(os.sched_getaffinity(0)))
            except Exception:
                pass

    def _load_libc(self) -> None:
        if not self.is_linux or self._libc_loaded:
            return
        
        self._libc_loaded = True
        candidates = ["libc.so.6", ctypes.util.find_library("c"), "libc.so"]
        for c in candidates:
            if not c:
                continue
            try:
                self._libc = ctypes.CDLL(c)
                break
            except Exception:
                continue

    def set_thread_name(self, name: str) -> bool:
        """
        Sets the calling thread's name in Linux task table (visible in htop/top/perf).
        Name is truncated to 15 chars + null terminator per Linux PR_SET_NAME spec.
        """
        if not self.is_linux or not self._libc:
            return False

        try:
            name_bytes = name[:15].encode("utf-8")
            # prctl(PR_SET_NAME, unsigned long arg2, ...)
            if hasattr(self._libc, "prctl"):
                self._libc.prctl(PR_SET_NAME, ctypes.c_char_p(name_bytes), 0, 0, 0)
                return True
        except Exception:
            pass
        return False

    def set_thread_affinity(self, core_ids: List[int]) -> bool:
        """
        Pins calling thread or process to specified CPU core IDs.
        Prevents thread migration and cache invalidation.
        """
        if not self.is_linux or not hasattr(os, "sched_setaffinity"):
            return False

        try:
            valid_cores = set(core_ids).intersection(set(range(self.total_cores)))
            if valid_cores:
                os.sched_setaffinity(0, valid_cores)
                return True
        except Exception:
            pass
        return False

    def get_affinity(self) -> List[int]:
        """Returns currently assigned CPU cores for the calling thread."""
        if self.is_linux and hasattr(os, "sched_getaffinity"):
            try:
                return sorted(list(os.sched_getaffinity(0)))
            except Exception:
                pass
        return list(range(self.total_cores))

    def set_process_priority(self, nice_increment: int = -2) -> bool:
        """
        Adjusts process priority (niceness).
        Negative nice gives higher CPU scheduling priority on Linux.
        """
        if not self.is_linux or not hasattr(os, "nice"):
            return False

        try:
            os.nice(nice_increment)
            return True
        except Exception:
            # Requires root or CAP_SYS_NICE for negative increments; fail silently
            return False

    def malloc_trim(self, pad: int = 0) -> bool:
        """
        Trims free memory from GLIBC heap arenas and returns pages to the Linux kernel.
        Crucial for long-running ALife simulations creating/destroying millions of objects.
        """
        if not self.is_linux or not self._libc:
            return False

        try:
            if hasattr(self._libc, "malloc_trim"):
                res = self._libc.malloc_trim(ctypes.c_size_t(pad))
                self.last_trim_timestamp = time.time()
                self.trim_count += 1
                return bool(res == 1)
        except Exception:
            pass
        return False

    def get_optimized_cache_dir(self, app_name: str = "echo_evolution_simulator") -> str:
        """
        Returns the optimal cache directory path:
        Uses Linux /dev/shm (POSIX shared memory tmpfs in RAM) when available,
        providing nanosecond I/O and zero disk wear.
        Falls back to workspace ./cache.
        """
        default_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cache"))
        if not self.is_linux:
            os.makedirs(default_dir, exist_ok=True)
            return default_dir

        shm_dir = f"/dev/shm/{app_name}"
        try:
            if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK):
                os.makedirs(shm_dir, exist_ok=True)
                # Test write access
                test_f = os.path.join(shm_dir, ".test_write")
                with open(test_f, "w") as f:
                    f.write("1")
                os.remove(test_f)
                return shm_dir
        except Exception:
            pass

        os.makedirs(default_dir, exist_ok=True)
        return default_dir

    def posix_advise_sequential(self, fd: int, offset: int = 0, length: int = 0) -> None:
        """Hints Linux page cache that file descriptor will be accessed sequentially."""
        if self.is_linux and hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_SEQUENTIAL"):
            try:
                os.posix_fadvise(fd, offset, length, os.POSIX_FADV_SEQUENTIAL)
            except Exception:
                pass

    def posix_advise_willneed(self, fd: int, offset: int = 0, length: int = 0) -> None:
        """Hints Linux page cache to prefetch pages into memory."""
        if self.is_linux and hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_WILLNEED"):
            try:
                os.posix_fadvise(fd, offset, length, os.POSIX_FADV_WILLNEED)
            except Exception:
                pass

    def get_memory_telemetry(self) -> Dict[str, Any]:
        """
        Extracts high-fidelity memory statistics from /proc/self/status on Linux.
        """
        metrics: Dict[str, Any] = {
            "platform": "linux" if self.is_linux else sys.platform,
            "vm_rss_kb": 0,
            "vm_peak_kb": 0,
            "vm_hwm_kb": 0,
            "vm_size_kb": 0,
            "trim_count": self.trim_count,
            "last_trim_time": self.last_trim_timestamp,
            "active_cores": self.get_affinity(),
            "total_cores": self.total_cores,
        }

        if not self.is_linux:
            return metrics

        try:
            if os.path.exists("/proc/self/status"):
                with open("/proc/self/status", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            metrics["vm_rss_kb"] = int(line.split()[1])
                        elif line.startswith("VmPeak:"):
                            metrics["vm_peak_kb"] = int(line.split()[1])
                        elif line.startswith("VmHWM:"):
                            metrics["vm_hwm_kb"] = int(line.split()[1])
                        elif line.startswith("VmSize:"):
                            metrics["vm_size_kb"] = int(line.split()[1])
        except Exception:
            pass

        return metrics


# Global Linux Platform Optimizer Singleton
linux_optimizer = LinuxPlatformOptimizer()
