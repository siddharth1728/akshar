"""
Thermodynamic Swarm Environment (M01 WORLDFOUNDRY)
Simulates an N-body particle system interacting via Lennard-Jones style pairwise forces
within a bounded thermal container.
"""

from typing import Optional, Dict
import numpy as np
from senseforge.core.environments.base import BaseEnvironment, EnvironmentConfig


class ThermodynamicSwarmEnvironment(BaseEnvironment):
    """
    Simulates N particles in 2D interacting via soft-core Lennard-Jones repulsive potentials
    with damping and thermal fluctuations:
    F_ij = 4 * epsilon * [ (sigma/r)^12 - (sigma/r)^6 ] * (r_vec / r)
    """

    def _initialize_private_state(self) -> None:
        self._n_particles = self._config.num_entities
        n = self._n_particles
        self._box_size = 10.0

        # Parameters
        self._sigma = 1.0
        self._epsilon = 0.5
        self._damping = 0.1

        # Hidden coordinates and velocities
        self._pos = self._rng.uniform(1.0, self._box_size - 1.0, size=(n, 2))
        self._vel = self._rng.normal(0.0, 0.5, size=(n, 2))

    def _compute_forces(self) -> np.ndarray:
        n = self._n_particles
        forces = np.zeros_like(self._pos)

        # Pairwise displacement tensor (N, N, 2)
        diff = self._pos[:, np.newaxis, :] - self._pos[np.newaxis, :, :]  # diff[i, j] = pos[i] - pos[j]
        dist_sq = np.sum(diff ** 2, axis=-1)  # (N, N)

        # Add diagonal epsilon to prevent self-force division by zero
        np.fill_diagonal(dist_sq, 1e6)
        dist = np.sqrt(dist_sq)

        # Truncated soft-core Lennard-Jones force magnitude
        cutoff = 4.0
        mask = dist < cutoff
        np.fill_diagonal(mask, False)

        r_inv = 1.0 / np.maximum(dist, 0.2)
        sr6 = (self._sigma * r_inv) ** 6
        sr12 = sr6 ** 2
        f_mag = 24.0 * self._epsilon * (2.0 * sr12 - sr6) * (r_inv ** 2)
        f_mag = np.clip(f_mag, -50.0, 50.0)

        # Accumulate forces
        f_vec = diff * f_mag[:, :, np.newaxis]  # (N, N, 2)
        f_vec[~mask] = 0.0
        forces = np.sum(f_vec, axis=1)

        # Container wall repulsion
        d_left = self._pos[:, 0]
        d_right = self._box_size - self._pos[:, 0]
        d_bottom = self._pos[:, 1]
        d_top = self._box_size - self._pos[:, 1]

        forces[:, 0] += np.where(d_left < 1.0, 10.0 * (1.0 - d_left), 0.0)
        forces[:, 0] -= np.where(d_right < 1.0, 10.0 * (1.0 - d_right), 0.0)
        forces[:, 1] += np.where(d_bottom < 1.0, 10.0 * (1.0 - d_bottom), 0.0)
        forces[:, 1] -= np.where(d_top < 1.0, 10.0 * (1.0 - d_top), 0.0)

        return forces

    def _step_internal(self, action: Optional[np.ndarray]) -> None:
        dt = self._config.step_size
        forces = self._compute_forces()
        
        # Apply velocity damping and action force
        accel = forces - self._damping * self._vel

        if action is not None:
            act = np.asarray(action, dtype=np.float64)
            if len(act) >= 2:
                # Direct force on lead particle 0
                accel[0, 0] += act[0] * 5.0
                accel[0, 1] += act[1] * 5.0

        # Velocity Verlet / Euler step
        self._vel += dt * accel
        self._pos += dt * self._vel

        # Hard boundary reflections
        for dim in [0, 1]:
            mask_low = self._pos[:, dim] < 0.0
            self._pos[mask_low, dim] = -self._pos[mask_low, dim]
            self._vel[mask_low, dim] = -0.5 * self._vel[mask_low, dim]

            mask_high = self._pos[:, dim] > self._box_size
            self._pos[mask_high, dim] = 2.0 * self._box_size - self._pos[mask_high, dim]
            self._vel[mask_high, dim] = -0.5 * self._vel[mask_high, dim]

    def _get_raw_observable_vector(self) -> np.ndarray:
        # Returns flattened positions and velocities
        return np.concatenate([self._pos.flatten(), self._vel.flatten()])

    @property
    def total_observable_channels(self) -> int:
        return 4 * self._n_particles

