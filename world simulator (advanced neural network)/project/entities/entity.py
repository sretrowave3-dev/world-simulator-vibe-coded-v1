"""
project/entities/entity.py

Master Base Entity Data Model for the ALife Simulation Platform.

Architectural Guarantees:
- Zero Rendering Logic: Pure domain state and lightweight validation.
- Zero Saving Logic: Serializers inspect entities externally.
- Stateless System Coordination: Systems calculate and mutate entity state; entities do not own system loops.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class EntityType(Enum):
    GENERIC = auto()
    BACTERIA = auto()
    PLANT = auto()
    HERBIVORE = auto()
    CARNIVORE = auto()
    PREDATOR = auto()
    OMNIVORE = auto()
    DECOMPOSER = auto()
    HUMAN = auto()
    AVIAN = auto()
    AMPHIBIAN = auto()
    ARTHROPOD = auto()
    REPTILE = auto()
    FUNGUS = auto()


class HealthState(Enum):
    HEALTHY = auto()
    INJURED = auto()
    STARVING = auto()
    DEHYDRATED = auto()
    POISONED = auto()
    DISEASED = auto()
    DEAD = auto()


@dataclass(eq=False)
class Entity:
    """
    Base Biological Entity Container.
    Owns physical coordinates, metabolic vitals, and references to AI/genetics.
    """

    # Identification & Taxonomy
    entity_id: str
    species_id: str
    entity_type: EntityType = EntityType.GENERIC
    generation: int = 1
    parent_ids: Tuple[str, ...] = ()
    birth_tick: int = 0

    # Physical / Spatial State
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    heading_angle: float = 0.0  # Radians
    radius: float = 1.0
    mass_kg: float = 1.0

    # Physical Capabilities & Soft-Capped Limits
    base_speed: float = 3.5
    max_speed_cap: float = 14.0
    strength: float = 10.0
    max_strength_cap: float = 120.0
    stamina: float = 100.0
    max_stamina: float = 100.0
    stamina_recovery_rate: float = 0.6
    constitution: float = 1.0  # Biological resilience factor (0.7 to 1.3)

    # Metabolic & Thermoregulation Vitals
    health: float = 100.0
    max_health: float = 100.0
    energy: float = 100.0
    max_energy: float = 100.0
    hydration: float = 100.0
    max_hydration: float = 100.0
    body_temperature_c: float = 37.0
    is_endotherm: bool = True
    hunger_desperation: float = 0.0
    age_ticks: int = 0
    max_age_ticks: int = 10000

    # Metabolic & Reproduction Tuning
    metabolic_rate: float = 0.05
    reproduction_cooldown: int = 0
    maturity_age_ticks: int = 1000

    # Lifecycle State
    is_alive: bool = True
    cause_of_death: Optional[str] = None
    death_tick: Optional[int] = None

    # AI & Biological Sub-references
    genome: Optional[Any] = None
    brain: Optional[Any] = None
    memory: Optional[Any] = None

    # Sensory & Action Buffers
    current_action: str = "IDLE"
    status_effects: Dict[str, float] = field(default_factory=dict)
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-instantiate Neural Network Brain if missing (except for Plant)
        if self.brain is None and type(self).__name__ != "Plant" and self.entity_type != EntityType.PLANT:
            from project.ai.brain import Brain
            self.brain = Brain()
            
        self._apply_individual_variance()

    def _apply_individual_variance(self) -> None:
        """Applies natural individual diversity and genetic alleles to organism physical traits."""
        id_hash = hash(self.entity_id) & 0xFFFF
        var_norm = (id_hash / 65535.0) - 0.5  # [-0.5, 0.5]
        self.mass_kg = max(0.01, self.mass_kg * (1.0 + var_norm * 0.18))
        self.constitution = max(0.65, min(1.35, 1.0 + var_norm * 0.22))
        self.max_health = max(10.0, self.max_health * (1.0 + var_norm * 0.15))
        self.health = min(self.health, self.max_health)
        self.max_stamina = max(20.0, self.max_stamina * (1.0 + var_norm * 0.15))
        self.stamina = self.max_stamina
        if self.base_speed > 0.0:
            self.base_speed = max(0.2, self.base_speed * (1.0 + var_norm * 0.12))
        if self.strength > 0.0:
            self.strength = max(0.2, self.strength * (1.0 + var_norm * 0.15))

        # Apply genetic phenotype traits if genome is present
        if self.genome is not None:
            try:
                pheno = self.genome.express_phenotype()
                self.mass_kg *= pheno.size_modifier
                self.radius *= (pheno.size_modifier ** 0.33)
                if self.base_speed > 0.0:
                    self.base_speed *= pheno.speed_modifier
                self.metabolic_rate *= pheno.metabolism_modifier
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # STATE HELPER & MUTATION METHODS
    # -------------------------------------------------------------------------

    @property
    def position(self) -> Tuple[float, float, float]:
        return (self.pos_x, self.pos_y, self.pos_z)

    @property
    def is_mature(self) -> bool:
        return self.is_alive and self.age_ticks >= self.maturity_age_ticks

    @property
    def is_starving(self) -> bool:
        return self.energy <= 0.0

    @property
    def is_dehydrated(self) -> bool:
        return self.hydration <= 0.0

    @property
    def speed(self) -> float:
        return math.hypot(self.vel_x, self.vel_y)

    @property
    def stamina_ratio(self) -> float:
        return max(0.0, min(1.0, self.stamina / max(1.0, self.max_stamina)))

    @property
    def health_ratio(self) -> float:
        return max(0.0, min(1.0, self.health / max(1.0, self.max_health)))

    @property
    def energy_ratio(self) -> float:
        return max(0.0, min(1.0, self.energy / max(1.0, self.max_energy)))

    @property
    def hydration_ratio(self) -> float:
        return max(0.0, min(1.0, self.hydration / max(1.0, self.max_hydration)))

    @property
    def vitality(self) -> float:
        from project.core.biology import calculate_vitality_multiplier
        return calculate_vitality_multiplier(self.age_ticks, self.maturity_age_ticks, self.max_age_ticks)

    @property
    def combat_power(self) -> float:
        from project.core.biology import calculate_combat_power
        return calculate_combat_power(
            mass_kg=self.mass_kg,
            base_strength=self.strength,
            stamina_ratio=self.stamina_ratio,
            health_ratio=self.health_ratio,
            vitality=self.vitality,
            soft_cap_limit=self.max_strength_cap,
        )

    def drain_stamina(self, amount: float) -> None:
        """Consumes stamina during sprinting/combat."""
        self.stamina = max(0.0, self.stamina - amount)

    def recover_stamina(self, amount: float) -> None:
        """Regenerates stamina when resting or walking."""
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def take_damage(self, amount: float, reason: str = "DAMAGE", tick: int = 0) -> None:
        """Applies damage and handles death state transitions."""
        if not self.is_alive or amount <= 0.0:
            return

        self.health = max(0.0, self.health - amount)
        if self.health <= 0.0:
            self.die(reason=reason, tick=tick)

    def heal(self, amount: float) -> None:
        if not self.is_alive or amount <= 0.0:
            return
        self.health = min(self.max_health, self.health + amount)

    def consume_energy(self, amount: float, tick: int = 0) -> bool:
        """Consumes energy. If depleted, applies starvation damage."""
        if not self.is_alive:
            return False

        self.energy -= amount
        if self.energy <= 0.0:
            self.energy = 0.0
            # Starvation damage
            self.take_damage(amount=1.0, reason="STARVATION", tick=tick)
            return False
        return True

    def gain_energy(self, amount: float) -> None:
        if not self.is_alive or amount <= 0.0:
            return
        self.energy = min(self.max_energy, self.energy + amount)

    def quench_thirst(self, amount: float) -> None:
        if not self.is_alive or amount <= 0.0:
            return
        self.hydration = min(self.max_hydration, self.hydration + amount)

    def consume_hydration(self, amount: float, tick: int = 0) -> bool:
        if not self.is_alive:
            return False

        self.hydration -= amount
        if self.hydration <= 0.0:
            self.hydration = 0.0
            self.take_damage(amount=1.5, reason="DEHYDRATION", tick=tick)
            return False
        return True

    def die(self, reason: str = "NATURAL", tick: int = 0) -> None:
        """Marks the entity as dead."""
        self.is_alive = False
        self.health = 0.0
        self.cause_of_death = reason
        self.death_tick = tick

    def add_status_effect(self, effect_name: str, duration_seconds: float) -> None:
        self.status_effects[effect_name] = max(
            self.status_effects.get(effect_name, 0.0), duration_seconds
        )

    def has_status_effect(self, effect_name: str) -> bool:
        return self.status_effects.get(effect_name, 0.0) > 0.0

    def __hash__(self) -> int:
        return hash(self.entity_id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.entity_id == other.entity_id
