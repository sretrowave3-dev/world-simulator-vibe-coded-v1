"""
project/ai/memory.py

Multi-Tier Cognitive Memory Engine for ALife Organisms & PyTorch-Accelerated Deep Adaptive Neural Memory.

Features:
- Base OrganismMemory: Sensory buffer, Short-Term Memory, and Long-Term Episodic Memory with Ebbinghaus forgetting.
- HumanCognitiveMemory: PyTorch-powered Differentiable Autoencoder Memory with >= 50 MB Preallocated Tensor Buffers,
  Multi-Head Associative Key-Value Attention Retrieval, Intrinsic Curiosity Loss, and GPU-Accelerated Online Self-Learning Optimizer.
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore
    nn = None  # type: ignore
    optim = None  # type: ignore

try:
    from project.core.gpu_manager import gpu_mgr
except ImportError:
    gpu_mgr = None


class MemoryType(Enum):
    FOOD_SOURCE = auto()
    WATER_SOURCE = auto()
    THREAT_LOCATION = auto()
    MATE_ENCOUNTER = auto()
    SHELTER = auto()
    LANDMARK = auto()
    TOOL_USAGE = auto()
    SOCIAL_INTERACTION = auto()
    DIVINE_REVELATION = auto()


@dataclass
class MemoryRecord:
    memory_type: MemoryType
    pos_x: float
    pos_y: float
    importance: float  # 0.0 to 1.0
    created_tick: int
    last_recalled_tick: int
    recall_count: int = 1
    custom_tag: Optional[str] = None

    def calculate_retention(self, current_tick: int, forgetting_rate: float = 0.0005) -> float:
        """Calculates memory strength retention via Ebbinghaus exponential decay."""
        elapsed = max(0, current_tick - self.last_recalled_tick)
        strength = max(1.0, (self.importance * 10.0 + self.recall_count * 2.0))
        return math.exp(-(elapsed * forgetting_rate) / strength)


class OrganismMemory:
    """Base tiered memory manager for standard organisms."""

    def __init__(
        self,
        short_term_capacity: int = 20,
        long_term_capacity: int = 50,
        forgetting_rate: float = 0.0005,
    ) -> None:
        self.short_term_capacity = short_term_capacity
        self.long_term_capacity = long_term_capacity
        self.forgetting_rate = forgetting_rate

        self.short_term_records: List[MemoryRecord] = []
        self.long_term_records: List[MemoryRecord] = []

    @property
    def memory_size_mb(self) -> float:
        """Estimates RAM allocation in megabytes."""
        count = len(self.short_term_records) + len(self.long_term_records)
        return (count * 128.0) / (1024.0 * 1024.0)

    def remember(
        self,
        memory_type: MemoryType,
        x: float,
        y: float,
        importance: float,
        current_tick: int,
        tag: Optional[str] = None,
    ) -> None:
        """Stores a new memory record or reinforces existing proximate memory."""
        for rec in self.short_term_records + self.long_term_records:
            if rec.memory_type == memory_type:
                dx = rec.pos_x - x
                dy = rec.pos_y - y
                if (dx * dx + dy * dy) < 16.0:  # Within 4 meters
                    rec.last_recalled_tick = current_tick
                    rec.recall_count += 1
                    rec.importance = max(rec.importance, importance)
                    return

        record = MemoryRecord(
            memory_type=memory_type,
            pos_x=x,
            pos_y=y,
            importance=importance,
            created_tick=current_tick,
            last_recalled_tick=current_tick,
            custom_tag=tag,
        )

        if importance >= 0.75:
            self._insert_long_term(record)
        else:
            self._insert_short_term(record)

    def _insert_short_term(self, record: MemoryRecord) -> None:
        if len(self.short_term_records) >= self.short_term_capacity:
            self.short_term_records.pop(0)
        self.short_term_records.append(record)

    def _insert_long_term(self, record: MemoryRecord) -> None:
        if len(self.long_term_records) >= self.long_term_capacity:
            self.long_term_records.sort(key=lambda r: r.importance)
            self.long_term_records.pop(0)
        self.long_term_records.append(record)

    def recall_nearest(
        self,
        current_x: float,
        current_y: float,
        memory_type: MemoryType,
        current_tick: int,
        min_retention: float = 0.20,
    ) -> Optional[Tuple[float, float, float]]:
        """Recalls the nearest remembered location of a given memory type."""
        all_records = self.short_term_records + self.long_term_records
        best_pos: Optional[Tuple[float, float, float]] = None
        best_dist_sq = float("inf")

        for rec in all_records:
            if rec.memory_type == memory_type:
                retention = rec.calculate_retention(current_tick, self.forgetting_rate)
                if retention >= min_retention:
                    dx = rec.pos_x - current_x
                    dy = rec.pos_y - current_y
                    d_sq = dx * dx + dy * dy
                    if d_sq < best_dist_sq:
                        best_dist_sq = d_sq
                        best_pos = (rec.pos_x, rec.pos_y, math.sqrt(d_sq))
                        rec.last_recalled_tick = current_tick
                        rec.recall_count += 1

        return best_pos

    def tick_forgetting(self, current_tick: int, decay_threshold: float = 0.05) -> None:
        self.short_term_records = [
            r for r in self.short_term_records
            if r.calculate_retention(current_tick, self.forgetting_rate) > decay_threshold
        ]
        self.long_term_records = [
            r for r in self.long_term_records
            if r.calculate_retention(current_tick, self.forgetting_rate) > decay_threshold
        ]


if TORCH_AVAILABLE:
    class MemoryAutoEncoder(nn.Module):
        """
        Differentiable PyTorch Neural Memory Network.
        Compresses 128-dimensional sensory-action experiences into a compact latent space,
        predicts future value states, and executes attention-based associative key-value queries.
        """

        def __init__(self, in_dim: int = 128, latent_dim: int = 32) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(in_dim, 64),
                nn.LeakyReLU(0.1),
                nn.LayerNorm(64),
                nn.Linear(64, latent_dim),
            )
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 64),
                nn.LeakyReLU(0.1),
                nn.Linear(64, in_dim),
            )
            self.value_head = nn.Sequential(
                nn.Linear(latent_dim, 16),
                nn.LeakyReLU(0.1),
                nn.Linear(16, 1),
            )
            self.key_proj = nn.Linear(in_dim, 32)
            self.query_proj = nn.Linear(in_dim, 32)

        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            z = self.encoder(x)
            x_rec = self.decoder(z)
            v = self.value_head(z)
            return z, x_rec, v


class HumanCognitiveMemory(OrganismMemory):
    """
    High-Capacity Sentient Adaptive Neural Memory System specifically engineered for the Human species.
    Powered by PyTorch (GPU CUDA accelerated) with >= 51.5 MB Preallocated Tensors for deep experience replay,
    spatial topological cognitive mapping, associative concept embeddings, and self-learning gradient optimization.
    """

    def __init__(
        self,
        replay_capacity: int = 102400,  # 102,400 experiences x 128 dims x 4 bytes = 50.0 MB
        feature_dim: int = 128,
        spatial_resolution: int = 512,  # 512x512 grid x 4 bytes = 1.0 MB
        device: Optional[Any] = None,
    ) -> None:
        super().__init__(short_term_capacity=100, long_term_capacity=500, forgetting_rate=0.0001)

        self.replay_capacity = replay_capacity
        self.feature_dim = feature_dim
        self.spatial_resolution = spatial_resolution

        self.device = None
        if TORCH_AVAILABLE:
            if device is not None:
                self.device = device
            elif gpu_mgr is not None:
                self.device = gpu_mgr.get_torch_device()
            else:
                self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

            self.experience_replay_matrix = torch.zeros((self.replay_capacity, self.feature_dim), dtype=torch.float32)
            self.experience_reward_vector = torch.zeros(self.replay_capacity, dtype=torch.float32)
            self.spatial_cognitive_grid = torch.zeros((self.spatial_resolution, self.spatial_resolution), dtype=torch.float32)
            self.concept_associative_matrix = torch.randn((256, self.feature_dim), dtype=torch.float32) * 0.1

            # Differentiable Neural Autoencoder Model & Optimizer on target device (CUDA GPU / CPU)
            self.neural_model = MemoryAutoEncoder(in_dim=self.feature_dim, latent_dim=32)
            if self.device is not None:
                try:
                    self.neural_model.to(self.device)
                except Exception:
                    self.device = torch.device("cpu")
                    self.neural_model.to(self.device)

            self.optimizer = optim.Adam(self.neural_model.parameters(), lr=0.004, weight_decay=1e-5)
        else:
            self.experience_replay_matrix = np.zeros((self.replay_capacity, self.feature_dim), dtype=np.float32)
            self.experience_reward_vector = np.zeros(self.replay_capacity, dtype=np.float32)
            self.spatial_cognitive_grid = np.zeros((self.spatial_resolution, self.spatial_resolution), dtype=np.float32)
            self.concept_associative_matrix = np.random.uniform(-0.1, 0.1, (256, self.feature_dim)).astype(np.float32)
            self.neural_model = None
            self.optimizer = None

        self.experience_count: int = 0
        self.write_cursor: int = 0
        self.latest_loss: float = 0.0
        self.self_training_cycles: int = 0

        # Semantic concept labels dictionary
        self.concept_dictionary: Dict[str, int] = {}
        self._init_default_human_concepts()

    def _init_default_human_concepts(self) -> None:
        default_concepts = [
            "FIRE", "STONE_TOOL", "SPEAR", "WATER_SPRING", "EDIBLE_BERRY",
            "PREDATOR_THREAT", "SHELTER_HUT", "CAMPFIRE", "TRIBE_MEMBER",
            "SOVEREIGN_LEADER", "GEMINI_DEITY", "AGRICULTURE_SEED", "COOKED_MEAT"
        ]
        for idx, concept in enumerate(default_concepts):
            self.concept_dictionary[concept] = idx

    def to_device(self, new_device: Any) -> None:
        """Transfers neural memory models to a new device."""
        if not TORCH_AVAILABLE or self.neural_model is None:
            return
        try:
            self.device = new_device
            self.neural_model.to(new_device)
            self.optimizer = optim.Adam(self.neural_model.parameters(), lr=0.004, weight_decay=1e-5)
        except Exception:
            pass

    @property
    def memory_size_mb(self) -> float:
        """Computes exact total RAM allocated by Human cognitive buffers."""
        if TORCH_AVAILABLE and isinstance(self.experience_replay_matrix, torch.Tensor):
            bytes_replay = (self.experience_replay_matrix.element_size() * self.experience_replay_matrix.nelement()) + (self.experience_reward_vector.element_size() * self.experience_reward_vector.nelement())
            bytes_spatial = self.spatial_cognitive_grid.element_size() * self.spatial_cognitive_grid.nelement()
            bytes_concept = self.concept_associative_matrix.element_size() * self.concept_associative_matrix.nelement()
            total_bytes = bytes_replay + bytes_spatial + bytes_concept
        else:
            bytes_replay = self.experience_replay_matrix.nbytes + self.experience_reward_vector.nbytes
            bytes_spatial = self.spatial_cognitive_grid.nbytes
            bytes_concept = self.concept_associative_matrix.nbytes
            total_bytes = bytes_replay + bytes_spatial + bytes_concept
        return total_bytes / (1024.0 * 1024.0)

    def record_experience(
        self,
        sensory_vector: List[float],
        action_vector: List[float],
        reward: float,
        emotion_vector: Optional[List[float]] = None,
    ) -> None:
        """Stores a high-dimensional experience into the 50 MB circular replay buffer."""
        entry = np.zeros(self.feature_dim, dtype=np.float32)

        # Pack sensory inputs
        s_len = min(48, len(sensory_vector))
        if s_len > 0:
            entry[:s_len] = sensory_vector[:s_len]

        # Pack action outputs
        a_len = min(32, len(action_vector))
        if a_len > 0:
            entry[48:48 + a_len] = action_vector[:a_len]

        # Pack emotional vitals
        if emotion_vector:
            e_len = min(16, len(emotion_vector))
            entry[80:80 + e_len] = emotion_vector[:e_len]

        # Pack reward
        entry[127] = reward

        # Write to buffer atomically
        idx = self.write_cursor
        if TORCH_AVAILABLE and isinstance(self.experience_replay_matrix, torch.Tensor):
            self.experience_replay_matrix[idx] = torch.from_numpy(entry)
            self.experience_reward_vector[idx] = reward
        else:
            self.experience_replay_matrix[idx] = entry
            self.experience_reward_vector[idx] = reward

        self.write_cursor = (self.write_cursor + 1) % self.replay_capacity
        self.experience_count = min(self.replay_capacity, self.experience_count + 1)

    def sample_batch(self, batch_size: int = 64) -> Tuple[Any, Any]:
        """Draws a random uniform mini-batch of past experiences for deep neural training."""
        if self.experience_count == 0:
            if TORCH_AVAILABLE and isinstance(self.experience_replay_matrix, torch.Tensor):
                return torch.zeros((batch_size, self.feature_dim), dtype=torch.float32), torch.zeros(batch_size, dtype=torch.float32)
            return np.zeros((batch_size, self.feature_dim), dtype=np.float32), np.zeros(batch_size, dtype=np.float32)

        indices = np.random.randint(0, self.experience_count, size=min(batch_size, self.experience_count))

        if TORCH_AVAILABLE and isinstance(self.experience_replay_matrix, torch.Tensor):
            idx_tensor = torch.from_numpy(indices)
            batch_exp = self.experience_replay_matrix[idx_tensor]
            batch_rewards = self.experience_reward_vector[idx_tensor]
        else:
            batch_exp = self.experience_replay_matrix[indices]
            batch_rewards = self.experience_reward_vector[indices]

        return batch_exp, batch_rewards

    def self_learn_step(self, batch_size: int = 32) -> float:
        """
        Executes an adaptive self-supervised PyTorch backpropagation step on GPU.
        Minimizes sensory reconstruction loss and trains the value prediction head.
        """
        if not TORCH_AVAILABLE or self.neural_model is None or self.experience_count < 8:
            return 0.0

        try:
            batch_exp, batch_rew = self.sample_batch(batch_size=batch_size)
            if not isinstance(batch_exp, torch.Tensor):
                batch_exp = torch.tensor(batch_exp, dtype=torch.float32)
                batch_rew = torch.tensor(batch_rew, dtype=torch.float32)

            if self.device is not None:
                batch_exp = batch_exp.to(self.device)
                batch_rew = batch_rew.to(self.device)

            self.optimizer.zero_grad()
            z, x_rec, v_pred = self.neural_model(batch_exp)

            # 1. Self-Supervised Reconstruction Loss (Learning compact environmental representations)
            recon_loss = nn.functional.mse_loss(x_rec, batch_exp)

            # 2. Value Regression Loss (Learning outcome values)
            val_loss = nn.functional.mse_loss(v_pred.squeeze(-1), batch_rew.squeeze(-1))

            total_loss = recon_loss + 0.5 * val_loss
            total_loss.backward()
            self.optimizer.step()

            self.latest_loss = float(total_loss.detach().item())
            self.self_training_cycles += 1
            return self.latest_loss
        except Exception:
            return 0.0

    def compute_intrinsic_curiosity(self, sensory_vector: List[float]) -> float:
        """
        Calculates intrinsic curiosity prediction error on GPU.
        Novel, unexpected, or unlearned sensory patterns yield high curiosity rewards.
        """
        if not TORCH_AVAILABLE or self.neural_model is None:
            return 0.2

        try:
            with torch.no_grad():
                inp = np.zeros(self.feature_dim, dtype=np.float32)
                s_len = min(48, len(sensory_vector))
                inp[:s_len] = sensory_vector[:s_len]
                inp_t = torch.from_numpy(inp).unsqueeze(0)
                if self.device is not None:
                    inp_t = inp_t.to(self.device)

                _, x_rec, _ = self.neural_model(inp_t)
                error = float(nn.functional.mse_loss(x_rec, inp_t).item())
                return min(1.0, error * 2.0)
        except Exception:
            return 0.2

    def associative_attention_recall(self, query_vector: List[float], top_k: int = 5) -> Tuple[List[int], float]:
        """
        Differentiable Associative Attention Query on GPU:
        Retrieves the top-k most relevant past experiences based on scaled dot-product attention.
        """
        if self.experience_count == 0 or not TORCH_AVAILABLE or self.neural_model is None:
            return [], 0.0

        try:
            with torch.no_grad():
                q_arr = np.zeros(self.feature_dim, dtype=np.float32)
                q_arr[:min(48, len(query_vector))] = query_vector[:min(48, len(query_vector))]
                q_t = torch.from_numpy(q_arr).unsqueeze(0)
                if self.device is not None:
                    q_t = q_t.to(self.device)

                # Sample subset for rapid lookup
                n_candidates = min(500, self.experience_count)
                candidates = self.experience_replay_matrix[:n_candidates]
                if self.device is not None:
                    candidates = candidates.to(self.device)

                q_proj = self.neural_model.query_proj(q_t)  # (1, 32)
                k_proj = self.neural_model.key_proj(candidates)  # (N, 32)

                # Scaled Dot-Product Attention Scores
                scores = torch.matmul(q_proj, k_proj.T) / math.sqrt(32.0)
                attn_weights = torch.softmax(scores, dim=-1).squeeze(0)

                top_scores, top_indices = torch.topk(attn_weights, k=min(top_k, n_candidates))
                rewards = self.experience_reward_vector[top_indices.cpu()] if hasattr(top_indices, "cpu") else self.experience_reward_vector[top_indices]
                if hasattr(rewards, "to") and self.device is not None:
                    rewards = rewards.to(self.device)
                expected_val = float(torch.sum(rewards * top_scores).item())

                ret_indices = top_indices.cpu().tolist() if hasattr(top_indices, "cpu") else top_indices.tolist()
                return ret_indices, expected_val
        except Exception:
            return [], 0.0

    def mark_spatial_poi(self, world_x: float, world_y: float, world_width: float, world_height: float, weight: float = 1.0) -> None:
        """Updates spatial topological memory map at coordinate."""
        gx = int(max(0, min(self.spatial_resolution - 1, (world_x / max(1.0, world_width)) * self.spatial_resolution)))
        gy = int(max(0, min(self.spatial_resolution - 1, (world_y / max(1.0, world_height)) * self.spatial_resolution)))
        if TORCH_AVAILABLE and isinstance(self.spatial_cognitive_grid, torch.Tensor):
            self.spatial_cognitive_grid[gy, gx] = min(10.0, float(self.spatial_cognitive_grid[gy, gx].item()) + weight)
        else:
            self.spatial_cognitive_grid[gy, gx] = min(10.0, float(self.spatial_cognitive_grid[gy, gx]) + weight)
