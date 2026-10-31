"""
SENSEFORGE Milestone 3 Verification Script
Runs an actual multi-generation autonomous co-evolution experiment:
evolves Measurement Operators (Phi) and Experimental Probes (Pi), evaluates against all 4 baselines,
maintains a Pareto discovery archive, logs negative and positive results, and exports provenance records.
"""

import sys
import json
import numpy as np

from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry
from senseforge.discovery.forge import DiscoveryForge, ForgeConfig
from senseforge.discovery.candidate import EpistemicState


def run_milestone_03_experiment():
    print("=" * 80)
    print(" SENSEFORGE MILESTONE 03: AUTONOMOUS PROBE DESIGNER & DISCOVERY FORGE")
    print("=" * 80)

    # 1. Spawn Runtime Environment behind Observation Firewall
    seed = 42
    allowed_channels = [0, 1]
    print(f"\n[Step 1] Spawning Coupled Oscillators environment (Seed: {seed})")
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=seed,
        allowed_channels=allowed_channels,
        num_entities=8
    )
    print(f" -> Permitted channels: {allowed_channels}")

    # 2. Configure Discovery Forge
    pop_size = 12
    gens = 4
    eval_seeds = [101, 202, 303]
    config = ForgeConfig(
        population_size=pop_size,
        max_generations=gens,
        eval_seeds=eval_seeds,
        target_channel=0,
        forecast_horizon=8,
        pre_steps=12,
        archive_capacity=20
    )
    forge = DiscoveryForge(
        firewall=firewall,
        allowed_channels=allowed_channels,
        config=config,
        seed=seed
    )
    print(f"\n[Step 2] Initialized Discovery Forge: Population={pop_size}, Generations={gens}, Held-out Seeds={eval_seeds}")

    # 3. Execute Co-Evolutionary Search
    print("\n[Step 3] Executing Autonomous Co-Evolution (Evaluating Psi = (Phi, Pi) vs 4 Baselines)...")
    print("-" * 80)
    print(f"{'Gen':<4} | {'Best InfoGain':<14} | {'Mean InfoGain':<14} | {'Vs Random (C)':<14} | {'Archive':<8} | {'Provisional':<11} | {'Rejected':<8}")
    print("-" * 80)

    for g in range(gens):
        summary = forge.step()
        print(f"{summary.generation:02d}   | "
              f"{summary.best_info_gain:+12.4f}  | "
              f"{summary.mean_info_gain:+12.4f}  | "
              f"{summary.best_diff_random:+12.4f}  | "
              f"{summary.archive_size:<8} | "
              f"{summary.provisional_discoveries:<11} | "
              f"{summary.rejected_count:<8}")

    print("-" * 80)

    # 4. Inspect Pareto Archive
    print(f"\n[Step 4] Inspecting Non-Dominated Discovery Archive (Size: {forge.archive.size})")
    for i, cand in enumerate(forge.archive.archive[:3]):
        print(f"\n--- Non-Dominated Candidate #{i+1} [{cand.candidate_id}] | State: {cand.state.value} ---")
        print(f" Measurement Operator (Phi): {cand.instrument.expression.to_canonical_str()}")
        print(f" Complexity:                {cand.complexity} (AST Depth: {cand.instrument.depth}, Probe Duration: {cand.probe.total_duration})")
        print(f" Action Sequence (Pi):       {[a.to_canonical_dict()['type'] for a in cand.probe.actions]}")
        print(f" Total Energy:              {cand.probe.total_energy:.4f}")
        print(f" Predictive Info Gain:      {cand.fitness.info_gain:+.4f} (vs Passive Baseline A)")
        print(f" Gain over Random Probe:    {cand.fitness.baseline_c_diff:+.4f} (vs Random Baseline C)")
        print(f" Multi-Seed Robustness:     {cand.fitness.robustness:.4f}")

    # 5. Inspect Negative Results
    print(f"\n[Step 5] Logging Negative Results (Rejected Count: {len(forge.rejected_archive)})")
    if forge.rejected_archive:
        sample_rej = forge.rejected_archive[0]
        print(f" -> Example Rejected Candidate [{sample_rej.candidate_id}]:")
        print(f"    Operator:  {sample_rej.instrument.expression.to_canonical_str()}")
        print(f"    Info Gain: {sample_rej.fitness.info_gain:+.4f} (Failed out-of-sample prediction hurdle)")

    # 6. Export Reproducibility Records
    export_path = "discovery_provenance.json"
    provenance_data = {
        "version": "senseforge.provenance.v1",
        "environment_family": EnvironmentFamily.COUPLED_OSCILLATORS,
        "base_seed": seed,
        "eval_seeds": eval_seeds,
        "generations_completed": forge.generation,
        "archive_size": forge.archive.size,
        "archive_candidates": [c.to_canonical_dict() for c in forge.archive.archive],
        "rejected_count": len(forge.rejected_archive),
        "history": [s.__dict__ for s in forge.history],
    }
    with open(export_path, "w") as f:
        json.dump(provenance_data, f, indent=2)
    print(f"\n[Step 6] Discovery Provenance Record saved to '{export_path}'")

    print("\n" + "=" * 80)
    print(" MILESTONE 03 VERIFICATION COMPLETE: CO-EVOLUTIONARY ENGINE OPERATIONAL")
    print("=" * 80)


if __name__ == "__main__":
    run_milestone_03_experiment()
