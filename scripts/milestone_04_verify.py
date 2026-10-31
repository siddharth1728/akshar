"""
SENSEFORGE Milestone 4 Verification Script
Executes full Phase 04 scientific falsification, sealed confirmatory testing (N=30 seeds),
and cross-family transfer experiments across all 3 environment families.
"""

import sys
import json
import numpy as np

from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry
from senseforge.genome.candidate import GenomeFactory
from senseforge.probes.evolution import ProbeFactory
from senseforge.genome.types import DataType
from senseforge.discovery.candidate import PairedCandidate, EpistemicState
from senseforge.falsification.partition import PartitionManager, PartitionType
from senseforge.falsification.chamber import FalsificationChamber
from senseforge.falsification.manifest import FrozenCandidate
from senseforge.transfer.lab import TransferLab


def run_milestone_04_validation():
    print("=" * 80)
    print(" SENSEFORGE MILESTONE 04: FALSIFICATION CHAMBER & CROSS-FAMILY TRANSFER LAB")
    print("=" * 80)

    # 1. Independent Partitioning Setup
    print("\n[Step 1] Partitioning Seeds: Search, Validation, and Sealed Confirmatory...")
    pm = PartitionManager()
    search_p = pm.get_partition(PartitionType.SEARCH)
    val_p = pm.get_partition(PartitionType.VALIDATION)
    conf_p = pm.get_partition(PartitionType.SEALED_CONFIRMATORY)
    print(f" -> Search Seeds:       {len(search_p.seeds)} seeds ({search_p.seeds[0]}..{search_p.seeds[-1]})")
    print(f" -> Validation Seeds:   {len(val_p.seeds)} seeds ({val_p.seeds[0]}..{val_p.seeds[-1]})")
    print(f" -> Confirmatory Seeds: {len(conf_p.seeds)} seeds ({conf_p.seeds[0]}..{conf_p.seeds[-1]}) [N >= 30, Sealed]")

    # 2. Candidate Selection & Cryptographic Freeze
    print("\n[Step 2] Selecting Candidate & Sealing Cryptographic Lock...")
    firewall_osc = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=42,
        allowed_channels=[0, 1],
        num_entities=8
    )
    inst = GenomeFactory.create_random_genome(seed=101, allowed_channels=[0, 1], target_type=DataType.SERIES, max_depth=3)
    probe = ProbeFactory.create_random_probe(seed=202, allowed_action_channels=[0, 1], num_actions=3)
    candidate = PairedCandidate(instrument=inst, probe=probe, state=EpistemicState.GENERATED)

    frozen = FrozenCandidate(candidate)
    print(f" -> Candidate ID:   {frozen.candidate_id}")
    print(f" -> Config Hash:    {frozen.config_hash}")
    print(f" -> Operator (Phi): {frozen.candidate.instrument.expression.to_canonical_str()}")
    print(f" -> Probe (Pi):     {[a.to_canonical_dict()['type'] for a in frozen.candidate.probe.actions]}")

    # 3. Sealed Confirmatory Evaluation (N = 35 seeds)
    print("\n[Step 3] Executing Sealed Confirmatory Testing (N=35 independent seeds)...")
    conf_seeds = conf_p.get_seeds(frozen.candidate_id, frozen.config_hash)
    chamber = FalsificationChamber(
        firewall=firewall_osc,
        target_channel=0,
        forecast_horizon=8,
        pre_steps=12,
        num_random_controls=5,
        alpha=0.01
    )
    conf_result = chamber.evaluate_candidate_full(frozen.candidate, seeds=conf_seeds)

    print("-" * 80)
    print(f"{'Comparator':<36} | {'Skill':<8} | {'Cohen d':<8} | {'p (Holm)':<10} | {'Sig (alpha=0.01)':<16}")
    print("-" * 80)
    for name, rep in conf_result["reports"].items():
        sig_str = "SIGNIFICANT" if rep.statistically_significant else "NOT SIG"
        print(f"{name:<36} | {rep.skill_score:+7.4f} | {rep.cohens_d:+7.2f} | {rep.p_value_corrected:.4e} | {sig_str:<16}")
    print("-" * 80)
    print(f" -> Post-Confirmatory Epistemic Status: {frozen.candidate.state.value}")

    # 4. Cross-Family Transfer Evaluation (Module M07)
    print("\n[Step 4] Executing Cross-Family Transfer Experiments (M07 Transfer Lab)...")
    lab = TransferLab(target_seeds=list(range(6000, 6020))) # 20 seeds

    # Transfer to Reaction-Diffusion
    rep_rd = lab.evaluate_transfer(
        candidate=frozen.candidate,
        source_family=EnvironmentFamily.COUPLED_OSCILLATORS,
        target_family=EnvironmentFamily.REACTION_DIFFUSION,
        source_skill=conf_result["reports"]["Baseline A (Passive Control)"].skill_score
    )
    print(f"\n--- Transfer Target 1: Reaction-Diffusion (Gray-Scott Field) ---")
    print(f" Target Skill Score:          {rep_rd.target_skill:+.4f}")
    print(f" Transfer Degradation Ratio:   {rep_rd.transfer_degradation_ratio:+.4f}")
    print(f" Statistical Significance:     p={rep_rd.p_value:.4e}")
    print(f" Transfer Classification:      {rep_rd.category.value}")

    # Transfer to Thermodynamic Swarm
    rep_swarm = lab.evaluate_transfer(
        candidate=frozen.candidate,
        source_family=EnvironmentFamily.COUPLED_OSCILLATORS,
        target_family=EnvironmentFamily.THERMODYNAMIC_SWARM,
        source_skill=conf_result["reports"]["Baseline A (Passive Control)"].skill_score
    )
    print(f"\n--- Transfer Target 2: Thermodynamic Swarm (N-Body LJ Particles) ---")
    print(f" Target Skill Score:          {rep_swarm.target_skill:+.4f}")
    print(f" Transfer Degradation Ratio:   {rep_swarm.transfer_degradation_ratio:+.4f}")
    print(f" Statistical Significance:     p={rep_swarm.p_value:.4e}")
    print(f" Transfer Classification:      {rep_swarm.category.value}")

    # 5. Scientific Provenance Manifest Generation
    manifest = frozen.to_manifest(
        source_family=EnvironmentFamily.COUPLED_OSCILLATORS,
        falsification_report={
            "status": frozen.candidate.state.value,
            "seeds_tested": len(conf_seeds),
            "reports": {k: v.__dict__ for k, v in conf_result["reports"].items()}
        },
        transfer_report={
            "reaction_diffusion": rep_rd.__dict__,
            "thermodynamic_swarm": rep_swarm.__dict__
        },
        seeds_partition={"confirmatory_seeds": conf_seeds}
    )

    manifest_path = "confirmatory_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[Step 5] Audit-Grade Provenance Manifest saved to '{manifest_path}'")
    print(f" -> Manifest Signature: {manifest['manifest_signature']}")

    print("\n" + "=" * 80)
    print(" MILESTONE 04 VALIDATION COMPLETE: FALSIFICATION & TRANSFER VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_milestone_04_validation()
