"""
Unit, Statistical, and Falsification Tests for Module M06: FALSIFICATION CHAMBER
"""

import pytest
import numpy as np

from senseforge.falsification.partition import (
    PartitionManager,
    PartitionType,
    PartitionSealedViolation,
)
from senseforge.falsification.statistics import (
    StatisticalEngine,
    StatisticalReport,
)
from senseforge.falsification.chamber import (
    FalsificationChamber,
    compute_mse,
)
from senseforge.falsification.manifest import FrozenCandidate
from senseforge.discovery.candidate import PairedCandidate, EpistemicState
from senseforge.genome.candidate import GenomeFactory
from senseforge.probes.evolution import ProbeFactory
from senseforge.genome.types import DataType
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry


def test_partition_manager_disjoint_and_power_calc():
    """Seed partitions must be strictly disjoint, and power analysis must calculate N >= 30."""
    pm = PartitionManager()
    s = set(pm.get_partition(PartitionType.SEARCH).seeds)
    v = set(pm.get_partition(PartitionType.VALIDATION).seeds)
    c = set(pm.get_partition(PartitionType.SEALED_CONFIRMATORY).seeds)

    assert s.isdisjoint(v)
    assert s.isdisjoint(c)
    assert v.isdisjoint(c)
    assert len(c) >= 30

    min_n = PartitionManager.calculate_minimum_sample_size(effect_size=0.6, alpha=0.01, power=0.80)
    assert min_n >= 30


def test_sealed_partition_retuning_prevention():
    """Any attempt to retune or re-access the sealed partition with a modified config must be blocked."""
    pm = PartitionManager()
    c_part = pm.get_partition(PartitionType.SEALED_CONFIRMATORY)

    cand_id = "test_cand_123"
    hash_v1 = "hash_initial_version"
    hash_v2 = "hash_retuned_version"

    # First access is granted
    seeds = c_part.get_seeds(cand_id, hash_v1)
    assert len(seeds) > 0

    # Second access with identical hash is permitted (re-validation)
    seeds2 = c_part.get_seeds(cand_id, hash_v1)
    assert seeds == seeds2

    # Access with modified configuration hash raises PartitionSealedViolation
    with pytest.raises(PartitionSealedViolation, match="Retuning on .* is strictly prohibited"):
        c_part.get_seeds(cand_id, hash_v2)


def test_statistical_engine_wilcoxon_and_bootstrap():
    """Verifies bootstrap confidence intervals and Wilcoxon signed-rank testing."""
    rng = np.random.default_rng(42)
    cand_losses = [0.1, 0.12, 0.09, 0.11, 0.08]
    base_losses = [0.5, 0.55, 0.48, 0.52, 0.49] # Candidate strictly better

    rep = StatisticalEngine.evaluate_paired_test(cand_losses, base_losses, "Baseline A", alpha=0.05, rng=rng)
    assert rep.skill_score > 0.70
    assert rep.cohens_d > 5.0
    assert rep.p_value < 0.05
    assert rep.ci_95_lower > 0.0
    assert rep.statistically_significant is True


def test_holm_bonferroni_correction():
    """Corrects p-values for family-wise error rate control."""
    rep1 = StatisticalReport("B1", 10, 1.0, 0.5, 0.5, 1.0, 0.005, 0.005, 0.1, 0.9, True)
    rep2 = StatisticalReport("B2", 10, 1.0, 0.8, 0.2, 0.5, 0.02, 0.02, 0.05, 0.5, True)
    rep3 = StatisticalReport("B3", 10, 1.0, 0.95, 0.05, 0.1, 0.08, 0.08, -0.05, 0.2, False)

    corrected = StatisticalEngine.apply_holm_bonferroni([rep1, rep2, rep3], alpha=0.01)
    # Most significant (p=0.005) multiplied by 3 -> 0.015
    assert corrected[0].p_value_corrected == pytest.approx(0.015)
    # Second most significant (p=0.02) multiplied by 2 -> 0.04
    assert corrected[1].p_value_corrected == pytest.approx(0.04)


def test_falsification_chamber_comprehensive_evaluation():
    """
    Runs candidate through FalsificationChamber against Baselines A-D and Ablations F-G.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=42,
        allowed_channels=[0, 1],
        num_entities=8
    )
    chamber = FalsificationChamber(
        firewall=firewall,
        target_channel=0,
        forecast_horizon=5,
        pre_steps=8,
        num_random_controls=3,
        alpha=0.05
    )

    inst = GenomeFactory.create_random_genome(101, [0, 1], DataType.SERIES, max_depth=2)
    probe = ProbeFactory.create_random_probe(202, [0, 1], num_actions=2)
    cand = PairedCandidate(inst, probe)

    eval_result = chamber.evaluate_candidate_full(cand, seeds=[1001, 1002, 1003])
    assert "reports" in eval_result
    assert "Baseline A (Passive Control)" in eval_result["reports"]
    assert "Baseline C (Random Ensemble Control)" in eval_result["reports"]
    assert "Ablation F (Raw Obs + Evolved Probe)" in eval_result["reports"]
    assert "Ablation G (Evolved Obs + Random Probe)" in eval_result["reports"]
    assert cand.state in [EpistemicState.PROVISIONAL_DISCOVERY, EpistemicState.INCONCLUSIVE, EpistemicState.REJECTED]


def test_frozen_candidate_and_provenance_manifest():
    """Freezing candidate creates cryptographic hash signature and immutable manifest."""
    inst = GenomeFactory.create_random_genome(1, [0], DataType.SERIES, 2)
    probe = ProbeFactory.create_random_probe(2, [0], num_actions=1)
    cand = PairedCandidate(inst, probe)

    frozen = FrozenCandidate(cand)
    assert len(frozen.config_hash) == 64
    manifest = frozen.to_manifest(source_family=EnvironmentFamily.COUPLED_OSCILLATORS)

    assert manifest["candidate_id"] == cand.candidate_id
    assert "manifest_signature" in manifest
    assert len(manifest["manifest_signature"]) == 64
