"""
project/tests/test_physiology.py

Unit tests for Biological Allometry, Soft-Capped Traits, Kleiber Metabolism,
Non-Linear Hunger/Thirst Curves, and Gompertz-Makeham Stochastic Senescence.
"""

import math
import unittest
from project.core.biology import (
    soft_cap,
    calculate_basal_metabolism,
    calculate_locomotion_cost,
    calculate_hunger_urgency,
    calculate_thirst_urgency,
    calculate_vitality_multiplier,
    calculate_gompertz_senescence_hazard,
    calculate_combat_power,
)
from project.entities.entity import Entity, EntityType
from project.entities.herbivore import Herbivore
from project.entities.predator import Predator
from project.entities.human import Human
from project.entities.avian import Avian
from project.entities.reptile import Reptile


class TestPhysiologyAndAllometry(unittest.TestCase):

    def test_soft_cap_asymptotic_compression(self) -> None:
        """Verifies soft_cap behaves linearly at low values and compresses asymptotically above limit."""
        soft_limit = 10.0
        # Below 50% limit, nearly exact linear match
        self.assertAlmostEqual(soft_cap(4.0, soft_limit), 4.0, delta=0.1)

        # At limit (10.0), output is smoothly compressed below limit
        val_at_limit = soft_cap(10.0, soft_limit)
        self.assertLess(val_at_limit, 10.0)
        self.assertGreater(val_at_limit, 7.0)

        # Extreme input (100.0) is soft-capped, not exploding
        val_extreme = soft_cap(100.0, soft_limit, hardness=1.0)
        self.assertLess(val_extreme, 11.0)

    def test_kleiber_metabolic_scaling(self) -> None:
        """Verifies BMR follows Kleiber's Law (M^0.75) and thermal adjustments."""
        small_mass_bmr = calculate_basal_metabolism(mass_kg=1.0, is_endotherm=True, ambient_temp_c=37.0)
        large_mass_bmr = calculate_basal_metabolism(mass_kg=16.0, is_endotherm=True, ambient_temp_c=37.0)

        # 16^0.75 = 8.0
        ratio = large_mass_bmr / small_mass_bmr
        self.assertAlmostEqual(ratio, 8.0, delta=0.05)

        # Endotherm cold response burns more energy
        cold_bmr = calculate_basal_metabolism(mass_kg=10.0, is_endotherm=True, ambient_temp_c=5.0, optimal_temp_c=37.0)
        warm_bmr = calculate_basal_metabolism(mass_kg=10.0, is_endotherm=True, ambient_temp_c=37.0, optimal_temp_c=37.0)
        self.assertGreater(cold_bmr, warm_bmr)

        # Ectotherm cold response reduces metabolic rate (Q10 rule)
        ecto_cold = calculate_basal_metabolism(mass_kg=10.0, is_endotherm=False, ambient_temp_c=12.0)
        ecto_warm = calculate_basal_metabolism(mass_kg=10.0, is_endotherm=False, ambient_temp_c=32.0)
        self.assertLess(ecto_cold, ecto_warm)

    def test_locomotion_cost(self) -> None:
        """Verifies kinetic locomotion cost scales with mass and non-linear speed."""
        stationary_cost = calculate_locomotion_cost(mass_kg=50.0, speed=0.0)
        self.assertEqual(stationary_cost, 0.0)

        walk_cost = calculate_locomotion_cost(mass_kg=50.0, speed=3.0)
        sprint_cost = calculate_locomotion_cost(mass_kg=50.0, speed=9.0)
        self.assertGreater(sprint_cost, walk_cost * 4.0)

    def test_hunger_and_thirst_curves(self) -> None:
        """Verifies non-linear hunger pangs and thirst escalation."""
        # Full energy (100%) -> negligible hunger
        self.assertLess(calculate_hunger_urgency(100.0, 100.0), 0.05)

        # Moderate energy (50%) -> mild hunger
        self.assertGreater(calculate_hunger_urgency(50.0, 100.0), 0.15)

        # Low energy (15%) -> acute desperation
        self.assertGreater(calculate_hunger_urgency(15.0, 100.0), 0.85)

        # Depleted hydration -> critical thirst
        self.assertGreater(calculate_thirst_urgency(5.0, 100.0), 0.90)

    def test_vitality_and_senescence_curves(self) -> None:
        """Verifies developmental vitality and Gompertz mortality hazard."""
        # Juvenile has lower initial vitality
        juv_vitality = calculate_vitality_multiplier(age_ticks=10, maturity_ticks=100, max_age_ticks=1000)
        adult_vitality = calculate_vitality_multiplier(age_ticks=200, maturity_ticks=100, max_age_ticks=1000)
        elder_vitality = calculate_vitality_multiplier(age_ticks=950, maturity_ticks=100, max_age_ticks=1000)

        self.assertLess(juv_vitality, adult_vitality)
        self.assertEqual(adult_vitality, 1.0)
        self.assertLess(elder_vitality, adult_vitality)

        # Youth mortality hazard is 0
        youth_hazard = calculate_gompertz_senescence_hazard(age_ticks=200, max_age_ticks=1000)
        self.assertEqual(youth_hazard, 0.0)

        # Old age mortality hazard is non-zero and escalates smoothly
        senior_hazard = calculate_gompertz_senescence_hazard(age_ticks=900, max_age_ticks=1000)
        extreme_hazard = calculate_gompertz_senescence_hazard(age_ticks=1200, max_age_ticks=1000)
        self.assertGreater(senior_hazard, 0.0)
        self.assertGreater(extreme_hazard, senior_hazard)

    def test_combat_power_soft_capping(self) -> None:
        """Verifies attack power scales with mass and is softly capped."""
        small_power = calculate_combat_power(mass_kg=5.0, base_strength=10.0)
        giant_power = calculate_combat_power(mass_kg=500.0, base_strength=100.0, soft_cap_limit=100.0)

        self.assertGreater(giant_power, small_power)
        self.assertLessEqual(giant_power, 110.0)  # Soft capped near limit

    def test_individual_phenotypic_variance(self) -> None:
        """Verifies distinct organism instances have natural phenotypic diversity without being identical clones."""
        h1 = Herbivore(entity_id="herbivore_alpha", species_id="grazer")
        h2 = Herbivore(entity_id="herbivore_beta", species_id="grazer")

        # Two individuals must have slightly different mass, constitution, or stamina
        self.assertNotEqual(h1.mass_kg, h2.mass_kg)
        self.assertNotEqual(h1.constitution, h2.constitution)
        self.assertNotEqual(h1.max_health, h2.max_health)

    def test_species_specialized_attributes(self) -> None:
        """Verifies distinct species subclasses instantiate with their ecological physiological baselines."""
        pred = Predator(entity_id="pred_1", species_id="feline")
        human = Human(entity_id="human_1", species_id="sap")
        avian = Avian(entity_id="bird_1", species_id="raptor")
        reptile = Reptile(entity_id="lizard_1", species_id="viper")

        # Avian has high speed cap and light mass
        self.assertLess(avian.mass_kg, 10.0)
        self.assertGreater(avian.base_speed, 5.0)

        # Predator is heavy, strong, and endothermic
        self.assertGreater(pred.mass_kg, 80.0)
        self.assertTrue(pred.is_endotherm)
        self.assertGreater(pred.strength, 30.0)

        # Reptile is ectothermic with cold body temperature baseline
        self.assertFalse(reptile.is_endotherm)
        self.assertLess(reptile.body_temperature_c, 30.0)

        # Human has high omnivorous energy and memory
        self.assertGreater(human.max_energy, 400.0)
        self.assertIsNotNone(human.memory)


if __name__ == "__main__":
    unittest.main()
