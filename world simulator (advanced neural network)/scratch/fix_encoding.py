import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('run_gui.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

start_marker = 'elif cmd_name == "civilization integration":'
end_marker = 'if unit in ("year", "years"):'

start_idx = text.find(start_marker)
end_idx = text.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_text = text[:start_idx] + '''elif cmd_name == "civilization integration":
                    civ_score = min(100.0, len(entities_list) * 0.15 + (tick_count * 0.001))
                    print("========================================================")
                    print("          CIVILIZATION INTEGRATION DASHBOARD        ")
                    print("========================================================")
                    print(f" Global Social Cohesion: {civ_score:>25.1f}% ")
                    print(f" Neural Affinity Nodes:  {len(entities_list):>25} ")
                    print(f" Gemini Hivemind Status: {('Active' if civ_score > 50 else 'Developing'):>25} ")
                    print("========================================================")

                elif cmd_name == "step":
                    try:
                        args = cmd_args.split()
                        amount = int(args[0]) if args else 1
                        unit = args[1].lower() if len(args) > 1 else "ticks"
                        
                        ticks_to_run = amount
                        dt_override = None
                        
                        ''' + text[end_idx:]
                        
    with open('run_gui.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Fixed corrupted run_gui.py")
else:
    print("Markers not found!")
