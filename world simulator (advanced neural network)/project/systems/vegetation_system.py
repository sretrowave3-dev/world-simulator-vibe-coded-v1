"""
project/systems/vegetation_system.py

Vegetation System running photosynthesis, plant canopy growth, root mineral absorption,
and spontaneous dynamic flora generation in nutrient-rich favorable soil biomes.
"""

from __future__ import annotations

import random
from typing import Set, List, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.world.vegetation import VegetationManager
from project.world.soil import SoilManager
from project.entities.plant import Plant
from project.entities.fungus import Fungus
from project.entities.entity import Entity


class VegetationSystem:
    """Manages plant growth, ecological coverage, and spontaneous flora sprouting in fertile soil."""

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
            avg_om = sum(soil_chunk.organic_matter) / len(soil_chunk.organic_matter)
            
            # Grow vegetation chunk with solar flux
            veg_chunk.grow(
                dt=dt,
                sunlight_flux=sunlight_flux,
                temperature_c=22.0,
                moisture=max(0.2, avg_m),
                nitrogen_available=avg_n,
            )

        # 1b. Sunlight Photosynthesis for living plant entities
        if sunlight_flux > 0.15:
            from project.entities.entity import EntityType
            for ent in self._entities_list:
                if ent.is_alive and ent.entity_type == EntityType.PLANT:
                    ent.gain_energy(sunlight_flux * 0.5 * dt)

            # -------------------------------------------------------------
            # 2. Spontaneous Diverse Flora Germination in Favorable Soil
            # -------------------------------------------------------------
            # When soil has high moisture, nitrogen, and organic matter, new flora emerges
            if context.tick % 25 == 0:
                if avg_n > 12.0 and avg_m > 0.20 and len(self._entities_list) < 700 and random.random() < 0.35:
                    cx, cy = coords
                    world_x = cx * 16.0 + random.uniform(2.0, 14.0)
                    world_y = cy * 16.0 + random.uniform(2.0, 14.0)

                    flora_choice = random.choice(["berry_bush", "wild_grain", "fruit_tree", "medicinal_herb", "mycelium_fungus"])
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
                        new_plant = Plant(
                            entity_id=eid,
                            species_id=flora_choice,
                            pos_x=world_x,
                            pos_y=world_y,
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
