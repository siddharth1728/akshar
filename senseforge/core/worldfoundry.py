"""
SENSEFORGE M01: WORLDFOUNDRY
High-level factory and procedural generator that provisions environments
wrapped securely in an Observation Firewall.
"""

from typing import List, Optional
from senseforge.core.environments.base import EnvironmentConfig, EnvironmentFamily
from senseforge.core.environments import make_environment
from senseforge.core.firewall import ObservationFirewall


class WorldFoundry:
    """
    Procedural world generator providing fully encapsulated environments
    behind strict observation boundaries.
    """

    @staticmethod
    def spawn_sandboxed_environment(
        family: str,
        seed: int,
        allowed_channels: List[int],
        step_size: float = 0.01,
        noise_std: float = 0.0,
        num_entities: int = 16,
        max_action_amplitude: float = 1.0,
        custom_params: Optional[dict] = None
    ) -> ObservationFirewall:
        """
        Instantiates an environment and immediately seals it within an Observation Firewall.
        The caller receives ONLY the firewall interface; the raw environment reference is discarded.
        """
        config = EnvironmentConfig(
            family=family,
            seed=seed,
            step_size=step_size,
            noise_std=noise_std,
            num_entities=num_entities,
            custom_params=custom_params or {}
        )
        raw_env = make_environment(config)
        # Seal environment inside firewall
        firewall = ObservationFirewall(
            env=raw_env,
            allowed_channels=allowed_channels,
            max_action_amplitude=max_action_amplitude
        )
        return firewall

