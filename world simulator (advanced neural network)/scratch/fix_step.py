import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('run_gui.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

start_marker = 'elif cmd_name == "step":'
end_marker = 'elif cmd_name == "uio":'

start_idx = text.find(start_marker)
end_idx = text.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_text = text[:start_idx] + '''elif cmd_name == "step":
                    try:
                        args = cmd_args.split()
                        amount = int(args[0]) if args else 1
                        unit = args[1].lower() if len(args) > 1 else "ticks"
                        
                        ticks_to_run = amount
                        dt_override = None
                        
                        if unit in ("year", "years"):
                            # 1 year = 2,592,000 ticks. We do 1 loop per year with massive dt.
                            ticks_to_run = amount
                            dt_override = 2592000.0
                        elif unit in ("day", "days"):
                            # 1 day = 7200 ticks. 1 loop per day.
                            ticks_to_run = amount
                            dt_override = 7200.0
                            
                        print(f"Stepping simulation by {amount} {unit} (Deep Time mode: {ticks_to_run} cycles)...")
                        
                        if ticks_to_run > 100:
                            scheduler.unregister_system("RenderSyncSystem")
                            
                        prev_speed = getattr(renderer, "simulation_speed", 0.0)
                        renderer.simulation_speed = 0.0
                        
                        import time
                        time.sleep(0.1) # Wait for worker loop to pause safely
                        step_start = time.time()
                        
                        for i in range(ticks_to_run):
                            try:
                                scheduler.update(dt_override=dt_override)
                                tick_count += 1
                                if i > 0 and i % 100 == 0:
                                    pct = (i / ticks_to_run) * 100.0
                                    bar_len = 40
                                    filled = int(bar_len * i / ticks_to_run)
                                    bar = '#' * filled + '-' * (bar_len - filled)
                                    print(f"\\r[LOADING] {bar} {pct:.1f}% ({time.time()-step_start:.1f}s)", end='', flush=True)
                            except Exception as e:
                                print(f"\\nCRASH HANDLER (Step command): Exception caught in backend scheduler: {e}")
                                import traceback
                                traceback.print_exc()
                                break
                            
                        if ticks_to_run > 100:
                            scheduler.register_system(render_sync_sys)
                            
                        renderer.simulation_speed = prev_speed
                        print(f"\\nDone stepping {amount} {unit} in {(time.time()-step_start):.2f}s.")
                    except Exception as e:
                        print(f"Error: step requires a number (and optional unit: ticks/days/years). Details: {e}")

                ''' + text[end_idx:]
                        
    with open('run_gui.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Fixed corrupted run_gui.py step block")
else:
    print("Markers not found!")
