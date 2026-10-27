"""
project/systems/learning_system.py

PyTorch-Accelerated Deep Self-Learning System & Synaptic Plasticity Engine.
Updates neural network weights via GPU gradient backpropagation, Actor-Critic TD self-learning,
intrinsic curiosity prediction errors, and Hebbian neuromodulation across all ALife organisms.
"""

from __future__ import annotations

import random
from typing import Set, List, Optional, Dict, Any
from project.core.scheduler import SchedulerPhase, ExecutionPriority, UpdateContext
from project.entities.entity import Entity, EntityType
from project.entities.human import Human
from project.ai.memory import HumanCognitiveMemory
from project.ai.brain import Brain, TORCH_AVAILABLE

try:
    from project.core.gpu_manager import gpu_mgr
except ImportError:
    gpu_mgr = None


class LearningSystem:
    """Manages synaptic weight changes, neuromodulation, and PyTorch deep self-learning memory training."""

    def __init__(self, entities_list: List[Entity]) -> None:
        self._entities_list = entities_list
        self.self_learning_enabled: bool = True
        self.total_self_learning_steps: int = 0
        self.latest_loss: float = 0.0
        self.loss_history: List[float] = []
        self.active_learners_count: int = 0

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

    def toggle_self_learning(self, enabled: Optional[bool] = None) -> bool:
        """Toggles or sets the global online PyTorch self-learning engine state."""
        if enabled is not None:
            self.self_learning_enabled = enabled
        else:
            self.self_learning_enabled = not self.self_learning_enabled
        return self.self_learning_enabled

    def get_self_learning_stats(self) -> Dict[str, Any]:
        """Returns deep telemetry metrics regarding PyTorch GPU utilization and self-learning convergence."""
        gpu_info = gpu_mgr.get_torch_gpu_info() if gpu_mgr else {"device": "cpu", "device_name": "CPU"}
        avg_loss = sum(self.loss_history[-50:]) / max(1, len(self.loss_history[-50:])) if self.loss_history else 0.0
        return {
            "self_learning_enabled": self.self_learning_enabled,
            "torch_available": TORCH_AVAILABLE,
            "device": gpu_info.get("device", "cpu"),
            "device_name": gpu_info.get("device_name", "CPU"),
            "cuda_available": gpu_info.get("cuda_available", False),
            "vram_allocated_mb": gpu_info.get("vram_allocated_mb", 0.0),
            "vram_reserved_mb": gpu_info.get("vram_reserved_mb", 0.0),
            "total_self_learning_steps": self.total_self_learning_steps,
            "latest_loss": round(self.latest_loss, 5),
            "avg_recent_loss": round(avg_loss, 5),
            "active_learners": self.active_learners_count,
        }

    def train_all_entities(self, iterations: int = 25) -> Dict[str, Any]:
        """
        Executes dedicated PyTorch GPU backpropagation self-learning cycles across
        all living organisms equipped with neural brains in the world.
        """
        trained_entities = 0
        total_loss_accum = 0.0
        loss_steps = 0

        for entity in self._entities_list:
            if not entity.is_alive or not entity.brain:
                continue

            # Boost brain learning rate during dedicated training cycle
            old_lr = entity.brain.learning_rate
            entity.brain.learning_rate = 0.03

            # 1. PyTorch Neural Brain Actor-Critic Backpropagation Steps
            for _ in range(iterations):
                step_loss = entity.brain.self_learn_step(batch_size=16)
                if step_loss > 0.0:
                    total_loss_accum += step_loss
                    loss_steps += 1
                entity.brain.apply_hebbian_learning(reward=1.0)

            # 2. PyTorch Human Autoencoder & Value Memory Training
            if entity.entity_type == EntityType.HUMAN and hasattr(entity, "memory") and isinstance(entity.memory, HumanCognitiveMemory):
                for _ in range(iterations):
                    mem_loss = entity.memory.self_learn_step(batch_size=32)
                    if mem_loss > 0.0:
                        total_loss_accum += mem_loss
                        loss_steps += 1

                if hasattr(entity, "intelligence_quotient"):
                    entity.intelligence_quotient = min(250.0, entity.intelligence_quotient + (0.05 * iterations))

            entity.brain.learning_rate = old_lr
            entity.custom_data["dopamine"] = 1.0
            entity.custom_data["confidence"] = 1.0
            entity.custom_data["last_trained_cycles"] = iterations
            trained_entities += 1

        avg_loss = (total_loss_accum / max(1, loss_steps)) if loss_steps > 0 else 0.0
        if avg_loss > 0:
            self.latest_loss = avg_loss
            self.loss_history.append(avg_loss)
            self.total_self_learning_steps += loss_steps

        return {
            "trained_entities": trained_entities,
            "cycles_per_entity": iterations,
            "average_loss": round(avg_loss, 5),
            "total_gradient_steps": loss_steps,
        }

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
                        if loss > 0.0:
                            self.latest_loss = loss
                            self.loss_history.append(loss)
                            self.total_self_learning_steps += 1

                        # PyTorch Actor-Critic step on Brain
                        brain_loss = entity.brain.self_learn_step(batch_size=16)
                        if brain_loss > 0.0:
                            self.latest_loss = brain_loss
                            self.loss_history.append(brain_loss)
                            self.total_self_learning_steps += 1

                        # Hebbian policy training
                        batch_exp, batch_rew = entity.memory.sample_batch(batch_size=32)
                        if len(batch_rew) > 0:
                            avg_rew = float(batch_rew.mean().item() if hasattr(batch_rew, "mean") else 0.0)
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
        active_learners = 0

        for entity in self._entities_list:
            if not entity.is_alive or not entity.brain:
                continue

            active_learners += 1

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
            # 3. PyTorch Experience Replay & Self-Learning Across All Organisms
            # -------------------------------------------------------------
            norm_e = min(1.0, entity.energy / max(1.0, getattr(entity, "max_energy", 100.0)))
            norm_h = min(1.0, entity.hydration / max(1.0, getattr(entity, "max_hydration", 100.0)))
            norm_hp = min(1.0, entity.health / max(1.0, getattr(entity, "max_health", 100.0)))

            current_sensory_state = [
                norm_e, norm_h, norm_hp,
                0.0, 0.0, 0.0, 0.0,
                dopamine, serotonin, stress, fear, curiosity, confidence,
                0.0,
                entity.pos_x / 4096.0,
                entity.pos_y / 4096.0,
            ]

            # Record transition in Brain's circular experience buffer for self-learning
            if entity.brain.last_state is not None and entity.brain.last_action is not None:
                entity.brain.record_transition(
                    state=entity.brain.last_state,
                    action=entity.brain.last_action,
                    reward=reward,
                    next_state=current_sensory_state,
                    done=not entity.is_alive,
                )

            # Periodic PyTorch GPU Self-Learning Optimization Step
            if self.self_learning_enabled and context.tick % 4 == 0:
                b_loss = entity.brain.self_learn_step(batch_size=16)
                if b_loss > 0.0:
                    self.latest_loss = b_loss
                    self.loss_history.append(b_loss)
                    if len(self.loss_history) > 200:
                        self.loss_history.pop(0)
                    self.total_self_learning_steps += 1

            # -------------------------------------------------------------
            # 4. Human-Specific 50+ MB Memory Autoencoder Self-Learning
            # -------------------------------------------------------------
            if entity.entity_type == EntityType.HUMAN:
                entity.brain.learning_rate = 0.04

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

                    # Periodic PyTorch Autoencoder Backprop
                    if self.self_learning_enabled and context.tick % 4 == 0:
                        h_loss = entity.memory.self_learn_step(batch_size=32)
                        if h_loss > 0.0:
                            self.latest_loss = h_loss
                            self.loss_history.append(h_loss)
                            if len(self.loss_history) > 200:
                                self.loss_history.pop(0)
                            self.total_self_learning_steps += 1

            # -------------------------------------------------------------
            # 5. Immediate Hebbian Synaptic Plasticity
            # -------------------------------------------------------------
            learning_modulator = reward * (1.0 + dopamine) * max(0.1, confidence)
            entity.brain.apply_hebbian_learning(reward=max(-1.0, min(1.0, learning_modulator)))

            entity.custom_data["prev_energy"] = entity.energy
            entity.custom_data["prev_hydration"] = entity.hydration
            entity.custom_data["last_learning_reward"] = reward

        self.active_learners_count = active_learners

    def late_update(self, context: UpdateContext) -> None:
        pass

    def shutdown(self) -> None:
        pass
