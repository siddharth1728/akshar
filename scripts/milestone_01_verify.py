"""
SENSEFORGE Milestone 1 Verification Script
Demonstrates runtime environment generation, Observation Firewall enforcement,
active probe perturbation, anti-leakage protection, and deterministic replayability.
"""

import sys
import numpy as np
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry
from senseforge.core.firewall import FirewallSecurityViolation


def run_milestone_verification():
    print("=" * 70)
    print(" SENSEFORGE MILESTONE 01: ENVIRONMENT & OBSERVATION FIREWALL VERIFICATION")
    print("=" * 70)

    # 1. Spawning Sandboxed Environment
    print("\n[Step 1] Spawning procedurally generated environment: Coupled Oscillators")
    seed = 42
    allowed_channels = [0, 2]  # Only observe oscillator 0 and oscillator 2 positions
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=seed,
        allowed_channels=allowed_channels,
        num_entities=8,
        step_size=0.01
    )
    print(f" -> Environment successfully sealed inside firewall.")
    print(f" -> Permitted observation channels: {firewall.allowed_channels}")

    # 2. Initial Observation
    frame_0 = firewall.observe()
    print(f"\n[Step 2] Initial Observation Frame (t={frame_0.timestamp:.2f}, step={frame_0.step_index}):")
    print(f" -> Channel Readings: {frame_0.readings}")
    print(f" -> SHA256 Frame Hash: {frame_0.frame_hash}")

    # 3. Active Probing Intervention
    print("\n[Step 3] Executing active experimental probe perturbation: [0.8, -0.8]")
    frame_1 = firewall.probe([0.8, -0.8])
    print(f" -> Post-probe readings: {frame_1.readings}")
    print(f" -> New Frame Hash:     {frame_1.frame_hash}")

    # 4. Hidden State Isolation Check
    print("\n[Step 4] Adversarial Security Verification: Attempting hidden state exfiltration")
    leak_attempts = ["_env", "state", "positions", "velocities", "_k", "_beta"]
    blocked_count = 0
    for target in leak_attempts:
        try:
            _ = getattr(firewall, target)
            print(f" [CRITICAL FAILURE] Attribute '{target}' was exposed!")
            sys.exit(1)
        except FirewallSecurityViolation:
            blocked_count += 1

    print(f" -> {blocked_count}/{len(leak_attempts)} exfiltration attempts intercepted and blocked with FirewallSecurityViolation.")

    # 5. Deterministic Replay Verification
    print("\n[Step 5] Deterministic Replay Verification across independent instances")
    firewall_replay = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=seed,
        allowed_channels=allowed_channels,
        num_entities=8,
        step_size=0.01
    )
    frame_replay_0 = firewall_replay.observe()
    frame_replay_1 = firewall_replay.probe([0.8, -0.8])

    assert frame_0.frame_hash == frame_replay_0.frame_hash, "Initial hash mismatch!"
    assert frame_1.frame_hash == frame_replay_1.frame_hash, "Post-probe hash mismatch!"
    print(f" -> Replay hashes match byte-for-byte: {frame_1.frame_hash}")

    print("\n" + "=" * 70)
    print(" MILESTONE 01 VERIFICATION SUCCESSFUL: ALL SECURITY & NUMERICAL INVARIANTS MET")
    print("=" * 70)


if __name__ == "__main__":
    run_milestone_verification()

