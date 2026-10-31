"""
Reaction-Diffusion Field Environment (M01 WORLDFOUNDRY)
Simulates a 1D/2D Gray-Scott continuous activator-inhibitor system.
"""

from typing import Optional, Dict
import numpy as np
from senseforge.core.environments.base import BaseEnvironment, EnvironmentConfig


class ReactionDiffusionEnvironment(BaseEnvironment):
    """
    Simulates Gray-Scott reaction-diffusion kinetics:
    du/dt = D_u * Laplace(u) - u * v^2 + F * (1 - u)
    dv/dt = D_v * Laplace(v) + u * v^2 - (F + k) * v
    
    Exhibits spot formation, chaotic spatiotemporal turbulence, and traveling solitions.
    """

    def _initialize_private_state(self) -> None:
        self._grid_size = self._config.num_entities
        n = self._grid_size

        # Morphogenetic parameters
        self._Du = 0.16
        self._Dv = 0.08
        self._F = self._config.custom_params.get("feed_rate", 0.035)
        self._k = self._config.custom_params.get("kill_rate", 0.060)

        # Hidden chemical concentration grids
        self._u = np.ones(n, dtype=np.float64)
        self._v = np.zeros(n, dtype=np.float64)

        # Seed with randomized local perturbation
        center = n // 2
        radius = max(2, n // 8)
        self._u[center - radius : center + radius] = 0.5
        self._v[center - radius : center + radius] = 0.25
        # Add random perturbation
        self._v += self._rng.uniform(0.0, 0.05, size=n)

    def _step_internal(self, action: Optional[np.ndarray]) -> None:
        dt = self._config.step_size * 2.0  # Normalized integration timescale
        u = self._u
        v = self._v
        n = self._grid_size

        # 1D discrete periodic Laplacian operator
        laplace_u = np.roll(u, 1) + np.roll(u, -1) - 2.0 * u
        laplace_v = np.roll(v, 1) + np.roll(v, -1) - 2.0 * v

        # Reaction terms
        uvv = u * (v ** 2)
        du = self._Du * laplace_u - uvv + self._F * (1.0 - u)
        dv = self._Dv * laplace_v + uvv - (self._F + self._k) * v

        # Apply external chemical injection probes if provided
        if action is not None:
            act = np.asarray(action, dtype=np.float64)
            if len(act) > 0:
                m = min(len(act), n)
                dv[:m] += act[:m] * 0.1

        self._u = np.clip(u + dt * du, 0.0, 1.0)
        self._v = np.clip(v + dt * dv, 0.0, 1.0)

    def _get_raw_observable_vector(self) -> np.ndarray:
        return np.concatenate([self._u, self._v])

    @property
    def total_observable_channels(self) -> int:
        return 2 * self._grid_size

