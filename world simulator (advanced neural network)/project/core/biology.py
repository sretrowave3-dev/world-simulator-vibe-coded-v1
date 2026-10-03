"""
project/core/biology.py

Natural Biological Allometry, Physiology & Continuous Trait Scaling Engine.

Features:
- Asymptotic Soft-Capping Functions: Smooth hyperbolic tangent diminishing returns preventing
  unbounded trait growth while allowing meaningful phenotypic divergence.
- Kleiber's Law Allometric Metabolism: Basal Metabolic Rate scaling with body mass (M^0.75)
  and kinetic movement energy dissipation (M * v^1.5).
- Thermoregulation & Temperature Homeostasis: Endothermic shivering/sweating energy burn vs
  Ectothermic Q10 physiological activity scaling.
- Continuous Non-Linear Hunger & Thirst Urgency Curves (logistic/sigmoidal urgency progression).
- Gompertz-Makeham Stochastic Senescence: Natural cellular aging hazard with bell-curve mortality.
- Age-Vitality Curves: Smooth maturation ramp-up, peak adult vitality, and gradual elder decline.
"""

from __future__ import annotations

import math
from typing import Tuple


def soft_cap(raw_value: float, soft_limit: float, hardness: float = 1.0) -> float:
    """
    Smooth asymptotic soft-cap function using scaled hyperbolic tangent.
    Below soft_limit * 0.75, behavior is nearly linear.
    Above soft_limit, diminishing returns asymptotically approach soft_limit * (1 + 1/hardness).
    """
    if soft_limit <= 0.0:
        return 0.0
    if raw_value <= 0.0:
        return 0.0
    
    # Normalized ratio
    ratio = raw_value / soft_limit
    if ratio < 0.5:
        return raw_value
    
    # Asymptotic compression
    compressed = math.tanh(ratio / hardness) * hardness
    return soft_limit * compressed


def calculate_basal_metabolism(
    mass_kg: float,
    metabolic_factor: float = 1.0,
    is_endotherm: bool = True,
    ambient_temp_c: float = 20.0,
    optimal_temp_c: float = 37.0,
) -> float:
    """
    Computes basal metabolic rate (BMR) per tick based on Kleiber's Law (Mass^0.75).
    Endotherms burn additional caloric reserves to maintain thermal homeostasis in extreme cold/heat.
    Ectotherms experience physiological slowing in cold and acceleration in warm climates (Q10 rule).
    """
    safe_mass = max(0.001, mass_kg)
    # Kleiber's Law standard allometric scaling
    base_bmr = 0.035 * (safe_mass ** 0.75) * metabolic_factor

    if is_endotherm:
        # Thermoregulation cost when ambient temperature diverges from internal optimum
        temp_delta = abs(ambient_temp_c - optimal_temp_c)
        thermal_cost = 1.0 + (temp_delta * 0.02)  # +2% per degree C deviation
        return base_bmr * thermal_cost
    else:
        # Ectotherm Q10 temperature coefficient (Q10 = 2.0 per 10°C)
        temp_diff = ambient_temp_c - 22.0
        q10_factor = 2.0 ** (temp_diff / 10.0)
        q10_clamped = max(0.25, min(2.5, q10_factor))
        return base_bmr * q10_clamped


def calculate_locomotion_cost(
    mass_kg: float,
    speed: float,
    efficiency: float = 1.0,
) -> float:
    """
    Computes kinetic and muscular locomotion energy cost based on mass and speed (Mass * Speed^1.5).
    """
    if speed <= 0.01:
        return 0.0
    safe_mass = max(0.001, mass_kg)
    eff = max(0.1, efficiency)
    cost = 0.012 * safe_mass * (speed ** 1.5) / eff
    return cost


def calculate_hunger_urgency(energy: float, max_energy: float) -> float:
    """
    Non-linear logistic curve mapping energy reserve ratio to hunger urgency [0.0 to 1.0].
    - > 70% Energy: Satiated, negligible urgency (< 0.1).
    - 40% - 60% Energy: Mild to moderate foraging appetite.
    - 20% - 35% Energy: Acute hunger, prioritized search for sustenance.
    - < 15% Energy: Critical starvation desperation (> 0.9).
    """
    if max_energy <= 0.0:
        return 1.0
    ratio = max(0.0, min(1.0, energy / max_energy))
    # Inverted sigmoid centered around 0.35
    urgency = 1.0 / (1.0 + math.exp(10.0 * (ratio - 0.35)))
    return max(0.0, min(1.0, urgency))


def calculate_thirst_urgency(hydration: float, max_hydration: float) -> float:
    """
    Non-linear logistic curve mapping hydration ratio to thirst urgency [0.0 to 1.0].
    """
    if max_hydration <= 0.0:
        return 1.0
    ratio = max(0.0, min(1.0, hydration / max_hydration))
    # Steep sigmoid centered around 0.30 (thirst escalates faster than hunger)
    urgency = 1.0 / (1.0 + math.exp(12.0 * (ratio - 0.30)))
    return max(0.0, min(1.0, urgency))


def calculate_vitality_multiplier(
    age_ticks: int,
    maturity_ticks: int,
    max_age_ticks: int,
) -> float:
    """
    Smooth developmental vitality curve:
    - Juvenile: Ramps up smoothly from 0.5 to 1.0 as organism approaches maturity.
    - Prime Adult: Sustained peak vitality (1.0).
    - Elder: Gradual physiological decline (down to ~0.65 in extreme age).
    """
    if age_ticks < maturity_ticks:
        # Juvenile growth curve
        prog = max(0.0, age_ticks / max(1, maturity_ticks))
        return 0.5 + 0.5 * (prog ** 0.6)
    
    if age_ticks <= max_age_ticks * 0.70:
        # Prime adult phase
        return 1.0
    
    # Elder senescence phase
    elder_prog = (age_ticks - (max_age_ticks * 0.70)) / max(1, (max_age_ticks * 0.30))
    elder_prog = min(2.0, elder_prog)  # Allow over-age organisms to experience deeper decay
    vitality = 1.0 - (0.35 * (elder_prog ** 1.3))
    return max(0.30, vitality)


def calculate_gompertz_senescence_hazard(
    age_ticks: int,
    max_age_ticks: int,
    health_ratio: float = 1.0,
    constitution: float = 1.0,
) -> float:
    """
    Gompertz-Makeham mortality hazard model:
    Calculates per-tick probability of natural age-related cellular failure.
    Youth (< 75% lifespan): Near-zero hazard (< 0.00001).
    Senior (100% lifespan): Modest baseline hazard per tick (~0.001 - 0.003).
    Super-elder (> 120% lifespan): Rapidly escalating natural mortality risk.
    """
    if max_age_ticks <= 0:
        return 0.001
    
    relative_age = age_ticks / max_age_ticks
    if relative_age < 0.70:
        # Minimal youth mortality hazard
        return 0.0
    
    # Gompertz exponential parameterization
    alpha = 0.0001
    beta = 4.2
    safe_health = max(0.1, health_ratio)
    safe_const = max(0.5, constitution)
    
    hazard = alpha * math.exp(beta * (relative_age - 0.70)) / (safe_health * safe_const)
    return min(0.08, hazard)


def calculate_combat_power(
    mass_kg: float,
    base_strength: float,
    stamina_ratio: float = 1.0,
    health_ratio: float = 1.0,
    vitality: float = 1.0,
    soft_cap_limit: float = 120.0,
) -> float:
    """
    Calculates dynamic physical attack/defense striking force:
    Power = (Mass^0.65) * Strength * StaminaFactor * HealthFactor * Vitality
    Soft-capped smoothly to prevent infinite damage inflation.
    """
    safe_mass = max(0.01, mass_kg)
    stamina_mult = 0.4 + 0.6 * max(0.0, min(1.0, stamina_ratio))
    health_mult = 0.3 + 0.7 * max(0.0, min(1.0, health_ratio))
    raw_power = (safe_mass ** 0.65) * base_strength * 0.25 * stamina_mult * health_mult * vitality
    return soft_cap(raw_power, soft_limit=soft_cap_limit, hardness=1.0)
