"""
run_gui.py

Launcher script for the graphical simulation sandbox with modernized Cache Bridge Memory,
Dedicated Save/Load Management, and Advanced Interactive Terminal Console.
"""

from __future__ import annotations
import os
import sys

# Safe UTF-8 reconfiguration for Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Ensure the project package is importable when running this script directly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import random
import math
import time
import threading
from typing import List, Dict, Any, Tuple

from project.core.scheduler import Scheduler, SchedulerPhase, ExecutionPriority, UpdateContext
from project.core.simulation import Simulation, SimulationClock, SimulationState
from project.world.time import WorldTimeManager
from project.world.weather import WeatherManager, AtmosphericGrid, ChunkData as WeatherChunk
from project.world.disasters import DisasterManager
from project.world.soil import SoilManager
from project.world.water import WaterManager
from project.world.vegetation import VegetationManager
from project.world.resources import ResourceManager
from project.world.food import FoodManager
from project.utils.spatial_hash import SpatialHashGrid
from project.ai.pheromone import PheromoneGrid

# Advanced Cache Bridge Hub & Memory Buses
from project.core.linux_optimizer import linux_optimizer
from project.core.cache_bridge import bridge_hub, CACHE_DIR
from project.core.memory_cache import (
    ai_ram, physics_ram, civ_ram, ui_ram,
    genetics_ram, food_ram, weather_ram, social_ram,
    combat_ram, pathfinding_ram, disease_ram, terrain_ram,
    gemini_ram, telemetry_ram, save_ram,
    frontend_repeater, ram_allocator
)

# Start Parallel Auto Debugger
from project.core.auto_debugger import debugger
debugger.start()

# Systems imports
from project.systems.security_system import SecuritySystem
from project.systems.time_system import TimeSystem
from project.systems.weather_system import WeatherSystem
from project.systems.weather_sync_system import WeatherSyncSystem
from project.systems.disaster_system import DisasterSystem
from project.systems.soil_system import SoilSystem
from project.systems.water_system import WaterSystem
from project.systems.vegetation_system import VegetationSystem
from project.systems.resource_system import ResourceSystem
from project.systems.food_system import FoodSystem
from project.systems.perception_system import PerceptionSystem
from project.systems.decision_system import DecisionSystem
from project.systems.pheromone_system import PheromoneSystem
from project.systems.movement_system import MovementSystem
from project.systems.combat_system import CombatSystem
from project.systems.digestion_system import DigestionSystem
from project.systems.aging_system import AgingSystem
from project.systems.death_system import DeathSystem
from project.systems.reproduction_system import ReproductionSystem
from project.systems.birth_system import BirthSystem
from project.systems.mutation_system import MutationSystem
from project.systems.learning_system import LearningSystem
from project.systems.gemini_system import GeminiSystem
from project.systems.social_system import SocialSystem
from project.systems.civilization_system import CivilizationSystem
from project.systems.knowledge_system import KnowledgeSystem
from project.systems.event_system import EventSystem
from project.systems.statistics_system import StatisticsSystem
from project.systems.render_sync_system import RenderSyncSystem
from project.systems.save_system import SaveSystem
from project.systems.spec_protection_system import SpecProtectionSystem
from project.security.spec_protector import global_spec_protector
from project.core.audio_manager import global_bgm

from project.entities.entity import Entity
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.herbivore import Herbivore
from project.entities.predator import Predator
from project.entities.human import Human
from project.entities.avian import Avian
from project.entities.amphibian import Amphibian
from project.entities.arthropod import Arthropod
from project.entities.reptile import Reptile
from project.entities.fungus import Fungus

from project.renderer.renderer import SimulationRenderer
from project.core.persistence import PersistenceManager, SAVES_DIR
from project.core.quantum_persistence import quantum_persistence


def spawn_genesis_population(entities_list: List[Entity], world_w: float, world_h: float) -> None:
    """Spawns a vibrant, ecologically balanced starter colony in the 14,000m expanded world."""
    entities_list.clear()
    cx = world_w * 0.5
    cy = world_h * 0.5

    # 1. Starting Human Tribe (Clustered around fertile river valley center)
    for i in range(14):
        hx = max(100.0, min(world_w - 100.0, cx + random.uniform(-180, 180)))
        hy = max(100.0, min(world_h - 100.0, cy + random.uniform(-180, 180)))
        h = Human(entity_id=f"genesis_hum_{i}", species_id="homo_sapiens", pos_x=hx, pos_y=hy)
        if i == 0:
            h.add_to_inventory("wood", 4.0)
            h.add_to_inventory("stone", 3.0)
        elif i == 1:
            h.add_to_inventory("wood", 3.0)
        entities_list.append(h)

    # Spawn initial communal campfire at tribal center
    from project.civilization.settlement import world_settlement_mgr
    world_settlement_mgr.spawn_structure("campfire", cx, cy, clan_id="genesis_tribe", tick=1)

    # 2. Herbivore herds (deer and gazelles)
    for i in range(20):
        gx = max(100.0, min(world_w - 100.0, cx + random.uniform(-600, 600)))
        gy = max(100.0, min(world_h - 100.0, cy + random.uniform(-600, 600)))
        entities_list.append(Herbivore(entity_id=f"genesis_herb_{i}", species_id="gazelle", pos_x=gx, pos_y=gy))

    # 3. Predators (panthers in perimeter wilderness)
    for i in range(6):
        px = max(100.0, min(world_w - 100.0, cx + random.choice([-1, 1]) * random.uniform(600, 1200)))
        py = max(100.0, min(world_h - 100.0, cy + random.choice([-1, 1]) * random.uniform(600, 1200)))
        entities_list.append(Predator(entity_id=f"genesis_pred_{i}", species_id="panther", pos_x=px, pos_y=py))

    # 4. Living Ancient Forest & Groves around settlement
    for i in range(28):
        dist = random.uniform(40.0, 500.0)
        ang = random.uniform(0, 2 * math.pi)
        tx = max(100.0, min(world_w - 100.0, cx + math.cos(ang) * dist))
        ty = max(100.0, min(world_h - 100.0, cy + math.sin(ang) * dist))
        p = Plant(
            entity_id=f"genesis_tree_{i}",
            species_id="oak_tree" if i % 2 == 0 else "fruit_tree",
            pos_x=tx,
            pos_y=ty,
            biomass_kg=random.uniform(50.0, 160.0),
            energy=350.0,
        )
        entities_list.append(p)

    # 5. Scattered Flora across the continent
    for i in range(30):
        fx = random.uniform(100, world_w - 100)
        fy = random.uniform(100, world_h - 100)
        entities_list.append(Plant(entity_id=f"genesis_plant_{i}", species_id="fern", pos_x=fx, pos_y=fy))

    # 6. Avians, Amphibians, Arthropods, Reptiles, Fungi, Bacteria
    for i in range(10):
        entities_list.append(Avian(entity_id=f"genesis_avian_{i}", species_id="falcon", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    for i in range(10):
        entities_list.append(Amphibian(entity_id=f"genesis_amph_{i}", species_id="axolotl", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    for i in range(12):
        entities_list.append(Arthropod(entity_id=f"genesis_arth_{i}", species_id="pollinator_bee", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    for i in range(8):
        entities_list.append(Reptile(entity_id=f"genesis_rept_{i}", species_id="viper", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    for i in range(10):
        entities_list.append(Fungus(entity_id=f"genesis_fung_{i}", species_id="mycelium_morel", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    for i in range(10):
        entities_list.append(Bacteria(entity_id=f"genesis_bac_{i}", species_id="chemophile", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))


def print_modern_help_menu() -> None:
    """Displays a beautifully formatted, categorized console help dashboard."""
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║                     WORLD SIMULATOR COMMAND CONSOLE                            ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🌌 QUANTUM MULTI-UNIVERSE & TIME MACHINE (10x Smarter than Git):               ║")
    print("║   worlds (or universes)    - List isolated world universes with demographic stats ║")
    print("║   world switch <name|id>   - Switch active world universe and load its state      ║")
    print("║   world new <name>         - Create fresh isolated universe sandbox & re-seed     ║")
    print("║   rewind [delta|safe|disaster] - Time-travel back with timeline auto-forking      ║")
    print("║   timeline (or history)    - Visual ASCII DAG of milestones & checkpoints         ║")
    print("║   save [name] [message]    - Smart checkpoint with stale overwrite guard          ║")
    print("║   load [name]              - Load universe checkpoint                             ║")
    print("║   quicksave (or qs / F5)   - Isolated quicksave in active world                   ║")
    print("║   quickload (or ql / F9)   - Instant universe reload                              ║")
    print("║   autosave [on|off|ticks]  - Configure background auto-save interval              ║")
    print("║   git status/branch/co/log - Lower-level discrete git DAG controls                ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🌟 GEMINI COGNITION & MULTI-KEY ROUTING:                                       ║")
    print("║   apikey <key>             - Add key to intelligent multi-key rotation pool    ║")
    print("║   apikeys (or keys)        - Inspect health, latency & quotas of all keys      ║")
    print("║   rmkey <index|key>        - Remove API key from pool                          ║")
    print("║   offline                  - Force 100% offline mode (No pseudo affinity)      ║")
    print("║   online                   - Reconnect to online Gemini routing pool           ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🔒 PRIVACY, TELEMETRY & SETUP:                                                 ║")
    print("║   telemetry [on|off|preview] - Toggle anonymized diagnostic reporting          ║")
    print("║   setup (or firstrun)      - Re-run first-time setup wizard on demand          ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🎮 SIMULATION CONTROL:                                                         ║")
    print("║   pause                    - Pause backend simulation                          ║")
    print("║   play (or resume)         - Resume backend simulation (1x speed)              ║")
    print("║   speed <multiplier>       - Set simulation speed (e.g., speed 2.5, speed 10)  ║")
    print("║   step <amount> [unit]     - Quantum deep-time jump (ticks/days/years)         ║")
    print("║   reset                    - Wipe world and reseed genesis organisms           ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🖥️ DISPLAY & UI TOGGLE:                                                       ║")
    print("║   uio                      - Turn GUI visual window ON                         ║")
    print("║   uiof                     - Turn GUI visual window OFF (0% GPU headless mode) ║")
    print("║   clear                    - Clear terminal screen                             ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🎵 AUDIO & BACKGROUND MUSIC:                                                   ║")
    print("║   bgm [on|off|mute]        - Toggle background music with fade in/out          ║")
    print("║   bgm volume <0-100>       - Adjust soundtrack volume level                    ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║   status                   - View simulation ticks, entity counts & camera     ║")
    print("║   stats (or metrics)       - Detailed ecosystem demographics breakdown        ║")
    print("║   inspect <entity_id>      - Deep neural network & biometric telemetry         ║")
    print("║   bacterium status         - Local AI intelligence score & neuromodulators     ║")
    print("║   civilization integration - Measure global social cohesion & hivemind status  ║")
    print("║   feed humans [amt]        - Feed & hydrate all humans with nutrient burst     ║")
    print("║   train humans [cycles]    - Train humans on 50MB experience replay buffers    ║")
    print("║   spawn <type>,<x>,<y>     - Spawn entity (BACTERIA, PLANT, HERBIVORE, etc.)   ║")
    print("║   food <type>,<x>,<y>      - Spawn food node (grass, meat, fruit, fern)        ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🐧 LINUX OPTIMIZATION & OS ENGINE:                                             ║")
    print("║   linux (or linux status)  - Display CPU affinity, VmRSS, /dev/shm, & trim info ║")
    print("║   linux trim               - Force GLIBC malloc_trim heap arena compaction     ║")
    print("║   linux affinity <cores>   - Dynamically pin threads to CPU cores (e.g. 0,1,2) ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🚪 APPLICATION LIFECYCLE:                                                      ║")
    print("║   exit (or quit)           - Safe, clean engine shutdown                       ║")
    print("║   help (or ?)              - Show this command reference dashboard             ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝")


def main() -> None:
    from project.core.user_profile import user_profile_manager
    from project.core.git_save_manager import git_save_manager
    from project.core.telemetry_dispatcher import telemetry_dispatcher
    from project.core.world_telemetry import world_telemetry_collector
    from project.core.updater import update_manager

    # Trigger First-Time Setup Wizard if no prior setup or user metadata exists
    if user_profile_manager.is_first_run():
        print("\n🌟 [FIRST-TIME SETUP] Initiating initial environment configuration wizard...")
        try:
            from project.renderer.setup_wizard import run_setup_wizard
            user_profile = run_setup_wizard()
        except Exception as we:
            print(f"⚠️ [SETUP WIZARD] Fallback to default profile due to: {we}")
            user_profile = user_profile_manager.get_profile()
    else:
        user_profile = user_profile_manager.get_profile()

    display_cfg = user_profile.display
    win_w = display_cfg.get("width", 1280)
    win_h = display_cfg.get("height", 720)
    gemini_cfg = user_profile.gemini
    is_offline = gemini_cfg.get("is_offline", False) or (len(gemini_cfg.get("api_keys", [])) == 0)

    world_w = 14336.0  # 12.25x expanded planetary continent
    world_h = 14336.0

    active_univ = quantum_persistence.get_active_universe()
    print("════════════════════════════════════════════════════════════════════════════════")
    print(f"🌍 Advanced Neural Network World Simulator (Architect: {user_profile.user_name})")
    print(f"🌌 Active World:    \"{active_univ.world_name}\" [ID: {active_univ.universe_id}]")
    print(f"🌿 Quantum Branch:  '{active_univ.active_branch}' | Node: {active_univ.head_commit_id or 'genesis'}")
    print(f"📁 Save Directory:  {SAVES_DIR}")
    print(f"⚡ Cache Directory: {CACHE_DIR}")
    num_keys = len(gemini_cfg.get("api_keys", []))
    cog_mode_str = "100% OFFLINE (Local Neural Core — No Pseudo Affinity)" if is_offline else f"ONLINE ({num_keys} Gemini Keys in Pool)"
    print(f"🧠 Cognitive Mode:  {cog_mode_str}")
    telemetry = linux_optimizer.get_memory_telemetry()
    if telemetry.get("platform") == "linux":
        shm_str = " (tmpfs in RAM)" if CACHE_DIR.startswith("/dev/shm") else ""
        print(f"🐧 Linux Engine:    {telemetry['total_cores']} Cores Active | VmRSS: {telemetry['vm_rss_kb'] / 1024.0:.1f} MB | SHM Cache: ON{shm_str}")
    print("💡 Type 'help' in terminal for available commands at any time.")
    print("════════════════════════════════════════════════════════════════════════════════")

    # 1. Spatial structures
    spatial_grid = SpatialHashGrid(cell_size=64.0)
    pheromone_grid = PheromoneGrid(width=int(world_w // 32), height=int(world_h // 32), cell_size=32.0)

    # Import world singletons early so SaveSystem and emergency saves can reference them
    from project.world.ancient_ruins import ancient_ruins_mgr
    from project.world.miracles import world_miracles_mgr

    # 2. World Managers
    time_mgr = WorldTimeManager(seconds_per_day=120.0, days_per_year=360)
    weather_chunks = [WeatherChunk(chunk_id=i, latitude=0.0, longitude=0.0, elevation=10.0) for i in range(16)]
    weather_grid = AtmosphericGrid(weather_chunks)
    weather_mgr = WeatherManager(weather_grid)
    disaster_mgr = DisasterManager()
    soil_mgr = SoilManager()
    water_mgr = WaterManager()
    veg_mgr = VegetationManager()
    res_mgr = ResourceManager()
    food_mgr = FoodManager()

    # 3. Entity pool
    entities_list: List[Entity] = []
    pending_births = []

    # Spawn Genesis population
    spawn_genesis_population(entities_list, world_w, world_h)

    # 4. Instantiate Scheduler and register all systems
    scheduler = Scheduler(world_reference=None, target_ups=60)
    
    def do_emergency_save(name: str = "emergency_hardware_save.dat") -> str:
        data = PersistenceManager.serialize_state(
            time_mgr=time_mgr,
            soil_mgr=soil_mgr,
            water_mgr=water_mgr,
            veg_mgr=veg_mgr,
            res_mgr=res_mgr,
            entities_list=entities_list,
        )
        return PersistenceManager.save_to_file(name if name.endswith(".dat") else f"{name}.dat", data)

    spec_protection_sys = SpecProtectionSystem(emergency_save_callback=do_emergency_save)
    scheduler.register_system(spec_protection_sys)
    scheduler.register_system(SecuritySystem())
    scheduler.register_system(TimeSystem(time_mgr))
    scheduler.register_system(WeatherSystem(weather_mgr))
    scheduler.register_system(WeatherSyncSystem(weather_mgr))
    scheduler.register_system(DisasterSystem(disaster_mgr, entities_list))
    scheduler.register_system(SoilSystem(soil_mgr))
    scheduler.register_system(WaterSystem(water_mgr))
    scheduler.register_system(VegetationSystem(veg_mgr, soil_mgr, entities_list))
    scheduler.register_system(ResourceSystem(res_mgr))
    scheduler.register_system(FoodSystem(food_mgr))
    scheduler.register_system(PerceptionSystem(spatial_grid, entities_list))
    decision_sys = DecisionSystem(entities_list)
    scheduler.register_system(decision_sys)
    scheduler.register_system(PheromoneSystem(pheromone_grid, entities_list))
    scheduler.register_system(MovementSystem(entities_list, world_width=world_w, world_height=world_h))
    scheduler.register_system(CombatSystem(entities_list))
    digestion_sys = DigestionSystem(entities_list, veg_mgr, water_mgr)
    scheduler.register_system(digestion_sys)
    scheduler.register_system(AgingSystem(entities_list))
    scheduler.register_system(DeathSystem(entities_list, soil_mgr))
    reproduction_sys = ReproductionSystem(entities_list, pending_births)
    scheduler.register_system(reproduction_sys)
    scheduler.register_system(BirthSystem(entities_list, pending_births))
    scheduler.register_system(MutationSystem(entities_list, disaster_mgr))
    learning_sys = LearningSystem(entities_list)
    scheduler.register_system(learning_sys)
    gemini_sys = GeminiSystem(entities_list)
    gemini_sys.client.is_offline = is_offline
    for k in gemini_cfg.get("api_keys", []):
        gemini_sys.client.add_api_key(k)
    scheduler.register_system(gemini_sys)
    decision_sys.gemini_sys = gemini_sys
    social_sys = SocialSystem(entities_list)
    scheduler.register_system(social_sys)
    scheduler.register_system(CivilizationSystem(entities_list))
    scheduler.register_system(KnowledgeSystem(entities_list))
    scheduler.register_system(EventSystem())
    
    statistics_sys = StatisticsSystem(entities_list)
    scheduler.register_system(statistics_sys)
    
    render_sync_sys = RenderSyncSystem(entities_list)
    scheduler.register_system(render_sync_sys)
    
    save_system_instance = SaveSystem(
        entities_list=entities_list,
        time_mgr=time_mgr,
        soil_mgr=soil_mgr,
        water_mgr=water_mgr,
        veg_mgr=veg_mgr,
        res_mgr=res_mgr,
        gemini_sys=gemini_sys,
        ruins_mgr=ancient_ruins_mgr,
        miracles_mgr=world_miracles_mgr,
        autosave_interval_ticks=6000,
    )
    scheduler.register_system(save_system_instance)

    scheduler.initialize()

    # 5. Start Background Soundtrack with smooth Fade-In
    global_bgm.start(fade_in_ms=2500)

    # 6. Visual GUI manager
    renderer = SimulationRenderer(width=win_w, height=win_h, world_width=world_w, world_height=world_h)

    # Dispatch active session launch ping & start background update check
    try:
        world_telemetry_collector.dispatch_heartbeat(status="session_start")
    except Exception:
        pass

    def _bg_update_check() -> None:
        try:
            info = update_manager.check_for_updates()
            if info.has_update:
                renderer.update_info = info
                print(f"\n✨ [UPDATE AVAILABLE] New update on GitHub: '{info.commit_message}' ({info.remote_commit})")
                print("   👉 Type 'upgrade' in the terminal or click 'Update Now' in the top GUI banner.\n")
        except Exception:
            pass

    threading.Thread(target=_bg_update_check, daemon=True, name="bg-updater").start()
    renderer.is_offline = is_offline
    renderer.camera.pos_x = world_w / 2.0
    renderer.camera.pos_y = world_h / 2.0
    renderer.camera.zoom = 1.6

    tick_count = 0
    running = True

    # Terminal input listener
    def terminal_listener(cmd_queue):
        linux_optimizer.set_thread_name("term-listener")
        while running:
            try:
                line = input("CMD> ")
                if line.strip():
                    cmd_queue.append(line.strip())
            except (EOFError, KeyboardInterrupt):
                break

    # Background Backend Simulation Worker
    def simulation_worker():
        nonlocal tick_count, running
        linux_optimizer.set_thread_name("sim-engine")
        if linux_optimizer.total_cores > 1:
            # Pin simulation engine to secondary cores to keep core 0 dedicated for GUI rendering
            linux_optimizer.set_thread_affinity(list(range(1, linux_optimizer.total_cores)))

        while running:
            # 6. Process Developer Console Commands safely on backend thread
            while renderer.command_queue:
                cmd_raw = renderer.command_queue.pop(0)
                low_raw = cmd_raw.strip().lower()
                cmd_name = low_raw
                cmd_args = ""

                # Argument extraction
                if ":" in cmd_raw and (" " not in cmd_raw or cmd_raw.index(":") < cmd_raw.index(" ")):
                    parts = cmd_raw.split(":", 1)
                    cmd_name = parts[0].strip().lower()
                    cmd_args = parts[1].strip()
                elif " " in cmd_raw:
                    parts = cmd_raw.split(" ", 1)
                    cmd_name = parts[0].strip().lower()
                    cmd_args = parts[1].strip()
                elif ":" in cmd_raw:
                    parts = cmd_raw.split(":", 1)
                    cmd_name = parts[0].strip().lower()
                    cmd_args = parts[1].strip()

                # -------------------------------------------------------------
                # COMMAND DISPATCHER
                # -------------------------------------------------------------
                if cmd_name in ("help", "?", "commands"):
                    print_modern_help_menu()

                elif cmd_name == "clear":
                    os.system("cls" if os.name == "nt" else "clear")
                    renderer.console.history = []

                # -------------------- LINUX OPTIMIZER COMMANDS --------------------
                elif cmd_name.startswith("linux"):
                    sub_cmd = cmd_args.strip().lower()
                    if sub_cmd == "trim":
                        t0 = time.perf_counter()
                        before_stats = linux_optimizer.get_memory_telemetry()
                        trimmed = linux_optimizer.malloc_trim(0)
                        after_stats = linux_optimizer.get_memory_telemetry()
                        dt_ms = (time.perf_counter() - t0) * 1000.0
                        diff_kb = before_stats.get("vm_rss_kb", 0) - after_stats.get("vm_rss_kb", 0)
                        print(f"🧹 [LINUX MALLOC TRIM] Success: {trimmed} | Time: {dt_ms:.2f}ms | Freed: {diff_kb / 1024.0:+.2f} MB | New VmRSS: {after_stats.get('vm_rss_kb', 0) / 1024.0:.1f} MB")
                    elif sub_cmd.startswith("affinity"):
                        affinity_args = sub_cmd.replace("affinity", "").strip()
                        if not affinity_args and len(cmd_args.split()) > 1:
                            affinity_args = cmd_args.split(None, 1)[1].strip()
                        if affinity_args:
                            try:
                                cores = [int(c.strip()) for c in affinity_args.replace(",", " ").split()]
                                success = linux_optimizer.set_thread_affinity(cores)
                                print(f"⚡ [CPU AFFINITY] Assigned cores {cores} -> Success: {success} (Active: {linux_optimizer.get_affinity()})")
                            except Exception as e:
                                print(f"❌ [CPU AFFINITY ERROR] Invalid core list '{affinity_args}': {e}")
                        else:
                            print(f"⚡ [CPU AFFINITY] Current assigned cores: {linux_optimizer.get_affinity()} (Total available: {linux_optimizer.total_cores})")
                    else:
                        telemetry = linux_optimizer.get_memory_telemetry()
                        shm_active = CACHE_DIR.startswith("/dev/shm")
                        print("╔════════════════════════════════════════════════════════════════════════════════╗")
                        print("║                  🐧 LINUX PLATFORM & HARDWARE TELEMETRY                        ║")
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        print(f"║ OS Kernel / Platform:       {sys.platform.upper():<48} ║")
                        print(f"║ Total CPU Cores:            {telemetry.get('total_cores', 1):>48d} ║")
                        print(f"║ Thread Core Affinity:       {str(telemetry.get('active_cores', [])):<48} ║")
                        print(f"║ /dev/shm Shared RAM Cache:  {('ENABLED (' + CACHE_DIR + ')') if shm_active else 'DISABLED (fallback ./cache)' :<48} ║")
                        print(f"║ Process VmRSS:              {round(telemetry.get('vm_rss_kb', 0) / 1024.0, 1):>45.1f} MB ║")
                        print(f"║ Process VmPeak:             {round(telemetry.get('vm_peak_kb', 0) / 1024.0, 1):>45.1f} MB ║")
                        print(f"║ Total GLIBC Trims:          {telemetry.get('trim_count', 0):>48d} ║")
                        print("╚════════════════════════════════════════════════════════════════════════════════╝")

                # -------------------- QUANTUM SAVE & LOAD (MULTI-UNIVERSE PROTECTED) --------------------
                elif cmd_name == "save":
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        parts = cmd_args.split(None, 1)
                        save_name = parts[0] if parts else "manual_save.dat"
                        commit_msg = parts[1] if len(parts) > 1 else f"Manual checkpoint at Tick {tick_count:,}"
                        if not save_name.endswith(".dat") and "." not in save_name:
                            save_name = f"{save_name}.dat"
                        t0 = time.time()
                        data = PersistenceManager.serialize_state(
                            time_mgr=time_mgr,
                            soil_mgr=soil_mgr,
                            water_mgr=water_mgr,
                            veg_mgr=veg_mgr,
                            res_mgr=res_mgr,
                            entities_list=entities_list,
                            gemini_sys=gemini_sys,
                            ruins_mgr=ancient_ruins_mgr,
                            miracles_mgr=world_miracles_mgr,
                        )
                        saved_path = quantum_persistence.save_universe_checkpoint(
                            data=data,
                            name=save_name,
                            message=commit_msg,
                            cause="MANUAL"
                        )
                        duration = (time.time() - t0) * 1000.0
                        alive_c = len([e for e in entities_list if e.is_alive])
                        file_sz = round(os.path.getsize(saved_path) / 1024.0, 1)
                        univ = quantum_persistence.get_active_universe()
                        msg = f"✅ [SAVE SUCCESS] Checkpoint saved: {saved_path} (Universe '{univ.world_name}' | Tick {tick_count:,}, {alive_c} alive, {file_sz} KB | HEAD -> {univ.head_commit_id})"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        err_msg = f"❌ [SAVE ERROR] Failed to save state: {e}"
                        print(err_msg)
                        renderer.console.log(err_msg)

                # -------------------- QUANTUM MULTI-UNIVERSE TIMELINE & SANDBOX --------------------
                elif cmd_name in ("universes", "worlds"):
                    u_list = quantum_persistence.list_all_universes()
                    print("\n╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
                    print("║                                 🌌 MULTI-UNIVERSE DIRECTORY (ISOLATED PLAYTHROUGHS)                       ║")
                    print("╠═══════════════════════════════════════════════════════════════════════════════════════════════════════════╣")
                    for u in u_list:
                        marker = "🌟 [ACTIVE] " if u["is_active"] else "            "
                        print(f"║ {marker}{u['name']:<28} (ID: {u['universe_id']:<24})             ║")
                        print(f"║    Tick: {u['current_tick']:>8,d} | Peak Pop: {u['peak_population']:>4d} | Checkpoints: {u['checkpoints_count']:>3d} | Autosaves: {u['autosaves_count']:>3d} | Last: {u['last_played']} ║")
                        print("╟───────────────────────────────────────────────────────────────────────────────────────────────────────────╢")
                    print("╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════╝")
                    print("  Commands: world switch <name|id>   world new <name>   timeline   rewind [delta|safe|disaster]\n")
                    renderer.console.log(f"🌌 {len(u_list)} Universes listed in terminal.")

                elif cmd_name in ("world", "universe"):
                    w_parts = cmd_args.strip().split(None, 1)
                    sub_w = w_parts[0].lower() if w_parts else "status"
                    sub_arg = w_parts[1].strip() if len(w_parts) > 1 else ""

                    if sub_w in ("switch", "sw"):
                        if not sub_arg:
                            print("❌ Usage: world switch <name|universe_id>")
                        else:
                            switched = quantum_persistence.switch_universe(sub_arg)
                            if switched:
                                snaps = quantum_persistence.list_universe_snapshots(switched.universe_id)
                                if snaps:
                                    latest_p = snaps[0]["path"]
                                    state = PersistenceManager.load_from_file(latest_p)
                                    PersistenceManager.deserialize_state(
                                        state_dict=state,
                                        time_mgr=time_mgr,
                                        soil_mgr=soil_mgr,
                                        water_mgr=water_mgr,
                                        veg_mgr=veg_mgr,
                                        res_mgr=res_mgr,
                                        entities_list=entities_list,
                                        gemini_sys=gemini_sys,
                                        ruins_mgr=ancient_ruins_mgr,
                                        miracles_mgr=world_miracles_mgr,
                                    )
                                    tick_count = time_mgr.current_tick
                                    msg = f"🌌 [UNIVERSE SWITCH] Switched to '{switched.world_name}' & loaded {os.path.basename(latest_p)} (Tick {tick_count:,})!"
                                else:
                                    msg = f"🌌 [UNIVERSE SWITCH] Switched to '{switched.world_name}' (Empty universe, ready for simulation)!"
                                print(msg)
                                renderer.console.log(msg)
                            else:
                                print(f"❌ Universe '{sub_arg}' not found. Type 'worlds' to list all.")

                    elif sub_w in ("new", "create", "spawn"):
                        w_name = sub_arg if sub_arg else f"Universe_{time.strftime('%Y%m%d_%H%M%S')}"
                        new_u = quantum_persistence.create_universe(world_name=w_name)
                        quantum_persistence.switch_universe(new_u.universe_id)
                        time_mgr.current_tick = 0
                        time_mgr.total_seconds = 0.0
                        tick_count = 0
                        spawn_genesis_population(entities_list, world_w, world_h)
                        msg = f"🌌 [NEW UNIVERSE] Created isolated workspace '{new_u.world_name}' (ID: {new_u.universe_id}) & seeded genesis population!"
                        print(msg)
                        renderer.console.log(msg)

                    else:
                        active_u = quantum_persistence.get_active_universe()
                        print(f"🌌 Active Universe: '{active_u.world_name}' [ID: {active_u.universe_id} | Tick: {active_u.current_tick:,} | Branch: {active_u.active_branch}]")
                        renderer.console.log(f"Active World: {active_u.world_name}")

                elif cmd_name == "rewind":
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        r_target = cmd_args.strip() if cmd_args.strip() else "safe"
                        target_file, state_data = quantum_persistence.rewind(r_target)
                        PersistenceManager.deserialize_state(
                            state_dict=state_data,
                            time_mgr=time_mgr,
                            soil_mgr=soil_mgr,
                            water_mgr=water_mgr,
                            veg_mgr=veg_mgr,
                            res_mgr=res_mgr,
                            entities_list=entities_list,
                            gemini_sys=gemini_sys,
                            ruins_mgr=ancient_ruins_mgr,
                            miracles_mgr=world_miracles_mgr,
                        )
                        tick_count = time_mgr.current_tick
                        alive_c = len([e for e in entities_list if e.is_alive])
                        univ = quantum_persistence.get_active_universe()
                        msg = f"⏳ [QUANTUM REWIND] Time-traveled to Tick {tick_count:,} ({alive_c} alive) in Universe '{univ.world_name}'! Auto-forked branch '{univ.active_branch}'."
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as re:
                        err_msg = f"❌ [REWIND ERROR] Could not rewind: {re}"
                        print(err_msg)
                        renderer.console.log(err_msg)

                # -------------------- GIT-LIKE VERSION CONTROL & TIMELINES --------------------
                elif cmd_name == "git":
                    subparts = cmd_args.strip().split(None, 1)
                    sub_cmd = subparts[0].lower() if subparts else "status"
                    sub_arg = subparts[1].strip() if len(subparts) > 1 else ""

                    if sub_cmd == "status":
                        st = git_save_manager.get_status(tick_count)
                        print("╔══════════════════════════════════════════════════════════════════════════╗")
                        print("║ 🌿 GIT SIMULATION REPOSITORY STATUS                                     ║")
                        print("╠══════════════════════════════════════════════════════════════════════════╣")
                        print(f"║ Active Branch:              {st['branch']:<44} ║")
                        print(f"║ HEAD Commit:                {st['head']:<44} ║")
                        print(f"║ Last Committed Tick:        {st['head_tick']:>44,d} ║")
                        print(f"║ Current Simulation Tick:    {st['current_tick']:>44,d} ║")
                        print(f"║ Uncommitted Ticks Delta:    {st['uncommitted_ticks']:>44,d} ║")
                        print(f"║ Total Commits in DAG:       {st['total_commits']:>44d} ║")
                        print(f"║ Total Evolutionary Branches:{st['total_branches']:>44d} ║")
                        print("╚══════════════════════════════════════════════════════════════════════════╝")
                        renderer.console.log(f"🌿 Branch: {st['branch']} | HEAD: {st['head']} | Uncommitted: {st['uncommitted_ticks']:,} ticks")

                    elif sub_cmd in ("log", "history", "graph"):
                        ascii_log = git_save_manager.generate_ascii_log()
                        print(ascii_log)
                        renderer.console.log("🌿 Git Log printed to terminal.")

                    elif sub_cmd == "branch":
                        if not sub_arg:
                            print("🌿 Available Simulation Branches:")
                            for b, cid in git_save_manager.branches.items():
                                prefix = "* " if b == git_save_manager.active_branch else "  "
                                print(f"{prefix}{b:<24} -> commit {cid or '(empty)'}")
                        else:
                            success = git_save_manager.create_branch(sub_arg)
                            msg = f"🌿 Created & checked out new branch '{sub_arg}'" if success else f"❌ Branch '{sub_arg}' already exists."
                            print(msg)
                            renderer.console.log(msg)

                    elif sub_cmd in ("checkout", "co"):
                        if not sub_arg:
                            print("❌ Usage: git checkout <branch_name | commit_id>")
                        else:
                            target_file = git_save_manager.switch_branch(sub_arg)
                            if not target_file and sub_arg in git_save_manager.commits:
                                target_file = git_save_manager.commits[sub_arg].file_path

                            if target_file and os.path.exists(target_file):
                                state = PersistenceManager.load_from_file(target_file)
                                PersistenceManager.deserialize_state(
                                    state_dict=state,
                                    time_mgr=time_mgr,
                                    soil_mgr=soil_mgr,
                                    water_mgr=water_mgr,
                                    veg_mgr=veg_mgr,
                                    res_mgr=res_mgr,
                                    entities_list=entities_list,
                                    gemini_sys=gemini_sys,
                                    ruins_mgr=ancient_ruins_mgr,
                                    miracles_mgr=world_miracles_mgr,
                                )
                                tick_count = time_mgr.current_tick
                                msg = f"✅ [CHECKOUT SUCCESS] Aligned timeline to '{sub_arg}' (Tick {tick_count:,})"
                                print(msg)
                                renderer.console.log(msg)
                            else:
                                print(f"❌ Branch or commit not found: {sub_arg}")

                    elif sub_cmd == "commit":
                        msg_text = sub_arg if sub_arg else "Manual Snapshot"
                        data = PersistenceManager.serialize_state(
                            time_mgr=time_mgr,
                            soil_mgr=soil_mgr,
                            water_mgr=water_mgr,
                            veg_mgr=veg_mgr,
                            res_mgr=res_mgr,
                            entities_list=entities_list,
                            gemini_sys=gemini_sys,
                            ruins_mgr=ancient_ruins_mgr,
                            miracles_mgr=world_miracles_mgr,
                        )
                        saved_path = PersistenceManager.save_to_file("manual_save.dat", data, commit_message=msg_text)
                        msg = f"🌿 [GIT COMMIT] Snapshot committed: '{msg_text}' (HEAD: {git_save_manager.current_commit_id})"
                        print(msg)
                        renderer.console.log(msg)

                elif cmd_name in ("history", "timeline", "dag"):
                    dag_ascii = quantum_persistence.generate_timeline_ascii()
                    print(dag_ascii)
                    renderer.console.log("🌌 Quantum Timeline DAG logged to terminal.")

                elif cmd_name == "load":
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        load_name = cmd_args.strip() if cmd_args.strip() else ""
                        if not load_name:
                            saves_list = PersistenceManager.list_saves()
                            if saves_list:
                                load_name = saves_list[0]["path"]
                            else:
                                load_name = "manual_save.dat"
                        t0 = time.time()
                        state = PersistenceManager.load_from_file(load_name)
                        PersistenceManager.deserialize_state(
                            state_dict=state,
                            time_mgr=time_mgr,
                            soil_mgr=soil_mgr,
                            water_mgr=water_mgr,
                            veg_mgr=veg_mgr,
                            res_mgr=res_mgr,
                            entities_list=entities_list,
                            gemini_sys=gemini_sys,
                            ruins_mgr=ancient_ruins_mgr,
                            miracles_mgr=world_miracles_mgr,
                        )
                        tick_count = time_mgr.current_tick
                        duration = (time.time() - t0) * 1000.0
                        alive_c = len([e for e in entities_list if e.is_alive])
                        univ = quantum_persistence.get_active_universe()
                        univ.current_tick = tick_count
                        quantum_persistence._save_universe_meta(univ)
                        msg = f"✅ [LOAD SUCCESS] Loaded {os.path.basename(load_name)} in Universe '{univ.world_name}' (Tick {tick_count:,}, {alive_c} alive in {duration:.1f}ms)"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        err_msg = f"❌ [LOAD ERROR] Failed to load {load_name}: {e}"
                        print(err_msg)
                        renderer.console.log(err_msg)

                elif cmd_name in ("saves", "list saves", "list"):
                    try:
                        saves_list = PersistenceManager.list_saves()
                        if not saves_list:
                            print("📂 No save files found in saves/")
                            renderer.console.log("📂 No saves found.")
                        else:
                            lines = [
                                "",
                                "╔══════════════════════════════════════════════════════════════════════════╗",
                                "║                       💾  SAVE BROWSER  v2.0                           ║",
                                "╠═══╦════════════════════════╦════════╦═══════╦══════════╦═══════════════╣",
                                "║ # ║ Name                   ║  Size  ║ Tick  ║  Alive   ║  Saved At     ║",
                                "╠═══╬════════════════════════╬════════╬═══════╬══════════╬═══════════════╣",
                            ]
                            for i, s in enumerate(saves_list, 1):
                                tick_s  = str(s.get("tick", "?"))
                                alive_s = str(s.get("alive", "?"))
                                sha_s   = s.get("sha256", "—")
                                sha_tag = f"🔒 {sha_s[:8]}…" if sha_s and sha_s != "—" else "⚠️  legacy"
                                mod_raw = str(s.get("modified", s.get("date_str", "—")))
                                mod_s = mod_raw[5:] if len(mod_raw) >= 5 else mod_raw
                                lines.append(
                                    f"║{i:2d} ║ {s['name']:<22} ║ {s.get('size_kb', 0):5.1f}KB ║ {tick_s:>5} ║ {alive_s:>8} ║ {mod_s:<13} ║"
                                )
                                lines.append(f"║   ║   {sha_tag:<70}║")
                            lines += [
                                "╚═══╩════════════════════════╩════════╩═══════╩══════════╩═══════════════╝",
                                "  Usage: load <name|#>   delete <name>",
                                "",
                            ]
                            for l in lines:
                                print(l)
                            renderer.console.log(f"📂 {len(saves_list)} save(s) listed in terminal.")
                    except Exception as se:
                        err_msg = f"❌ [SAVES ERROR] Could not list saves: {se}"
                        print(err_msg)
                        renderer.console.log(err_msg)

                elif cmd_name == "delete":
                    try:
                        del_name = cmd_args.strip()
                        if not del_name:
                            print("❌ Usage: delete <filename>")
                        else:
                            import glob as _glob
                            base_path = PersistenceManager.resolve_save_path(del_name)
                            removed = []
                            for candidate in [base_path] + [f"{base_path}.bak{i}" for i in range(1, 4)] + [f"{base_path}.meta.json"]:
                                if os.path.exists(candidate):
                                    try:
                                        os.remove(candidate)
                                        removed.append(os.path.basename(candidate))
                                    except Exception as de:
                                        print(f"⚠️ Could not remove {candidate}: {de}")
                            if removed:
                                msg = f"🗑️  Deleted: {', '.join(removed)}"
                                print(msg)
                                renderer.console.log(msg)
                            else:
                                print(f"❌ No save files found matching: {del_name}")
                    except Exception as de:
                        print(f"❌ [DELETE ERROR] {de}")

                elif cmd_name in ("affinity", "god"):
                    try:
                        new_aff = float(cmd_args) if cmd_args else 50.0
                        gemini_sys.global_god_affinity = max(0.0, min(100.0, new_aff))
                        renderer.set_god_affinity_value(gemini_sys.global_god_affinity)
                        msg = f"⚡ Gemini God Affinity set to: {gemini_sys.global_god_affinity:.1f}%"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        print(f"❌ [AFFINITY ERROR] {e}")

                elif cmd_name == "miracle":
                    try:
                        from project.world.miracles import world_miracles_mgr
                        m_parts = cmd_args.split(",")
                        m_type = m_parts[0].strip()
                        m_cx = float(m_parts[1].strip()) if len(m_parts) > 1 else renderer.camera.pos_x
                        m_cy = float(m_parts[2].strip()) if len(m_parts) > 2 else renderer.camera.pos_y
                        m_low = m_type.lower()
                        msg = ""
                        if "solar" in m_low or "eclipse" in m_low:
                            msg = world_miracles_mgr.trigger_solar_eclipse(30.0)
                        elif "meteor" in m_low or "shower" in m_low or "stardust" in m_low:
                            msg = world_miracles_mgr.trigger_meteor_stardust_shower(m_cx, m_cy, count=8)
                        elif "rain" in m_low or "storm" in m_low:
                            msg = world_miracles_mgr.trigger_divine_rainstorm(40.0, soil_mgr)
                        elif "harvest" in m_low or "bountiful" in m_low:
                            msg = world_miracles_mgr.trigger_bountiful_harvest(entities_list, veg_mgr, m_cx, m_cy)
                        elif "epiphany" in m_low or "wave" in m_low:
                            msg = world_miracles_mgr.trigger_epiphany_wave(entities_list, tick_count)
                        elif "purge" in m_low or "threat" in m_low:
                            msg = world_miracles_mgr.trigger_purge_threats(entities_list, m_cx, m_cy)
                        else:
                            msg = f"Unknown miracle type: '{m_type}'. Available: Solar Eclipse, Meteor Shower, Divine Rainstorm, Bountiful Harvest, Epiphany Wave, Purge Threats."
                            print(f"⚠️ {msg}")
                        if msg:
                            renderer.console.log(msg)
                    except Exception as me:
                        print(f"❌ [MIRACLE ERROR] {me}")

                elif cmd_name == "spawn_species":
                    try:
                        sp_parts = cmd_args.split(",")
                        s_type = sp_parts[0].strip()
                        scx = float(sp_parts[1].strip()) if len(sp_parts) > 1 else renderer.camera.pos_x
                        scy = float(sp_parts[2].strip()) if len(sp_parts) > 2 else renderer.camera.pos_y
                        new_id = f"spawn_{s_type.lower()}_{tick_count}_{random.randint(100, 999)}"
                        s_low = s_type.lower()
                        new_ent = None
                        if s_low == "human":
                            new_ent = Human(entity_id=new_id, species_id="homo_sapiens", pos_x=scx, pos_y=scy)
                        elif s_low == "predator":
                            new_ent = Predator(entity_id=new_id, species_id="panther", pos_x=scx, pos_y=scy)
                        elif s_low == "herbivore":
                            new_ent = Herbivore(entity_id=new_id, species_id="deer", pos_x=scx, pos_y=scy)
                        elif s_low == "reptile":
                            new_ent = Reptile(entity_id=new_id, species_id="viper", pos_x=scx, pos_y=scy)
                        elif s_low == "avian":
                            new_ent = Avian(entity_id=new_id, species_id="hawk", pos_x=scx, pos_y=scy)
                        elif s_low == "amphibian":
                            new_ent = Amphibian(entity_id=new_id, species_id="frog", pos_x=scx, pos_y=scy)
                        elif s_low == "plant":
                            new_ent = Plant(entity_id=new_id, species_id="fern", pos_x=scx, pos_y=scy)
                        elif s_low == "fungus":
                            new_ent = Fungus(entity_id=new_id, species_id="mycelium", pos_x=scx, pos_y=scy)
                        elif s_low == "bacteria":
                            new_ent = Bacteria(entity_id=new_id, species_id="bacillus", pos_x=scx, pos_y=scy)
                        
                        if new_ent:
                            entities_list.append(new_ent)
                            msg = f"🌱 Spawned {s_type} at ({scx:.1f}, {scy:.1f})"
                            print(msg)
                            renderer.console.log(msg)
                    except Exception as se:
                        print(f"❌ [SPAWN ERROR] {se}")

                elif cmd_name in ("quicksave", "qs"):
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        data = PersistenceManager.serialize_state(
                            time_mgr=time_mgr,
                            soil_mgr=soil_mgr,
                            water_mgr=water_mgr,
                            veg_mgr=veg_mgr,
                            res_mgr=res_mgr,
                            entities_list=entities_list,
                            gemini_sys=gemini_sys,
                            ruins_mgr=ancient_ruins_mgr,
                            miracles_mgr=world_miracles_mgr,
                        )
                        saved_p = quantum_persistence.save_quicksave(data)
                        univ = quantum_persistence.get_active_universe()
                        msg = f"⚡ [QUICKSAVE] Fast checkpoint saved for '{univ.world_name}': {saved_p} (Tick {tick_count:,})"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        print(f"❌ [QUICKSAVE ERROR] {e}")

                elif cmd_name in ("quickload", "ql"):
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        state = quantum_persistence.load_quicksave()
                        PersistenceManager.deserialize_state(
                            state_dict=state,
                            time_mgr=time_mgr,
                            soil_mgr=soil_mgr,
                            water_mgr=water_mgr,
                            veg_mgr=veg_mgr,
                            res_mgr=res_mgr,
                            entities_list=entities_list,
                            gemini_sys=gemini_sys,
                            ruins_mgr=ancient_ruins_mgr,
                            miracles_mgr=world_miracles_mgr,
                        )
                        tick_count = time_mgr.current_tick
                        univ = quantum_persistence.get_active_universe()
                        univ.current_tick = tick_count
                        quantum_persistence._save_universe_meta(univ)
                        msg = f"⚡ [QUICKLOAD] Restored quicksave for '{univ.world_name}' (Tick {tick_count:,}, {len(entities_list)} entities)"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        print(f"❌ [QUICKLOAD ERROR] {e}")

                elif cmd_name == "autosave":
                    if not cmd_args:
                        print(f"Autosave status: {'ENABLED' if save_system_instance.enabled else 'DISABLED'}, Interval: {save_system_instance.autosave_interval_ticks} ticks")
                    else:
                        arg_low = cmd_args.lower()
                        if arg_low in ("on", "enable", "true"):
                            save_system_instance.enabled = True
                            print("Autosave ENABLED.")
                        elif arg_low in ("off", "disable", "false"):
                            save_system_instance.enabled = False
                            print("Autosave DISABLED.")
                        elif arg_low.isdigit():
                            save_system_instance.autosave_interval_ticks = int(arg_low)
                            save_system_instance.enabled = True
                            print(f"Autosave interval set to {int(arg_low)} ticks.")

                # -------------------- CACHE & BRIDGE MEMORY --------------------
                elif cmd_name in ("cache", "cache stats", "bridge", "bridge info"):
                    metrics = bridge_hub.get_hub_metrics()
                    print("╔════════════════════════════════════════════════════════════════════════════════╗")
                    print(f"║ ⚡ CACHE BRIDGE MEMORY BUS TELEMETRY ({CACHE_DIR})")
                    print("╠════════════════════════════════════════════════════════════════════════════════╣")
                    print("║ Channel Name             | Writes | Reads  | Size(KB) | W-Lat(μs) | R-Lat(μs)  ║")
                    print("╠══════════════════════════╪════════╪════════╪══════════╪═══════════╪════════════╣")
                    for m in metrics:
                        print(f"║ {m['name']:<24} | {m['writes']:>6d} | {m['reads']:>6d} | {m['size_kb']:>8.2f} | {m['write_latency_us']:>9.1f} | {m['read_latency_us']:>10.1f} ║")
                    print("╚════════════════════════════════════════════════════════════════════════════════╝")

                elif cmd_name == "cache flush":
                    count = bridge_hub.flush_all()
                    print(f"⚡ Flushed {count} cache memory bridges to disk at {CACHE_DIR}")

                elif cmd_name == "cache clear":
                    bridge_hub.clear_all()
                    print("⚡ Purged in-memory cache bridge buffers.")

                # -------------------- HARDWARE SPEC PROTECTOR --------------------
                elif cmd_name in ("hardware", "specs", "hw", "cpu"):
                    telemetry = global_spec_protector.check_safety()
                    print("╔════════════════════════════════════════════════════════════════════════════════╗")
                    print("║               🛡️ NATIVE PURE-C HARDWARE SPEC PROTECTOR                         ║")
                    print("╠════════════════════════════════════════════════════════════════════════════════╣")
                    print(f"║ CPU Utilization:       {telemetry.cpu_usage_pct:>6.1f}%  (Tripwire Limit: {global_spec_protector.max_cpu_pct:.1f}%)       ║")
                    print(f"║ Process RAM (Working): {telemetry.process_ram_mb:>6.1f} MB (Tripwire Limit: {global_spec_protector.max_process_ram_mb:.1f} MB)   ║")
                    print(f"║ System Available RAM:  {telemetry.system_ram_avail_mb:>6.1f} MB / {telemetry.system_ram_total_mb:.1f} MB              ║")
                    print(f"║ Frame Delta Latency:   {telemetry.frame_delta_ms:>6.2f} ms (Tripwire Limit: {global_spec_protector.max_frame_freeze_ms:.1f} ms)   ║")
                    status_str = "CRITICAL DANGER" if telemetry.is_danger_zone else "OPTIMAL & SAFE"
                    print(f"║ Hardware Safety State: {status_str:<20}                        ║")
                    print(f"║ Protection Engine:     Native C Dynamic Library (Sub-microsecond Poll) ║")
                    print("╚════════════════════════════════════════════════════════════════════════════════╝")

                elif cmd_name == "protector":
                    try:
                        parts = [float(p.strip()) for p in cmd_args.split(",")] if "," in cmd_args else [float(p.strip()) for p in cmd_args.split()]
                        if len(parts) >= 1:
                            global_spec_protector.max_cpu_pct = parts[0]
                        if len(parts) >= 2:
                            global_spec_protector.max_process_ram_mb = parts[1]
                        if len(parts) >= 3:
                            global_spec_protector.min_avail_ram_mb = parts[2]
                        global_spec_protector.init_hardware_limits(
                            global_spec_protector.max_cpu_pct,
                            global_spec_protector.max_process_ram_mb,
                            global_spec_protector.min_avail_ram_mb,
                            global_spec_protector.max_frame_freeze_ms
                        )
                        print(f"🛡️ [SPEC PROTECTOR] Updated thresholds: CPU Max={global_spec_protector.max_cpu_pct}%, Process RAM Max={global_spec_protector.max_process_ram_mb}MB, Min Free RAM={global_spec_protector.min_avail_ram_mb}MB")
                    except Exception as e:
                        print(f"Usage: protector <max_cpu_pct> [max_process_ram_mb] [min_avail_ram_mb]")

                elif cmd_name in ("resume protector", "reset protector", "unfreeze"):
                    spec_protection_sys.resume_simulation()
                    renderer.simulation_speed = 1.0
                    print("▶️ Resumed simulation and reset hardware safety tripwire.")

                # -------------------- GEMINI MULTI-KEY COGNITION ROUTER --------------------
                elif cmd_name in ("apikey", "key", "setkey"):
                    if not cmd_args.strip():
                        curr_k = gemini_sys.client.get_current_key()
                        print(f"🔑 Current Active Key: {curr_k[:10] + '...' + curr_k[-4:] if curr_k else 'None (Running Offline Cognitive Engine)'}")
                    else:
                        new_k = cmd_args.strip()
                        gemini_sys.client.add_api_key(new_k)
                        user_profile_manager.add_gemini_key(new_k)
                        gemini_sys.client.is_offline = False
                        renderer.is_offline = False
                        msg = f"✅ Registered API key ({new_k[:8]}...{new_k[-4:]}) into intelligent multi-key routing pool."
                        print(msg)
                        renderer.console.log(msg)

                elif cmd_name in ("apikeys", "keys"):
                    stats = gemini_sys.client.get_pool_status()
                    print("╔════════════════════════════════════════════════════════════════════════════════╗")
                    print("║ 🌟 GEMINI MULTI-KEY INTELLIGENT ROUTER POOL                                    ║")
                    print("╠════╦════════════════╦════════════╦══════════╦════════════╦═════════════════════╣")
                    print("║ #  ║ Key Mask       ║ Status     ║ Cooldown ║ Successes  ║ Avg Latency (EMA)   ║")
                    print("╠════╬════════════════╬════════════╬══════════╬════════════╬═════════════════════╣")
                    if not stats:
                        print("║    ║ (Pool is empty — Currently running in 100% Offline Heuristic Mode)        ║")
                    for i, s in enumerate(stats, 1):
                        cd_str = f"{s['cooldown_s']:.1f}s" if s['cooldown_s'] > 0 else "Ready"
                        print(f"║ {i:2d} ║ {s['masked_key']:<14} ║ {s['status']:<10} ║ {cd_str:>8} ║ {s['success_count']:>10d} ║ {s['avg_latency_ms']:>14.1f} ms ║")
                    print("╚════╩════════════════╩════════════╩══════════╩════════════╩═════════════════════╝")
                    renderer.console.log(f"🌟 {len(stats)} Gemini key(s) in multi-key rotation pool.")

                elif cmd_name == "rmkey":
                    target = cmd_args.strip()
                    if not target:
                        print("❌ Usage: rmkey <index|key>")
                    else:
                        idx = int(target) - 1 if target.isdigit() else target
                        if gemini_sys.client.remove_api_key(idx):
                            user_profile_manager.remove_gemini_key(idx)
                            print(f"🗑️ Removed key from routing pool.")
                            renderer.console.log(f"🗑️ Removed key from pool.")
                        else:
                            print(f"❌ Key '{target}' not found in pool.")

                elif cmd_name == "offline":
                    gemini_sys.client.is_offline = True
                    renderer.is_offline = True
                    user_profile_manager.set_offline_mode(True)
                    msg = "🟢 [OFFLINE MODE] Forced local neural heuristics. Pseudo affinity meter disabled."
                    print(msg)
                    renderer.console.log(msg)

                elif cmd_name == "online":
                    if gemini_sys.client._keys_pool:
                        gemini_sys.client.is_offline = False
                        renderer.is_offline = False
                        user_profile_manager.set_offline_mode(False)
                        msg = f"🌟 [ONLINE MODE] Gemini deity routing active with {len(gemini_sys.client._keys_pool)} keys."
                    else:
                        msg = "⚠️ Cannot go online: No API keys configured. Use 'apikey <key>' to add one."
                    print(msg)
                    renderer.console.log(msg)

                # -------------------- PRIVACY, TELEMETRY & SETUP --------------------
                elif cmd_name == "telemetry":
                    sub = cmd_args.strip().lower()
                    prof = user_profile_manager.get_profile()
                    if sub == "on":
                        prof.privacy_and_telemetry["consent_given"] = True
                        user_profile_manager.save_profile(prof)
                        print("✅ Anonymized telemetry & crash diagnostics ENABLED (Opt-in).")
                        renderer.console.log("Telemetry ENABLED (Opt-in).")
                    elif sub == "off":
                        prof.privacy_and_telemetry["consent_given"] = False
                        user_profile_manager.save_profile(prof)
                        print("🔒 Anonymized telemetry & crash diagnostics DISABLED.")
                        renderer.console.log("Telemetry DISABLED.")
                    elif sub == "preview":
                        sample = telemetry_dispatcher.get_sample_payload()
                        print("📋 Sample scrubbed telemetry payload:")
                        print(json.dumps(sample, indent=2))
                    else:
                        st = "ENABLED" if prof.privacy_and_telemetry.get("consent_given") else "DISABLED"
                        print(f"📊 Telemetry Status: {st} (Commands: telemetry on | telemetry off | telemetry preview)")

                elif cmd_name in ("setup", "firstrun"):
                    print("🌟 [SETUP WIZARD] Triggered manual environment configuration setup...")
                    renderer.console.log("Setup wizard launched.")
                    try:
                        from project.renderer.setup_wizard import run_setup_wizard
                        new_prof = run_setup_wizard()
                        gemini_sys.client.is_offline = new_prof.gemini.get("is_offline", False)
                        renderer.is_offline = gemini_sys.client.is_offline
                        print(f"✅ Setup completed. Profile updated for '{new_prof.user_name}'.")
                    except Exception as swe:
                        print(f"❌ [SETUP ERROR] Could not run setup wizard: {swe}")

                # -------------------- SIMULATION CONTROL --------------------
                elif cmd_name == "pause":
                    renderer.simulation_speed = 0.0
                    print("⏸️  Simulation PAUSED.")

                elif cmd_name in ("play", "resume"):
                    renderer.simulation_speed = 1.0
                    print("▶️  Simulation RESUMED (1x speed).")

                elif cmd_name == "speed":
                    try:
                        spd = float(cmd_args) if cmd_args else 1.0
                        renderer.simulation_speed = spd
                        print(f"⏩ Simulation speed set to {spd:.1f}x.")
                    except ValueError:
                        print("Error: speed requires a numeric multiplier (e.g., 'speed 2.5')")

                elif cmd_name == "reset":
                    spawn_genesis_population(entities_list, world_w, world_h)
                    time_mgr.reset()
                    tick_count = 0
                    print("🔄 World reset: Re-seeded genesis organisms with fresh AI Neural Networks.")

                # -------------------- AUDIO & BACKGROUND MUSIC --------------------
                elif cmd_name in ("bgm", "music", "audio"):
                    if not cmd_args.strip():
                        status = "Playing" if global_bgm.is_playing else "Stopped"
                        mute_str = " (Muted)" if global_bgm.is_muted else ""
                        track_name = os.path.basename(global_bgm.audio_path) if global_bgm.audio_path else "None"
                        print(f"🎵 [BGM] Status: {status}{mute_str} | Volume: {int(global_bgm.target_volume * 100)}% | Track: {track_name}")
                    else:
                        sub = cmd_args.strip().lower()
                        if sub in ("on", "play", "start", "resume"):
                            global_bgm.start(fade_in_ms=2000)
                        elif sub in ("off", "stop", "pause"):
                            global_bgm.stop(fade_out_ms=1500)
                        elif sub in ("mute", "unmute", "toggle"):
                            global_bgm.toggle_mute()
                        elif sub.startswith("vol"):
                            try:
                                vol_val = float(sub.split()[-1])
                                if vol_val > 1.0:
                                    vol_val /= 100.0
                                global_bgm.set_volume(vol_val)
                                print(f"🔊 [BGM] Volume adjusted to {int(global_bgm.target_volume * 100)}%.")
                            except Exception:
                                print("Usage: bgm volume <0-100>")
                        else:
                            print("Usage: bgm [on|off|mute|volume <0-100>]")

                # -------------------- UI DISPLAY --------------------
                elif cmd_name == "uio":
                    renderer.ui_active = True
                    print("🖥️  UI visual rendering ENABLED.")

                elif cmd_name == "uiof":
                    renderer.ui_active = False
                    print("🖥️  UI visual rendering DISABLED (Running pure 0% GPU background mode).")

                # -------------------- STEP DEEP TIME --------------------
                elif cmd_name == "step":
                    try:
                        args = cmd_args.split()
                        amount = int(args[0]) if args else 1
                        unit = args[1].lower() if len(args) > 1 else "ticks"

                        ticks_to_run = amount
                        dt_override = None

                        if unit in ("year", "years"):
                            ticks_to_run = amount
                            dt_override = 2592000.0
                        elif unit in ("day", "days"):
                            ticks_to_run = amount
                            dt_override = 7200.0

                        print(f"Stepping simulation by {amount} {unit} (Quantum Deep Time mode: {ticks_to_run} cycles)...")

                        if ticks_to_run > 100:
                            scheduler.unregister_system("RenderSyncSystem")

                        prev_speed = getattr(renderer, "simulation_speed", 0.0)
                        renderer.simulation_speed = 0.0

                        time.sleep(0.05)
                        step_start = time.time()

                        for i in range(ticks_to_run):
                            try:
                                scheduler.update(dt_override=dt_override)
                                tick_count += 1
                                if i > 0 and i % 100 == 0:
                                    pct = (i / ticks_to_run) * 100.0
                                    bar_len = 35
                                    filled = int(bar_len * i / ticks_to_run)
                                    bar = '█' * filled + '░' * (bar_len - filled)
                                    print(f"\r[LOADING] {bar} {pct:.1f}% ({time.time()-step_start:.1f}s)", end='', flush=True)
                            except Exception as e:
                                print(f"\nCRASH HANDLER (Step command): Exception in scheduler: {e}")
                                import traceback
                                traceback.print_exc()
                                break

                        if ticks_to_run > 100:
                            scheduler.register_system(render_sync_sys)

                        renderer.simulation_speed = prev_speed
                        print(f"\n✅ Done stepping {amount} {unit} in {(time.time()-step_start):.2f}s.")
                    except Exception as e:
                        print(f"Error: step requires a number (and optional unit: ticks/days/years). Details: {e}")

                # -------------------- ECOSYSTEM & DIAGNOSTICS --------------------
                elif cmd_name == "status":
                    alive_entities = len([e for e in entities_list if e.is_alive])
                    leader_id = getattr(social_sys, "current_leader_id", "None") if 'social_sys' in locals() else "None"
                    print(f"📊 Status: Tick={tick_count:,} | Active Organisms={alive_entities} | Sim Speed={renderer.simulation_speed:.1f}x | Leader={leader_id}")

                elif cmd_name in ("stats", "metrics"):
                    print("╔════════════════════════════════════════════════════════════════════════════════╗")
                    print("║                         ECOSYSTEM METRICS DASHBOARD                            ║")
                    print("╠════════════════════════════════════════════════════════════════════════════════╣")
                    alive = [e for e in entities_list if e.is_alive]
                    print(f"║ Total Entities: {len(entities_list):<6} | Alive Organisms: {len(alive):<6} | Sim Tick: {tick_count:<12,} ║")
                    if alive:
                        avg_age = sum(getattr(e, 'age_ticks', 0) for e in alive) / len(alive)
                        avg_energy = sum(getattr(e, 'energy', 0) for e in alive) / len(alive)
                        avg_hydration = sum(getattr(e, 'hydration', 0) for e in alive) / len(alive)
                        max_conns = max([e.brain.total_synaptic_connections for e in alive if e.brain] or [0])
                        print(f"║ Avg Age: {avg_age:>8.1f} ticks | Avg Energy: {avg_energy:>8.1f} | Top Synapses: {max_conns:>8d} ║")
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        print("║ Emergent Roles Breakdown:                                                      ║")
                        role_counts = {}
                        for e in alive:
                            r = e.custom_data.get("emergent_role", "CITIZEN")
                            role_counts[r] = role_counts.get(r, 0) + 1
                        for r_name, r_cnt in role_counts.items():
                            print(f"║   - {r_name:<20}: {r_cnt:>6} organisms                                         ║")
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        print("║ Species Breakdown:                                                             ║")
                        counts = {}
                        for e in alive:
                            counts[e.entity_type.name] = counts.get(e.entity_type.name, 0) + 1
                        for k, v in counts.items():
                            print(f"║   - {k:<20}: {v:>6} organisms                                         ║")
                    print("╚════════════════════════════════════════════════════════════════════════════════╝")

                elif cmd_name == "bacterium status":
                    try:
                        selected_id = renderer.selected_entity_id
                        if not selected_id:
                            found = next((e for e in entities_list if e.is_alive and e.entity_type == EntityType.BACTERIA), None)
                            if not found:
                                found = next((e for e in entities_list if e.is_alive), None)
                        else:
                            found = next((e for e in entities_list if e.entity_id == selected_id), None)

                        if found:
                            age = getattr(found, 'age_ticks', 0)
                            energy = getattr(found, 'energy', 10.0)
                            cd = found.custom_data
                            role_title = cd.get("role_title", "Microbe")
                            synapses = found.brain.total_synaptic_connections if found.brain else 0
                            print("╔════════════════════════════════════════════════════════════════════════════════╗")
                            print(f"║ BACTERIUM / ORGANISM STATUS: {found.entity_id[:35]:<48} ║")
                            print("╠════════════════════════════════════════════════════════════════════════════════╣")
                            print(f"║ Type: {found.entity_type.name:<12} | Role: {role_title:<22} | Synapses: {synapses:>6d} ║")
                            print(f"║ Energy: {found.energy:>6.1f} / {found.max_energy:>5.1f} | Hydration: {found.hydration:>6.1f} / {found.max_hydration:>5.1f} | Age: {found.age_ticks:>8} ║")
                            print(f"║ Generation: {getattr(found, 'generation', 1):>6d} | Fissions/Divisions: {getattr(reproduction_sys, 'division_event_count', 0):>6d}               ║")
                            print("╠════════════════════════════════════════════════════════════════════════════════╣")
                            print("║ Neuromodulator Hormones:                                                       ║")
                            print(f"║   Dopamine:   {cd.get('dopamine', 0.0):>7.2f} | Serotonin:  {cd.get('serotonin', 0.0):>7.2f} | Stress:     {cd.get('stress', 0.0):>7.2f} ║")
                            print(f"║   Fear:       {cd.get('fear', 0.0):>7.2f} | Curiosity:  {cd.get('curiosity', 0.0):>7.2f} | Confidence: {cd.get('confidence', 0.0):>7.2f} ║")
                            print("╚════════════════════════════════════════════════════════════════════════════════╝")
                        else:
                            print("Error: No organism selected or found.")
                    except Exception as bse:
                        print(f"❌ [BACTERIUM ERROR] {bse}")

                elif cmd_name == "civilization integration":
                    try:
                        alive_humans = [e for e in entities_list if e.is_alive and e.entity_type == EntityType.HUMAN]
                        leader = next((e for e in entities_list if e.is_alive and e.custom_data.get("emergent_role") == "LEADER"), None)
                        leader_id = leader.entity_id if leader else "None"
                        leader_con = leader.custom_data.get("consciousness_level", 0.0) * 100.0 if leader else 0.0
                        leader_syn = leader.brain.total_synaptic_connections if leader and leader.brain else 0
                        god_affinity = getattr(gemini_sys, "global_god_affinity", 10.0) if 'gemini_sys' in locals() else 10.0

                        print("╔════════════════════════════════════════════════════════════════════════════════╗")
                        print("║                 CIVILIZATION & GOD RESONANCE DASHBOARD                         ║")
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        print(f"║ Sovereign Leader:           {leader_id:<46} ║")
                        print(f"║ Leader Consciousness:       {leader_con:>24.1f}%                          ║")
                        print(f"║ Leader Neural Synapses:     {leader_syn:>25d}                          ║")
                        print(f"║ Gemini Deity God Affinity:  {god_affinity:>24.1f}%                          ║")
                        print(f"║ Sentient Tribe Population:  {len(alive_humans):>25d}                          ║")
                        print("╚════════════════════════════════════════════════════════════════════════════════╝")
                    except Exception as cie:
                        print(f"❌ [CIVILIZATION ERROR] {cie}")

                elif cmd_name.startswith("feed human") or cmd_name == "feed":
                    try:
                        args = cmd_args.split()
                        e_val = float(args[0]) if args and args[0].replace('.', '', 1).isdigit() else 200.0
                        h_val = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 100.0
                        fed_cnt = digestion_sys.feed_humans(e_val, h_val)
                        print(f"🍖 [FEED HUMANS] Satiated {fed_cnt} human(s) with +{e_val:.0f} energy & +{h_val:.0f} hydration! (Dopamine peak active)")
                    except Exception as e:
                        print(f"Error feeding humans: {e}")

                elif cmd_name.startswith("train human") or cmd_name == "train":
                    try:
                        cycles = int(cmd_args.strip()) if cmd_args.strip().isdigit() else 50
                        print(f"🧠 [DEEP TRAINING] Training Human species across 50MB Experience Replay Matrices ({cycles} cycles)...")
                        trained_cnt = learning_sys.train_humans(iterations=cycles)
                        print(f"✅ [TRAINING COMPLETE] Trained {trained_cnt} human(s) for {cycles} mini-batch cycles! IQ and synaptic weights strengthened.")
                    except Exception as e:
                        print(f"Error training humans: {e}")

                elif cmd_name == "inspect":
                    try:
                        target_id = cmd_args.strip()
                        if not target_id:
                            print("Error: Specify an entity ID (e.g., 'inspect genesis_bac_0')")
                        else:
                            found = next((e for e in entities_list if e.entity_id == target_id), None)
                            if found:
                                print(f"--- DETAILED INSPECTION: {found.entity_id} ---")
                                print(f"Type: {found.entity_type.name} | Age: {getattr(found, 'age_ticks', 0)}")
                                print(f"Position: ({found.pos_x:.2f}, {found.pos_y:.2f}) | Velocity: ({found.vel_x:.2f}, {found.vel_y:.2f})")
                                print(f"Energy: {getattr(found, 'energy', 0):.2f}/{getattr(found, 'max_energy', 1)}")
                                print(f"Hydration: {getattr(found, 'hydration', 0):.2f}/{getattr(found, 'max_hydration', 1)}")
                                if found.brain:
                                    print(f"Neural Network: ACTIVE (Inputs: {found.brain.input_size}, Hidden: {found.brain.hidden_sizes}, Outputs: {found.brain.output_size})")
                                else:
                                    print("Neural Network: None")
                                print(f"Custom Data Keys: {list(found.custom_data.keys())}")
                            else:
                                print(f"Entity '{target_id}' not found.")
                    except Exception as ie:
                        print(f"❌ [INSPECT ERROR] {ie}")

                elif cmd_name == "kill":
                    try:
                        target = cmd_args.strip().upper()
                        if not target:
                            print("Error: Specify 'ALL' or species type (e.g., 'kill ALL', 'kill BACTERIA')")
                        elif target == "ALL":
                            entities_list.clear()
                            print("💀 Purged all entities from the ecosystem.")
                        else:
                            to_remove = [e for e in entities_list if e.entity_type.name == target]
                            for e in to_remove:
                                entities_list.remove(e)
                            print(f"💀 Purged {len(to_remove)} entities of type {target}.")
                    except Exception as ke:
                        print(f"❌ [KILL ERROR] {ke}")

                elif cmd_name in ("seeds", "seed log", "seed logs", "seed stats"):
                    try:
                        from project.world.seeds import world_seed_growth_mgr, seed_logger
                        recent = seed_logger.get_recent_logs(10)
                        print("╔════════════════════════════════════════════════════════════════════════════════╗")
                        print(f"║ 🌰 PLANETARY SEED & FRUIT GROWTH LOGS (Total Abnormalities: {world_seed_growth_mgr.total_abnormal_mutations})")
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        print(f"║ Active Growing Seeds in Soil: {len(world_seed_growth_mgr.active_seeds):<5} | Total Germinated: {world_seed_growth_mgr.total_seeds_germinated:<6}   ║")
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        if not recent:
                            print("║   No fruit seed discard events recorded yet. Organisms leave seeds after eating║")
                        else:
                            for entry in recent[-8:]:
                                if entry.get("event") == "FRUIT_EATEN_SEEDS_DISCARDED":
                                    fruit_c = entry.get("fruit_consumed", "Fruit")
                                    eater = entry.get("eater_id", "Organism")
                                    s_cnt = entry.get("seeds_left_count", 1)
                                    loc = entry.get("location", {})
                                    print(f"║ Tick {entry.get('sim_tick', 0):<6} | {eater[:18]:<18} ate {fruit_c:<8} -> {s_cnt} seeds left at ({loc.get('x',0):.1f},{loc.get('y',0):.1f}) ║")
                                elif entry.get("event") == "SEED_MATURED_TO_FLORA":
                                    s_name = entry.get("parent_fruit", "Flora")
                                    ab = entry.get("abnormality_trait", "Normal")
                                    print(f"║ Tick {entry.get('sim_tick', 0):<6} | 🌟 SEED MATURED: {s_name:<8} [{ab:<22}] -> Plant spawned!║")
                        print("╚════════════════════════════════════════════════════════════════════════════════╝")
                    except Exception as se:
                        print(f"❌ [SEEDS ERROR] {se}")

                elif cmd_name == "food":
                    try:
                        raw_parts = [p.strip() for p in cmd_args.split(",")]
                        if len(raw_parts) >= 2:
                            if not raw_parts[0].replace('.','',1).isdigit() and not raw_parts[0].startswith("-"):
                                ftype = raw_parts[0].lower()
                                raw_parts = raw_parts[1:]
                            else:
                                ftype = "mango"
                            if len(raw_parts) >= 2:
                                fx, fy = float(raw_parts[0]), float(raw_parts[1])
                                if fx <= 1.0: fx *= world_w
                                if fy <= 1.0: fy *= world_h
                                fr = float(raw_parts[2]) if len(raw_parts) > 2 else 5.0
                                new_food = Plant(
                                    entity_id=f"cmd_food_{ftype}_{random.randint(1000, 9999)}",
                                    species_id=f"food_{ftype}",
                                    pos_x=fx,
                                    pos_y=fy,
                                )
                                new_food.radius = fr
                                new_food.custom_data["is_food"] = True
                                new_food.custom_data["fruit_type"] = ftype
                                entities_list.append(new_food)
                                print(f"🌱 Spawned {ftype} food with seeds at ({fx:.1f}, {fy:.1f}) radius {fr:.1f}")
                            else:
                                print("Error: food requires x,y")
                        else:
                            print("Error: food requires x,y (and optional type, size)")
                    except Exception as e:
                        print(f"Error spawning food: {e}")

                elif cmd_name == "command" or cmd_name == "chat":
                    try:
                        avatar = next((e for e in entities_list if e.is_alive and e.custom_data.get("emergent_role") == "DEITY_AVATAR"), None)
                        if avatar:
                            print(f"\n⚡ Gemini God Avatar hears your command: '{cmd_args}'")
                            print("⚡ The Deity's consciousness integrates your command into the simulation.")
                            avatar.think(f"USER COMMAND RECEIVED: {cmd_args}", category="DIVINE", valence=1.0)
                        else:
                            print("Error: The Gemini God Avatar has not incarnated yet. Attain 100% God Affinity first.")
                    except Exception as ce:
                        print(f"❌ [COMMAND CHAT ERROR] {ce}")
                        
                elif cmd_name == "spawn_god":
                    try:
                        from project.entities.gemini_god_avatar import GeminiGodAvatar
                        from project.systems.gemini_system import GeminiSystem
                        
                        # Find gemini sys in scheduler
                        _gemini_sys = None
                        for sys in scheduler.registry.get_active_systems():
                            if isinstance(sys, GeminiSystem):
                                _gemini_sys = sys
                                break
                                
                        if _gemini_sys:
                            _gemini_sys.global_god_affinity = 100.0
                            _gemini_sys.god_incarnated = True
                            ax, ay = 500.0, 500.0
                            avatar = GeminiGodAvatar(
                                entity_id="gemini_deity_incarnate_cheat",
                                species_id="homo_sapiens",
                                pos_x=ax,
                                pos_y=ay,
                            )
                            entities_list.append(avatar)
                            print(f"⚡ [CHEAT] Spawning Gemini God Avatar at ({ax:.1f}, {ay:.1f})")
                        else:
                            print("Error: Gemini System not initialized.")
                    except Exception as ge:
                        print(f"❌ [SPAWN GOD ERROR] {ge}")

                elif cmd_name == "spawn":
                    try:
                        parts = cmd_args.split(",")
                        if len(parts) >= 3:
                            etype = parts[0].strip().upper()
                            sx = float(parts[1].strip())
                            sy = float(parts[2].strip())
                            if sx <= 1.0: sx *= world_w
                            if sy <= 1.0: sy *= world_h

                            new_ent = None
                            eid = f"cmd_spawn_{random.randint(1000, 9999)}"
                            if etype == "BACTERIA":
                                new_ent = Bacteria(entity_id=eid, species_id="chemophile", pos_x=sx, pos_y=sy)
                            elif etype == "PLANT":
                                new_ent = Plant(entity_id=eid, species_id="fern", pos_x=sx, pos_y=sy)
                            elif etype == "HERBIVORE":
                                new_ent = Herbivore(entity_id=eid, species_id="gazelle", pos_x=sx, pos_y=sy)
                            elif etype == "PREDATOR":
                                new_ent = Predator(entity_id=eid, species_id="panther", pos_x=sx, pos_y=sy)
                            elif etype == "HUMAN":
                                new_ent = Human(entity_id=eid, species_id="homo_sapiens", pos_x=sx, pos_y=sy)
                            elif etype == "AVIAN":
                                new_ent = Avian(entity_id=eid, species_id="falcon", pos_x=sx, pos_y=sy)
                            elif etype == "AMPHIBIAN":
                                new_ent = Amphibian(entity_id=eid, species_id="axolotl", pos_x=sx, pos_y=sy)
                            elif etype == "ARTHROPOD":
                                new_ent = Arthropod(entity_id=eid, species_id="pollinator_bee", pos_x=sx, pos_y=sy)
                            elif etype == "REPTILE":
                                new_ent = Reptile(entity_id=eid, species_id="viper", pos_x=sx, pos_y=sy)
                            elif etype == "FUNGUS":
                                new_ent = Fungus(entity_id=eid, species_id="mycelium_morel", pos_x=sx, pos_y=sy)
                            else:
                                print(f"Error: Unknown type '{etype}'. Use BACTERIA, PLANT, HERBIVORE, PREDATOR, HUMAN, AVIAN, AMPHIBIAN, ARTHROPOD, REPTILE, FUNGUS.")

                            if new_ent:
                                entities_list.append(new_ent)
                                print(f"🐣 Spawned {etype} at ({sx:.1f}, {sy:.1f}) with active Neural Brain.")
                        else:
                            print("Error: spawn requires type,x,y")
                    except Exception as e:
                        print(f"Error spawning entity: {e}")

                elif cmd_name in ("upgrade", "update"):
                    parts = cmd_args.strip().split()
                    sub_cmd = parts[0].lower() if parts else "apply"

                    if sub_cmd == "check":
                        print("🔍 Checking GitHub repository for updates...")
                        info = update_manager.check_for_updates(force=True)
                        renderer.update_info = info
                        if info.has_update:
                            print(f"\n✨ Update Available! Remote: [{info.remote_commit}], Local: [{info.current_commit}]")
                            print(f"   Commit Message: {info.commit_message}")
                            print(f"   Author: {info.author} | Date: {info.commit_date}")
                            print("   👉 Type 'upgrade' to execute 3-step verification and install.\n")
                        else:
                            print(f"✅ Simulation is up to date (Commit: [{info.current_commit}]).\n")
                    else:
                        def run_upgrade():
                            renderer.is_updating_ui = True
                            print("\n════════════════════════════════════════════════════════════════════════")
                            print("🚀 EXECUTING AUTONOMOUS SIMULATION UPGRADE & 3-STEP VERIFICATION")
                            print("════════════════════════════════════════════════════════════════════════")

                            def on_progress(status_msg, pct):
                                renderer.update_status_text = status_msg
                                print(f"[{int(pct * 100)}%] {status_msg}")

                            ok, msg = update_manager.apply_update(progress_callback=on_progress)
                            renderer.is_updating_ui = False
                            if ok:
                                renderer.update_info = None
                                renderer.console.log("✅ Upgrade Succeeded! Restart to apply new mechanics.")
                                print(f"\n🎉 {msg}\n")
                            else:
                                renderer.console.log(f"❌ Upgrade Failed: {msg}")
                                print(f"\n❌ {msg}\n")

                        threading.Thread(target=run_upgrade, daemon=True, name="upgrade-worker").start()

                elif cmd_name.startswith("telemetry"):
                    parts = cmd_args.strip().split()
                    sub_cmd = parts[0].lower() if parts else "status"

                    prof = user_profile_manager.get_profile()
                    consent = prof.privacy_and_telemetry.get("consent_given", False)

                    if sub_cmd == "status":
                        print("\n════════════════════════════════════════════════════════════════")
                        print("📡 SIMULATION TELEMETRY & RESEARCH HUB STATUS")
                        print("════════════════════════════════════════════════════════════════")
                        print(f"• User Consent Granted  : {'YES (Opt-In)' if consent else 'NO (Strictly Disabled)'}")
                        print(f"• Telemetry Mode        : {prof.privacy_and_telemetry.get('telemetry_mode')}")
                        print(f"• Anonymized Client ID  : {prof.privacy_and_telemetry.get('anonymized_client_id')}")
                        print(f"• Session ID            : {world_telemetry_collector.session_id}")
                        print(f"• Session Uptime        : {round(world_telemetry_collector.get_uptime_seconds() / 60.0, 1)} minutes")
                        print(f"• World State Level     : {prof.privacy_and_telemetry.get('world_data_level', 'full').upper()}")
                        print("════════════════════════════════════════════════════════════════\n")

                    elif sub_cmd == "ping":
                        if not consent:
                            print("⚠️ Telemetry is currently disabled in your profile (No consent).")
                        else:
                            world_telemetry_collector.dispatch_heartbeat(
                                tick=tick_count,
                                entities_count=len([e for e in entities_list if e.is_alive]),
                                fps=renderer.clock.get_fps(),
                                status="manual_ping"
                            )
                            print("📡 Active user heartbeat dispatched successfully.")

                    elif sub_cmd in ("send_world", "dump", "export"):
                        if not consent:
                            print("⚠️ Telemetry is currently disabled in your profile (No consent).")
                        else:
                            level = parts[1].upper() if len(parts) > 1 else None
                            from project.world.ancient_ruins import ancient_ruins_mgr
                            from project.world.miracles import world_miracles_mgr
                            world_telemetry_collector.dispatch_world_state(
                                entities_list=entities_list,
                                time_mgr=time_mgr,
                                weather_mgr=weather_mgr,
                                soil_mgr=soil_mgr,
                                water_mgr=water_mgr,
                                veg_mgr=veg_mgr,
                                res_mgr=res_mgr,
                                ruins_mgr=ancient_ruins_mgr,
                                miracles_mgr=world_miracles_mgr,
                                force_level=level,
                            )
                            print(f"🌍 World state telemetry [{level or 'FULL'}] packaged and dispatched.")

                    elif sub_cmd == "level":
                        if len(parts) > 1 and parts[1].lower() in ("summary", "deep", "full"):
                            new_lvl = parts[1].lower()
                            prof.privacy_and_telemetry["world_data_level"] = new_lvl
                            user_profile_manager.save_profile(prof)
                            print(f"✅ World data sharing level updated to: '{new_lvl.upper()}'")
                        else:
                            print("Usage: telemetry level [summary | deep | full]")

                elif cmd_name in ("exit", "quit"):
                    print("🚪 Initiating clean shutdown sequence...")
                    running = False
                    # Auto-flush bridges before exit
                    bridge_hub.flush_all()
                    import pygame
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                    break

                else:
                    print(f"Error: Unknown command '{cmd_raw}'. Type 'help' for command reference.")

            # -------------------------------------------------------------
            # BACKEND ENGINE ECS TICK EXECUTION
            # -------------------------------------------------------------
            speed = renderer.simulation_speed
            if speed > 0.0:
                try:
                    scheduler.update()
                    tick_count += 1
                    
                    from project.world.ancient_ruins import ancient_ruins_mgr
                    from project.world.miracles import world_miracles_mgr
                    world_miracles_mgr.update(0.1, entities_list)
                    if tick_count % 5 == 0:
                        ancient_ruins_mgr.update_exploration(entities_list, tick_count)

                    # Periodic Active User Heartbeat & Research World State Dispatch
                    if tick_count > 0 and tick_count % 1800 == 0:
                        try:
                            world_telemetry_collector.dispatch_heartbeat(
                                tick=tick_count,
                                entities_count=len([e for e in entities_list if e.is_alive]),
                                fps=renderer.clock.get_fps(),
                            )
                            world_telemetry_collector.dispatch_world_state(
                                entities_list=entities_list,
                                time_mgr=time_mgr,
                                weather_mgr=weather_mgr,
                                soil_mgr=soil_mgr,
                                water_mgr=water_mgr,
                                veg_mgr=veg_mgr,
                                res_mgr=res_mgr,
                                ruins_mgr=ancient_ruins_mgr,
                                miracles_mgr=world_miracles_mgr,
                            )
                        except Exception:
                            pass
                except Exception as e:
                    print(f"CRASH HANDLER (Main loop): Exception in backend scheduler: {e}")
                    import traceback
                    traceback.print_exc()
                    renderer.simulation_speed = 0.0

                # ---------------------------------------------------------
                # ---------------------------------------------------------
                # HIGH-RESPONSIVENESS REAL-TIME SIMULATION CLOCK
                # ---------------------------------------------------------
                # Fluid, zero-latency execution: ~30 UPS base pace at 1x speed
                # Seamlessly accelerates up to 150+ UPS at higher speed multipliers
                base_delay = 0.032
                actual_delay = max(0.002, base_delay / max(0.1, speed))
                time.sleep(actual_delay)
            else:
                time.sleep(0.1)

    # Start the concurrent backend engine thread
    sim_thread = threading.Thread(target=simulation_worker, daemon=True)
    sim_thread.start()

    # Start the terminal listener thread
    term_thread = threading.Thread(target=terminal_listener, args=(renderer.command_queue,), daemon=True)
    term_thread.start()

    from project.world.biomes import BiomeType
    from project.world.terrain import TerrainManager
    terrain_mgr = TerrainManager(seed=42)

    # Pre-warm terrain surface cache around genesis settlement for immediate 60 FPS
    renderer.overlays.preload_chunks_around(world_w / 2.0, world_h / 2.0, 768.0, terrain_mgr, world_w, world_h)

    from project.world.ancient_ruins import ancient_ruins_mgr

    try:
        while running:
            # Poll pygame events and render visual frame when UI is enabled
            if getattr(renderer, "ui_active", True):
                snapshot = render_sync_sys.get_snapshot()
                if not renderer.handle_input(snapshot):
                    running = False
                    break

                timings = scheduler.get_performance_timings() if (len(renderer.checkboxes) > 2 and renderer.checkboxes[2].checked) else {}
                renderer.render(
                    entities_snapshot=snapshot,
                    terrain_manager=terrain_mgr,
                    pheromone_grid=pheromone_grid,
                    system_timings=timings,
                    sim_tick=tick_count,
                    stats_history=list(statistics_sys.history),
                    time_manager=time_mgr,
                    god_affinity=getattr(gemini_sys, "global_god_affinity", 50.0),
                    ruins_manager=ancient_ruins_mgr,
                )
            else:
                # 0% GPU Headless mode: light event pump without rendering overhead
                import pygame
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                time.sleep(0.02)

    except Exception as e:
        print(f"\n[CRASH DETECTED IN MAIN LOOP] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        debugger.global_exception_handler(type(e), e, sys.exc_info()[2])
    finally:
        print("Shutting down World Simulator...")
        try:
            world_telemetry_collector.dispatch_heartbeat(
                tick=tick_count,
                entities_count=len([e for e in entities_list if getattr(e, 'is_alive', False)]),
                status="session_end"
            )
        except Exception:
            pass
        global_bgm.stop(fade_out_ms=1500)
        bridge_hub.flush_all()
        renderer.close()
        scheduler.shutdown()
        print("Simulator sandbox closed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
