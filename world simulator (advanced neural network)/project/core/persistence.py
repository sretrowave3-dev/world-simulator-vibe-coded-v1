"""
project/core/persistence.py

Enhanced High-Performance Persistence Subsystem.
Manages deep serialization, compression, atomic disk storage, rolling backups,
and complete multi-species restoration for all simulation layers:
- Planetary Time & Calendar
- Soil & Geological Layers
- Hydrology & Water Bodies
- Flora & Vegetation Biomass
- Mineral Resource Nodes
- All 13 Biological Species (Human, Predator, Herbivore, Avian, Reptile, Amphibian, Arthropod, Fungus, Plant, Bacteria, Carnivore, Omnivore, Decomposer)
- AI Brain Neural Network Weights & Genomes
- Gemini God Affinity, Golden Monolith, Ancient Ruins Exploration, and Celestial Miracles
"""

from __future__ import annotations

import os
import time
import zlib
import json
import hashlib
import pickle
import shutil
import struct
from typing import Dict, Any, List, Optional, Tuple, Set

from project.world.time import WorldTimeManager
from project.world.soil import SoilManager, SoilChunk
from project.world.water import WaterManager, WaterChunk
from project.world.vegetation import VegetationManager, VegetationChunk
from project.world.resources import ResourceManager, ResourceNode, ResourceType
from project.entities.entity import Entity, EntityType
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.herbivore import Herbivore
from project.entities.carnivore import Carnivore
from project.entities.predator import Predator
from project.entities.human import Human
from project.entities.omnivore import Omnivore
from project.entities.decomposer import Decomposer
from project.entities.avian import Avian
from project.entities.amphibian import Amphibian
from project.entities.arthropod import Arthropod
from project.entities.reptile import Reptile
from project.entities.fungus import Fungus
from project.core.linux_optimizer import linux_optimizer
from project.core.git_save_manager import git_save_manager

SAVES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saves"))
os.makedirs(SAVES_DIR, exist_ok=True)

# ── Save file format constants ───────────────────────────────────────────────
# Header layout (v2.0 — 52 bytes total):
#   [0:4]   Magic  b"ECHO"
#   [4:8]   CRC32  uint32 (LE) of compressed payload
#   [8:40]  SHA-256 digest (32 bytes) of compressed payload
#   [40:44] Format version uint32 (LE)  — 0x0200 = v2.0
#   [44:52] Unix save timestamp int64 (LE)
_HEADER_MAGIC    = b"ECHO"
_HEADER_FMT      = "<4sI32sIq"        # 4+4+32+4+8 = 52 bytes
_HEADER_SIZE     = struct.calcsize(_HEADER_FMT)
_SAVE_VERSION    = 0x0200
_LEGACY_HDR_SIZE = 8                  # old v1.x header was only 8 bytes
_MAX_BAK_GENS    = 3                  # number of rolling backup generations


def sanitize_custom_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes custom_data and status dictionaries to safely strip unpicklable runtime references."""
    if not isinstance(data, dict):
        return {}
    cleaned = {}
    for k, v in data.items():
        if k in ("perceived_entities", "world_ref", "world_reference", "renderer_ref", "thought_logger"):
            continue
        if isinstance(v, list) and v and hasattr(v[0], "entity_id"):
            cleaned[k] = [item.entity_id for item in v if hasattr(item, "entity_id")]
            continue
        try:
            pickle.dumps(v, protocol=pickle.HIGHEST_PROTOCOL)
            cleaned[k] = v
        except Exception:
            try:
                cleaned[k] = str(v)
            except Exception:
                pass
    return cleaned


def _sha256_of(data: bytes) -> bytes:
    """Returns raw 32-byte SHA-256 digest of *data*."""
    return hashlib.sha256(data).digest()


def serialize_compressed_payload(data: Dict[str, Any]) -> Tuple[bytes, int, bytes]:
    """Pickles a Python dict, compresses with zlib, and computes CRC32 + SHA-256."""
    raw_bytes  = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
    compressed = zlib.compress(raw_bytes, level=6)
    checksum   = zlib.crc32(compressed) & 0xFFFFFFFF
    sha256     = _sha256_of(compressed)
    return compressed, checksum, sha256


def deserialize_compressed_payload(
    compressed_bytes: bytes,
    expected_checksum: int,
    expected_sha256: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Validates CRC32 + optional SHA-256, decompresses zlib payload, and unpickles data."""
    actual_checksum = zlib.crc32(compressed_bytes) & 0xFFFFFFFF
    if actual_checksum != expected_checksum:
        raise ValueError(
            f"CRC32 mismatch: expected {expected_checksum:#010x}, got {actual_checksum:#010x}"
        )
    if expected_sha256 is not None:
        actual_sha256 = _sha256_of(compressed_bytes)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"SHA-256 integrity check failed — file may have been tampered with!\n"
                f"  Expected: {expected_sha256.hex()}\n"
                f"  Actual:   {actual_sha256.hex()}"
            )
    raw_bytes = zlib.decompress(compressed_bytes)
    return pickle.loads(raw_bytes)


class PersistenceManager:
    """Master persistence manager for checkpoints and world state serializations."""

    @classmethod
    def resolve_save_path(cls, filepath_or_name: str) -> str:
        """Resolves save file path with universe awareness, numeric index, or fuzzy matching."""
        clean_input = filepath_or_name.strip()
        os.makedirs(SAVES_DIR, exist_ok=True)

        # 1. Direct path check
        if os.path.isabs(clean_input) and os.path.exists(clean_input):
            return clean_input

        # 2. Number index resolution (e.g. "load 1", "load 2")
        if clean_input.isdigit():
            idx = int(clean_input) - 1
            saves = cls.list_saves()
            if 0 <= idx < len(saves):
                return saves[idx]["path"]

        # 3. Check active universe checkpoints & autosaves first
        try:
            from project.core.quantum_persistence import quantum_persistence
            univ_dir = quantum_persistence._get_universe_dir(quantum_persistence.active_universe_id)
            for sub in ("checkpoints", "autosaves", "blackbox"):
                cand = os.path.join(univ_dir, sub, clean_input)
                if os.path.exists(cand):
                    return cand
                cand_ext = os.path.join(univ_dir, sub, f"{clean_input}.dat")
                if os.path.exists(cand_ext):
                    return cand_ext
        except Exception:
            pass

        # 4. Exact filename match in SAVES_DIR
        target = os.path.join(SAVES_DIR, clean_input)
        if os.path.exists(target):
            return target
        
        target_with_ext = os.path.join(SAVES_DIR, f"{clean_input}.dat")
        if os.path.exists(target_with_ext):
            return target_with_ext

        # 5. Fuzzy substring / prefix matching
        saves = cls.list_saves()
        low = clean_input.lower()
        for s in saves:
            s_low = s["name"].lower()
            if s_low == low or s_low.startswith(low) or low in s_low:
                return s["path"]

        # Default fallback: save inside active universe checkpoints directory
        if not clean_input.endswith(".dat"):
            clean_input = f"{clean_input}.dat"
        try:
            from project.core.quantum_persistence import quantum_persistence
            univ_dir = quantum_persistence._get_universe_dir(quantum_persistence.active_universe_id)
            return os.path.join(univ_dir, "checkpoints", clean_input)
        except Exception:
            return os.path.join(SAVES_DIR, clean_input)

    @classmethod
    def list_saves(cls) -> List[Dict[str, Any]]:
        """Scans active universe snapshots and global saves directory."""
        os.makedirs(SAVES_DIR, exist_ok=True)
        results = []
        scanned_paths: Set[str] = set()

        # 1. First scan active universe snapshots
        try:
            from project.core.quantum_persistence import quantum_persistence
            univ_snaps = quantum_persistence.list_universe_snapshots()
            for s in univ_snaps:
                scanned_paths.add(os.path.abspath(s["path"]))
                results.append(s)
        except Exception:
            pass

        # 2. Scan global SAVES_DIR for legacy/shared checkpoints
        for fname in sorted(os.listdir(SAVES_DIR)):
            if not fname.endswith(".dat") or fname.endswith(".tmp"):
                continue
            full_p = os.path.join(SAVES_DIR, fname)
            abs_p = os.path.abspath(full_p)
            if abs_p in scanned_paths:
                continue

            try:
                stat = os.stat(full_p)
                size_kb = round(stat.st_size / 1024.0, 1)
                mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))

                meta_path = full_p + ".meta.json"
                meta: Dict[str, Any] = {}
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as mf:
                            meta = json.load(mf)
                    except Exception:
                        pass

                info = {
                    "name":      fname,
                    "path":      full_p,
                    "category":  "LEGACY",
                    "size_kb":   size_kb,
                    "modified":  mtime_str,
                    "date_str":  mtime_str,
                    "timestamp": stat.st_mtime,
                    "valid":     True,
                    "tick":      meta.get("tick", "?"),
                    "alive":     meta.get("alive", "?"),
                    "affinity":  meta.get("affinity", "?"),
                    "sha256":    meta.get("sha256", "—"),
                    "commit_id": meta.get("commit_id", "—"),
                    "branch":    meta.get("branch", "legacy"),
                    "version":   meta.get("save_fmt", "v1.x"),
                }
                results.append(info)
            except Exception:
                pass

        return sorted(results, key=lambda x: x.get("timestamp", 0.0), reverse=True)

    @classmethod
    def _write_meta_sidecar(
        cls,
        filepath: str,
        data: Dict[str, Any],
        sha256_hex: str,
        save_fmt: str = "v2.0",
        commit_id: Optional[str] = None,
    ) -> None:
        """Writes a lightweight .meta.json sidecar next to the .dat file for instant browsing."""
        meta = {
            "tick":      data.get("time", {}).get("tick", 0),
            "alive":     sum(1 for e in data.get("entities", []) if e.get("alive", True)),
            "affinity":  round(data.get("gemini", {}).get("god_affinity", 0.0), 1),
            "saved_at":  time.strftime("%Y-%m-%d %H:%M:%S"),
            "size_kb":   round(os.path.getsize(filepath) / 1024.0, 1) if os.path.exists(filepath) else 0,
            "sha256":    sha256_hex,
            "save_fmt":  save_fmt,
            "commit_id": commit_id or "",
            "branch":    git_save_manager.active_branch,
        }
        meta_path = filepath + ".meta.json"
        try:
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(meta, mf, indent=2)
        except Exception:
            pass  # sidecar failure must never break the save

    @classmethod
    def _rotate_backups(cls, filepath: str) -> None:
        """Rotates existing backups: .bak3 dropped, .bak2→.bak3, .bak1→.bak2, .dat→.bak1."""
        # Rotate oldest-first to avoid data loss on rename failures
        bak_paths = [f"{filepath}.bak{i}" for i in range(_MAX_BAK_GENS, 0, -1)]
        for i, bak in enumerate(bak_paths):
            if os.path.exists(bak):
                if i == 0:
                    try:
                        os.remove(bak)  # drop oldest generation
                    except Exception:
                        pass
                else:
                    try:
                        os.replace(bak, bak_paths[i - 1])
                    except Exception:
                        pass
        # Push current .dat → .bak1
        if os.path.exists(filepath):
            try:
                shutil.copy2(filepath, f"{filepath}.bak1")
            except Exception:
                pass

    @staticmethod
    def serialize_state(
        time_mgr: WorldTimeManager,
        soil_mgr: SoilManager,
        water_mgr: WaterManager,
        veg_mgr: VegetationManager,
        res_mgr: ResourceManager,
        entities_list: List[Entity],
        gemini_sys: Optional[Any] = None,
        ruins_mgr: Optional[Any] = None,
        miracles_mgr: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Serializes all mutable engine layers into a nested Python data dict."""
        state = {
            "version": "1.3",
            "saved_timestamp": time.time(),
        }

        # 1. Time keeper
        if time_mgr:
            state["time"] = {
                "tick": getattr(time_mgr, "current_tick", 0),
                "seconds": getattr(time_mgr, "total_seconds", 0.0),
                "seconds_per_day": getattr(time_mgr, "seconds_per_day", 86400.0),
                "days_per_year": getattr(time_mgr, "days_per_year", 365),
                "ticks_per_second": getattr(time_mgr, "ticks_per_second", 60),
            }
        else:
            state["time"] = {
                "tick": 0,
                "seconds": 0.0,
                "seconds_per_day": 86400.0,
                "days_per_year": 365,
                "ticks_per_second": 60,
            }

        # 2. Soil Chunks
        state["soil"] = {}
        for coords, chunk in getattr(soil_mgr, "chunks", getattr(soil_mgr, "_chunks", {})).items():
            key = f"{coords[0]},{coords[1]}"
            state["soil"][key] = {
                "nitrogen": list(chunk.nitrogen),
                "phosphorus": list(chunk.phosphorus),
                "potassium": list(chunk.potassium),
                "organic_matter": list(chunk.organic_matter),
                "moisture": list(chunk.moisture),
                "ph": list(chunk.ph),
                "salinity": list(chunk.salinity),
                "density": list(chunk.density),
            }

        # 3. Water Chunks
        state["water"] = {}
        for coords, chunk in getattr(water_mgr, "chunks", getattr(water_mgr, "_chunks", {})).items():
            key = f"{coords[0]},{coords[1]}"
            state["water"][key] = {
                "water_type": list(chunk.water_type),
                "depth": list(chunk.depth),
                "flow_x": list(chunk.flow_x),
                "flow_y": list(chunk.flow_y),
                "salinity": list(chunk.salinity),
                "purity": list(chunk.purity),
                "temperature": list(chunk.temperature),
            }

        # 4. Vegetation Chunks
        state["vegetation"] = {}
        for coords, chunk in getattr(veg_mgr, "chunks", getattr(veg_mgr, "_chunks", {})).items():
            key = f"{coords[0]},{coords[1]}"
            state["vegetation"][key] = {
                "type": list(chunk.veg_type),
                "biomass": list(chunk.biomass),
                "max_biomass": list(chunk.max_biomass),
                "height": list(chunk.canopy_height),
                "density": list(chunk.density),
                "health": list(chunk.health),
            }

        # 5. Resource Nodes
        state["resources"] = []
        for node in getattr(res_mgr, "nodes", getattr(res_mgr, "_nodes", {})).values():
            state["resources"].append({
                "id": node.node_id,
                "type": node.resource_type.value,
                "x": node.pos_x,
                "y": node.pos_y,
                "quantity": node.quantity,
                "max_capacity": getattr(node, "max_capacity", getattr(node, "max_quantity", 100.0)),
                "regen_rate": getattr(node, "regeneration_rate_per_sec", getattr(node, "regen_rate", 0.1)),
                "hardness": getattr(node, "hardness", getattr(node, "purity", 0.5)),
                "is_depleted": getattr(node, "is_depleted", getattr(node, "depleted", False)),
            })

        # 6. Entities & Neural Networks
        state["entities"] = []
        for e in entities_list:
            ent_dict = {
                "id": e.entity_id,
                "species_id": e.species_id,
                "type": e.entity_type.value,
                "generation": getattr(e, "generation", 1),
                "birth_tick": getattr(e, "birth_tick", 0),
                "parents": list(getattr(e, "parent_ids", ())),
                "x": e.pos_x,
                "y": e.pos_y,
                "z": getattr(e, "pos_z", 0.0),
                "vx": getattr(e, "vel_x", 0.0),
                "vy": getattr(e, "vel_y", 0.0),
                "heading": getattr(e, "heading_angle", 0.0),
                "radius": getattr(e, "radius", 1.0),
                "mass": getattr(e, "mass_kg", 1.0),
                "health": getattr(e, "health", 100.0),
                "max_health": getattr(e, "max_health", 100.0),
                "energy": getattr(e, "energy", 100.0),
                "max_energy": getattr(e, "max_energy", 100.0),
                "hydration": getattr(e, "hydration", 100.0),
                "max_hydration": getattr(e, "max_hydration", 100.0),
                "stamina": getattr(e, "stamina", 100.0),
                "max_stamina": getattr(e, "max_stamina", 100.0),
                "age": getattr(e, "age_ticks", 0),
                "max_age": getattr(e, "max_age_ticks", 10000),
                "metabolism": getattr(e, "metabolic_rate", 0.05),
                "cooldown": getattr(e, "reproduction_cooldown", 0),
                "maturity": getattr(e, "maturity_age_ticks", 100),
                "alive": getattr(e, "is_alive", True),
                "cause_death": getattr(e, "cause_of_death", None),
                "death_tick": getattr(e, "death_tick", None),
                "action": getattr(e, "current_action", "IDLE"),
                "status": sanitize_custom_data(getattr(e, "status_effects", {})),
                "custom_data": sanitize_custom_data(getattr(e, "custom_data", {})),
            }

            # Serialize Neural Genome & Brain Weights
            if e.genome and hasattr(e.genome, "genes"):
                ent_dict["genome"] = list(e.genome.genes)
            if e.brain and hasattr(e.brain, "export_weights_to_vector"):
                ent_dict["brain"] = e.brain.export_weights_to_vector()

            # Human-specific attributes
            if isinstance(e, Human):
                ent_dict["tribe_id"] = getattr(e, "tribe_id", None)
                ent_dict["civ_id"] = getattr(e, "civilization_id", None)
                ent_dict["social_rank"] = getattr(e, "social_rank", 0)
                ent_dict["reputation"] = getattr(e, "reputation", 50.0)
                ent_dict["iq"] = getattr(e, "intelligence_quotient", 100.0)
                ent_dict["creativity"] = getattr(e, "creativity", 50.0)
                ent_dict["social_affinity"] = getattr(e, "social_affinity", 50.0)
                ent_dict["tech_level"] = getattr(e, "technology_level", 0)
                ent_dict["known_tech"] = list(getattr(e, "known_technologies", []))
                ent_dict["inventory"] = dict(getattr(e, "inventory", {}))
                ent_dict["inv_capacity"] = getattr(e, "max_inventory_capacity_kg", 25.0)
                ent_dict["weapon"] = getattr(e, "equipped_weapon", None)
                ent_dict["tool"] = getattr(e, "equipped_tool", None)

            state["entities"].append(ent_dict)

        # 7. Gemini God & Miracles Subsystem
        if gemini_sys:
            state["gemini"] = {
                "god_affinity": getattr(gemini_sys, "global_god_affinity", 50.0),
                "monolith_spawned": getattr(gemini_sys, "monolith_spawned", False),
            }

        # 8. Ancient Ruins Exploration Subsystem
        if ruins_mgr:
            state["ancient_ruins"] = {
                "discovered": getattr(ruins_mgr, "civilization_discovered", False),
                "discovered_ids": list(getattr(ruins_mgr, "discovered_entity_ids", set())),
            }

        # 9. Celestial Miracles Subsystem
        if miracles_mgr:
            state["miracles"] = {
                "eclipse_remaining": getattr(miracles_mgr, "eclipse_remaining_seconds", 0.0),
                "rainstorm_remaining": getattr(miracles_mgr, "rainstorm_remaining_seconds", 0.0),
                "stardust": [
                    {"x": d.pos_x, "y": d.pos_y, "energy": d.energy_value, "iq": d.iq_bonus}
                    for d in getattr(miracles_mgr, "stardust_deposits", [])
                    if not d.is_collected
                ],
            }

        return state

    @staticmethod
    def deserialize_state(
        state_dict: Dict[str, Any],
        time_mgr: WorldTimeManager,
        soil_mgr: SoilManager,
        water_mgr: WaterManager,
        veg_mgr: VegetationManager,
        res_mgr: ResourceManager,
        entities_list: List[Entity],
        gemini_sys: Optional[Any] = None,
        ruins_mgr: Optional[Any] = None,
        miracles_mgr: Optional[Any] = None,
    ) -> None:
        """Restores simulation state deeply from decoded dictionary."""
        # 1. Restore Planetary Time
        t_data = state_dict.get("time", {})
        time_mgr.current_tick = t_data.get("tick", 0)
        time_mgr.total_seconds = t_data.get("seconds", 0.0)
        time_mgr.seconds_per_day = t_data.get("seconds_per_day", 120.0)
        time_mgr.days_per_year = t_data.get("days_per_year", 360)
        time_mgr.ticks_per_second = t_data.get("ticks_per_second", 60)

        # 2. Restore Soil Chunks
        soil_chunks = state_dict.get("soil", {})
        for key, s_data in soil_chunks.items():
            coords = tuple(map(int, key.split(",")))
            if hasattr(soil_mgr, "get_or_create_chunk"):
                chunk = soil_mgr.get_or_create_chunk(coords)
            elif hasattr(soil_mgr, "chunks"):
                chunk = soil_mgr.chunks.get(coords)
            else:
                chunk = None

            if chunk:
                for attr in ("nitrogen", "phosphorus", "potassium", "organic_matter", "moisture", "ph", "salinity", "density"):
                    if attr in s_data and hasattr(chunk, attr):
                        src = s_data[attr]
                        dst = getattr(chunk, attr)
                        for i in range(min(len(src), len(dst))):
                            dst[i] = src[i]

        # 3. Restore Water Chunks
        water_chunks = state_dict.get("water", {})
        for key, w_data in water_chunks.items():
            coords = tuple(map(int, key.split(",")))
            if hasattr(water_mgr, "get_or_create_chunk"):
                chunk = water_mgr.get_or_create_chunk(coords)
            elif hasattr(water_mgr, "chunks"):
                chunk = water_mgr.chunks.get(coords)
            else:
                chunk = None

            if chunk:
                for attr in ("water_type", "depth", "flow_x", "flow_y", "salinity", "purity", "temperature"):
                    if attr in w_data and hasattr(chunk, attr):
                        src = w_data[attr]
                        dst = getattr(chunk, attr)
                        for i in range(min(len(src), len(dst))):
                            dst[i] = src[i]

        # 4. Restore Vegetation Chunks
        veg_chunks = state_dict.get("vegetation", {})
        for key, v_data in veg_chunks.items():
            coords = tuple(map(int, key.split(",")))
            if hasattr(veg_mgr, "get_or_create_chunk"):
                chunk = veg_mgr.get_or_create_chunk(coords)
            elif hasattr(veg_mgr, "chunks"):
                chunk = veg_mgr.chunks.get(coords)
            else:
                chunk = None

            if chunk:
                for attr in (("type", "veg_type"), ("biomass", "biomass"), ("max_biomass", "max_biomass"), ("height", "canopy_height"), ("density", "density"), ("health", "health")):
                    src_k, dst_k = attr
                    if src_k in v_data and hasattr(chunk, dst_k):
                        src = v_data[src_k]
                        dst = getattr(chunk, dst_k)
                        for i in range(min(len(src), len(dst))):
                            dst[i] = src[i]

        # 5. Restore Resource Nodes
        target_nodes = getattr(res_mgr, "nodes", getattr(res_mgr, "_nodes", {}))
        target_nodes.clear()
        if hasattr(res_mgr, "_chunk_node_map"):
            res_mgr._chunk_node_map.clear()
        
        for r_data in state_dict.get("resources", []):
            nid = r_data["id"]
            node = ResourceNode(
                node_id=nid,
                resource_type=ResourceType(r_data["type"]),
                pos_x=r_data["x"],
                pos_y=r_data["y"],
                quantity=r_data["quantity"],
                max_capacity=r_data.get("max_capacity", r_data.get("max_quantity", 100.0)),
                regeneration_rate_per_sec=r_data.get("regen_rate", r_data.get("regeneration_rate_per_sec", 0.1)),
                hardness=r_data.get("hardness", r_data.get("purity", 0.5)),
                is_depleted=r_data.get("is_depleted", r_data.get("depleted", False)),
            )
            target_nodes[nid] = node
            cx, cy = int(node.pos_x // 32.0), int(node.pos_y // 32.0)
            if hasattr(res_mgr, "_chunk_node_map"):
                if (cx, cy) not in res_mgr._chunk_node_map:
                    res_mgr._chunk_node_map[(cx, cy)] = set()
                res_mgr._chunk_node_map[(cx, cy)].add(nid)
            res_mgr._next_node_id = max(getattr(res_mgr, "_next_node_id", 0), nid + 1)

        # 6. Restore Entities (Full Multi-Species Coverage)
        entities_list.clear()
        for ent_data in state_dict.get("entities", []):
            try:
                raw_type = ent_data.get("type", 1)
                etype = EntityType(raw_type) if isinstance(raw_type, int) else EntityType[raw_type]
            except Exception:
                etype = EntityType.HERBIVORE

            eid = ent_data["id"]
            spid = ent_data.get("species_id", "organism")
            x = ent_data.get("x", 0.0)
            y = ent_data.get("y", 0.0)
            parents = tuple(ent_data.get("parents", ()))

            genome = None
            if ent_data.get("genome"):
                try:
                    from project.ai.genome import Genome
                    genome = Genome(genes=list(ent_data["genome"]))
                except Exception:
                    pass

            brain = None
            if ent_data.get("brain"):
                try:
                    from project.ai.brain import Brain
                    brain = Brain()
                    brain.load_weights_from_vector(ent_data["brain"])
                except Exception:
                    pass

            child = None
            if etype == EntityType.BACTERIA:
                child = Bacteria(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.PLANT:
                child = Plant(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.HERBIVORE:
                child = Herbivore(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.CARNIVORE:
                child = Carnivore(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.PREDATOR:
                child = Predator(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.OMNIVORE:
                child = Omnivore(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.DECOMPOSER:
                child = Decomposer(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.AVIAN:
                child = Avian(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.AMPHIBIAN:
                child = Amphibian(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.ARTHROPOD:
                child = Arthropod(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.REPTILE:
                child = Reptile(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.FUNGUS:
                child = Fungus(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
            elif etype == EntityType.HUMAN:
                cdata = dict(ent_data.get("custom_data", {}))
                if cdata.get("emergent_role") == "DEITY_AVATAR":
                    from project.entities.gemini_god_avatar import GeminiGodAvatar
                    child = GeminiGodAvatar(entity_id=eid, species_id=spid, pos_x=x, pos_y=y)
                    # Restore brain manually since avatar initializes its own but we might have saved state
                    if brain:
                        child.brain = brain
                else:
                    child = Human(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)
                child.tribe_id = ent_data.get("tribe_id")
                child.civilization_id = ent_data.get("civ_id")
                child.social_rank = ent_data.get("social_rank", 0)
                child.reputation = ent_data.get("reputation", 50.0)
                child.intelligence_quotient = ent_data.get("iq", 100.0)
                child.creativity = ent_data.get("creativity", 50.0)
                child.social_affinity = ent_data.get("social_affinity", 50.0)
                child.technology_level = ent_data.get("tech_level", 0)
                child.known_technologies = list(ent_data.get("known_tech", []))
                child.inventory = dict(ent_data.get("inventory", {}))
                child.max_inventory_capacity_kg = ent_data.get("inv_capacity", 25.0)
                child.equipped_weapon = ent_data.get("weapon")
                child.equipped_tool = ent_data.get("tool")
            else:
                # Fallback generic container
                child = Herbivore(entity_id=eid, species_id=spid, pos_x=x, pos_y=y, parent_ids=parents, genome=genome, brain=brain)

            if child:
                child.generation = ent_data.get("generation", 1)
                child.birth_tick = ent_data.get("birth_tick", 0)
                child.pos_z = ent_data.get("z", 0.0)
                child.vel_x = ent_data.get("vx", 0.0)
                child.vel_y = ent_data.get("vy", 0.0)
                child.heading_angle = ent_data.get("heading", 0.0)
                child.radius = ent_data.get("radius", 1.0)
                child.mass_kg = ent_data.get("mass", 1.0)
                child.health = ent_data.get("health", 100.0)
                child.max_health = ent_data.get("max_health", 100.0)
                child.energy = ent_data.get("energy", 100.0)
                child.max_energy = ent_data.get("max_energy", 100.0)
                child.hydration = ent_data.get("hydration", 100.0)
                child.max_hydration = ent_data.get("max_hydration", 100.0)
                child.stamina = ent_data.get("stamina", 100.0)
                child.max_stamina = ent_data.get("max_stamina", 100.0)
                child.age_ticks = ent_data.get("age", 0)
                child.max_age_ticks = ent_data.get("max_age", 10000)
                child.metabolic_rate = ent_data.get("metabolism", 0.05)
                child.reproduction_cooldown = ent_data.get("cooldown", 0)
                child.maturity_age_ticks = ent_data.get("maturity", 100)
                child.is_alive = ent_data.get("alive", True)
                child.cause_of_death = ent_data.get("cause_death")
                child.death_tick = ent_data.get("death_tick")
                child.current_action = ent_data.get("action", "IDLE")
                child.status_effects = dict(ent_data.get("status", {}))
                child.custom_data = dict(ent_data.get("custom_data", {}))

                entities_list.append(child)

        # 7. Restore Gemini God Affinity
        if gemini_sys and "gemini" in state_dict:
            g_data = state_dict["gemini"]
            gemini_sys.global_god_affinity = g_data.get("god_affinity", 50.0)
            gemini_sys.monolith_spawned = g_data.get("monolith_spawned", False)

        # 8. Restore Ancient Ruins State
        if ruins_mgr and "ancient_ruins" in state_dict:
            r_data = state_dict["ancient_ruins"]
            ruins_mgr.civilization_discovered = r_data.get("discovered", False)
            ruins_mgr.discovered_entity_ids = set(r_data.get("discovered_ids", []))

        # 9. Restore Miracles & Stardust Deposits
        if miracles_mgr and "miracles" in state_dict:
            from project.world.miracles import StardustDeposit
            m_data = state_dict["miracles"]
            miracles_mgr.eclipse_remaining_seconds = m_data.get("eclipse_remaining", 0.0)
            miracles_mgr.rainstorm_remaining_seconds = m_data.get("rainstorm_remaining", 0.0)
            miracles_mgr.stardust_deposits = [
                StardustDeposit(pos_x=sd["x"], pos_y=sd["y"], energy_value=sd.get("energy", 120.0), iq_bonus=sd.get("iq", 25.0))
                for sd in m_data.get("stardust", [])
            ]

    @classmethod
    def save_to_file(cls, filepath_or_name: str, data: Dict[str, Any], commit_message: Optional[str] = None) -> str:
        """
        Smart save v2.0 with Git-like Overwrite Protection:
        - Checks and prevents accidental overwrites of progressed states (Zero Data Loss)
        - Serializes + compresses payload
        - Writes 52-byte header: magic | CRC32 | SHA-256 | version | timestamp
        - Atomically replaces the .dat via temp-file swap
        - Rotates up to 3 rolling backup generations (.bak1/.bak2/.bak3)
        - Registers discrete Git commit node in git_manifest.json
        - Writes a .meta.json sidecar for instant browsing without decompression
        """
        filepath = cls.resolve_save_path(filepath_or_name)

        # Accidental Overwrite Safeguard
        current_tick = data.get("time", {}).get("tick", 0)
        current_alive = sum(1 for e in data.get("entities", []) if e.get("alive", True))
        try:
            git_save_manager.check_and_protect_overwrite(
                target_file_path=filepath,
                current_tick=current_tick,
                current_alive=current_alive,
            )
        except Exception as ge:
            print(f"[GIT SAVE] Warning in conflict check: {ge}")

        compressed, checksum, sha256_raw = serialize_compressed_payload(data)
        sha256_hex = sha256_raw.hex()
        save_ts = int(time.time())

        header = struct.pack(
            _HEADER_FMT,
            _HEADER_MAGIC,
            checksum,
            sha256_raw,
            _SAVE_VERSION,
            save_ts,
        )

        temp_path = filepath + ".tmp"
        with open(temp_path, "wb") as f:
            linux_optimizer.posix_advise_sequential(f.fileno())
            f.write(header)
            f.write(compressed)

        # Rotate backups before overwriting primary file
        cls._rotate_backups(filepath)

        # Atomic swap — POSIX guarantees this is crash-safe
        os.replace(temp_path, filepath)

        # Register Git commit node
        commit_id = None
        try:
            commit = git_save_manager.record_commit(
                file_path=filepath,
                tick=current_tick,
                alive_count=current_alive,
                message=commit_message,
            )
            commit_id = commit.commit_id
        except Exception:
            pass

        # Write lightweight metadata sidecar
        cls._write_meta_sidecar(filepath, data, sha256_hex, commit_id=commit_id)

        return filepath

    @classmethod
    def load_from_file(cls, filepath_or_name: str) -> Dict[str, Any]:
        """
        Smart load v2.0:
        - Reads and validates the 52-byte v2 header (SHA-256 + CRC32)
        - Falls back to legacy 8-byte v1 header for old saves (no SHA-256 check)
        - On corruption: quarantines bad file as .corrupt_<ts> then tries bak1→bak2→bak3
        - On missing primary: tries bak1→bak2→bak3 in order
        """
        filepath = cls.resolve_save_path(filepath_or_name)

        def _try_load(path: str) -> Dict[str, Any]:
            """Inner helper: read, parse header, decompress and validate one file."""
            with open(path, "rb") as f:
                linux_optimizer.posix_advise_sequential(f.fileno())
                linux_optimizer.posix_advise_willneed(f.fileno())
                raw_header = f.read(_HEADER_SIZE)
                compressed_payload = f.read()

            if len(raw_header) < _LEGACY_HDR_SIZE:
                raise ValueError("File is too short to be a valid save (header truncated)")

            magic_bytes = raw_header[:4]
            if magic_bytes != _HEADER_MAGIC:
                raise ValueError(f"Magic mismatch: expected b'ECHO', got {magic_bytes!r}")

            # Detect v2.0 vs legacy v1.x by header length
            if len(raw_header) >= _HEADER_SIZE:
                _, checksum, sha256_raw, fmt_ver, _ = struct.unpack(_HEADER_FMT, raw_header[:_HEADER_SIZE])
                # Any remaining bytes beyond the header are part of the payload in v1 reads;
                # For v2 the payload starts right after the full 52-byte header.
                if fmt_ver == _SAVE_VERSION:
                    return deserialize_compressed_payload(compressed_payload, checksum, sha256_raw)
                # fmt_ver mismatch: treat as legacy (don't SHA-256-check — old format)
                _, legacy_checksum = struct.unpack("<4sI", raw_header[:_LEGACY_HDR_SIZE])
                legacy_payload = raw_header[_LEGACY_HDR_SIZE:] + compressed_payload
                return deserialize_compressed_payload(legacy_payload, legacy_checksum, None)
            else:
                # Pure legacy: 8-byte header only
                _, checksum = struct.unpack("<4sI", raw_header[:_LEGACY_HDR_SIZE])
                payload = raw_header[_LEGACY_HDR_SIZE:] + compressed_payload
                return deserialize_compressed_payload(payload, checksum, None)

        def _quarantine(path: str, reason: str) -> None:
            """Rename a corrupted save so it is never silently overwritten."""
            ts = int(time.time())
            quarantine_path = f"{path}.corrupt_{ts}"
            try:
                os.rename(path, quarantine_path)
                print(f"☣️  [QUARANTINE] Corrupted save moved to: {quarantine_path}\n    Reason: {reason}")
            except Exception:
                pass

        # Build ordered candidate list: primary → bak1 → bak2 → bak3
        candidates = [filepath] + [f"{filepath}.bak{i}" for i in range(1, _MAX_BAK_GENS + 1)]
        last_error: Optional[Exception] = None

        for candidate in candidates:
            if not os.path.exists(candidate):
                continue
            try:
                result = _try_load(candidate)
                if candidate != filepath:
                    print(f"✅ [LOAD FALLBACK] Successfully loaded from backup: {candidate}")

                # Align Git lineage on load
                try:
                    loaded_tick = result.get("time", {}).get("tick", 0)
                    meta_p = candidate + ".meta.json"
                    cid = None
                    if os.path.exists(meta_p):
                        with open(meta_p, "r", encoding="utf-8") as mf:
                            cid = json.load(mf).get("commit_id")
                    git_save_manager.on_load_checkpoint(candidate, loaded_tick, cid)
                except Exception:
                    pass

                return result
            except Exception as e:
                last_error = e
                is_primary = (candidate == filepath)
                label = "primary" if is_primary else f"backup {candidate}"
                print(f"❌ [LOAD] {label} is corrupted: {e}")
                _quarantine(candidate, str(e))

        raise RuntimeError(
            f"All save candidates for '{filepath_or_name}' are corrupted or missing. "
            f"Last error: {last_error}"
        )

