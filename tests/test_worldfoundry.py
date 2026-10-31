"""
Unit and Property Tests for WORLDFOUNDRY (M01)
Verifies determinism, seed reproducibility, multi-family generation, and numerical stability.
"""

import pytest
import numpy as np
from senseforge.core.environments.base import EnvironmentConfig, EnvironmentFamily
from senseforge.core.environments import make_environment


@pytest.mark.parametrize("family", [
    EnvironmentFamily.COUPLED_OSCILLATORS,
    EnvironmentFamily.REACTION_DIFFUSION,
    EnvironmentFamily.THERMODYNAMIC_SWARM,
])
def test_deterministic_reproducibility(family: str):
    """
    Two independent environments created with the exact same seed
    must produce byte-for-byte identical state trajectories.
    """
    seed = 98765
    config1 = EnvironmentConfig(family=family, seed=seed, num_entities=8, step_size=0.01)
    config2 = EnvironmentConfig(family=family, seed=seed, num_entities=8, step_size=0.01)

    env1 = make_environment(config1)
    env2 = make_environment(config2)

    # Initial state must match
    obs1 = env1._get_raw_observable_vector()
    obs2 = env2._get_raw_observable_vector()
    np.testing.assert_array_equal(obs1, obs2)

    # Advance both environments through identical steps
    for _ in range(50):
        env1.step()
        env2.step()
        o1 = env1._get_raw_observable_vector()
        o2 = env2._get_raw_observable_vector()
        np.testing.assert_array_equal(o1, o2)


@pytest.mark.parametrize("family", [
    EnvironmentFamily.COUPLED_OSCILLATORS,
    EnvironmentFamily.REACTION_DIFFUSION,
    EnvironmentFamily.THERMODYNAMIC_SWARM,
])
def test_seed_divergence(family: str):
    """Different random seeds must produce distinct trajectories."""
    config1 = EnvironmentConfig(family=family, seed=111, num_entities=8, step_size=0.01)
    config2 = EnvironmentConfig(family=family, seed=222, num_entities=8, step_size=0.01)

    env1 = make_environment(config1)
    env2 = make_environment(config2)

    for _ in range(10):
        env1.step()
        env2.step()

    o1 = env1._get_raw_observable_vector()
    o2 = env2._get_raw_observable_vector()
    assert not np.allclose(o1, o2), f"Environment {family} failed to diverge under different seeds."


@pytest.mark.parametrize("family", [
    EnvironmentFamily.COUPLED_OSCILLATORS,
    EnvironmentFamily.REACTION_DIFFUSION,
    EnvironmentFamily.THERMODYNAMIC_SWARM,
])
def test_numerical_stability_long_run(family: str):
    """
    Simulations must remain finite and bounded over 500 continuous steps
    without generating NaN, Inf, or catastrophic explosion.
    """
    config = EnvironmentConfig(family=family, seed=42, num_entities=8, step_size=0.01)
    env = make_environment(config)

    for step in range(500):
        # Apply intermittent perturbation
        action = np.array([0.5, -0.5]) if step % 20 == 0 else None
        env.step(action)
        obs = env._get_raw_observable_vector()

        assert not np.isnan(obs).any(), f"NaN detected at step {step} in {family}"
        assert not np.isinf(obs).any(), f"Inf detected at step {step} in {family}"
        assert np.max(np.abs(obs)) < 100.0, f"Divergence detected at step {step} in {family}: max={np.max(np.abs(obs))}"

