"""
project/systems/digestion_system.py

Digestion System processing metabolic consumption, photosynthesis, chemosynthesis,
grazing, predatory hunting, saprophytic decomposition, and diverse food consumption across all species.
"""

from __future__ import annotations

import math
from typing import Set, List
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.fungus import Fungus
from project.entities.amphibian import Amphibian
from project.entities.avian import Avian
from project.entities.arthropod import Arthropod
from project.entities.reptile import Reptile
from project.world.vegetation import VegetationManager
from project.world.water import WaterManager


class DigestionSystem:
    """Manages multi-trophic metabolic decay, autotrophic synthesis, nutrient ingestion, and varied diets."""

    def __init__(
        self,
        entities_list: List[Entity],
        vegetation_manager: VegetationManager,
        water_manager: WaterManager,
    ) -> None:
        self._entities_list = entities_list
        self._vegetation_manager = vegetation_manager
        self._water_manager = water_manager

    @property
    def name(self) -> str:
        return "DigestionSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.DIGESTION

    @property
    def dependencies(self) -> Set[str]:
        return {"MovementSystem"}

    @property
    def is_critical(self) -> bool:
        return True

    def initialize(self, context: UpdateContext) -> None:
        pass

    def feed_humans(self, energy_amount: float = 150.0, hydration_amount: float = 80.0) -> int:
        """Explicitly feeds and hydrates all active humans in the world."""
        count = 0
        for entity in self._entities_list:
            if entity.is_alive and entity.entity_type == EntityType.HUMAN:
                if isinstance(entity, Human):
                    entity.feed(energy_amount, hydration_amount)
                else:
                    entity.gain_energy(energy_amount)
                    entity.quench_thirst(hydration_amount)
                count += 1
        return count

    def update(self, context: UpdateContext) -> None:
        dt = context.delta_time
        from project.core.biology import calculate_basal_metabolism, calculate_hunger_urgency, calculate_thirst_urgency
        from project.world.seeds import world_seed_growth_mgr

        # 0. Live Seed Germination & Abnormal Mutation Growth
        world_seed_growth_mgr.update(dt, context.tick, self._entities_list, getattr(self, "_soil_mgr", None))

        for entity in list(self._entities_list):
            if not entity.is_alive:
                continue

            # -------------------------------------------------------------
            # 1. Kleiber's Law Allometric Metabolism & Thermoregulation
            # -------------------------------------------------------------
            is_endo = getattr(entity, "is_endotherm", True)
            opt_temp = getattr(entity, "body_temperature_c", 37.0)
            bmr = calculate_basal_metabolism(
                mass_kg=entity.mass_kg,
                metabolic_factor=entity.metabolic_rate,
                is_endotherm=is_endo,
                ambient_temp_c=22.0,
                optimal_temp_c=opt_temp,
            ) * (dt * 15.0)

            # Sessile autotrophs/fungi have minimal resting maintenance
            if entity.entity_type in (EntityType.PLANT, EntityType.FUNGUS):
                bmr *= 0.15
            elif entity.entity_type == EntityType.BACTERIA:
                bmr *= 0.20

            entity.consume_energy(bmr, tick=context.tick)
            entity.consume_hydration(bmr * 0.55, tick=context.tick)

            # Update continuous psychological hunger & thirst urgency
            entity.hunger_desperation = calculate_hunger_urgency(entity.energy, entity.max_energy)

            if not entity.is_alive:
                continue

            # -------------------------------------------------------------
            # 2. Trophic Nutrient Ingestion & Dietary Specialization
            # -------------------------------------------------------------
            cx = int(math.floor(entity.pos_x / 16.0))
            cy = int(math.floor(entity.pos_y / 16.0))
            lx = int(math.floor(entity.pos_x)) % 16
            ly = int(math.floor(entity.pos_y)) % 16

            # A. Autotrophs (Plants): Photosynthesis & Soil Root Absorption
            if entity.entity_type == EntityType.PLANT:
                photosynthesis_gain = 5.5 * dt * getattr(entity, "photosynthesis_efficiency", 0.85)
                entity.gain_energy(photosynthesis_gain)
                entity.quench_thirst(3.0 * dt)
                if isinstance(entity, Plant):
                    entity.biomass_kg = min(entity.max_biomass_kg, entity.biomass_kg + (0.04 * dt))
                    if entity.is_mature and entity.energy >= 45.0:
                        entity.is_flowering = True
                        entity.is_pollinated = True

            # B. Saprophytes (Fungus & Decomposers): Detritus & Carcass Breakdown
            elif entity.entity_type in (EntityType.FUNGUS, EntityType.DECOMPOSER):
                saprophyte_gain = 4.5 * dt * getattr(entity, "decomposition_efficiency", 1.2)
                entity.gain_energy(saprophyte_gain)
                entity.quench_thirst(3.0 * dt)

            # C. Chemophiles (Bacteria): Rapid Chemosynthesis & Substrate Absorption
            elif entity.entity_type == EntityType.BACTERIA:
                absorption_gain = 5.0 * dt
                entity.gain_energy(absorption_gain)
                entity.quench_thirst(2.5 * dt)

            # D. Herbivores: Active Grazing from Local Vegetation Chunk
            elif entity.entity_type == EntityType.HERBIVORE:
                veg_chunk = self._vegetation_manager.get_or_create_chunk((cx, cy))
                grazed_kg = veg_chunk.graze(lx, ly, requested_kg=8.0 * dt)
                if grazed_kg > 0.001:
                    graze_gain = grazed_kg * 42.0 * getattr(entity, "graze_efficiency", 0.9)
                    entity.gain_energy(graze_gain)
                    entity.quench_thirst(grazed_kg * 15.0)

            # E. Carnivores & Predators: Feast-and-fast metabolism (Combat kills feed predators)
            elif entity.entity_type in (EntityType.CARNIVORE, EntityType.PREDATOR):
                # Mild baseline energy conservation when rested
                if entity.energy < (entity.max_energy * 0.4):
                    # Scavenge small prey / insects if starving
                    entity.gain_energy(1.2 * dt)

            # F. Avians: Aerial Foraging (Seeds, Insects, Small Prey)
            elif entity.entity_type == EntityType.AVIAN:
                entity.gain_energy(3.5 * dt)
                entity.quench_thirst(2.5 * dt)

            # G. Amphibians: Cutaneous Moisture & Insect Foraging
            elif entity.entity_type == EntityType.AMPHIBIAN:
                entity.gain_energy(3.0 * dt)
                entity.quench_thirst(4.5 * dt)

            # H. Arthropods: Nectar & Pollen Foraging
            elif entity.entity_type == EntityType.ARTHROPOD:
                entity.gain_energy(3.8 * dt)
                entity.quench_thirst(2.0 * dt)

            # I. Reptiles: Low Consumption & Solar Thermoregulation
            elif entity.entity_type == EntityType.REPTILE:
                entity.gain_energy(2.2 * dt)
                entity.quench_thirst(1.8 * dt)

            # J. Humans: Omnivorous Cooking, Agriculture, & High-Calorie Diets
            elif entity.entity_type == EntityType.HUMAN:
                # Active foraging and cultural cultivation
                veg_chunk = self._vegetation_manager.get_or_create_chunk((cx, cy))
                grazed_kg = veg_chunk.graze(lx, ly, requested_kg=4.0 * dt)
                foraging_gain = (grazed_kg * 40.0) + (5.0 * dt)
                entity.gain_energy(foraging_gain)
                entity.quench_thirst(4.0 * dt)
                if entity.energy >= 300.0:
                    entity.custom_data["dopamine"] = max(entity.custom_data.get("dopamine", 0.5), 0.85)

            elif entity.entity_type == EntityType.OMNIVORE:
                veg_chunk = self._vegetation_manager.get_or_create_chunk((cx, cy))
                grazed_kg = veg_chunk.graze(lx, ly, requested_kg=5.0 * dt)
                entity.gain_energy((grazed_kg * 35.0) + (3.0 * dt))
                entity.quench_thirst(3.0 * dt)

            # -------------------------------------------------------------
            # 3. Dedicated Drinking Behavior at Water Sources
            # -------------------------------------------------------------
            if entity.current_action == "DRINK_WATER" or getattr(entity, "thirst_urgency", 0.0) > 0.65:
                water_chunk = self._water_manager.get_or_create_chunk((cx, cy))
                drank_l, toxicity = water_chunk.drink(lx, ly, volume_liters=12.0 * dt)
                if drank_l > 0.0:
                    entity.quench_thirst(drank_l * 20.0)
                    if toxicity > 0.1:
                        entity.take_damage(toxicity * 10.0 * dt, reason="POISONING", tick=context.tick)

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
