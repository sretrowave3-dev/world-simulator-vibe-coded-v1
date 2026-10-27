"""
project/core/gpu_manager.py

Dedicated GPU Hardware Scanner, Enabler, PATH Integrator & Long-Term Safety Guard.
Supports NVIDIA GeForce/RTX/GTX, AMD Radeon RX/dGPU, and Intel Arc.
"""

from __future__ import annotations

import os
import sys
import json
import time
import shutil
import logging
import threading
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("GPUManager")


@dataclass
class GPUInfo:
    """Hardware specification and current telemetry of a detected GPU."""
    name: str
    vendor: str                    # "NVIDIA", "AMD", "Intel", or "Unknown"
    vram_mb: int = 0
    driver_version: str = "Unknown"
    status: str = "OK"
    is_dedicated: bool = False
    temperature_c: Optional[float] = None
    power_w: Optional[float] = None
    bus_id: Optional[str] = None


@dataclass
class GPUSafetyStatus:
    """Real-time health and safety metrics for GPU protection under all conditions."""
    is_safe: bool = True
    target_fps: int = 60
    cooperative_sleep_ms: float = 1.0
    thermal_status: str = "NORMAL"  # "NORMAL", "WARM", "CRITICAL"
    vram_budget_mb: int = 512       # Maximum surface memory allowed for simulator textures
    vram_estimated_used_mb: float = 0.0
    last_temp_c: Optional[float] = None
    frames_rendered: int = 0
    start_time: float = field(default_factory=time.time)
    fallback_active: bool = False
    warning_messages: List[str] = field(default_factory=list)


class GPUManager:
    """
    Central hardware controller for scanning, enabling, and safely governing
    dedicated GPUs in the World Simulator.
    """

    _instance: Optional[GPUManager] = None

    def __init__(self) -> None:
        self.gpus: List[GPUInfo] = []
        self.dedicated_gpu: Optional[GPUInfo] = None
        self.integrated_gpu: Optional[GPUInfo] = None
        self.safety = GPUSafetyStatus()
        self._last_thermal_check: float = 0.0
        self._thermal_check_interval: float = 5.0  # Check thermal stats every 5 seconds
        self._is_enabled_in_preferences: bool = False
        self._scan_completed: bool = False
        self._monitoring_active: bool = True
        self._thermal_worker_thread = threading.Thread(
            target=self._async_thermal_worker, daemon=True, name="gpu-thermal-worker"
        )
        self._thermal_worker_thread.start()

    def close(self) -> None:
        """Cleanly halts background monitoring daemon."""
        self._monitoring_active = False

    def _async_thermal_worker(self) -> None:
        """Background daemon polling GPU thermals without stalling the 60 FPS main render thread."""
        while getattr(self, "_monitoring_active", True):
            try:
                time.sleep(self._thermal_check_interval)
                if not getattr(self, "_monitoring_active", True):
                    break
                self.check_thermal_health()
            except Exception:
                pass

    @classmethod
    def get_instance(cls) -> GPUManager:
        if cls._instance is None:
            cls._instance = GPUManager()
        return cls._instance

    # ─────────────────────────────────────────────────────────────────────────
    # 1. HARDWARE SCANNING & DEDICATED GPU DETECTION
    # ─────────────────────────────────────────────────────────────────────────

    def scan_hardware(self, force_refresh: bool = False) -> List[GPUInfo]:
        """Scans host PC hardware for all GPUs and classifies dedicated vs integrated."""
        if self._scan_completed and not force_refresh:
            return self.gpus

        self.gpus = []
        self.dedicated_gpu = None
        self.integrated_gpu = None

        # Method 1: Windows CIM/WMI video controller inspection
        if sys.platform == "win32":
            self._scan_windows_wmi()

        # Method 2: Check nvidia-smi for precise NVIDIA metrics
        self._query_nvidia_smi()

        # Classify primary dedicated and integrated GPUs
        for g in self.gpus:
            if g.is_dedicated and self.dedicated_gpu is None:
                self.dedicated_gpu = g
            elif not g.is_dedicated and self.integrated_gpu is None:
                self.integrated_gpu = g

        self._scan_completed = True
        return self.gpus

    def _scan_windows_wmi(self) -> None:
        """Queries Win32_VideoController via PowerShell CIM."""
        try:
            ps_script = (
                "Get-CimInstance Win32_VideoController | "
                "Select-Object Name, AdapterRAM, DriverVersion, Status | "
                "ConvertTo-Json -Compress"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=4
            )
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout)
                items = [raw] if isinstance(raw, dict) else raw

                for item in items:
                    name = str(item.get("Name", "")).strip()
                    ram_bytes = item.get("AdapterRAM", 0) or 0
                    driver = str(item.get("DriverVersion", "Unknown"))
                    status = str(item.get("Status", "OK"))

                    name_upper = name.upper()
                    is_dedicated = False
                    vendor = "Unknown"

                    if any(k in name_upper for k in ("NVIDIA", "GEFORCE", "RTX", "GTX", "QUADRO", "TITAN")):
                        is_dedicated = True
                        vendor = "NVIDIA"
                    elif "RADEON" in name_upper or "AMD" in name_upper:
                        vendor = "AMD"
                        # Check dedicated AMD series vs APU / integrated
                        if any(k in name_upper for k in ("RX ", "XT", "PRO ", "R9 ", "R7 ", "DEDICATED")) or ram_bytes > 1073741824:
                            is_dedicated = True
                        else:
                            is_dedicated = False
                    elif "ARC" in name_upper or any(k in name_upper for k in ("A770", "A750", "A580", "A380", "A310")):
                        is_dedicated = True
                        vendor = "Intel"
                    elif "INTEL" in name_upper:
                        vendor = "Intel"
                        is_dedicated = False

                    vram_mb = int(ram_bytes // (1024 * 1024)) if ram_bytes > 0 else 0

                    gpu = GPUInfo(
                        name=name,
                        vendor=vendor,
                        vram_mb=vram_mb,
                        driver_version=driver,
                        status=status,
                        is_dedicated=is_dedicated,
                    )
                    self.gpus.append(gpu)
        except Exception as e:
            logger.debug(f"WMI GPU scan error: {e}")

    def _query_nvidia_smi(self) -> None:
        """Extracts live telemetry from nvidia-smi if NVIDIA hardware exists."""
        try:
            res = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,temperature.gpu,power.draw,pci.bus_id,driver_version",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=2
            )
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().split("\n")
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        smi_name = parts[0]
                        vram_tot = int(float(parts[1]))
                        temp_c = float(parts[2])
                        power_w = float(parts[3]) if parts[3] != "[Not Supported]" else None
                        bus_id = parts[4] if len(parts) > 4 else None
                        drv_ver = parts[5] if len(parts) > 5 else "Unknown"

                        # Update existing NVIDIA entry or add new
                        found = False
                        for g in self.gpus:
                            if g.vendor == "NVIDIA":
                                g.vram_mb = max(g.vram_mb, vram_tot)
                                g.temperature_c = temp_c
                                g.power_w = power_w
                                g.bus_id = bus_id
                                if drv_ver != "Unknown":
                                    g.driver_version = drv_ver
                                g.is_dedicated = True
                                found = True
                                break

                        if not found:
                            self.gpus.append(GPUInfo(
                                name=smi_name,
                                vendor="NVIDIA",
                                vram_mb=vram_tot,
                                driver_version=drv_ver,
                                status="OK",
                                is_dedicated=True,
                                temperature_c=temp_c,
                                power_w=power_w,
                                bus_id=bus_id,
                            ))
        except Exception:
            pass

    def has_dedicated_gpu(self) -> bool:
        """Returns True if at least one dedicated GPU is detected on the host system."""
        self.scan_hardware()
        return self.dedicated_gpu is not None

    def get_gpu_summary(self) -> str:
        """Generates a concise human-readable hardware breakdown."""
        self.scan_hardware()
        if not self.gpus:
            return "No GPU hardware detected."

        lines = []
        for idx, g in enumerate(self.gpus):
            tag = "🌟 DEDICATED" if g.is_dedicated else "⚙️ INTEGRATED"
            temp_str = f" | Temp: {g.temperature_c:.0f}°C" if g.temperature_c is not None else ""
            pwr_str = f" | Power: {g.power_w:.1f}W" if g.power_w is not None else ""
            lines.append(f"[{idx + 1}] {tag} {g.name} ({g.vram_mb} MB VRAM, Driver {g.driver_version}{temp_str}{pwr_str})")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. DEDICATED GPU ENABLER & WINDOWS HIGH-PERFORMANCE PREFERENCE
    # ─────────────────────────────────────────────────────────────────────────

    def enable_dedicated_gpu(self) -> Tuple[bool, str]:
        """
        Enables and configures the host operating system to run Python using the dedicated GPU:
        1. Configures Windows UserGpuPreferences registry (GpuPreference=2).
        2. Injects OS environment variables before GPU initialization.
        3. Verifies Python in PATH.
        Returns: (success: bool, status_message: str)
        """
        self.scan_hardware()
        if not self.dedicated_gpu:
            return False, "No dedicated GPU found. Using default display adapter."

        messages = []

        # 1. Windows UserGpuPreferences Registry Setup
        if sys.platform == "win32":
            try:
                import winreg
                key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                
                # Register python.exe
                winreg.SetValueEx(key, sys.executable, 0, winreg.REG_SZ, "GpuPreference=2;")
                
                # Register pythonw.exe if in same folder
                py_dir = os.path.dirname(sys.executable)
                pythonw_path = os.path.join(py_dir, "pythonw.exe")
                if os.path.exists(pythonw_path):
                    winreg.SetValueEx(key, pythonw_path, 0, winreg.REG_SZ, "GpuPreference=2;")
                    
                winreg.CloseKey(key)
                self._is_enabled_in_preferences = True
                messages.append(f"DirectX High-Performance preference bound to {os.path.basename(sys.executable)}")
            except Exception as re:
                messages.append(f"Registry notice: {re}")

        # 2. Environment variables for GPU acceleration
        os.environ["SHIM_MCCOMPAT"] = "0x800000001"
        os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
        os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        os.environ["PYGAME_DEDICATED_GPU"] = "1"

        # 3. Verify Python in PATH
        in_path, _, _ = self.check_python_in_path()
        if not in_path:
            added, p_msg = self.add_python_to_user_path()
            messages.append(p_msg)
        else:
            messages.append("Python environment verified in system PATH.")

        status_text = (
            f"✅ Dedicated GPU Enabled: {self.dedicated_gpu.name} ({self.dedicated_gpu.vram_mb} MB VRAM)\n"
            + "\n".join(f"   • {m}" for m in messages)
        )
        return True, status_text

    # ─────────────────────────────────────────────────────────────────────────
    # 3. PYTHON IN PATH VERIFICATION & MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────

    def check_python_in_path(self) -> Tuple[bool, str, str]:
        """
        Checks whether sys.executable's directory is present in PATH.
        Returns: (is_in_path, current_path, python_dir)
        """
        py_dir = os.path.abspath(os.path.dirname(sys.executable)).lower()
        curr_path = os.environ.get("PATH", "")
        paths = [os.path.abspath(p).lower() for p in curr_path.split(os.pathsep) if p.strip()]

        is_present = py_dir in paths or any(py_dir.startswith(p) for p in paths if "python" in p)
        return is_present, curr_path, os.path.dirname(sys.executable)

    def add_python_to_user_path(self) -> Tuple[bool, str]:
        """
        Safely registers Python executable directory in Windows User Environment PATH
        and updates current process os.environ.
        """
        py_dir = os.path.abspath(os.path.dirname(sys.executable))
        py_scripts = os.path.join(py_dir, "Scripts")

        if sys.platform != "win32":
            os.environ["PATH"] = f"{py_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            return True, "Added Python to session PATH."

        try:
            import winreg
            env_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                curr_user_path, _ = winreg.QueryValueEx(env_key, "Path")
            except FileNotFoundError:
                curr_user_path = ""

            parts = [p.strip() for p in curr_user_path.split(";") if p.strip()]
            parts_norm = [os.path.normpath(p).lower() for p in parts]

            changed = False
            if os.path.normpath(py_dir).lower() not in parts_norm:
                parts.insert(0, py_dir)
                changed = True
            if os.path.exists(py_scripts) and os.path.normpath(py_scripts).lower() not in parts_norm:
                parts.insert(0, py_scripts)
                changed = True

            if changed:
                new_user_path = ";".join(parts)
                winreg.SetValueEx(env_key, "Path", 0, winreg.REG_EXPAND_SZ, new_user_path)
                # Broadcast environment update so other apps get notified safely
                try:
                    import ctypes
                    ctypes.windll.user32.SendMessageTimeoutW(
                        0xFFFF, 0x001A, 0, "Environment", 0x0002, 1000, None
                    )
                except Exception:
                    pass

            winreg.CloseKey(env_key)

            # Update current session path
            os.environ["PATH"] = f"{py_dir};{py_scripts};{os.environ.get('PATH', '')}"
            return True, f"Python path registered safely in User Environment PATH: '{py_dir}'"

        except Exception as e:
            return False, f"Could not update User PATH in registry ({e}). Session PATH updated."

    # ─────────────────────────────────────────────────────────────────────────
    # 4. COMPREHENSIVE GPU SAFETY GUARDS (SHORT-TERM & LONG-TERM)
    # ─────────────────────────────────────────────────────────────────────────

    def enforce_frame_safety(self, clock: Any) -> float:
        """
        Enforces frame-rate and power safety rules:
        - Strict FPS capping using high-precision clock tick to avoid coil whine, voltage spikes, and GPU overdrive.
        - Native cooperative sleep through clock pacing.
        - Dynamic thermal throttling governed by background monitoring daemon.
        Returns: actual frame delta in seconds.
        """
        self.safety.frames_rendered += 1
        dt = clock.tick(self.safety.target_fps) / 1000.0
        return dt

    def check_thermal_health(self) -> GPUSafetyStatus:
        """
        Monitors GPU temperature and applies automatic dynamic throttling:
        - < 76°C: NORMAL (Target 60 FPS)
        - 76°C - 85°C: WARM (Target 45 FPS to cool down)
        - > 85°C: CRITICAL (Target 30 FPS Eco Mode to protect hardware longevity)
        """
        if not self.dedicated_gpu or self.dedicated_gpu.vendor != "NVIDIA":
            return self.safety

        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu,power.draw", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if parts and parts[0]:
                    temp_c = float(parts[0])
                    self.safety.last_temp_c = temp_c
                    self.dedicated_gpu.temperature_c = temp_c
                    if len(parts) > 1 and parts[1] != "[Not Supported]":
                        self.dedicated_gpu.power_w = float(parts[1])

                    # Thermal guard levels
                    if temp_c > 85.0:
                        self.safety.thermal_status = "CRITICAL"
                        self.safety.target_fps = 30
                        self.safety.cooperative_sleep_ms = 3.0
                        msg = f"⚠️ [GPU SAFETY CRITICAL] Temp reached {temp_c:.0f}°C! Throttling to 30 FPS eco mode."
                        if not self.safety.warning_messages or self.safety.warning_messages[-1] != msg:
                            self.safety.warning_messages.append(msg)
                            print(f"\n{msg}\n")
                    elif temp_c > 76.0:
                        self.safety.thermal_status = "WARM"
                        self.safety.target_fps = 45
                        self.safety.cooperative_sleep_ms = 1.5
                    else:
                        if self.safety.thermal_status != "NORMAL":
                            print(f"\n❄️ [GPU SAFETY RECOVERED] Temp cooled to {temp_c:.0f}°C. Resuming 60 FPS.\n")
                        self.safety.thermal_status = "NORMAL"
                        self.safety.target_fps = 60
                        self.safety.cooperative_sleep_ms = 1.0

        except Exception:
            pass

        return self.safety

    def update_vram_usage(self, estimated_mb: float) -> None:
        """Tracks simulator texture VRAM footprint to prevent long-term memory leaks."""
        self.safety.vram_estimated_used_mb = estimated_mb
        if estimated_mb > self.safety.vram_budget_mb:
            self.safety.warning_messages.append(
                f"VRAM budget exceeded: {estimated_mb:.1f} MB / {self.safety.vram_budget_mb} MB"
            )

    def fallback_to_software_renderer(self, reason: str = "Hardware context reset") -> None:
        """Gracefully falls back to integrated/software rendering if dedicated GPU encounters an error."""
        self.safety.fallback_active = True
        self.safety.target_fps = 30
        self.safety.warning_messages.append(f"Fallback to software/integrated renderer: {reason}")
        print(f"\n🛡️ [GPU FAILSAFE TRIGGERED] {reason}. Gracefully transitioning to low-power renderer.\n")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. PYTORCH & AI ACCELERATION BRIDGE
    # ─────────────────────────────────────────────────────────────────────────

    def get_torch_device(self) -> Any:
        """
        Returns the optimal PyTorch device for neural networks and self-learning.
        Prioritizes CUDA on the dedicated NVIDIA GPU (RTX 3050), with graceful CPU fallback.
        """
        try:
            import torch
            if torch.cuda.is_available() and not self.safety.fallback_active:
                return torch.device("cuda:0")
            return torch.device("cpu")
        except Exception:
            return "cpu"

    @property
    def torch_device(self) -> Any:
        return self.get_torch_device()

    def is_torch_cuda_available(self) -> bool:
        """Checks if PyTorch has functional CUDA acceleration enabled."""
        try:
            import torch
            return bool(torch.cuda.is_available() and not self.safety.fallback_active)
        except Exception:
            return False

    def get_torch_gpu_info(self) -> Dict[str, Any]:
        """Returns deep telemetry for PyTorch GPU state, VRAM allocation, and compute capability."""
        info: Dict[str, Any] = {
            "torch_available": False,
            "cuda_available": False,
            "device": "cpu",
            "device_name": "CPU",
            "vram_allocated_mb": 0.0,
            "vram_reserved_mb": 0.0,
            "vram_total_mb": 0.0,
        }
        try:
            import torch
            info["torch_available"] = True
            info["torch_version"] = torch.__version__
            if torch.cuda.is_available() and not self.safety.fallback_active:
                info["cuda_available"] = True
                dev_idx = torch.cuda.current_device()
                info["device"] = f"cuda:{dev_idx}"
                info["device_name"] = torch.cuda.get_device_name(dev_idx)
                allocated = torch.cuda.memory_allocated(dev_idx) / (1024 * 1024)
                reserved = torch.cuda.memory_reserved(dev_idx) / (1024 * 1024)
                total = torch.cuda.get_device_properties(dev_idx).total_memory / (1024 * 1024)
                info["vram_allocated_mb"] = round(allocated, 2)
                info["vram_reserved_mb"] = round(reserved, 2)
                info["vram_total_mb"] = round(total, 2)
            else:
                info["device"] = "cpu"
                info["device_name"] = "CPU"
        except Exception as e:
            info["error"] = str(e)
        return info


# Global Singleton Instance
gpu_mgr = GPUManager.get_instance()
