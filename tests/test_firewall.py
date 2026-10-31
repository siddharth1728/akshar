"""
Unit and Adversarial Security Tests for OBSERVATION FIREWALL (M02)
Verifies information boundaries, hidden-state isolation, channel projection,
anti-tampering, and sanitized error handling.
"""

import pytest
import pickle
import numpy as np
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry
from senseforge.core.firewall import FirewallSecurityViolation, FirewallExecutionError, ObservationFrame


def test_channel_restriction():
    """
    Firewall must project the high-dimensional internal state down to
    ONLY the explicitly permitted channels.
    """
    allowed = [0, 2, 4]
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=123,
        allowed_channels=allowed,
        num_entities=10  # Raw state has 20 channels
    )

    frame = firewall.observe()
    assert isinstance(frame, ObservationFrame)
    assert len(frame.readings) == len(allowed)
    assert firewall.num_observable_channels == 3
    assert len(frame.frame_hash) == 64  # SHA256 hex length


def test_hidden_state_isolation_direct_access():
    """
    Direct attempts to access private simulation attributes on the firewall
    must trigger an immediate FirewallSecurityViolation.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=123,
        allowed_channels=[0, 1]
    )

    forbidden_attributes = [
        "_env", "env", "state", "_state",
        "positions", "_positions",
        "velocities", "_velocities",
        "params", "_params",
        "seed", "_seed",
        "_rng", "rng",
        "_k", "_beta", "_mu"
    ]

    for attr in forbidden_attributes:
        with pytest.raises(FirewallSecurityViolation):
            _ = getattr(firewall, attr)


def test_introspection_sanitization():
    """dir() on the firewall must not expose any internal simulation objects."""
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.REACTION_DIFFUSION,
        seed=42,
        allowed_channels=[0, 1]
    )

    exposed_members = dir(firewall)
    for forbidden in ["_env", "env", "_u", "_v", "state", "_state"]:
        assert forbidden not in exposed_members, f"Forbidden attribute '{forbidden}' leaked via dir()!"


def test_immutable_frame_anti_tampering():
    """
    Observation frames must be immutable. Modifying the readings tuple
    or attempt to mutate attributes must fail.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.THERMODYNAMIC_SWARM,
        seed=777,
        allowed_channels=[0, 1]
    )

    frame = firewall.observe()
    with pytest.raises(Exception):
        # Tuple is immutable
        frame.readings[0] = 9999.0

    with pytest.raises(Exception):
        # Frozen dataclass cannot be reassigned
        frame.step_index = 999


def test_action_clamping_and_bounded_probing():
    """
    Probes with extreme amplitudes must be safely clamped to max_action_amplitude
    and advance the simulation without crashing.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=555,
        allowed_channels=[0, 1],
        max_action_amplitude=1.5
    )

    initial_step = firewall.step_count
    # Apply an out-of-bounds action vector
    extreme_action = [1000.0, -9999.0]
    frame = firewall.probe(extreme_action)

    assert firewall.step_count == initial_step + 1
    assert np.all(np.isfinite(frame.readings))


def test_anti_serialization_exfiltration():
    """
    Attempting to pickle the ObservationFirewall to exfiltrate
    internal simulator pointers must be blocked.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=101,
        allowed_channels=[0]
    )

    with pytest.raises(FirewallSecurityViolation):
        pickle.dumps(firewall)

