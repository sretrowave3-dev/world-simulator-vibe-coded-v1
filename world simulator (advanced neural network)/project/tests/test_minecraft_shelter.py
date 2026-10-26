"""
tests/test_minecraft_shelter.py

Tests Minecraft-inspired game logic:
- Tiered shelters (Dugouts -> Wooden Cabins -> Cobblestone Houses)
- Human shelter need evaluation and learning from night exposure
- Occupancy and predator immunity inside shelters
- Crafting and construction progression
"""

import unittest
from project.entities.human import Human
from project.entities.predator import Predator
from project.civilization.settlement import world_settlement_mgr, WorldStructure
from project.civilization.technology import world_tech_tree
from project.systems.combat_system import CombatSystem
from project.core.scheduler import UpdateContext


class TestMinecraftShelterLogic(unittest.TestCase):

    def setUp(self) -> None:
        world_settlement_mgr.structures.clear()
        world_settlement_mgr._next_id = 1

    def test_shelter_tiers_and_occupancy(self) -> None:
        # Spawn a Wooden Cabin
        cabin = world_settlement_mgr.spawn_structure("wooden_cabin", pos_x=500.0, pos_y=500.0)
        self.assertEqual(cabin.tier, 2)
        self.assertEqual(cabin.capacity, 6)
        self.assertTrue(cabin.is_predator_proof)
        self.assertEqual(cabin.light_level, 11)

        # Human enters shelter
        h = Human(entity_id="steve_1", species_id="homo_sapiens", pos_x=500.0, pos_y=500.0)
        entered = h.enter_shelter(cabin)
        self.assertTrue(entered)
        self.assertEqual(h.in_shelter_id, cabin.structure_id)
        self.assertIn("steve_1", cabin.occupants)
        self.assertEqual(len(cabin.occupants), 1)

        # Human exits shelter
        h.exit_shelter(cabin)
        self.assertIsNone(h.in_shelter_id)
        self.assertEqual(len(cabin.occupants), 0)

    def test_human_shelter_importance_learning(self) -> None:
        h = Human(entity_id="alex_1", species_id="homo_sapiens", pos_x=1000.0, pos_y=1000.0)
        initial_importance = h.shelter_importance_score
        self.assertEqual(h.desired_shelter_tier, 1)

        # Simulate cold night exposure (daylight = 0.1)
        for tick in range(1, 150):
            h.evaluate_shelter_need(daylight=0.1, threats_nearby=0, sim_tick=tick)

        # Importance should have increased due to night vulnerability
        self.assertGreater(h.shelter_importance_score, initial_importance)

        # Simulate surviving a predator attack
        h.predator_attacks_survived += 1
        h.evaluate_shelter_need(daylight=0.1, threats_nearby=1, sim_tick=150)
        # Desired tier should advance towards cobblestone fortress (tier 3)
        self.assertEqual(h.desired_shelter_tier, 3)

    def test_sheltered_human_predator_immunity(self) -> None:
        # Create a cobblestone fortress house
        house = world_settlement_mgr.spawn_structure("cobblestone_house", pos_x=600.0, pos_y=600.0)
        h = Human(entity_id="miner_1", species_id="homo_sapiens", pos_x=600.0, pos_y=600.0)
        h.enter_shelter(house)

        predator = Predator(entity_id="wolf_1", species_id="panther", pos_x=601.0, pos_y=601.0)
        predator.custom_data["attack_cooldown_ticks"] = 0

        initial_human_hp = h.health
        initial_house_hp = house.health

        entities = [predator, h]
        combat_sys = CombatSystem(entities)

        ctx = UpdateContext(
            tick=10,
            delta_time=0.1,
            simulation_time=1.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
        )
        combat_sys.update(ctx)

        # Human inside shelter took 0 damage (predator proof walls!)
        self.assertEqual(h.health, initial_human_hp)
        # House absorbed the clawing attack
        self.assertLess(house.health, initial_house_hp)

    def test_emergent_shelter_crafting(self) -> None:
        h = Human(entity_id="crafter_1", species_id="homo_sapiens", pos_x=800.0, pos_y=800.0)
        h.intelligence_quotient = 125.0
        h.creativity = 0.75
        h.desired_shelter_tier = 2
        # Give materials for a wooden cabin (wood 5, stone 2)
        h.add_to_inventory("wood", 10.0)
        h.add_to_inventory("stone", 5.0)

        crafted = h.attempt_emergent_crafting(sim_tick=50)
        self.assertIsNotNone(crafted)
        # Check that a structure was erected and human entered it
        self.assertIsNotNone(h.in_shelter_id)
        shelter = world_settlement_mgr.structures[h.in_shelter_id]
        self.assertIn("struct_", str(h.in_shelter_id))
        self.assertIn(h.entity_id, shelter.occupants)

    def test_repeated_infrastructure_construction(self) -> None:
        h = Human(entity_id="builder_1", species_id="homo_sapiens", pos_x=900.0, pos_y=900.0)
        h.intelligence_quotient = 125.0
        h.creativity = 0.75
        h.desired_shelter_tier = 2
        # Human already knows Wooden Plank Cabin
        h.known_technologies.append("Wooden Plank Cabin")
        h.add_to_inventory("wood", 10.0)
        h.add_to_inventory("stone", 5.0)

        # Force emergency shelter need
        crafted = h.attempt_emergent_crafting(sim_tick=60, force_shelter=True)
        self.assertIsNotNone(crafted)
        self.assertEqual(crafted, "Wooden Plank Cabin")
        self.assertIsNotNone(h.in_shelter_id)
        self.assertIn("struct_wooden_cabin", str(h.in_shelter_id))


if __name__ == "__main__":
    unittest.main()
