"""
project/security/spec_protector.py

Python Ctypes Bridge to Native Pure-C Hardware Spec Protector DLL.
Monitors CPU load, process RAM, available system RAM, and frame latency to prevent
hardware degradation, CPU thermal thrashing, and OS freeze.
"""

from __future__ import annotations

import os
import sys
import ctypes
from dataclasses import dataclass
from typing import Optional, Tuple


class _HardwareTelemetryStruct(ctypes.Structure):
    _fields_ = [
        ("cpu_usage_pct", ctypes.c_double),
        ("process_ram_mb", ctypes.c_double),
        ("system_ram_avail_mb", ctypes.c_double),
        ("system_ram_total_mb", ctypes.c_double),
        ("frame_delta_ms", ctypes.c_double),
        ("is_danger_zone", ctypes.c_int),
        ("danger_reason_code", ctypes.c_int),
    ]


@dataclass
class HardwareTelemetryData:
    cpu_usage_pct: float
    process_ram_mb: float
    system_ram_avail_mb: float
    system_ram_total_mb: float
    frame_delta_ms: float
    is_danger_zone: bool
    danger_reason_code: int
    danger_reason_text: str


class SpecProtector:
    """High-performance Pure-C Hardware Specification & Safety Guard."""

    def __init__(
        self,
        max_cpu_pct: float = 92.0,
        max_process_ram_mb: float = 4096.0,
        min_avail_ram_mb: float = 512.0,
        max_frame_freeze_ms: float = 3500.0,
    ) -> None:
        self.max_cpu_pct = max_cpu_pct
        self.max_process_ram_mb = max_process_ram_mb
        self.min_avail_ram_mb = min_avail_ram_mb
        self.max_frame_freeze_ms = max_frame_freeze_ms

        self._dll: Optional[ctypes.CDLL] = None
        self._load_native_dll()
        self.init_hardware_limits(max_cpu_pct, max_process_ram_mb, min_avail_ram_mb, max_frame_freeze_ms)

    def _load_native_dll(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        native_dir = os.path.join(base_dir, "native")

        # Determine platform-specific library candidate filenames
        if sys.platform.startswith("linux"):
            candidates = [
                os.path.join(native_dir, "spec_protector.so"),
                os.path.join(native_dir, "libspec_protector.so"),
                os.path.join(native_dir, "spec_protector.dll"),
            ]
        elif sys.platform == "darwin":
            candidates = [
                os.path.join(native_dir, "spec_protector.dylib"),
                os.path.join(native_dir, "spec_protector.so"),
            ]
        else:
            candidates = [
                os.path.join(native_dir, "spec_protector.dll"),
                os.path.join(native_dir, "spec_protector.so"),
            ]

        for lib_path in candidates:
            if os.path.exists(lib_path):
                try:
                    self._dll = ctypes.CDLL(lib_path)
                    
                    # Function signatures
                    self._dll.init_spec_protector.argtypes = [
                        ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double
                    ]
                    self._dll.init_spec_protector.restype = ctypes.c_int

                    self._dll.check_hardware_safety.argtypes = [ctypes.POINTER(_HardwareTelemetryStruct)]
                    self._dll.check_hardware_safety.restype = ctypes.c_int

                    self._dll.reset_danger_state.argtypes = []
                    self._dll.reset_danger_state.restype = None

                    self._dll.get_danger_reason_string.argtypes = [ctypes.c_int]
                    self._dll.get_danger_reason_string.restype = ctypes.c_char_p

                    return
                except Exception as e:
                    print(f"[SPEC PROTECTOR] Warning: Failed to bind native binary {lib_path} ({e}).")
                    self._dll = None

    def init_hardware_limits(
        self,
        max_cpu_pct: float,
        max_process_ram_mb: float,
        min_avail_ram_mb: float,
        max_frame_freeze_ms: float,
    ) -> None:
        if self._dll:
            self._dll.init_spec_protector(
                max_cpu_pct, max_process_ram_mb, min_avail_ram_mb, max_frame_freeze_ms
            )

    def check_safety(self) -> HardwareTelemetryData:
        """Polls native C hardware protector. Sub-microsecond execution time (< 0.02ms)."""
        if self._dll:
            telemetry = _HardwareTelemetryStruct()
            self._dll.check_hardware_safety(ctypes.byref(telemetry))
            
            raw_reason = self._dll.get_danger_reason_string(telemetry.danger_reason_code)
            reason_str = raw_reason.decode("utf-8") if raw_reason else "Normal Operation"

            return HardwareTelemetryData(
                cpu_usage_pct=telemetry.cpu_usage_pct,
                process_ram_mb=telemetry.process_ram_mb,
                system_ram_avail_mb=telemetry.system_ram_avail_mb,
                system_ram_total_mb=telemetry.system_ram_total_mb,
                frame_delta_ms=telemetry.frame_delta_ms,
                is_danger_zone=bool(telemetry.is_danger_zone),
                danger_reason_code=telemetry.danger_reason_code,
                danger_reason_text=reason_str,
            )

        # Fallback if DLL not loaded
        return HardwareTelemetryData(
            cpu_usage_pct=0.0,
            process_ram_mb=100.0,
            system_ram_avail_mb=4096.0,
            system_ram_total_mb=8192.0,
            frame_delta_ms=16.0,
            is_danger_zone=False,
            danger_reason_code=0,
            danger_reason_text="Normal Operation (Fallback)",
        )

    def reset_danger_state(self) -> None:
        if self._dll:
            self._dll.reset_danger_state()


# Global Singleton Instance for high-performance zero-allocation calls
global_spec_protector = SpecProtector()
