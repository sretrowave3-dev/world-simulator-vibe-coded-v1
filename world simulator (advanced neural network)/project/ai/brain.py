"""
project/ai/brain.py

PyTorch-Accelerated Neural Network Brain Controller & Synaptic Plasticity Engine.
Supports GPU (CUDA) Tensor Cores, Hebbian Plasticity, Actor-Critic Self-Learning,
Recurrent Working Memory, and seamless NumPy/PyTorch bidirectional synchronization.

Features:
- PyTorch nn.Module acceleration with automatic NVIDIA GPU (CUDA) device placement.
- Self-learning backpropagation engine via online experience replay & policy-value loss.
- Hebbian synaptic learning plasticity: ΔW_ij = η * x_i * y_j - decay * W_ij.
- Recurrent working memory registers for temporal context and state persistence.
- Complete backward compatibility with ALife genome serialization and visualizer telemetry.
"""

from __future__ import annotations

import collections
import math
import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Any, Deque
from project.utils.random_utils import DeterministicPRNG

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


class ActivationType(Enum):
    TANH = auto()
    SIGMOID = auto()
    RELU = auto()
    LEAKY_RELU = auto()


if TORCH_AVAILABLE:
    class TorchBrainModule(nn.Module):
        """PyTorch neural module implementing feedforward perception and value estimation."""

        def __init__(self, layer_sizes: List[int], activation: ActivationType) -> None:
            super().__init__()
            self.layer_sizes = layer_sizes
            self.layers = nn.ModuleList()
            for i in range(len(layer_sizes) - 1):
                self.layers.append(nn.Linear(layer_sizes[i], layer_sizes[i + 1]))

            if activation == ActivationType.RELU:
                self.act = nn.ReLU()
            elif activation == ActivationType.LEAKY_RELU:
                self.act = nn.LeakyReLU(0.01)
            elif activation == ActivationType.SIGMOID:
                self.act = nn.Sigmoid()
            else:
                self.act = nn.Tanh()

            # Auxiliary value estimation head for Actor-Critic TD self-learning
            last_hidden = layer_sizes[-2] if len(layer_sizes) >= 3 else layer_sizes[0]
            self.value_head = nn.Sequential(
                nn.Linear(last_hidden, 16),
                nn.Tanh(),
                nn.Linear(16, 1)
            )

        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, List[torch.Tensor], List[torch.Tensor]]:
            layer_inputs: List[torch.Tensor] = []
            layer_outputs: List[torch.Tensor] = []
            curr = x
            penultimate = curr

            for i, layer in enumerate(self.layers):
                layer_inputs.append(curr)
                if i == len(self.layers) - 1:
                    penultimate = curr
                z = layer(curr)
                curr = self.act(z)
                layer_outputs.append(curr)

            value = self.value_head(penultimate)
            return curr, value, layer_inputs, layer_outputs


class Brain:
    """
    Neural Network controller executing agent sensory perception into motor/behavioral actions.
    Accelerated with PyTorch (CUDA GPU when available) and NumPy vectorization fallback.
    """

    def __init__(
        self,
        input_size: int = 16,
        hidden_sizes: Tuple[int, ...] = (24, 12),
        output_size: int = 8,
        activation: ActivationType = ActivationType.TANH,
        working_memory_size: int = 4,
        learning_rate: float = 0.01,
        device: Optional[Any] = None,
    ) -> None:
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.activation = activation
        self.working_memory_size = working_memory_size
        self.learning_rate = learning_rate

        effective_in = input_size + working_memory_size
        effective_out = output_size + working_memory_size
        self.layer_sizes: List[int] = [effective_in] + list(hidden_sizes) + [effective_out]

        self.weights: List[np.ndarray] = []
        self.biases: List[np.ndarray] = []

        self.working_memory: List[float] = [0.0] * working_memory_size
        self.layer_inputs: List[np.ndarray] = []
        self.layer_outputs: List[np.ndarray] = []

        # PyTorch & Device Setup
        self.device = None
        self.torch_module: Optional[Any] = None
        self.optimizer: Optional[Any] = None
        self.use_torch: bool = TORCH_AVAILABLE

        # Self-Learning Transition Memory & Telemetry
        self.experience_buffer: Deque[Tuple[List[float], List[float], float, List[float], bool]] = collections.deque(maxlen=256)
        self.self_learning_enabled: bool = True
        self.total_learning_steps: int = 0
        self.latest_loss: float = 0.0
        self.last_state: Optional[List[float]] = None
        self.last_action: Optional[List[float]] = None

        self._initialize_weights()

        # Initialize PyTorch module on device (CUDA GPU or CPU)
        if TORCH_AVAILABLE:
            if device is not None:
                self.device = device
            elif gpu_mgr is not None:
                self.device = gpu_mgr.get_torch_device()
            else:
                self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self._init_torch_module()

    def _initialize_weights(self, prng: Optional[DeterministicPRNG] = None) -> None:
        rng = prng or DeterministicPRNG()
        self.weights.clear()
        self.biases.clear()

        for l in range(len(self.layer_sizes) - 1):
            n_in = self.layer_sizes[l]
            n_out = self.layer_sizes[l + 1]
            limit = math.sqrt(6.0 / (n_in + n_out))

            w_layer = np.array(
                [[rng.uniform(-limit, limit) for _ in range(n_in)] for _ in range(n_out)],
                dtype=np.float32,
            )
            b_layer = np.zeros(n_out, dtype=np.float32)

            self.weights.append(w_layer)
            self.biases.append(b_layer)

    def _init_torch_module(self) -> None:
        """Instantiates or rebuilds the PyTorch module and synchronizes existing weights."""
        if not TORCH_AVAILABLE:
            return
        try:
            self.torch_module = TorchBrainModule(self.layer_sizes, self.activation)
            if self.device is not None:
                self.torch_module.to(self.device)
            self.optimizer = optim.Adam(self.torch_module.parameters(), lr=self.learning_rate, weight_decay=1e-5)
            self.sync_weights_from_numpy()
        except Exception:
            self.use_torch = False
            self.torch_module = None
            self.optimizer = None

    def sync_weights_from_numpy(self) -> None:
        """Copies NumPy weights/biases into the PyTorch module parameters."""
        if not TORCH_AVAILABLE or self.torch_module is None:
            return
        try:
            with torch.no_grad():
                for l, layer in enumerate(self.torch_module.layers):
                    if l < len(self.weights):
                        layer.weight.data.copy_(torch.from_numpy(self.weights[l]).to(self.device))
                    if l < len(self.biases):
                        layer.bias.data.copy_(torch.from_numpy(self.biases[l]).to(self.device))
        except Exception:
            pass

    def sync_weights_to_numpy(self) -> None:
        """Copies PyTorch module parameters back into NumPy arrays for visualizer and serialization."""
        if not TORCH_AVAILABLE or self.torch_module is None:
            return
        try:
            with torch.no_grad():
                for l, layer in enumerate(self.torch_module.layers):
                    if l < len(self.weights):
                        self.weights[l][:] = layer.weight.data.cpu().numpy()
                    if l < len(self.biases):
                        self.biases[l][:] = layer.bias.data.cpu().numpy()
        except Exception:
            pass

    def to_device(self, new_device: Any) -> None:
        """Transfers the neural network to a new device (e.g. cuda:0 or cpu)."""
        if not TORCH_AVAILABLE or self.torch_module is None:
            return
        try:
            self.device = new_device
            self.torch_module.to(new_device)
            self.optimizer = optim.Adam(self.torch_module.parameters(), lr=self.learning_rate, weight_decay=1e-5)
        except Exception:
            pass

    def _activate(self, x: np.ndarray) -> np.ndarray:
        if self.activation == ActivationType.TANH:
            return np.tanh(x)
        elif self.activation == ActivationType.SIGMOID:
            cx = np.clip(x, -15.0, 15.0)
            return 1.0 / (1.0 + np.exp(-cx))
        elif self.activation == ActivationType.RELU:
            return np.maximum(0.0, x)
        elif self.activation == ActivationType.LEAKY_RELU:
            return np.where(x > 0, x, 0.01 * x)
        return np.tanh(x)

    def forward(self, inputs: List[float]) -> List[float]:
        """
        Executes a cognitive feedforward pass.
        Uses PyTorch on GPU if active, with automatic fallback to NumPy vectorization.
        """
        current_input = list(inputs[:self.input_size])
        if len(current_input) < self.input_size:
            current_input.extend([0.0] * (self.input_size - len(current_input)))
        current_input.extend(self.working_memory)

        # PyTorch GPU-Accelerated Path
        if self.use_torch and self.torch_module is not None:
            try:
                with torch.no_grad():
                    inp_t = torch.tensor(current_input, dtype=torch.float32, device=self.device).unsqueeze(0)
                    act_out_t, _, l_ins, l_outs = self.torch_module(inp_t)

                    self.layer_inputs.clear()
                    self.layer_outputs.clear()
                    for li in l_ins:
                        self.layer_inputs.append(li.squeeze(0).cpu().numpy())
                    for lo in l_outs:
                        self.layer_outputs.append(lo.squeeze(0).cpu().numpy())

                    act_list = act_out_t.squeeze(0).cpu().tolist()
                    action_outputs = act_list[:self.output_size]
                    new_memory = act_list[self.output_size:self.output_size + self.working_memory_size]

                    if new_memory:
                        self.working_memory = new_memory

                    self.last_state = current_input
                    self.last_action = action_outputs
                    return action_outputs
            except Exception:
                # Fallback to NumPy on exception
                pass

        # NumPy Vectorized Fallback Path
        self.layer_inputs.clear()
        self.layer_outputs.clear()

        current_activations = np.array(current_input, dtype=np.float32)
        self.layer_inputs.append(current_activations)

        for l in range(len(self.weights)):
            w_matrix = self.weights[l]
            b_vector = self.biases[l]

            z = np.dot(w_matrix, current_activations) + b_vector
            next_activations = self._activate(z)

            self.layer_outputs.append(next_activations)
            current_activations = next_activations
            if l < len(self.weights) - 1:
                self.layer_inputs.append(current_activations)

        act_list = current_activations.tolist()
        action_outputs = act_list[:self.output_size]
        new_memory = act_list[self.output_size:self.output_size + self.working_memory_size]

        if new_memory:
            self.working_memory = new_memory

        self.last_state = current_input
        self.last_action = action_outputs
        return action_outputs

    def record_transition(
        self,
        state: List[float],
        action: List[float],
        reward: float,
        next_state: List[float],
        done: bool = False,
    ) -> None:
        """Stores experience transition into circular memory replay for self-learning."""
        self.experience_buffer.append((list(state), list(action), float(reward), list(next_state), done))

    def self_learn_step(self, batch_size: int = 16, gamma: float = 0.95) -> float:
        """
        Executes a PyTorch Actor-Critic backpropagation step on GPU.
        Optimizes weights by minimizing TD value prediction error and policy alignment.
        """
        if not self.self_learning_enabled or not TORCH_AVAILABLE or self.torch_module is None:
            return 0.0
        n_exp = len(self.experience_buffer)
        if n_exp == 0:
            return 0.0

        try:
            sample_count = min(batch_size, n_exp)
            indices = np.random.choice(n_exp, size=batch_size if n_exp >= batch_size else sample_count, replace=(n_exp < batch_size))
            batch = [self.experience_buffer[i] for i in indices]

            effective_in = self.layer_sizes[0]
            padded_states = []
            for b in batch:
                st = list(b[0])
                if len(st) < effective_in:
                    st.extend([0.0] * (effective_in - len(st)))
                padded_states.append(st[:effective_in])

            padded_next_states = []
            for b in batch:
                nst = list(b[3])
                if len(nst) < effective_in:
                    nst.extend([0.0] * (effective_in - len(nst)))
                padded_next_states.append(nst[:effective_in])

            states = torch.tensor(padded_states, dtype=torch.float32, device=self.device)
            actions = torch.tensor([b[1] for b in batch], dtype=torch.float32, device=self.device)
            rewards = torch.tensor([b[2] for b in batch], dtype=torch.float32, device=self.device)
            next_states = torch.tensor(padded_next_states, dtype=torch.float32, device=self.device)
            dones = torch.tensor([1.0 if b[4] else 0.0 for b in batch], dtype=torch.float32, device=self.device)

            self.optimizer.zero_grad()

            pred_actions, pred_values, _, _ = self.torch_module(states)
            with torch.no_grad():
                _, next_values, _, _ = self.torch_module(next_states)
                target_values = rewards + (1.0 - dones) * gamma * next_values.squeeze(-1)

            # Critic Value Loss
            critic_loss = nn.functional.mse_loss(pred_values.squeeze(-1), target_values)

            # Actor Advantage Loss: Reinforces actions that yielded positive advantage
            advantage = (target_values - pred_values.squeeze(-1).detach()).unsqueeze(-1)
            target_actions = actions + 0.1 * torch.tanh(advantage)
            actor_loss = nn.functional.mse_loss(pred_actions[:, :min(actions.shape[1], pred_actions.shape[1])], target_actions)

            total_loss = actor_loss + 0.5 * critic_loss
            total_loss.backward()

            nn.utils.clip_grad_norm_(self.torch_module.parameters(), max_norm=2.0)
            self.optimizer.step()

            # Keep NumPy weights in sync for visualizer
            self.sync_weights_to_numpy()

            self.latest_loss = float(total_loss.detach().item())
            self.total_learning_steps += 1
            return self.latest_loss
        except Exception:
            return 0.0

    def apply_hebbian_learning(self, reward: float = 1.0) -> None:
        """
        Hebbian synaptic plasticity rule: ΔW_ij = η * x_i * y_j - decay * W_ij.
        Updates weights based on recent neuron pre/post activations and reward signal.
        """
        if not self.layer_inputs or not self.layer_outputs:
            return

        eta = self.learning_rate * reward
        for l in range(len(self.weights)):
            inputs = self.layer_inputs[l]      # shape: (n_in,)
            outputs = self.layer_outputs[l]    # shape: (n_out,)
            w_matrix = self.weights[l]         # shape: (n_out, n_in)

            # Vectorized Hebbian rule: ΔW = η * (outputs ⊗ inputs - 0.01 * W)
            delta = eta * (np.outer(outputs, inputs) - 0.01 * w_matrix)
            w_matrix += delta
            # In-place clamping for numerical stability
            np.clip(w_matrix, -5.0, 5.0, out=w_matrix)

        # Reflect Hebbian plasticity changes into PyTorch module
        self.sync_weights_from_numpy()

    def export_weights_to_vector(self) -> List[float]:
        """Flattens all synaptic weights and biases into a 1D float list for genetic storage."""
        vec: List[float] = []
        for l in range(len(self.weights)):
            vec.extend(self.weights[l].flatten().tolist())
            vec.extend(self.biases[l].tolist())
        return vec

    def load_weights_from_vector(self, vec: List[float]) -> None:
        """Restores synaptic weights and biases from a 1D float vector."""
        idx = 0
        for l in range(len(self.weights)):
            w_matrix = self.weights[l]
            n_out, n_in = w_matrix.shape
            w_size = n_out * n_in

            if idx + w_size <= len(vec):
                w_matrix[:] = np.array(vec[idx:idx + w_size], dtype=np.float32).reshape(n_out, n_in)
                idx += w_size

            b_size = len(self.biases[l])
            if idx + b_size <= len(vec):
                self.biases[l][:] = np.array(vec[idx:idx + b_size], dtype=np.float32)
                idx += b_size

        self.sync_weights_from_numpy()

    @property
    def total_synaptic_connections(self) -> int:
        """Returns total count of learnable neural synaptic weights and biases."""
        total = 0
        for w in self.weights:
            total += int(w.size)
        for b in self.biases:
            total += len(b)
        return total

    def expand_synaptic_capacity(
        self,
        new_hidden_sizes: Tuple[int, ...] = (36, 24, 12),
        new_working_memory: int = 8,
    ) -> int:
        """
        Dynamically expands brain neural network dimensions into a high-order hyper-brain.
        Preserves overlapping learned knowledge.
        """
        old_weights = [w.copy() for w in self.weights]
        old_biases = [b.copy() for b in self.biases]

        self.hidden_sizes = new_hidden_sizes
        self.working_memory_size = new_working_memory

        effective_in = self.input_size + self.working_memory_size
        effective_out = self.output_size + self.working_memory_size
        self.layer_sizes = [effective_in] + list(new_hidden_sizes) + [effective_out]
        self.working_memory = [0.0] * self.working_memory_size

        self._initialize_weights()

        for l in range(min(len(old_weights), len(self.weights))):
            old_w = old_weights[l]
            new_w = self.weights[l]
            r = min(old_w.shape[0], new_w.shape[0])
            c = min(old_w.shape[1], new_w.shape[1])
            new_w[:r, :c] = old_w[:r, :c]

            old_b = old_biases[l]
            new_b = self.biases[l]
            b_len = min(len(old_b), len(new_b))
            new_b[:b_len] = old_b[:b_len]

        self._init_torch_module()
        return self.total_synaptic_connections

    def clone(self) -> 'Brain':
        """Produces an exact clone of this Brain controller with preserved weights and state."""
        new_brain = Brain(
            input_size=self.input_size,
            hidden_sizes=self.hidden_sizes,
            output_size=self.output_size,
            activation=self.activation,
            working_memory_size=self.working_memory_size,
            learning_rate=self.learning_rate,
            device=self.device,
        )
        for l in range(len(self.weights)):
            new_brain.weights[l] = self.weights[l].copy()
            new_brain.biases[l] = self.biases[l].copy()
        new_brain.working_memory = list(self.working_memory)
        new_brain.sync_weights_from_numpy()
        return new_brain
