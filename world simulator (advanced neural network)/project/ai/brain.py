"""
project/ai/brain.py

Neural Network Brain Controller & Synaptic Plasticity Engine for the ALife Platform.

Features:
- Multi-layer feed-forward network with recurrent working memory states.
- Configurable activation functions (Tanh, ReLU, Sigmoid, LeakyReLU).
- Hebbian synaptic learning plasticity: ΔW_ij = η * x_i * y_j - decay * W_ij.
- Reward reinforcement modulation.
- Direct vector serialization into Genome allele streams.
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple
from project.utils.random_utils import DeterministicPRNG

class ActivationType(Enum):
    TANH = auto()
    SIGMOID = auto()
    RELU = auto()
    LEAKY_RELU = auto()

class Brain:
    """
    Neural Network controller executing agent sensory perception into motor/behavioral actions.
    (Accelerated with NumPy vectorization)
    """

    def __init__(
        self,
        input_size: int = 16,
        hidden_sizes: Tuple[int, ...] = (24, 12),
        output_size: int = 8,
        activation: ActivationType = ActivationType.TANH,
        working_memory_size: int = 4,
        learning_rate: float = 0.01,
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

        self._initialize_weights()

    def _initialize_weights(self, prng: Optional[DeterministicPRNG] = None) -> None:
        rng = prng or DeterministicPRNG()
        self.weights.clear()
        self.biases.clear()

        for l in range(len(self.layer_sizes) - 1):
            n_in = self.layer_sizes[l]
            n_out = self.layer_sizes[l + 1]
            limit = math.sqrt(6.0 / (n_in + n_out))
            
            # Create matrices explicitly with RNG to maintain determinism if needed
            w_layer = np.array([[rng.uniform(-limit, limit) for _ in range(n_in)] for _ in range(n_out)], dtype=np.float32)
            b_layer = np.zeros(n_out, dtype=np.float32)

            self.weights.append(w_layer)
            self.biases.append(b_layer)

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
        current_input = list(inputs[:self.input_size])
        if len(current_input) < self.input_size:
            current_input.extend([0.0] * (self.input_size - len(current_input)))
        current_input.extend(self.working_memory)

        self.layer_inputs.clear()
        self.layer_outputs.clear()
        
        current_activations = np.array(current_input, dtype=np.float32)
        self.layer_inputs.append(current_activations)

        for l in range(len(self.weights)):
            w_matrix = self.weights[l]
            b_vector = self.biases[l]
            
            # Vectorized dense layer dot product
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

        return action_outputs

    def apply_hebbian_learning(self, reward: float = 1.0) -> None:
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
            # In-place clamping for stability
            np.clip(w_matrix, -5.0, 5.0, out=w_matrix)

    def export_weights_to_vector(self) -> List[float]:
        vec: List[float] = []
        for l in range(len(self.weights)):
            vec.extend(self.weights[l].flatten().tolist())
            vec.extend(self.biases[l].tolist())
        return vec

    def load_weights_from_vector(self, vec: List[float]) -> None:
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

    @property
    def total_synaptic_connections(self) -> int:
        """Returns total count of learnable neural synaptic weights and biases."""
        total = 0
        for w in self.weights:
            total += int(w.size)
        for b in self.biases:
            total += len(b)
        return total

    def expand_synaptic_capacity(self, new_hidden_sizes: Tuple[int, ...] = (36, 24, 12), new_working_memory: int = 8) -> int:
        """
        Dynamically expands brain neural network dimensions into a high-order hyper-brain.
        Used when an organism ascends to Leader or attains Gemini God communion.
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

        # Copy over old overlapping weights to preserve learned knowledge
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

        return self.total_synaptic_connections

    def clone(self) -> 'Brain':
        new_brain = Brain(
            input_size=self.input_size,
            hidden_sizes=self.hidden_sizes,
            output_size=self.output_size,
            activation=self.activation,
            working_memory_size=self.working_memory_size,
            learning_rate=self.learning_rate,
        )
        for l in range(len(self.weights)):
            new_brain.weights[l] = self.weights[l].copy()
            new_brain.biases[l] = self.biases[l].copy()
        return new_brain
