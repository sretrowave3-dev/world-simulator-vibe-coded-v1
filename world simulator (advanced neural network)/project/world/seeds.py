"""
project/world/seeds.py

Planetary Seed Lifecycle, Discard Logging & Live Growth Engine for the ALife Platform.

Features:
- Structured Fruit Seed Metadata (Pit Seeds, Vine Seeds, Berry Seeds, Grains).
- Real-Time Live Seed Growth Simulation (Dormant Seed -> Sprout -> Sapling -> Mature Flora).
- Stochastic Genetic Abnormalities & Mutations (Bioluminescent, Giant, Drought-Resistant, Rapid, etc.).
- Persistent & Thread-Safe JSON Seed Discard Logging with In-Memory Cache (`seeds_log.json`).
- Dynamic Ecosystem Conversion: Discarded seeds on fertile soil grow into physical Plants in the world.
"""

from __future__ import annotations

import os
import json
import time
import math
import random
import threading
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set

from project.entities.plant import Plant
from project.entities.entity import Entity, EntityType

SEED_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "seeds_log.json"))


class SeedAbnormality(Enum):
    NONE = "None (Normal Specimen)"
    BIOLUMINESCENT = "Bioluminescent Glow (Radiates cyan-violet aura)"
    GIANT_GROWTH = "Gigantism (2.5x biomass, hyper-yield canopy)"
    DROUGHT_RESISTANT = "Xerophytic Adaptation (Survives arid desert soil)"
    RAPID_METABOLISM = "Hyper-Sprout (3x germination speed)"
    SWEET_NECTAR = "Saccharine Mutation (Hyper-caloric +150 Energy fruit)"
    MEDICINAL_SAP = "Therapeutic Sap (Accelerated healing & disease cure)"
    VARIEGATED_CHIMERA = "Variegated Pigment (Exotic multicolor foliage)"


@dataclass
class Seed:
    seed_id: str
    parent_fruit: str
    pos_x: float
    pos_y: float
    dropped_by_entity_id: str
    eater_species: str
    drop_tick: int
    drop_timestamp: float = field(default_factory=time.time)
    
    # Growth parameters
    growth_progress: float = 0.0  # 0.0 to 1.0
    germination_speed: float = 0.05
    viability: float = 0.95
    stage: str = "DORMANT_SEED"  # DORMANT_SEED, SPROUT, SAPLING, MATURE_PLANT
    
    # Genetics & Abnormalities
    has_abnormality: bool = False
    abnormality: SeedAbnormality = SeedAbnormality.NONE
    abnormality_trait: str = "Normal"
    abnormality_description: str = "Standard biological phenotype."
    
    is_planted: bool = True
    is_germinated: bool = False
    is_mature: bool = False
    spawned_plant_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "parent_fruit": self.parent_fruit,
            "location": {"x": round(self.pos_x, 2), "y": round(self.pos_y, 2)},
            "dropped_by": self.dropped_by_entity_id,
            "eater_species": self.eater_species,
            "drop_tick": self.drop_tick,
            "drop_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.drop_timestamp)),
            "growth_progress_pct": round(self.growth_progress * 100.0, 1),
            "stage": self.stage,
            "viability": round(self.viability, 3),
            "has_abnormality": self.has_abnormality,
            "abnormality_trait": self.abnormality_trait,
            "abnormality_description": self.abnormality_description,
        }


class SeedLogManager:
    """Thread-safe persistent JSON logger and memory cache for discarded seeds."""

    def __init__(self, log_path: str = SEED_LOG_PATH) -> None:
        self.log_path = log_path
        self._lock = threading.Lock()
        self._cache: List[Dict[str, Any]] = []
        self._load_initial_log()

    def _load_initial_log(self) -> None:
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = []
        else:
            self._cache = []
            self._flush_to_disk()

    def _flush_to_disk(self) -> None:
        try:
            temp_p = f"{self.log_path}.tmp"
            with open(temp_p, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
            os.replace(temp_p, self.log_path)
        except Exception as e:
            pass

    def log_seed_drop(
        self,
        eater_id: str,
        eater_species: str,
        fruit_name: str,
        pos_x: float,
        pos_y: float,
        sim_tick: int,
        seeds: List[Seed],
    ) -> None:
        """Appends a new seed discard event to cache and persists to disk."""
        entry = {
            "event": "FRUIT_EATEN_SEEDS_DISCARDED",
            "sim_tick": sim_tick,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "eater_id": eater_id,
            "eater_species": eater_species,
            "fruit_consumed": fruit_name,
            "seeds_left_count": len(seeds),
            "location": {"x": round(pos_x, 2), "y": round(pos_y, 2)},
            "seeds_detail": [s.to_dict() for s in seeds],
        }

        with self._lock:
            self._cache.append(entry)
            # Keep cache bounded to last 5,000 events
            if len(self._cache) > 5000:
                self._cache = self._cache[-5000:]
            self._flush_to_disk()

    def log_growth_event(self, seed: Seed, event_type: str, sim_tick: int) -> None:
        """Logs germination or maturity milestones."""
        entry = {
            "event": event_type,
            "sim_tick": sim_tick,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "seed_id": seed.seed_id,
            "parent_fruit": seed.parent_fruit,
            "final_stage": seed.stage,
            "location": {"x": round(seed.pos_x, 2), "y": round(seed.pos_y, 2)},
            "has_abnormality": seed.has_abnormality,
            "abnormality_trait": seed.abnormality_trait,
            "spawned_plant_id": seed.spawned_plant_id,
        }
        with self._lock:
            self._cache.append(entry)
            self._flush_to_disk()

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._cache[-limit:])


# Global Seed Log Manager Singleton
seed_logger = SeedLogManager()


class SeedGrowthManager:
    """Manages real-time germination, physiological development, and abnormal mutations of seeds."""

    def __init__(self) -> None:
        self.active_seeds: List[Seed] = []
        self._lock = threading.Lock()
        self.total_seeds_germinated: int = 0
        self.total_abnormal_mutations: int = 0

    def generate_fruit_seeds(
        self,
        fruit_type: str,
        pos_x: float,
        pos_y: float,
        eater_id: str,
        eater_species: str,
        sim_tick: int,
    ) -> List[Seed]:
        """Creates physical seeds with species-specific counts and mutation chances."""
        f_low = fruit_type.lower()
        seeds: List[Seed] = []

        if "mango" in f_low:
            # Mango has 1 large stone pit seed
            count = 1
            base_viability = 0.96
            germ_spd = 0.04
            abnormality_chance = 0.10
        elif "cucumber" in f_low:
            # Cucumber has 8-16 small vine seeds
            count = random.randint(8, 16)
            base_viability = 0.90
            germ_spd = 0.08
            abnormality_chance = 0.07
        elif "berry" in f_low:
            # Berry has 4-8 small seeds
            count = random.randint(4, 8)
            base_viability = 0.88
            germ_spd = 0.10
            abnormality_chance = 0.06
        elif "apple" in f_low or "fruit" in f_low:
            # Apple has 3-6 core seeds
            count = random.randint(3, 6)
            base_viability = 0.92
            germ_spd = 0.06
            abnormality_chance = 0.08
        elif "grain" in f_low or "wheat" in f_low:
            # Grain has 6-12 crop seeds
            count = random.randint(6, 12)
            base_viability = 0.98
            germ_spd = 0.12
            abnormality_chance = 0.04
        else:
            # Default generic fruit seed
            count = random.randint(2, 4)
            base_viability = 0.90
            germ_spd = 0.07
            abnormality_chance = 0.05

        for i in range(count):
            sid = f"seed_{f_low}_{sim_tick}_{random.randint(1000, 9999)}_{i+1}"
            # Small random scatter around eating location
            sx = pos_x + random.uniform(-4.0, 4.0)
            sy = pos_y + random.uniform(-4.0, 4.0)
            
            # Roll for genetic abnormality
            has_ab = random.random() < abnormality_chance
            ab_type = SeedAbnormality.NONE
            ab_trait = "Normal"
            ab_desc = "Standard biological specimen."

            if has_ab:
                possible_abnormalities = [
                    (SeedAbnormality.BIOLUMINESCENT, "Bioluminescent Glow", "Radiates cyan-violet aura; glows brightly in dark biomes.", 1.2),
                    (SeedAbnormality.GIANT_GROWTH, "Gigantism Growth", "Produces massive 2.5x oversized canopy with double fruit yield.", 0.8),
                    (SeedAbnormality.DROUGHT_RESISTANT, "Xerophytic Adaptation", "Thrives in dry arid soil with near-zero moisture.", 1.0),
                    (SeedAbnormality.RAPID_METABOLISM, "Hyper-Sprout Rate", "Accelerated mitotic division; germinates 3x faster.", 2.5),
                    (SeedAbnormality.SWEET_NECTAR, "Saccharine Nectar", "Ultra-dense sugar accumulation providing +150 Energy when eaten.", 1.0),
                    (SeedAbnormality.MEDICINAL_SAP, "Therapeutic Bio-Sap", "Enriched with antimicrobial alkaloids that cure injuries.", 1.0),
                    (SeedAbnormality.VARIEGATED_CHIMERA, "Variegated Chimera", "Exotic polychromatic photosynthetic pigmentation.", 1.1),
                ]
                chosen = random.choice(possible_abnormalities)
                ab_type = chosen[0]
                ab_trait = chosen[1]
                ab_desc = chosen[2]
                germ_spd *= chosen[3]
                self.total_abnormal_mutations += 1

            seed = Seed(
                seed_id=sid,
                parent_fruit=fruit_type.capitalize(),
                pos_x=sx,
                pos_y=sy,
                dropped_by_entity_id=eater_id,
                eater_species=eater_species,
                drop_tick=sim_tick,
                germination_speed=germ_spd,
                viability=base_viability,
                has_abnormality=has_ab,
                abnormality=ab_type,
                abnormality_trait=ab_trait,
                abnormality_description=ab_desc,
            )
            seeds.append(seed)

        with self._lock:
            self.active_seeds.extend(seeds)

        # Log discarded seeds
        seed_logger.log_seed_drop(
            eater_id=eater_id,
            eater_species=eater_species,
            fruit_name=fruit_type.capitalize(),
            pos_x=pos_x,
            pos_y=pos_y,
            sim_tick=sim_tick,
            seeds=seeds,
        )

        return seeds

    def update(
        self,
        dt: float,
        sim_tick: int,
        entities_list: List[Entity],
        soil_mgr: Optional[Any] = None,
    ) -> None:
        """Updates live seed growth on terrain and converts mature seeds to plants."""
        with self._lock:
            surviving_seeds: List[Seed] = []

            for seed in self.active_seeds:
                if not seed.is_planted or seed.is_mature:
                    continue

                # Soil moisture & nutrient factor
                soil_factor = 1.0
                if soil_mgr and hasattr(soil_mgr, "query_soil"):
                    try:
                        profile = soil_mgr.query_soil(seed.pos_x, seed.pos_y)
                        if seed.abnormality == SeedAbnormality.DROUGHT_RESISTANT:
                            soil_factor = 1.2
                        else:
                            soil_factor = max(0.2, min(1.5, profile.moisture * 1.5 + profile.organic_matter * 0.5))
                    except Exception:
                        soil_factor = 1.0

                # Advance germination progress
                growth_delta = seed.germination_speed * soil_factor * dt * 0.5
                seed.growth_progress = min(1.0, seed.growth_progress + growth_delta)

                # Stage transitions
                if seed.growth_progress >= 1.0:
                    seed.stage = "MATURE_PLANT"
                    seed.is_mature = True
                    self.total_seeds_germinated += 1
                    
                    # Spawn real Plant in the living simulation ecosystem!
                    plant_id = f"plant_{seed.parent_fruit.lower()}_{sim_tick}_{random.randint(100, 999)}"
                    sp_id = f"{seed.parent_fruit.lower()}_flora"
                    new_plant = Plant(
                        entity_id=plant_id,
                        species_id=sp_id,
                        pos_x=seed.pos_x,
                        pos_y=seed.pos_y,
                    )
                    
                    # Apply genetic abnormality traits
                    new_plant.custom_data["parent_seed_id"] = seed.seed_id
                    new_plant.custom_data["parent_fruit"] = seed.parent_fruit
                    new_plant.custom_data["has_abnormality"] = seed.has_abnormality
                    new_plant.custom_data["abnormality_trait"] = seed.abnormality_trait
                    new_plant.custom_data["fruit_type"] = seed.parent_fruit.lower()

                    if seed.has_abnormality:
                        if seed.abnormality == SeedAbnormality.BIOLUMINESCENT:
                            new_plant.custom_data["bioluminescent"] = True
                            new_plant.custom_data["glow_color"] = (0, 240, 255)
                        elif seed.abnormality == SeedAbnormality.GIANT_GROWTH:
                            new_plant.radius *= 2.0
                            new_plant.max_health *= 2.5
                            new_plant.health = new_plant.max_health
                            new_plant.custom_data["giant"] = True
                        elif seed.abnormality == SeedAbnormality.SWEET_NECTAR:
                            new_plant.max_energy = 500.0
                            new_plant.energy = 450.0
                            new_plant.custom_data["sweet_nectar"] = True

                    entities_list.append(new_plant)
                    seed.spawned_plant_id = plant_id

                    seed_logger.log_growth_event(seed, "SEED_MATURED_TO_FLORA", sim_tick)

                elif seed.growth_progress >= 0.60:
                    if seed.stage != "SAPLING":
                        seed.stage = "SAPLING"
                    surviving_seeds.append(seed)
                elif seed.growth_progress >= 0.25:
                    if seed.stage != "SPROUT":
                        seed.stage = "SPROUT"
                        if not seed.is_germinated:
                            seed.is_germinated = True
                            seed_logger.log_growth_event(seed, "SEED_GERMINATED_SPROUT", sim_tick)
                    surviving_seeds.append(seed)
                else:
                    surviving_seeds.append(seed)

            self.active_seeds = surviving_seeds


# Global Seed Growth Manager Singleton
world_seed_growth_mgr = SeedGrowthManager()
