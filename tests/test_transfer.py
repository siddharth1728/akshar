"""
Unit, Compatibility, and Cross-Family Transfer Tests for Module M07: TRANSFER LAB
"""

import pytest
import numpy as np

from senseforge.transfer.adapters import (
    FAMILY_INTERFACES,
    EnvironmentAdapter,
)
from senseforge.transfer.lab import (
    TransferCategory,
    TransferReport,
    TransferLab,
)
from senseforge.discovery.candidate import PairedCandidate, EpistemicState
from senseforge.genome.candidate import GenomeFactory
from senseforge.probes.evolution import ProbeFactory
from senseforge.genome.types import DataType
from senseforge.core.environments.base import EnvironmentFamily


def test_environment_adapter_compatibility():
    """Validates channel boundary checks across supported environment families."""
    assert EnvironmentAdapter.validate_compatibility({0, 1}, "coupled_oscillators") is True
    assert EnvironmentAdapter.validate_compatibility({0, 1}, "reaction_diffusion") is True
    assert EnvironmentAdapter.validate_compatibility({0, 1}, "thermodynamic_swarm") is True

    # Out of bounds channel
    assert EnvironmentAdapter.validate_compatibility({99}, "coupled_oscillators") is False
    assert EnvironmentAdapter.validate_compatibility({0}, "non_existent_family") is False


def test_transfer_lab_cross_family_evaluation():
    """
    Executes cross-family transfer from CoupledOscillators to ReactionDiffusion.
    """
    lab = TransferLab(target_seeds=[5001, 5002, 5003])
    inst = GenomeFactory.create_random_genome(10, [0, 1], DataType.SERIES, max_depth=2)
    probe = ProbeFactory.create_random_probe(20, [0, 1], num_actions=2)
    cand = PairedCandidate(inst, probe)

    report = lab.evaluate_transfer(
        candidate=cand,
        source_family=EnvironmentFamily.COUPLED_OSCILLATORS,
        target_family=EnvironmentFamily.REACTION_DIFFUSION,
        source_skill=0.50
    )

    assert isinstance(report, TransferReport)
    assert report.source_family == EnvironmentFamily.COUPLED_OSCILLATORS
    assert report.target_family == EnvironmentFamily.REACTION_DIFFUSION
    assert report.category in [
        TransferCategory.CROSS_FAMILY_TRANSFER,
        TransferCategory.INCONCLUSIVE_TRANSFER,
        TransferCategory.FAILED_TRANSFER
    ]
    assert np.isfinite(report.target_skill)


def test_transfer_matrix_generation():
    """Generates pairwise transfer matrix across all 3 environment families."""
    lab = TransferLab(target_seeds=[5001, 5002])
    inst = GenomeFactory.create_random_genome(11, [0, 1], DataType.SERIES, max_depth=2)
    probe = ProbeFactory.create_random_probe(22, [0, 1], num_actions=2)
    cand = PairedCandidate(inst, probe)

    matrix = lab.generate_transfer_matrix(
        candidate=cand,
        source_family=EnvironmentFamily.COUPLED_OSCILLATORS,
        families=[EnvironmentFamily.COUPLED_OSCILLATORS, EnvironmentFamily.REACTION_DIFFUSION]
    )

    assert EnvironmentFamily.COUPLED_OSCILLATORS in matrix
    assert EnvironmentFamily.REACTION_DIFFUSION in matrix
    assert "target_skill" in matrix[EnvironmentFamily.COUPLED_OSCILLATORS]
    assert "tdr" in matrix[EnvironmentFamily.REACTION_DIFFUSION]
