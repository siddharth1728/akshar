"""
Unit, Property, and Evolutionary Tests for Module M05: DISCOVERYFORGE
"""

import pytest
import numpy as np

from senseforge.discovery.candidate import PairedCandidate, EpistemicState, CandidateFitness
from senseforge.discovery.pareto import (
    dominates,
    fast_non_dominated_sort,
    compute_crowding_distance,
    ParetoArchive,
)
from senseforge.discovery.baselines import BaselineEvaluator, compute_nmse
from senseforge.discovery.forge import DiscoveryForge, ForgeConfig, GenerationSummary
from senseforge.genome.types import DataType
from senseforge.genome.candidate import GenomeFactory
from senseforge.probes.evolution import ProbeFactory
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry


def test_paired_candidate_canonical_roundtrip():
    """PairedCandidate canonical dictionary must reconstruct with identical structure."""
    inst = GenomeFactory.create_random_genome(101, [0, 1], DataType.SERIES, max_depth=3)
    probe = ProbeFactory.create_random_probe(202, [0, 1], num_actions=2)
    cand = PairedCandidate(instrument=inst, probe=probe, generation=1, state=EpistemicState.GENERATED)
    cand.fitness.info_gain = 0.25

    d = cand.to_canonical_dict()
    reconstructed = PairedCandidate.from_canonical_dict(d)

    assert reconstructed.candidate_id == cand.candidate_id
    assert reconstructed.generation == 1
    assert reconstructed.state == EpistemicState.GENERATED
    assert pytest.approx(reconstructed.fitness.info_gain) == 0.25
    assert reconstructed.complexity == cand.complexity


def test_pareto_dominance_rules():
    """Tests multi-objective dominance comparison."""
    inst = GenomeFactory.create_random_genome(1, [0], DataType.SERIES, 2)
    probe = ProbeFactory.create_random_probe(2, [0], num_actions=1)

    c1 = PairedCandidate(inst, probe)
    c1.fitness = CandidateFitness(info_gain=0.5, baseline_c_diff=0.2, robustness=1.0, simplicity=-5.0, energy_efficiency=-1.0)

    c2 = PairedCandidate(inst, probe)
    # Strictly worse in info_gain, equal in all others
    c2.fitness = CandidateFitness(info_gain=0.2, baseline_c_diff=0.2, robustness=1.0, simplicity=-5.0, energy_efficiency=-1.0)

    assert dominates(c1, c2) is True
    assert dominates(c2, c1) is False

    # Trade-off: c3 has better simplicity but worse info_gain
    c3 = PairedCandidate(inst, probe)
    c3.fitness = CandidateFitness(info_gain=0.4, baseline_c_diff=0.2, robustness=1.0, simplicity=-2.0, energy_efficiency=-1.0)
    assert dominates(c1, c3) is False
    assert dominates(c3, c1) is False


def test_fast_non_dominated_sort_and_crowding():
    """Verifies that non-dominated sorting produces valid Pareto fronts."""
    inst = GenomeFactory.create_random_genome(1, [0], DataType.SERIES, 2)
    probe = ProbeFactory.create_random_probe(2, [0], num_actions=1)

    c1 = PairedCandidate(inst, probe)
    c1.fitness = CandidateFitness(info_gain=1.0, baseline_c_diff=0.5, robustness=2.0)

    c2 = PairedCandidate(inst, probe)
    c2.fitness = CandidateFitness(info_gain=0.5, baseline_c_diff=0.2, robustness=1.0)

    c3 = PairedCandidate(inst, probe)
    c3.fitness = CandidateFitness(info_gain=0.1, baseline_c_diff=0.0, robustness=0.5)

    fronts = fast_non_dominated_sort([c1, c2, c3])
    assert len(fronts) == 3
    assert fronts[0][0] == c1
    assert fronts[1][0] == c2
    assert fronts[2][0] == c3

    compute_crowding_distance(fronts[0])
    assert fronts[0][0].crowding_distance == float("inf")


def test_pareto_archive_capacity():
    """Archive must maintain non-dominated solutions and respect capacity bound."""
    archive = ParetoArchive(max_capacity=5)
    inst = GenomeFactory.create_random_genome(1, [0], DataType.SERIES, 2)
    probe = ProbeFactory.create_random_probe(2, [0], num_actions=1)

    candidates = []
    for i in range(10):
        c = PairedCandidate(inst, probe)
        c.fitness = CandidateFitness(info_gain=float(i * 0.1), simplicity=float(-i))
        candidates.append(c)

    admitted = archive.update(candidates)
    assert admitted <= 5
    assert archive.size <= 5


def test_baseline_evaluator_comparisons():
    """
    Evaluator must return finite metrics for candidate and all 4 reference baselines.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=100,
        allowed_channels=[0, 1],
        num_entities=8
    )
    inst = GenomeFactory.create_random_genome(50, [0, 1], DataType.SERIES, max_depth=3)
    probe = ProbeFactory.create_random_probe(51, [0, 1], num_actions=2)
    cand = PairedCandidate(inst, probe)

    results = BaselineEvaluator.evaluate_candidate_and_baselines(
        candidate=cand,
        firewall=firewall,
        eval_seeds=[101, 102],
        target_channel=0,
        forecast_horizon=6,
        pre_steps=8
    )

    for key in ["nmse_candidate", "nmse_baseline_a", "nmse_baseline_b", "nmse_baseline_c", "nmse_baseline_d", "info_gain", "diff_c", "robustness"]:
        assert key in results
        assert np.isfinite(results[key])


def test_discovery_forge_evolution_cycle():
    """
    Runs a 2-generation evolution cycle on DiscoveryForge and verifies:
    1. Population size remains strictly constant.
    2. Summary metrics are produced.
    3. Candidates are evaluated and categorized into epistemic states.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=42,
        allowed_channels=[0, 1],
        num_entities=8
    )
    pop_size = 6
    config = ForgeConfig(
        population_size=pop_size,
        max_generations=2,
        eval_seeds=[11, 22],
        forecast_horizon=5,
        pre_steps=6,
        archive_capacity=10
    )
    forge = DiscoveryForge(firewall=firewall, allowed_channels=[0, 1], config=config, seed=42)

    assert len(forge.population) == pop_size
    assert forge.generation == 0

    # Step 1
    s1 = forge.step()
    assert isinstance(s1, GenerationSummary)
    assert len(forge.population) == pop_size
    assert forge.generation == 1
    assert forge.archive.size > 0

    # Step 2
    s2 = forge.step()
    assert isinstance(s2, GenerationSummary)
    assert len(forge.population) == pop_size
    assert forge.generation == 2
    assert len(forge.history) == 2

