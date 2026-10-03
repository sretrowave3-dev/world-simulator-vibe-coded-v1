import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('run_gui.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

marker = 'elif cmd_name == "food":'
idx = text.find(marker)

if idx != -1:
    new_commands = '''elif cmd_name == "pause":
                    renderer.simulation_speed = 0.0
                    print("Simulation PAUSED.")
                    
                elif cmd_name in ("play", "resume"):
                    renderer.simulation_speed = 1.0
                    print("Simulation RESUMED (1x speed).")
                    
                elif cmd_name.startswith("speed"):
                    try:
                        args = cmd_args.split()
                        spd = float(args[0]) if args else 1.0
                        renderer.simulation_speed = spd
                        print(f"Simulation speed set to {spd}x.")
                    except ValueError:
                        print("Error: speed requires a numeric multiplier (e.g. 'speed 2.5')")

                elif cmd_name.startswith("kill"):
                    try:
                        target = cmd_args.strip().upper()
                        if not target:
                            print("Error: Specify 'all' or an entity type (e.g., 'kill BACTERIA')")
                        elif target == "ALL":
                            entities_list.clear()
                            print("Purged all entities from the ecosystem.")
                        else:
                            to_remove = [e for e in entities_list if e.entity_type.name == target]
                            for e in to_remove:
                                entities_list.remove(e)
                            print(f"Purged {len(to_remove)} entities of type {target}.")
                    except Exception as e:
                        print(f"Error purging entities: {e}")

                elif cmd_name in ("stats", "metrics"):
                    print("========================================================")
                    print("             ECOSYSTEM METRICS DASHBOARD            ")
                    print("========================================================")
                    print(f" Total Entities: {len(entities_list)}")
                    alive = [e for e in entities_list if e.is_alive]
                    print(f" Alive Entities: {len(alive)}")
                    if alive:
                        avg_age = sum(getattr(e, 'age_ticks', 0) for e in alive) / len(alive)
                        avg_energy = sum(getattr(e, 'energy', 0) for e in alive) / len(alive)
                        print(f" Average Age:    {avg_age:.1f} ticks")
                        print(f" Average Energy: {avg_energy:.1f}")
                        
                        counts = {}
                        for e in alive:
                            counts[e.entity_type.name] = counts.get(e.entity_type.name, 0) + 1
                        print(" Species Breakdown:")
                        for k, v in counts.items():
                            print(f"   - {k}: {v}")
                    print("========================================================")

                elif cmd_name == "inspect":
                    target_id = cmd_args.strip()
                    if not target_id:
                        print("Error: Specify an entity ID (e.g., 'inspect bact_0')")
                    else:
                        found = next((e for e in entities_list if e.entity_id == target_id), None)
                        if found:
                            print(f"--- DETAILED INSPECTION: {found.entity_id} ---")
                            print(f"Type: {found.entity_type.name} | Age: {getattr(found, 'age_ticks', 0)}")
                            print(f"Position: ({found.pos_x:.2f}, {found.pos_y:.2f}) | Velocity: ({found.vel_x:.2f}, {found.vel_y:.2f})")
                            print(f"Energy: {getattr(found, 'energy', 0):.2f}/{getattr(found, 'max_energy', 1)}")
                            print(f"Hydration: {getattr(found, 'hydration', 0):.2f}/{getattr(found, 'max_hydration', 1)}")
                            if found.brain:
                                print(f"Neural Network: Active")
                                print(f"  Inputs:  {found.brain.input_size}")
                                print(f"  Hidden:  {found.brain.hidden_sizes}")
                                print(f"  Outputs: {found.brain.output_size}")
                            else:
                                print("Neural Network: None")
                            print("Custom Data Keys:", list(found.custom_data.keys()))
                            print("------------------------------------------------")
                        else:
                            print(f"Entity '{target_id}' not found.")

                '''
    
    new_text = text[:idx] + new_commands + text[idx:]
    with open('run_gui.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Injected smart commands into run_gui.py")
else:
    print("Marker not found!")
