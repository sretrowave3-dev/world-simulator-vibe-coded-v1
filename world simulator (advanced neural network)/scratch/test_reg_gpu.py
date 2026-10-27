import winreg
import sys

key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
val_name = sys.executable
winreg.SetValueEx(key, val_name, 0, winreg.REG_SZ, "GpuPreference=2;")

# Read back
read_val, read_type = winreg.QueryValueEx(key, val_name)
winreg.CloseKey(key)

print(f"Registered {val_name} -> {read_val} (Type: {read_type})")
