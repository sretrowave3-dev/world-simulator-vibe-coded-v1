import os

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
run_gui_path = os.path.join(base_dir, "run_gui.py")

with open(run_gui_path, "r", encoding="utf-8") as f:
    text = f.read()

target1 = 'print(f"{BOLD}║   [2] terminal with gui                                                        ║{RESET}")'
replace1 = 'print(f"{BOLD}║   [2] terminal with Raylib Hardware GPU GUI (NVIDIA RTX 3050 - OpenGL 3.3)     ║{RESET}")'

target2 = 'print(f"{BOLD}🚀 Running: Terminal with gui (Graphical Sandbox Window Active){RESET}\\n")'
replace2 = 'print(f"{BOLD}🚀 Running: Terminal with Raylib Hardware GPU GUI (NVIDIA RTX 3050 Active){RESET}\\n")'

target3 = '''    # 6. Visual GUI manager & Terminal Activity Chronicler
    renderer = SimulationRenderer(width=win_w, height=win_h, world_width=world_w, world_height=world_h)
    if is_terminal_only:
        renderer.ui_active = False
    activity_chronicler.set_terminal_mode(is_terminal_only)'''

replace3 = '''    # 6. Visual GUI manager & Terminal Activity Chronicler
    if not is_terminal_only:
        try:
            from project.renderer.raylib_renderer import RaylibSimulationRenderer
            renderer = RaylibSimulationRenderer(width=win_w, height=win_h, world_width=world_w, world_height=world_h)
            print("⚡ Raylib Hardware GPU Engine (OpenGL 3.3 / NVIDIA RTX 3050) initialized successfully.")
        except Exception as e:
            print(f"⚠️ Falling back to Pygame renderer: {e}")
            renderer = SimulationRenderer(width=win_w, height=win_h, world_width=world_w, world_height=world_h)
    else:
        renderer = SimulationRenderer(width=win_w, height=win_h, world_width=world_w, world_height=world_h)
        renderer.ui_active = False
    activity_chronicler.set_terminal_mode(is_terminal_only)'''

if target1 not in text:
    print("Warning: target1 not found, checking if already replaced...")
else:
    text = text.replace(target1, replace1, 1)

if target2 not in text:
    print("Warning: target2 not found, checking if already replaced...")
else:
    text = text.replace(target2, replace2, 1)

if target3 not in text:
    print("Warning: target3 not found, checking if already replaced...")
else:
    text = text.replace(target3, replace3, 1)

with open(run_gui_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully patched run_gui.py with Raylib Hardware GPU Engine!")
