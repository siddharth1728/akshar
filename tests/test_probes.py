"""
Unit and Property Tests for Module M04: PROBEDESIGNER
"""

import pytest
import numpy as np

from senseforge.probes.actions import (
    WaitAction,
    PerturbAction,
    ReversePerturbAction,
    RepeatAction,
    action_from_dict,
)
from senseforge.probes.genome import ProbeGenome
from senseforge.probes.evolution import ProbeFactory, ProbeConstraints
from senseforge.probes.executor import ProbeExecutor, ExperimentTrajectory
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry


def test_probe_action_primitives_unroll():
    """Tests action primitives durations, energies, and unrolled schedule shapes."""
    wait = WaitAction(steps=4)
    assert wait.duration == 4
    assert wait.energy_cost == 0.0
    u_wait = wait.unroll(total_channels=3)
    assert len(u_wait) == 4
    assert u_wait[0] == [0.0, 0.0, 0.0]

    perturb = PerturbAction(channel=1, magnitude=0.5, duration=2)
    assert perturb.duration == 2
    assert pytest.approx(perturb.energy_cost) == 0.5
    u_pert = perturb.unroll(total_channels=3)
    assert len(u_pert) == 2
    assert u_pert[0] == [0.0, 0.5, 0.0]

    rev = ReversePerturbAction(channel=0, magnitude=0.8, duration=1)
    u_rev = rev.unroll(total_channels=3)
    assert u_rev[0] == [-0.8, 0.0, 0.0]

    repeat = RepeatAction(action=perturb, count=3)
    assert repeat.duration == 6
    assert pytest.approx(repeat.energy_cost) == 1.5
    u_rep = repeat.unroll(total_channels=3)
    assert len(u_rep) == 6


def test_probe_genome_canonical_roundtrip():
    """ProbeGenome canonical dictionary serialization must perfectly reconstruct."""
    actions = [
        WaitAction(steps=3),
        PerturbAction(channel=0, magnitude=0.75, duration=2),
        ReversePerturbAction(channel=1, magnitude=0.4, duration=3),
    ]
    genome = ProbeGenome(actions=actions, reproducibility_seed=12345)
    d = genome.to_canonical_dict()

    reconstructed = ProbeGenome.from_canonical_dict(d)
    assert reconstructed.genome_id == genome.genome_id
    assert reconstructed.total_duration == genome.total_duration
    assert pytest.approx(reconstructed.total_energy) == genome.total_energy
    assert reconstructed.to_canonical_dict() == d


def test_probe_factory_random_generation():
    """Generates random probes respecting constraints across multiple seeds."""
    constraints = ProbeConstraints(max_sequence_length=8, max_duration=30, max_magnitude=1.0, max_energy=10.0)
    for seed in range(15):
        probe = ProbeFactory.create_random_probe(
            seed=seed,
            allowed_action_channels=[0, 1],
            constraints=constraints
        )
        assert probe.num_actions <= constraints.max_sequence_length
        assert probe.total_duration <= constraints.max_duration
        assert probe.total_energy <= constraints.max_energy + 1e-4
        assert probe.max_magnitude <= constraints.max_magnitude + 1e-4


def test_probe_mutations_and_crossover():
    """Verifies that mutations and crossover preserve constraints and produce valid offspring."""
    constraints = ProbeConstraints(max_sequence_length=10, max_duration=40, max_magnitude=1.0, max_energy=15.0)
    rng = np.random.default_rng(999)

    p_a = ProbeFactory.create_random_probe(1, [0, 1], constraints)
    p_b = ProbeFactory.create_random_probe(2, [0, 1], constraints)

    # Magnitude mutation
    m_mag = ProbeFactory.mutate_magnitude(p_a, constraints, rng)
    assert m_mag.max_magnitude <= constraints.max_magnitude

    # Timing mutation
    m_time = ProbeFactory.mutate_timing(p_a, constraints, rng)
    assert m_time.total_duration <= constraints.max_duration

    # Sequence mutation
    m_seq = ProbeFactory.mutate_sequence(p_a, [0, 1], constraints, rng)
    assert m_seq.num_actions <= constraints.max_sequence_length

    # Crossover
    off_a, off_b = ProbeFactory.crossover(p_a, p_b, constraints, rng)
    assert off_a.total_duration <= constraints.max_duration
    assert off_b.total_duration <= constraints.max_duration


def test_probe_simplification():
    """Simplification merges adjacent Wait steps and preserves semantics."""
    actions = [WaitAction(steps=3), WaitAction(steps=4), PerturbAction(0, 0.5, 2)]
    probe = ProbeGenome(actions=actions, reproducibility_seed=42)
    simplified = ProbeFactory.simplify_probe(probe)

    assert simplified.num_actions == 2
    assert simplified.actions[0].duration == 7
    assert simplified.total_duration == probe.total_duration


def test_probe_execution_and_episode_isolation():
    """
    Executes a probe on a WorldFoundry environment and verifies:
    1. Output trajectory has valid readings.
    2. Two consecutive executions with same reset seed yield byte-for-byte identical trajectories.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=123,
        allowed_channels=[0, 1],
        num_entities=8
    )
    probe = ProbeFactory.create_random_probe(42, allowed_action_channels=[0])

    traj1 = ProbeExecutor.execute(firewall, probe, total_action_channels=2, reset_seed=500)
    traj2 = ProbeExecutor.execute(firewall, probe, total_action_channels=2, reset_seed=500)

    assert isinstance(traj1, ExperimentTrajectory)
    assert traj1.duration == traj2.duration
    np.testing.assert_array_equal(traj1.full_readings[0], traj2.full_readings[0])
    np.testing.assert_array_equal(traj1.full_readings[1], traj2.full_readings[1])

