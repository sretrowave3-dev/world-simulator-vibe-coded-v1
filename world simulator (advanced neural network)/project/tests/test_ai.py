"""
tests/test_ai.py

Unit tests for AI, Neural Brain, Genetics, Memory, Pheromones, Behavior Trees, and GOAP Planner.
"""

import unittest
from project.ai.genome import Genome
from project.ai.brain import Brain, ActivationType
from project.ai.memory import OrganismMemory, MemoryType
from project.ai.pheromone import PheromoneGrid, PheromoneType
from project.ai.needs import OrganismNeeds, NeedType
from project.ai.goals import GoalSolver, GoalType
from project.ai.blackboard import Blackboard
from project.ai.behavior_tree import Selector, Sequence, ConditionNode, ActionNode, NodeStatus
from project.ai.planner import GOAPAction, GOAPPlanner


class TestAISubsystems(unittest.TestCase):

    def test_genome_crossover_and_mutation(self):
        parent_a = Genome.create_random(length=16)
        parent_b = Genome.create_random(length=16)

        child = Genome.crossover_uniform(parent_a, parent_b)
        self.assertEqual(len(child.genes), 16)

        mutated = child.mutate(mutation_rate=0.5, mutation_magnitude=0.1)
        self.assertEqual(len(mutated.genes), 16)

        phenotype = mutated.express_phenotype()
        self.assertTrue(0.5 <= phenotype.size_modifier <= 2.0)
        self.assertTrue(0.0 <= phenotype.aggression <= 1.0)

    def test_brain_forward_pass_and_hebbian_learning(self):
        brain = Brain(
            input_size=8,
            hidden_sizes=(12, 6),
            output_size=4,
            activation=ActivationType.TANH,
            working_memory_size=2,
        )

        inputs = [0.5, -0.2, 0.8, 0.0, -0.5, 0.3, 0.1, -0.9]
        outputs = brain.forward(inputs)
        self.assertEqual(len(outputs), 4)

        # Test Hebbian learning update
        old_w0 = list(brain.weights[0][0])
        brain.apply_hebbian_learning(reward=1.0)
        new_w0 = list(brain.weights[0][0])
        # Weights should have shifted slightly
        self.assertNotEqual(old_w0, new_w0)

    def test_organism_memory_retention(self):
        memory = OrganismMemory()
        memory.remember(MemoryType.FOOD_SOURCE, x=15.0, y=25.0, importance=0.8, current_tick=100)

        # Recall immediately
        recalled = memory.recall_nearest(current_x=10.0, current_y=20.0, memory_type=MemoryType.FOOD_SOURCE, current_tick=105)
        self.assertIsNotNone(recalled)
        self.assertAlmostEqual(recalled[0], 15.0)
        self.assertAlmostEqual(recalled[1], 25.0)

    def test_pheromone_diffusion_and_gradients(self):
        grid = PheromoneGrid(width=32, height=32, cell_size=4.0)
        # Deposit scent at center (x=64, y=64)
        grid.deposit(64.0, 64.0, PheromoneType.FOOD_TRAIL, intensity=50.0)
        val = grid.sample(64.0, 64.0, PheromoneType.FOOD_TRAIL)
        self.assertAlmostEqual(val, 50.0)

        # Tick diffusion
        grid.tick(dt=0.1)

        # Sample gradient near center
        dx, dy = grid.sample_gradient(60.0, 64.0, PheromoneType.FOOD_TRAIL)
        # Scent is higher to the right, so dx should be positive
        self.assertGreater(dx, 0.0)

    def test_needs_and_goal_solver(self):
        needs = OrganismNeeds()
        needs.update_from_vitals(
            energy=20.0, max_energy=100.0,
            hydration=10.0, max_hydration=100.0,
            age_ticks=500, maturity_ticks=1000,
        )

        goal = GoalSolver.evaluate_goal(needs, is_carnivore=False)
        # Thirst should be prioritized since hydration is 10%
        self.assertEqual(goal.goal_type, GoalType.DRINK_WATER)

    def test_behavior_tree_execution(self):
        blackboard = Blackboard()
        blackboard.set("has_target", True)

        def check_target(agent, bb):
            return bb.get("has_target", False)

        def attack_target(agent, bb):
            return NodeStatus.SUCCESS

        tree = Sequence([
            ConditionNode(check_target),
            ActionNode(attack_target),
        ])

        status = tree.tick(agent=None, blackboard=blackboard)
        self.assertEqual(status, NodeStatus.SUCCESS)

    def test_goap_planner(self):
        actions = [
            GOAPAction(
                name="GatherWood",
                cost=2.0,
                preconditions={"has_wood": False},
                effects={"has_wood": True},
            ),
            GOAPAction(
                name="CraftAxe",
                cost=1.0,
                preconditions={"has_wood": True, "has_axe": False},
                effects={"has_axe": True},
            ),
            GOAPAction(
                name="BuildShelter",
                cost=5.0,
                preconditions={"has_axe": True, "has_shelter": False},
                effects={"has_shelter": True},
            ),
        ]

        initial_state = {"has_wood": False, "has_axe": False, "has_shelter": False}
        goal_state = {"has_shelter": True}

        plan = GOAPPlanner.plan(initial_state, goal_state, actions)
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan), 3)
        self.assertEqual([a.name for a in plan], ["GatherWood", "CraftAxe", "BuildShelter"])


if __name__ == "__main__":
    unittest.main()
