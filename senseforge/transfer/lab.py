"""
SENSEFORGE M07: Transfer Lab
Evaluates the cross-family generalization and invariance of frozen candidate instruments
across diverse procedural dynamical systems.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import numpy as np
from dataclasses import dataclass

from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry
from senseforge.discovery.candidate import PairedCandidate, EpistemicState
from senseforge.falsification.chamber import FalsificationChamber
from senseforge.transfer.adapters import EnvironmentAdapter


class TransferCategory(str, Enum):
    SAME_FAMILY_GENERALIZATION = "SAME_FAMILY_GENERALIZATION"
    CROSS_PARAMETER_GENERALIZATION = "CROSS_PARAMETER_GENERALIZATION"
    CROSS_FAMILY_TRANSFER = "CROSS_FAMILY_TRANSFER"
    FAILED_TRANSFER = "FAILED_TRANSFER"
    INCONCLUSIVE_TRANSFER = "INCONCLUSIVE_TRANSFER"


@dataclass(frozen=True)
class TransferReport:
    candidate_id: str
    source_family: str
    target_family: str
    source_skill: float
    target_skill: float
    transfer_degradation_ratio: float
    p_value: float
    category: TransferCategory
    seeds_evaluated: int


class TransferLab:
    """Executes frozen candidate transfer experiments across distinct environment families."""

    def __init__(self, target_seeds: Optional[List[int]] = None):
        self.target_seeds = target_seeds or list(range(5000, 5020)) # 20 seeds

    def evaluate_transfer(
        self,
        candidate: PairedCandidate,
        source_family: str,
        target_family: str,
        source_skill: float = 0.80
    ) -> TransferReport:
        """
        Transfers a frozen candidate to an independently generated target environment family.
        """
        # 1. Compatibility check
        if not EnvironmentAdapter.validate_compatibility(candidate.instrument.required_channels, target_family):
            return TransferReport(
                candidate_id=candidate.candidate_id,
                source_family=source_family,
                target_family=target_family,
                source_skill=source_skill,
                target_skill=-1.0,
                transfer_degradation_ratio=0.0,
                p_value=1.0,
                category=TransferCategory.FAILED_TRANSFER,
                seeds_evaluated=0,
            )

        # 2. Spawn target environment behind Observation Firewall
        target_firewall = WorldFoundry.spawn_sandboxed_environment(
            family=target_family,
            seed=self.target_seeds[0],
            allowed_channels=list(candidate.instrument.required_channels) or [0, 1],
            num_entities=8
        )

        # 3. Evaluate in target environment via FalsificationChamber
        chamber = FalsificationChamber(
            firewall=target_firewall,
            target_channel=min(candidate.instrument.required_channels) if candidate.instrument.required_channels else 0,
            forecast_horizon=8,
            pre_steps=12,
            num_random_controls=3,
            alpha=0.01
        )
        eval_res = chamber.evaluate_candidate_full(candidate, seeds=self.target_seeds)

        # Extract target skill over target passive baseline
        rep_a = eval_res["reports"]["Baseline A (Passive Control)"]
        target_skill = float(rep_a.skill_score)
        p_val = float(rep_a.p_value_corrected)

        # Compute Transfer Degradation Ratio (TDR)
        tdr = float(target_skill / (source_skill + 1e-6)) if source_skill > 0 else 0.0

        # Classification
        if source_family == target_family:
            cat = TransferCategory.SAME_FAMILY_GENERALIZATION if rep_a.statistically_significant else TransferCategory.FAILED_TRANSFER
        else:
            if rep_a.statistically_significant and target_skill >= 0.10:
                cat = TransferCategory.CROSS_FAMILY_TRANSFER
                candidate.state = EpistemicState.GENERALIZED_DISCOVERY
            elif target_skill > 0.0:
                cat = TransferCategory.INCONCLUSIVE_TRANSFER
            else:
                cat = TransferCategory.FAILED_TRANSFER

        return TransferReport(
            candidate_id=candidate.candidate_id,
            source_family=source_family,
            target_family=target_family,
            source_skill=source_skill,
            target_skill=target_skill,
            transfer_degradation_ratio=tdr,
            p_value=p_val,
            category=cat,
            seeds_evaluated=len(self.target_seeds),
        )

    def generate_transfer_matrix(
        self,
        candidate: PairedCandidate,
        source_family: str,
        families: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Computes pairwise transfer skill across all supported environment families."""
        fams = families or [
            EnvironmentFamily.COUPLED_OSCILLATORS,
            EnvironmentFamily.REACTION_DIFFUSION,
            EnvironmentFamily.THERMODYNAMIC_SWARM
        ]
        matrix: Dict[str, Dict[str, float]] = {}
        for target in fams:
            rep = self.evaluate_transfer(candidate, source_family=source_family, target_family=target)
            matrix[target] = {
                "target_skill": rep.target_skill,
                "tdr": rep.transfer_degradation_ratio,
                "category": rep.category.value,
            }
        return matrix
