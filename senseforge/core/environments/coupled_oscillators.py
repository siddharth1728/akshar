"""
Coupled Non-Linear Oscillators Environment (M01 WORLDFOUNDRY)
Simulates a chain of coupled Duffing-van der Pol oscillators with non-linear spring constants.
"""

from typing import Optional, Dict
import numpy as np
from senseforge.core.environments.base import BaseEnvironment, EnvironmentConfig


class CoupledOscillatorsEnvironment(BaseEnvironment):
    """
    Simulates N coupled non-linear oscillators governed by:
    d^2 x_i / dt^2 = -k_i x_i - beta_i x_i^3 - mu_i (x_i^2 - 1) dx_i/dt + c_coup (x_{i+1} + x_{i-1} - 2 x_i) + u_i
    
    Integrated via 4th-order Runge-Kutta (RK4) for numerical stability.
    """

    def _initialize_private_state(self) -> None:
        n = self._config.num_entities
        # Hidden dynamical parameters randomized by seed
        self._n_oscillators = n
        self._k = self._rng.uniform(0.5, 2.5, size=n)
        self._beta = self._rng.uniform(0.1, 0.8, size=n)
        self._mu = self._rng.uniform(0.05, 0.3, size=n)
        self._c_coupling = self._config.custom_params.get("coupling", 0.4)

        # Hidden state vectors: positions and velocities
        self._positions = self._rng.uniform(-0.5, 0.5, size=n)
        self._velocities = self._rng.uniform(-0.1, 0.1, size=n)

    def _compute_accelerations(self, pos: np.ndarray, vel: np.ndarray, action: Optional[np.ndarray]) -> np.ndarray:
        n = self._n_oscillators
        # Periodic ring coupling: x_{i-1} and x_{i+1}
        pos_left = np.roll(pos, 1)
        pos_right = np.roll(pos, -1)
        coupling_force = self._c_coupling * (pos_left + pos_right - 2.0 * pos)

        # Duffing restorative force + van der Pol non-linear damping
        restorative = -self._k * pos - self._beta * (pos ** 3)
        damping = -self._mu * (pos ** 2 - 1.0) * vel

        accel = restorative + damping + coupling_force

        if action is not None:
            # Action only couples into specific actuator ports
            act = np.asarray(action, dtype=np.float64)
            if len(act) > 0:
                m = min(len(act), n)
                accel[:m] += act[:m]

        if self._config.noise_std > 0.0:
            accel += self._rng.normal(0.0, self._config.noise_std, size=n)

        return accel

    def _step_internal(self, action: Optional[np.ndarray]) -> None:
        dt = self._config.step_size
        p0 = self._positions
        v0 = self._velocities

        # RK4 Integration
        k1_v = self._compute_accelerations(p0, v0, action)
        k1_p = v0

        k2_v = self._compute_accelerations(p0 + 0.5 * dt * k1_p, v0 + 0.5 * dt * k1_v, action)
        k2_p = v0 + 0.5 * dt * k1_v

        k3_v = self._compute_accelerations(p0 + 0.5 * dt * k2_p, v0 + 0.5 * dt * k2_v, action)
        k3_p = v0 + 0.5 * dt * k2_v

        k4_v = self._compute_accelerations(p0 + dt * k3_p, v0 + dt * k3_v, action)
        k4_p = v0 + dt * k3_v

        self._positions = p0 + (dt / 6.0) * (k1_p + 2.0 * k2_p + 2.0 * k3_p + k4_p)
        self._velocities = v0 + (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)

        # Numerical safety guard: prevent unbounded divergence
        np.clip(self._positions, -20.0, 20.0, out=self._positions)
        np.clip(self._velocities, -50.0, 50.0, out=self._velocities)

    def _get_raw_observable_vector(self) -> np.ndarray:
        # Full observable vector contains all oscillator positions and velocities
        return np.concatenate([self._positions, self._velocities])

    @property
    def total_observable_channels(self) -> int:
        return 2 * self._n_oscillators

