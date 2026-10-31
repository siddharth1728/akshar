"""
SENSEFORGE M04: Probe Executor
Executes experimental probe schedules against Observation Firewalls
with strict episode isolation and baseline tracking.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

from senseforge.core.firewall import ObservationFirewall
from senseforge.core.process_firewall import ProcessObservationFirewall
from senseforge.probes.genome import ProbeGenome


@dataclass(frozen=True)
class ExperimentTrajectory:
    """Complete experimental observation trajectory generated during a probe run."""
    pre_readings: Dict[int, np.ndarray]
    probe_readings: Dict[int, np.ndarray]
    post_readings: Dict[int, np.ndarray]
    full_readings: Dict[int, np.ndarray]
    applied_actions: List[List[float]]
    total_energy: float
    duration: int
    timestamps: List[float]


class ProbeExecutor:
    """Executes a probe protocol on an isolated environment."""

    @staticmethod
    def execute(
        firewall: Any,
        probe: ProbeGenome,
        total_action_channels: int,
        pre_steps: int = 15,
        post_steps: int = 15,
        reset_seed: Optional[int] = None
    ) -> ExperimentTrajectory:
        """
        Executes an experimental probe episode with clean reset to guarantee isolation.
        """
        # 1. Clean reset for episode isolation
        initial_frame = firewall.reset(new_seed=reset_seed)
        channels = firewall.allowed_channels

        # Buffers
        full_buffers: Dict[int, List[float]] = {ch: [initial_frame.readings[i]] for i, ch in enumerate(channels)}
        pre_buffers: Dict[int, List[float]] = {ch: [initial_frame.readings[i]] for i, ch in enumerate(channels)}
        probe_buffers: Dict[int, List[float]] = {ch: [] for ch in channels}
        post_buffers: Dict[int, List[float]] = {ch: [] for ch in channels}
        applied_actions: List[List[float]] = []
        timestamps: List[float] = [initial_frame.timestamp]

        # 2. Pre-intervention baseline collection (zero perturbation)
        for _ in range(pre_steps):
            frame = firewall.probe(None)
            timestamps.append(frame.timestamp)
            for i, ch in enumerate(channels):
                val = frame.readings[i]
                pre_buffers[ch].append(val)
                full_buffers[ch].append(val)

        # 3. Apply unrolled probe perturbation schedule
        unrolled_schedule = probe.unroll(total_action_channels)
        for act_vec in unrolled_schedule:
            applied_actions.append(act_vec)
            frame = firewall.probe(act_vec)
            timestamps.append(frame.timestamp)
            for i, ch in enumerate(channels):
                val = frame.readings[i]
                probe_buffers[ch].append(val)
                full_buffers[ch].append(val)

        # 4. Post-intervention relaxation window (zero perturbation)
        for _ in range(post_steps):
            frame = firewall.probe(None)
            timestamps.append(frame.timestamp)
            for i, ch in enumerate(channels):
                val = frame.readings[i]
                post_buffers[ch].append(val)
                full_buffers[ch].append(val)

        # Compute actual applied energy
        energy = float(sum(np.sum(np.square(vec)) for vec in applied_actions)) if applied_actions else 0.0

        return ExperimentTrajectory(
            pre_readings={ch: np.array(vals) for ch, vals in pre_buffers.items()},
            probe_readings={ch: np.array(vals) for ch, vals in probe_buffers.items()},
            post_readings={ch: np.array(vals) for ch, vals in post_buffers.items()},
            full_readings={ch: np.array(vals) for ch, vals in full_buffers.items()},
            applied_actions=applied_actions,
            total_energy=energy,
            duration=len(timestamps),
            timestamps=timestamps,
        )

