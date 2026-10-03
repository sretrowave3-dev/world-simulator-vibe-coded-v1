"""
project/systems/learning_system.py

Learning System updating neural network synaptic weights via Hebbian reinforcement,
dopamine modulation, and PyTorch-accelerated self-learning optimization over the 50+ MB human cognitive memory buffer.
"""

from __future__ import annotations

import random
from typing import Set, List, Optional
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human
from project.ai.memory import HumanCognitiveMemory


class LearningSystem:
    """Manages synaptic weight changes, neuromodulation, and PyTorch deep self-learning memory training."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list

    @property
    def name(self) -> str:
        return "LearningSystem"

    @property
    def phase(self) -> SchedulerPhase:
        return SchedulerPhase.BIOLOGY

    @property
    def priority(self) -> int:
        return ExecutionPriority.LEARNING

    @property
    def dependencies(self) -> Set[str]:
        return {"DigestionSystem"}

    @property
    def is_critical(self) -> bool:
        return False

    def initialize(self, context: UpdateContext) -> None:
        pass

    def train_humans(self, iterations: int = 50) -> int:
        """
        Runs dedicated high-intensity PyTorch neural memory backpropagation training
        and synaptic reinforcement cycles across all sentient humans.
        Boosts IQ, minimizes representation loss, and strengthens learned weights.
        """
        trained_count = 0
        for entity in self._entities_list:
            if not entity.is_alive or entity.entity_type != EntityType.HUMAN:
                continue

            if entity.brain is not None:
                entity.brain.learning_rate = 0.05

                # 1. PyTorch Self-Learning Autoencoder Backprop Steps
                if hasattr(entity, "memory") and isinstance(entity.memory, HumanCognitiveMemory):
                    for _ in range(iterations):
                        # PyTorch gradient descent on autoencoder & value head
                        loss = entity.memory.self_learn_step(batch_size=32)
                        
                        # Hebbian policy training
                        batch_exp, batch_rew = entity.memory.sample_batch(batch_size=32)
                        if len(batch_rew) > 0:
                            avg_rew = float(batch_rew.mean())
                            entity.brain.apply_hebbian_learning(reward=max(-1.0, min(1.0, avg_rew * 1.5)))
                else:
                    for _ in range(iterations):
                        entity.brain.apply_hebbian_learning(reward=1.0)

                # 2. Cognitive Growth & IQ Advancement
                if hasattr(entity, "intelligence_quotient"):
                    entity.intelligence_quotient = min(250.0, entity.intelligence_quotient + (0.05 * iterations))

                entity.custom_data["dopamine"] = 1.0
                entity.custom_data["confidence"] = 1.0
                entity.custom_data["last_trained_cycles"] = iterations
                trained_count += 1

        return trained_count

    def update(self, context: UpdateContext) -> None:
        for entity in self._entities_list:
            if not entity.is_alive or not entity.brain:
                continue

            # -------------------------------------------------------------
            # 1. Delta-Energy & Survival Reinforcement Signal
            # -------------------------------------------------------------
            prev_energy = entity.custom_data.get("prev_energy", entity.energy)
            prev_hydra = entity.custom_data.get("prev_hydration", entity.hydration)
            
            delta_e = entity.energy - prev_energy
            delta_h = entity.hydration - prev_hydra
            
            reward = 0.0
            if delta_e > 0:
                reward += 0.8
            elif delta_e < 0:
                reward -= 0.03
                
            if delta_h > 0:
                reward += 0.4
            
            reward = max(-1.0, min(1.0, reward))

            # -------------------------------------------------------------
            # 2. PyTorch Intrinsic Curiosity & Neuromodulators
            # -------------------------------------------------------------
            predicted_reward = entity.custom_data.get("predicted_reward", 0.0)
            prediction_error = reward - predicted_reward
            entity.custom_data["predicted_reward"] = reward * 0.5 + predicted_reward * 0.5

            curiosity_bonus = 0.0
            if entity.entity_type == EntityType.HUMAN and hasattr(entity, "memory") and isinstance(entity.memory, HumanCognitiveMemory):
                sensory_vec = [
                    entity.energy / 500.0,
                    entity.hydration / 300.0,
                    entity.health / 100.0,
                    entity.pos_x / 4096.0,
                    entity.pos_y / 4096.0,
                    getattr(entity, "speed", 0.0) / 10.0,
                ]
                # PyTorch Intrinsic Curiosity Prediction Error
                curiosity_bonus = entity.memory.compute_intrinsic_curiosity(sensory_vec)

            dopamine = max(0.0, entity.custom_data.get("dopamine", 0.0) * 0.9 + reward)
            serotonin = max(0.0, entity.custom_data.get("serotonin", 0.0) * 0.9 + (entity.energy / 100.0) * 0.1)
            stress = min(1.0, max(0.0, entity.custom_data.get("stress", 0.0) * 0.95 + (1.0 - entity.energy / 100.0) * 0.05))
            fear = max(0.0, entity.custom_data.get("fear", 0.0) * 0.9)
            curiosity = min(1.0, entity.custom_data.get("curiosity", 0.0) * 0.95 + abs(prediction_error) * 0.05 + curiosity_bonus * 0.1)
            confidence = min(1.0, entity.custom_data.get("confidence", 0.0) * 0.95 + (1.0 - abs(prediction_error)) * 0.05)
            
            entity.custom_data["dopamine"] = dopamine
            entity.custom_data["serotonin"] = serotonin
            entity.custom_data["stress"] = stress
            entity.custom_data["fear"] = fear
            entity.custom_data["curiosity"] = curiosity
            entity.custom_data["confidence"] = confidence

            # -------------------------------------------------------------
            # 3. Dedicated Human 50+ MB Experience Replay & PyTorch Self-Learning
            # -------------------------------------------------------------
            if entity.entity_type == EntityType.HUMAN:
                entity.brain.learning_rate = 0.04

                # Store transition in 50 MB PyTorch circular tensor buffer
                if hasattr(entity, "memory") and isinstance(entity.memory, HumanCognitiveMemory):
                    sensory_inputs = [
                        entity.energy / 500.0,
                        entity.hydration / 300.0,
                        entity.health / 100.0,
                        entity.pos_x / 4096.0,
                        entity.pos_y / 4096.0,
                    ]
                    action_outputs = list(entity.brain.working_memory) if entity.brain else []
                    emotion_vitals = [dopamine, serotonin, stress, curiosity, confidence]
                    
                    entity.memory.record_experience(
                        sensory_vector=sensory_inputs,
                        action_vector=action_outputs,
                        reward=reward,
                        emotion_vector=emotion_vitals,
                    )
                    
                    # Periodic PyTorch Self-Learning Gradient Step
                    if context.tick % 4 == 0:
                        entity.memory.self_learn_step(batch_size=32)

            # Apply immediate Hebbian synaptic learning
            learning_modulator = reward * (1.0 + dopamine) * max(0.1, confidence)
            entity.brain.apply_hebbian_learning(reward=max(-1.0, min(1.0, learning_modulator)))
            
            entity.custom_data["prev_energy"] = entity.energy
            entity.custom_data["prev_hydration"] = entity.hydration
            entity.custom_data["last_learning_reward"] = reward

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
