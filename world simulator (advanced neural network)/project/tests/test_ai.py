"""
tests/test_ai.py

Unit tests for AI, Neural Brain, PyTorch GPU Acceleration, Self-Learning,
Genetics, Cognitive Memory, Pheromones, Behavior Trees, and GOAP Planner.
"""

import unittest
from project.ai.genome import Genome
from project.ai.brain import Brain, ActivationType, TORCH_AVAILABLE
from project.ai.memory import OrganismMemory, MemoryType, HumanCognitiveMemory
from project.ai.pheromone import PheromoneGrid, PheromoneType
from project.ai.needs import OrganismNeeds, NeedType
from project.ai.goals import GoalSolver, GoalType
from project.ai.blackboard import Blackboard
from project.ai.behavior_tree import Selector, Sequence, ConditionNode, ActionNode, NodeStatus
from project.ai.planner import GOAPAction, GOAPPlanner
from project.core.gpu_manager import gpu_mgr
from project.systems.learning_system import LearningSystem
from project.entities.human import Human
from project.entities.bacteria import Bacteria
from project.core.scheduler import UpdateContext


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

    def test_brain_pytorch_and_gpu_acceleration(self):
        """Verifies PyTorch neural brain backend, device selection, and weight sync."""
        brain = Brain(
            input_size=16,
            hidden_sizes=(24, 12),
            output_size=8,
            activation=ActivationType.RELU,
            working_memory_size=4,
        )
        self.assertTrue(brain.use_torch)
        self.assertIsNotNone(brain.torch_module)
        self.assertIsNotNone(brain.device)

        inputs = [0.1 * i for i in range(16)]
        outputs = brain.forward(inputs)
        self.assertEqual(len(outputs), 8)
        self.assertEqual(len(brain.working_memory), 4)

        # Verify export / load weights maintains bidirectional sync
        vec = brain.export_weights_to_vector()
        self.assertGreater(len(vec), 0)
        brain.load_weights_from_vector(vec)

        # Verify synaptic capacity expansion
        old_conns = brain.total_synaptic_connections
        new_conns = brain.expand_synaptic_capacity(new_hidden_sizes=(32, 16), new_working_memory=6)
        self.assertGreater(new_conns, old_conns)

    def test_brain_self_learning_optimization(self):
        """Tests that PyTorch gradient descent backpropagates and optimizes neural weights."""
        brain = Brain(input_size=8, hidden_sizes=(16, 8), output_size=4)

        # Record multiple experiences with distinct rewards
        for i in range(20):
            s = [0.1 * (i % 8)] * 8
            a = [0.5, -0.2, 0.1, 0.0]
            r = 1.0 if i % 2 == 0 else -0.5
            s_next = [0.1 * ((i + 1) % 8)] * 8
            brain.record_transition(s, a, r, s_next, done=False)

        self.assertEqual(len(brain.experience_buffer), 20)
        loss = brain.self_learn_step(batch_size=8)
        self.assertGreater(loss, 0.0)
        self.assertEqual(brain.total_learning_steps, 1)

    def test_human_cognitive_memory_gpu_and_self_learning(self):
        """Verifies that HumanCognitiveMemory utilizes PyTorch tensors, autoencoders, and attention on GPU."""
        mem = HumanCognitiveMemory()
        self.assertGreater(mem.memory_size_mb, 50.0)
        self.assertIsNotNone(mem.device)

        # Record experiences into the 50MB tensor
        for i in range(15):
            sensory = [0.5] * 20
            action = [0.1] * 8
            emotion = [0.8, 0.7, 0.1, 0.9, 0.9]
            mem.record_experience(sensory, action, reward=1.0, emotion_vector=emotion)

        self.assertEqual(mem.experience_count, 15)

        # Run online self-learning step
        loss = mem.self_learn_step(batch_size=8)
        self.assertGreater(loss, 0.0)

        # Run intrinsic curiosity
        curiosity = mem.compute_intrinsic_curiosity([0.5] * 20)
        self.assertIsInstance(curiosity, float)
        self.assertGreaterEqual(curiosity, 0.0)

        # Run associative attention query
        indices, expected_val = mem.associative_attention_recall([0.5] * 20, top_k=3)
        self.assertIsInstance(indices, list)
        self.assertIsInstance(expected_val, float)

    def test_learning_system_self_learning_loop(self):
        """Verifies global LearningSystem online self-learning optimization across entities."""
        human = Human(entity_id="test_human", species_id="human", pos_x=100.0, pos_y=100.0)
        bac = Bacteria(entity_id="test_bac", species_id="bac", pos_x=120.0, pos_y=120.0)
        entities = [human, bac]

        learning_sys = LearningSystem(entities)
        self.assertTrue(learning_sys.self_learning_enabled)

        # Forward pass to seed brain states
        human.brain.forward([0.5] * 16)
        bac.brain.forward([0.3] * 16)

        # Mock update context
        class MockContext:
            tick = 4
            delta_time = 0.1

        # Simulate update tick
        learning_sys.update(MockContext())

        # Dedicated training run across all entities
        res = learning_sys.train_all_entities(iterations=5)
        self.assertEqual(res["trained_entities"], 2)
        self.assertGreater(res["total_gradient_steps"], 0)

        stats = learning_sys.get_self_learning_stats()
        self.assertTrue(stats["self_learning_enabled"])
        self.assertIn("device", stats)
        self.assertEqual(stats["active_learners"], 2)

    def test_gpu_manager_torch_integration(self):
        """Verifies that GPUManager properly bridges PyTorch device selection and telemetry."""
        dev = gpu_mgr.get_torch_device()
        self.assertIsNotNone(dev)
        info = gpu_mgr.get_torch_gpu_info()
        self.assertTrue(info["torch_available"])
        self.assertIn("device", info)
        self.assertIn("device_name", info)

    def test_organism_memory_retention(self):
        memory = OrganismMemory()
        memory.remember(MemoryType.FOOD_SOURCE, x=15.0, y=25.0, importance=0.8, current_tick=100)

        recalled = memory.recall_nearest(current_x=10.0, current_y=20.0, memory_type=MemoryType.FOOD_SOURCE, current_tick=105)
        self.assertIsNotNone(recalled)
        self.assertAlmostEqual(recalled[0], 15.0)
        self.assertAlmostEqual(recalled[1], 25.0)

    def test_pheromone_diffusion_and_gradients(self):
        grid = PheromoneGrid(width=32, height=32, cell_size=4.0)
        grid.deposit(64.0, 64.0, PheromoneType.FOOD_TRAIL, intensity=50.0)
        val = grid.sample(64.0, 64.0, PheromoneType.FOOD_TRAIL)
        self.assertAlmostEqual(val, 50.0)

        grid.tick(dt=0.1)

        dx, dy = grid.sample_gradient(60.0, 64.0, PheromoneType.FOOD_TRAIL)
        self.assertGreater(dx, 0.0)

    def test_needs_and_goal_solver(self):
        needs = OrganismNeeds()
        needs.update_from_vitals(
            energy=20.0, max_energy=100.0,
            hydration=10.0, max_hydration=100.0,
            age_ticks=500, maturity_ticks=1000,
        )

        goal = GoalSolver.evaluate_goal(needs, is_carnivore=False)
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
