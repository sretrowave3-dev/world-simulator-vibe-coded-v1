"""
project/systems/vegetation_system.py

Vegetation System running photosynthesis, plant-to-tree maturation, forest canopy growth,
seed dispersal, root mineral absorption, and dynamic woodland biome emergence.
"""

from __future__ import annotations

import random
import math
from typing import Set, List, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.vegetation import VegetationManager
from project.world.soil import SoilManager
from project.entities.plant import Plant
from project.entities.fungus import Fungus
from project.entities.entity import Entity, EntityType


class VegetationSystem:
    """Manages plant growth, ecological coverage, tree maturation, and forest expansion."""

    def __init__(self, vegetation_manager: VegetationManager, soil_manager: SoilManager, entities_list: Optional[List[Entity]] = None) -> None:
        self._vegetation_manager = vegetation_manager
        self._soil_manager = soil_manager
        self._entities_list = entities_list if entities_list is not None else []
        self._flora_spawn_id: int = 50000

    @property
    def name(self) -> str:
        return "VegetationSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.WORLD

    @property
    def priority(self) -> int:
        return ExecutionPriority.PLANTS

    @property
    def dependencies(self) -> Set[str]:
        return {"SoilSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        self._vegetation_manager.reset()

    def update(self, context: UpdateContext) -> None:
        dt = context.delta_time
        sim_tick = context.tick

        # Modulate sunlight by diurnal cycle and solar insolation
        daylight = 1.0
        insolation = 1.0
        time_snap = getattr(context, "time_snapshot", None)
        if time_snap:
            daylight = getattr(time_snap, "daylight_factor", 1.0)
            insolation = getattr(time_snap, "insolation_factor", 1.0)
        sunlight_flux = max(0.02, daylight * insolation)

        # 1. Loop through active chunks and grow vegetation canopy based on local soil nutrients and sunlight
        for coords, veg_chunk in list(self._vegetation_manager.chunks.items()):
            soil_chunk = self._soil_manager.get_or_create_chunk(coords)
            
            avg_n = sum(soil_chunk.nitrogen) / len(soil_chunk.nitrogen)
            avg_m = sum(soil_chunk.moisture) / len(soil_chunk.moisture)

            veg_chunk.grow(
                dt=dt,
                sunlight_flux=sunlight_flux,
                temperature_c=22.0,
                moisture=max(0.2, avg_m),
                nitrogen_available=avg_n,
            )

        # 2. Photosynthesis & Growth for living plant entities (Sprouts -> Trees -> Forests)
        plants_alive = [e for e in self._entities_list if e.is_alive and e.entity_type == EntityType.PLANT]

        for plant in plants_alive:
            # Query local soil condition
            soil_prof = self._soil_manager.query_soil(plant.pos_x, plant.pos_y)
            nutrient_factor = (soil_prof.nitrogen + soil_prof.moisture + soil_prof.organic_matter) / 3.0

            if sunlight_flux > 0.15:
                energy_gain = sunlight_flux * 0.8 * nutrient_factor * dt
                plant.gain_energy(energy_gain)

                # Grow biomass: Plants mature into Trees and Forests
                growth_rate = 0.08 * nutrient_factor * (plant.energy / max(1.0, plant.max_energy)) * dt
                if plant.energy > 80.0 and plant.biomass_kg < plant.max_biomass_kg:
                    plant.grow_biomass(growth_rate)
                    plant.energy -= growth_rate * 5.0

            # 3. Tree Seed Dispersal: Forming Clusters and Forests
            if plant.is_tree() and sim_tick % 60 == 0:
                if len(self._entities_list) < 1200 and random.random() < 0.15 and plant.can_reproduce_seed():
                    # Disperse seed within canopy radius
                    spread_dist = random.uniform(8.0, plant.seed_spread_radius)
                    angle = random.uniform(0.0, 2.0 * math.pi)
                    sapling_x = max(100.0, plant.pos_x + math.cos(angle) * spread_dist)
                    sapling_y = max(100.0, plant.pos_y + math.sin(angle) * spread_dist)

                    self._flora_spawn_id += 1
                    sapling = Plant(
                        entity_id=f"tree_offspring_{self._flora_spawn_id}",
                        species_id=plant.species_id,
                        pos_x=sapling_x,
                        pos_y=sapling_y,
                        biomass_kg=4.0,  # Starts as young sprout/sapling
                        energy=100.0,
                    )
                    sapling.custom_data["emergent_role"] = "PRODUCER"
                    sapling.custom_data["parent_tree"] = plant.entity_id
                    self._entities_list.append(sapling)
                    plant.energy -= plant.seed_production_cost
                    plant.reproduction_cooldown = 150

        # 4. Spontaneous Diverse Flora Germination in Favorable Soil
        if sim_tick % 35 == 0 and len(self._entities_list) < 1000 and random.random() < 0.30:
            if self._vegetation_manager.chunks:
                coords = random.choice(list(self._vegetation_manager.chunks.keys()))
                soil_chunk = self._soil_manager.get_or_create_chunk(coords)
                avg_n = sum(soil_chunk.nitrogen) / len(soil_chunk.nitrogen)
                avg_m = sum(soil_chunk.moisture) / len(soil_chunk.moisture)

                if avg_m > 0.20:
                    cx, cy = coords
                    world_x = cx * 16.0 + random.uniform(2.0, 14.0)
                    world_y = cy * 16.0 + random.uniform(2.0, 14.0)

                    flora_choice = random.choice(["oak_tree", "pine_tree", "fruit_tree", "berry_bush", "wild_grain", "mycelium_fungus"])
                    self._flora_spawn_id += 1
                    eid = f"flora_{flora_choice}_{self._flora_spawn_id}"

                    if flora_choice == "mycelium_fungus":
                        new_fungus = Fungus(
                            entity_id=eid,
                            species_id="fungus_spore",
                            pos_x=world_x,
                            pos_y=world_y,
                            max_health=80.0,
                            health=80.0,
                            energy=120.0,
                        )
                        new_fungus.custom_data["emergent_role"] = "PRODUCER"
                        self._entities_list.append(new_fungus)
                    else:
                        init_biomass = 35.0 if "tree" in flora_choice else 3.0
                        new_plant = Plant(
                            entity_id=eid,
                            species_id=flora_choice,
                            pos_x=world_x,
                            pos_y=world_y,
                            biomass_kg=init_biomass,
                            max_health=100.0,
                            health=100.0,
                            energy=250.0,
                        )
                        new_plant.custom_data["emergent_role"] = "PRODUCER"
                        new_plant.custom_data["flora_variety"] = flora_choice
                        self._entities_list.append(new_plant)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
