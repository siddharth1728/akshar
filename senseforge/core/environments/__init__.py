"""
SENSEFORGE Environment Registry and Factory
"""

from typing import Dict, Type
from senseforge.core.environments.base import BaseEnvironment, EnvironmentConfig, EnvironmentFamily
from senseforge.core.environments.coupled_oscillators import CoupledOscillatorsEnvironment
from senseforge.core.environments.reaction_diffusion import ReactionDiffusionEnvironment
from senseforge.core.environments.thermodynamic_swarm import ThermodynamicSwarmEnvironment

ENVIRONMENT_REGISTRY: Dict[str, Type[BaseEnvironment]] = {
    EnvironmentFamily.COUPLED_OSCILLATORS: CoupledOscillatorsEnvironment,
    EnvironmentFamily.REACTION_DIFFUSION: ReactionDiffusionEnvironment,
    EnvironmentFamily.THERMODYNAMIC_SWARM: ThermodynamicSwarmEnvironment,
}


def make_environment(config: EnvironmentConfig) -> BaseEnvironment:
    """Factory to instantiate any registered environment family."""
    if config.family not in ENVIRONMENT_REGISTRY:
        raise ValueError(f"Unknown environment family '{config.family}'. Registered families: {list(ENVIRONMENT_REGISTRY.keys())}")
    env_cls = ENVIRONMENT_REGISTRY[config.family]
    return env_cls(config)

