"""
SENSEFORGE Base Environment Interface (M01 WORLDFOUNDRY)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
from pydantic import BaseModel, Field


class EnvironmentFamily:
    COUPLED_OSCILLATORS = "coupled_oscillators"
    REACTION_DIFFUSION = "reaction_diffusion"
    THERMODYNAMIC_SWARM = "thermodynamic_swarm"


class EnvironmentConfig(BaseModel):
    family: str
    seed: int
    step_size: float = 0.01
    noise_std: float = 0.0
    num_entities: int = 16
    custom_params: Dict[str, float] = Field(default_factory=dict)


class BaseEnvironment(ABC):
    """
    Abstract base class for all procedural simulation environments.
    Strictly encapsulates all private internal state.
    """

    def __init__(self, config: EnvironmentConfig):
        self._config = config
        self._seed = config.seed
        self._rng = np.random.default_rng(config.seed)
        self._step_count = 0
        self._sim_time = 0.0
        self._initialize_private_state()

    @abstractmethod
    def _initialize_private_state(self) -> None:
        """Initializes internal latent physics/cellular state."""
        pass

    @abstractmethod
    def _step_internal(self, action: Optional[np.ndarray]) -> None:
        """Internal physics step advancing private state."""
        pass

    @abstractmethod
    def _get_raw_observable_vector(self) -> np.ndarray:
        """Returns the full raw observable vector from the current state."""
        pass

    @property
    @abstractmethod
    def total_observable_channels(self) -> int:
        """Returns the number of observable channels."""
        pass

    def step(self, action: Optional[np.ndarray] = None) -> None:
        """Advance the environment by one discrete time step."""
        self._step_internal(action)
        self._step_count += 1
        self._sim_time += self._config.step_size

    def reset(self, new_seed: Optional[int] = None) -> None:
        """Reset environment to initial conditions."""
        if new_seed is not None:
            self._seed = new_seed
        self._rng = np.random.default_rng(self._seed)
        self._step_count = 0
        self._sim_time = 0.0
        self._initialize_private_state()

    @property
    def step_count(self) -> int:
        return self._step_count

    @property
    def sim_time(self) -> float:
        return self._sim_time

    @property
    def family(self) -> str:
        return self._config.family

