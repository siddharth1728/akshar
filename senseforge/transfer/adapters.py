"""
SENSEFORGE M07: Environment Interface Adapters
Maps observation and intervention channels across structurally distinct environment families
without modifying candidate genome semantics.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyInterfaceSpec:
    family: str
    num_observation_channels: int
    num_action_channels: int
    description: str


FAMILY_INTERFACES: Dict[str, FamilyInterfaceSpec] = {
    "coupled_oscillators": FamilyInterfaceSpec(
        family="coupled_oscillators",
        num_observation_channels=16,
        num_action_channels=2,
        description="Non-linear coupled Duffing-van der Pol oscillator chain (positions and velocities)"
    ),
    "reaction_diffusion": FamilyInterfaceSpec(
        family="reaction_diffusion",
        num_observation_channels=16,
        num_action_channels=2,
        description="Gray-Scott continuous activator-inhibitor spatial lattice (u and v concentrations)"
    ),
    "thermodynamic_swarm": FamilyInterfaceSpec(
        family="thermodynamic_swarm",
        num_observation_channels=32,
        num_action_channels=2,
        description="2D particulate swarm interacting via soft-core Lennard-Jones forces (x, y, vx, vy)"
    ),
}


class EnvironmentAdapter:
    """
    Validates compatibility of candidate measurement channels and probe ports
    against a target environment family.
    """

    @staticmethod
    def validate_compatibility(candidate_required_channels: set, target_family: str) -> bool:
        """Checks if all candidate channels exist in target family."""
        if target_family not in FAMILY_INTERFACES:
            return False
        spec = FAMILY_INTERFACES[target_family]
        for ch in candidate_required_channels:
            if ch < 0 or ch >= spec.num_observation_channels:
                return False
        return True
