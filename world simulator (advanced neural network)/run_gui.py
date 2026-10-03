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


def spawn_genesis_population(entities_list: List[Entity], world_w: float, world_h: float) -> None:
    """Spawns diverse starting organisms across all 10 major taxonomic categories."""
    entities_list.clear()
    entities_list.append(Plant(entity_id="genesis_plant_0", species_id="fern", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Bacteria(entity_id="genesis_bac_0", species_id="chemophile", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Herbivore(entity_id="genesis_herb_0", species_id="gazelle", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Predator(entity_id="genesis_pred_0", species_id="panther", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Human(entity_id="genesis_hum_0", species_id="homo_sapiens", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Avian(entity_id="genesis_avian_0", species_id="falcon", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Amphibian(entity_id="genesis_amph_0", species_id="axolotl", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Arthropod(entity_id="genesis_arth_0", species_id="pollinator_bee", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Reptile(entity_id="genesis_rept_0", species_id="viper", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))
    entities_list.append(Fungus(entity_id="genesis_fung_0", species_id="mycelium_morel", pos_x=random.uniform(100, world_w - 100), pos_y=random.uniform(100, world_h - 100)))


def print_modern_help_menu() -> None:
    """Displays a beautifully formatted, categorized console help dashboard."""
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║                     WORLD SIMULATOR COMMAND CONSOLE                            ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 💾 SAVE & LOAD SYSTEM:                                                         ║")
    print("║   save [name]              - Save world to saves/<name>.dat                    ║")
    print("║   load [name]              - Load world from saves/<name>.dat                  ║")
    print("║   saves                    - List all saved checkpoints & metadata             ║")
    print("║   quicksave (or qs)        - Fast checkpoint to saves/quicksave.dat            ║")
    print("║   quickload (or ql)        - Instant reload from saves/quicksave.dat           ║")
    print("║   autosave [on|off|ticks]  - Configure background auto-save interval           ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ ⚡ CACHE & BRIDGE MEMORY:                                                      ║")
    print("║   cache stats (or bridge)  - Display real-time bridge RAM & latency telemetry  ║")
    print("║   cache flush              - Flush all memory bridges to cache/ disk storage   ║")
    print("║   cache clear              - Purge in-memory bridge buffers                    ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🛡️ HARDWARE SPEC PROTECTOR (PURE-C):                                           ║")
    print("║   hardware (or specs/hw)   - Real-time CPU, RAM, & hardware safety status      ║")
    print("║   protector <cpu> [ram]    - Configure safety limits (e.g. protector 90 4096)  ║")
    print("║   resume protector         - Reset hardware safety tripwire and resume         ║")
    print("╠════════════════════════════════════════════════════════════════════════════════╣")
    print("║ 🌟 GEMINI COGNITION API:                                                       ║")
    print("║   apikey <key>             - Register/update active Gemini API key dynamically ║")
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
    world_w = 4096.0
    world_h = 4096.0

    print("════════════════════════════════════════════════════════════════════════════════")
    print("🌍 Advanced Neural Network World Simulator (v2.0 Architecture)")
    print(f"📁 Save Directory:  {SAVES_DIR}")
    print(f"⚡ Cache Directory: {CACHE_DIR}")
    telemetry = linux_optimizer.get_memory_telemetry()
    if telemetry.get("platform") == "linux":
        shm_str = " (tmpfs in RAM)" if CACHE_DIR.startswith("/dev/shm") else ""
        print(f"🐧 Linux Engine:    {telemetry['total_cores']} Cores Active | VmRSS: {telemetry['vm_rss_kb'] / 1024.0:.1f} MB | SHM Cache: ON{shm_str}")
    print("💡 Type 'help' in terminal for available commands at any time.")
    print("════════════════════════════════════════════════════════════════════════════════")

    # 1. Spatial structures
    spatial_grid = SpatialHashGrid(cell_size=64.0)
    pheromone_grid = PheromoneGrid(width=int(world_w // 16), height=int(world_h // 16), cell_size=16.0)

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
    renderer = SimulationRenderer(width=1280, height=720, world_width=world_w, world_height=world_h)
    renderer.camera.pos_x = world_w / 2.0
    renderer.camera.pos_y = world_h / 2.0
    renderer.camera.zoom = 1.0

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
                if " " in cmd_raw:
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

                # -------------------- SAVE & LOAD --------------------
                elif cmd_name == "save":
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        save_name = cmd_args if cmd_args else "manual_save.dat"
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
                        saved_path = PersistenceManager.save_to_file(save_name, data)
                        duration = (time.time() - t0) * 1000.0
                        alive_c = len([e for e in entities_list if e.is_alive])
                        file_sz = round(os.path.getsize(saved_path) / 1024.0, 1)
                        msg = f"✅ [SAVE SUCCESS] Checkpoint saved: {saved_path} (Tick {tick_count:,}, {alive_c} alive, {file_sz} KB)"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        err_msg = f"❌ [SAVE ERROR] Failed to save state: {e}"
                        print(err_msg)
                        renderer.console.log(err_msg)

                elif cmd_name == "load":
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        load_name = cmd_args.strip() if cmd_args.strip() else ""
                        if not load_name:
                            saves_list = PersistenceManager.list_saves()
                            if saves_list:
                                load_name = saves_list[0]["name"]
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
                        msg = f"✅ [LOAD SUCCESS] Loaded {load_name} (Tick {tick_count:,}, {alive_c} alive in {duration:.1f}ms)"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        err_msg = f"❌ [LOAD ERROR] Failed to load {load_name}: {e}"
                        print(err_msg)
                        renderer.console.log(err_msg)

                elif cmd_name == "saves":
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
                            lines.append(
                                f"║{i:2d} ║ {s['name']:<22} ║ {s['size_kb']:5.1f}KB ║ {tick_s:>5} ║ {alive_s:>8} ║ {s['modified'][5:]} ║"
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

                elif cmd_name == "delete":
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
                        if m_type == "Solar Eclipse":
                            world_miracles_mgr.trigger_solar_eclipse(30.0)
                        elif m_type == "Meteor Shower":
                            world_miracles_mgr.trigger_meteor_stardust_shower(m_cx, m_cy, count=8)
                        elif m_type == "Divine Rainstorm":
                            world_miracles_mgr.trigger_divine_rainstorm(40.0, soil_mgr)
                        elif m_type == "Bountiful Harvest":
                            world_miracles_mgr.trigger_bountiful_harvest(entities_list, veg_mgr, m_cx, m_cy)
                        elif m_type == "Epiphany Wave":
                            world_miracles_mgr.trigger_epiphany_wave(entities_list, tick_count)
                        elif m_type == "Purge Threats":
                            world_miracles_mgr.trigger_purge_threats(entities_list, m_cx, m_cy)
                    except Exception as me:
                        print(f"❌ [MIRACLE ERROR] {me}")

                elif cmd_name == "spawn_species":
                    try:
                        sp_parts = cmd_args.split(",")
                        s_type = sp_parts[0].strip()
                        scx = float(sp_parts[1].strip()) if len(sp_parts) > 1 else renderer.camera.pos_x
                        scy = float(sp_parts[2].strip()) if len(sp_parts) > 2 else renderer.camera.pos_y
                        new_id = f"spawn_{s_type.lower()}_{tick_count}"
                        if s_type == "Human":
                            entities_list.append(Human(entity_id=new_id, species_id="homo_sapiens", pos_x=scx, pos_y=scy))
                        elif s_type == "Predator":
                            entities_list.append(Predator(entity_id=new_id, species_id="panther", pos_x=scx, pos_y=scy))
                        elif s_type == "Herbivore":
                            entities_list.append(Herbivore(entity_id=new_id, species_id="deer", pos_x=scx, pos_y=scy))
                        elif s_type == "Reptile":
                            entities_list.append(Reptile(entity_id=new_id, species_id="viper", pos_x=scx, pos_y=scy))
                        elif s_type == "Avian":
                            entities_list.append(Avian(entity_id=new_id, species_id="hawk", pos_x=scx, pos_y=scy))
                        elif s_type == "Amphibian":
                            entities_list.append(Amphibian(entity_id=new_id, species_id="frog", pos_x=scx, pos_y=scy))
                        elif s_type == "Plant":
                            entities_list.append(Plant(entity_id=new_id, species_id="fern", pos_x=scx, pos_y=scy))
                        elif s_type == "Fungus":
                            entities_list.append(Fungus(entity_id=new_id, species_id="mycelium", pos_x=scx, pos_y=scy))
                        elif s_type == "Bacteria":
                            entities_list.append(Bacteria(entity_id=new_id, species_id="bacillus", pos_x=scx, pos_y=scy))
                        print(f"🌱 Spawned {s_type} at ({scx:.1f}, {scy:.1f})")
                    except Exception as se:
                        print(f"❌ [SPAWN ERROR] {se}")

                elif cmd_name in ("saves", "list saves", "list"):
                    saves_list = PersistenceManager.list_saves()
                    print("╔════════════════════════════════════════════════════════════════════════════════╗")
                    print(f"║ SAVED SIMULATION CHECKPOINTS ({len(saves_list)} Found in {SAVES_DIR})")
                    print("╠════════════════════════════════════════════════════════════════════════════════╣")
                    if not saves_list:
                        print("║   No save files found yet. Type 'save <name>' to create one.                  ║")
                    else:
                        for i, s in enumerate(saves_list, 1):
                            print(f"║ [{i}] {s['name']:<28} | {s['size_kb']:>6.1f} KB | {s['modified']} ║")
                    print("╚════════════════════════════════════════════════════════════════════════════════╝")

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
                        saved_p = PersistenceManager.save_to_file("quicksave.dat", data)
                        msg = f"⚡ [QUICKSAVE] Fast checkpoint saved to {saved_p} (Tick {tick_count:,})"
                        print(msg)
                        renderer.console.log(msg)
                    except Exception as e:
                        print(f"❌ [QUICKSAVE ERROR] {e}")

                elif cmd_name in ("quickload", "ql"):
                    try:
                        from project.world.ancient_ruins import ancient_ruins_mgr
                        from project.world.miracles import world_miracles_mgr
                        state = PersistenceManager.load_from_file("quicksave.dat")
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
                        msg = f"⚡ [QUICKLOAD] Restored quicksave.dat (Tick {tick_count:,}, {len(entities_list)} entities)"
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

                # -------------------- GEMINI AI API KEYS --------------------
                elif cmd_name in ("apikey", "key", "setkey"):
                    if not cmd_args.strip():
                        curr_k = gemini_sys.client.get_current_key()
                        print(f"🔑 Current Active API Key: {curr_k[:10] + '...' + curr_k[-4:] if curr_k else 'None (Running Offline Cognitive Engine)'}")
                    else:
                        new_k = cmd_args.strip()
                        gemini_sys.client.add_api_key(new_k)
                        print(f"✅ Registered new Gemini API key into active rotation: {new_k[:10]}...{new_k[-4:]}")

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

                elif cmd_name == "civilization integration":
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

                elif cmd_name == "kill":
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

                elif cmd_name in ("seeds", "seed log", "seed logs", "seed stats"):
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
                    avatar = next((e for e in entities_list if e.is_alive and e.custom_data.get("emergent_role") == "DEITY_AVATAR"), None)
                    if avatar:
                        print(f"\n⚡ Gemini God Avatar hears your command: '{cmd_args}'")
                        print("⚡ The Deity's consciousness integrates your command into the simulation.")
                        avatar.think(f"USER COMMAND RECEIVED: {cmd_args}", category="DIVINE", valence=1.0)
                    else:
                        print("Error: The Gemini God Avatar has not incarnated yet. Attain 100% God Affinity first.")
                        
                elif cmd_name == "spawn_god":
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
                except Exception as e:
                    print(f"CRASH HANDLER (Main loop): Exception in backend scheduler: {e}")
                    import traceback
                    traceback.print_exc()
                    renderer.simulation_speed = 0.0

                # ---------------------------------------------------------
                # ELASTIC ADAPTIVE SIMULATION CLOCK
                # ---------------------------------------------------------
                # Base average pace is ~2.0s per tick.
                # When vital biological events, reproduction, cell divisions,
                # active combats, or leader ascensions occur, the clock dynamically
                # accelerates so program goals and evolutionary progress are never throttled!
                alive = [e for e in entities_list if e.is_alive]
                if not alive:
                    base_delay = 1.0
                elif len(pending_births) > 0:
                    base_delay = 0.15  # Accelerated birth and division processing
                else:
                    # Measure real-time biological and evolutionary urgency
                    repro_ready = sum(1 for e in alive if e.is_mature and e.energy > (e.max_energy * 0.55))
                    repro_urgency = min(1.0, repro_ready / max(1, len(alive)))

                    moving_count = sum(1 for e in alive if getattr(e, 'speed', 0.0) > 0.5)
                    movement_urgency = min(1.0, moving_count / max(1, len(alive)))

                    leader = next((e for e in alive if e.custom_data.get("emergent_role") == "LEADER"), None)
                    divine_urgency = 0.35 if (leader and leader.custom_data.get("divine_blessing_active")) else 0.0

                    activity_index = min(1.0, (repro_urgency * 0.45) + (movement_urgency * 0.35) + divine_urgency)

                    # Dynamic scaling: 2.0s when calm/idle -> 0.25s during peak biological progress
                    base_delay = 2.0 * (1.0 - (0.875 * activity_index))

                actual_delay = max(0.016, base_delay / max(0.1, speed))
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
    class MockTile:
        def __init__(self, height, biome):
            self.height = height
            self.biome = biome

    class MockTerrainManager:
        def get_tile(self, x, y):
            return MockTile(0.4, BiomeType.FOREST)

    mock_terrain = MockTerrainManager()

    try:
        while running:
            # Poll pygame events and render visual frame when UI is enabled
            if getattr(renderer, "ui_active", True):
                snapshot = render_sync_sys.get_snapshot()
                if not renderer.handle_input(snapshot):
                    running = False
                    break

                from project.world.ancient_ruins import ancient_ruins_mgr
                timings = scheduler.get_performance_timings()
                renderer.render(
                    entities_snapshot=snapshot,
                    terrain_manager=mock_terrain,
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
        global_bgm.stop(fade_out_ms=1500)
        bridge_hub.flush_all()
        renderer.close()
        scheduler.shutdown()
        print("Simulator sandbox closed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
