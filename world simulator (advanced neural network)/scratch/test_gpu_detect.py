import subprocess
import json
import os
import sys

def detect_gpus():
    gpus = []
    # 1. Try PowerShell CimInstance (built-in Windows)
    try:
        ps_cmd = 'Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, Status | ConvertTo-Json'
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = item.get("Name", "")
                ram = item.get("AdapterRAM", 0) or 0
                driver = item.get("DriverVersion", "")
                status = item.get("Status", "OK")
                
                # Determine if dedicated
                name_upper = name.upper()
                is_dedicated = False
                vendor = "Unknown"
                
                if "NVIDIA" in name_upper or "GEFORCE" in name_upper or "QUADRO" in name_upper or "RTX" in name_upper or "GTX" in name_upper:
                    is_dedicated = True
                    vendor = "NVIDIA"
                elif "RADEON" in name_upper:
                    # Check for dedicated Radeon vs integrated
                    # Integrated usually has 512MB RAM or names like 'Graphics', 'Vega 3/6/7/8', '740M', '680M' etc.
                    if any(term in name_upper for term in ["RX ", "PRO ", "XT", "R9 ", "R7 "]) or ram > 1073741824: # > 1GB
                        is_dedicated = True
                    vendor = "AMD"
                elif "ARC" in name_upper or "A770" in name_upper or "A750" in name_upper or "A580" in name_upper or "A380" in name_upper:
                    is_dedicated = True
                    vendor = "Intel"
                elif "INTEL" in name_upper:
                    vendor = "Intel"
                    is_dedicated = False

                gpus.append({
                    "name": name,
                    "vendor": vendor,
                    "ram_bytes": ram,
                    "ram_mb": ram // (1024 * 1024) if ram else 0,
                    "driver": driver,
                    "status": status,
                    "is_dedicated": is_dedicated
                })
    except Exception as e:
        print("CimInstance error:", e)

    # 2. Check nvidia-smi if NVIDIA present
    for g in gpus:
        if g["vendor"] == "NVIDIA":
            try:
                ns_res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,temperature.gpu,power.draw", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3)
                if ns_res.returncode == 0 and ns_res.stdout.strip():
                    parts = [p.strip() for p in ns_res.stdout.strip().split(",")]
                    if len(parts) >= 4:
                        g["vram_smi_mb"] = int(float(parts[1]))
                        g["temp_c"] = float(parts[2])
                        g["power_w"] = float(parts[3])
            except Exception:
                pass

    return gpus

gpus = detect_gpus()
for idx, g in enumerate(gpus):
    print(f"GPU {idx}: {g['name']} | Vendor: {g['vendor']} | Dedicated: {g['is_dedicated']} | VRAM: {g.get('vram_smi_mb', g['ram_mb'])} MB | Temp: {g.get('temp_c', 'N/A')} C")
