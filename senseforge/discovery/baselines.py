"""
SENSEFORGE M05: Baseline Evaluation Engine
Computes comparative performance against 4 required non-evolved baselines
under identical experimental budgets.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from senseforge.probes.actions import WaitAction, PerturbAction
from senseforge.probes.genome import ProbeGenome
from senseforge.probes.executor import ProbeExecutor, ExperimentTrajectory
from senseforge.genome.ast import ChannelNode, UnaryOpNode, BinaryOpNode
from senseforge.genome.candidate import InstrumentGenome
from senseforge.genome.evaluator import SafeEvaluator
from senseforge.discovery.candidate import PairedCandidate


def compute_nmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes Normalized Mean Squared Error (NMSE)."""
    var_y = np.var(y_true)
    if var_y < 1e-8:
        return float(np.mean((y_true - y_pred) ** 2))
    return float(np.mean((y_true - y_pred) ** 2) / (var_y + 1e-8))


class BaselineEvaluator:
    """
    Evaluates candidates against 4 reference baselines:
    Baseline A: Passive observation (zero action)
    Baseline B: Conventional statistical features over raw channels
    Baseline C: Random valid perturbation sequence
    Baseline D: Simple non-evolved probe + identity channel
    """

    @classmethod
    def evaluate_candidate_and_baselines(
        cls,
        candidate: PairedCandidate,
        firewall: Any,
        eval_seeds: List[int],
        target_channel: int = 0,
        forecast_horizon: int = 10,
        pre_steps: int = 15
    ) -> Dict[str, float]:
        """
        Evaluates candidate and all baselines across independent seeds.
        Returns a dictionary of mean NMSEs and information gain differentials.
        """
        evaluator = SafeEvaluator()
        total_action_ch = len(firewall.allowed_channels)

        cand_errors = []
        base_a_errors = []  # Passive
        base_b_errors = []  # Conventional stats
        base_c_errors = []  # Random probe
        base_d_errors = []  # Simple impulse

        # Baseline A probe: all wait steps of same duration
        probe_len = candidate.probe.total_duration
        probe_a = ProbeGenome(
            actions=[WaitAction(steps=max(1, probe_len))],
            reproducibility_seed=42
        )

        # Baseline D probe: single step impulse
        probe_d = ProbeGenome(
            actions=[PerturbAction(channel=0, magnitude=0.5, duration=2), WaitAction(steps=max(1, probe_len - 2))],
            reproducibility_seed=43
        )

        # Baseline C probe: randomized actions matching energy
        rng_c = np.random.default_rng(candidate.probe.reproducibility_seed)
        mag_c = max(0.1, candidate.probe.max_magnitude)
        probe_c = ProbeGenome(
            actions=[
                PerturbAction(channel=int(rng_c.choice(firewall.allowed_channels)),
                              magnitude=float(rng_c.uniform(0.1, mag_c)),
                              duration=max(1, probe_len // 2)),
                WaitAction(steps=max(1, probe_len - (probe_len // 2)))
            ],
            reproducibility_seed=44
        )

        for seed in eval_seeds:
            # 1. Execute Candidate (Baseline E)
            traj_e = ProbeExecutor.execute(
                firewall, candidate.probe, total_action_ch,
                pre_steps=pre_steps, post_steps=forecast_horizon, reset_seed=seed
            )
            # Evaluate measurement operator on pre+probe readings
            hist_obs = {
                ch: np.concatenate([traj_e.pre_readings[ch], traj_e.probe_readings[ch]])
                for ch in firewall.allowed_channels
            }
            res_e = evaluator.evaluate(candidate.instrument.expression, hist_obs)
            feat_e = res_e.value
            feat_val = float(feat_e[-1] if isinstance(feat_e, np.ndarray) else feat_e)
            y_target = traj_e.post_readings[target_channel][:forecast_horizon]

            # Linear prediction from evolved feature: simple gain projection
            # y_hat = feat_val
            err_e = compute_nmse(y_target, np.full_like(y_target, feat_val))
            cand_errors.append(err_e)

            # 2. Execute Baseline A (Passive)
            traj_a = ProbeExecutor.execute(
                firewall, probe_a, total_action_ch,
                pre_steps=pre_steps, post_steps=forecast_horizon, reset_seed=seed
            )
            y_target_a = traj_a.post_readings[target_channel][:forecast_horizon]
            raw_last_a = traj_a.pre_readings[target_channel][-1]
            err_a = compute_nmse(y_target_a, np.full_like(y_target_a, raw_last_a))
            base_a_errors.append(err_a)

            # 3. Evaluate Baseline B (Conventional stats on passive trajectory)
            # Moving average over last 5 steps
            win = min(5, len(traj_a.pre_readings[target_channel]))
            mean_b = float(np.mean(traj_a.pre_readings[target_channel][-win:]))
            err_b = compute_nmse(y_target_a, np.full_like(y_target_a, mean_b))
            base_b_errors.append(err_b)

            # 4. Execute Baseline C (Random intervention)
            traj_c = ProbeExecutor.execute(
                firewall, probe_c, total_action_ch,
                pre_steps=pre_steps, post_steps=forecast_horizon, reset_seed=seed
            )
            y_target_c = traj_c.post_readings[target_channel][:forecast_horizon]
            raw_last_c = traj_c.pre_readings[target_channel][-1]
            err_c = compute_nmse(y_target_c, np.full_like(y_target_c, raw_last_c))
            base_c_errors.append(err_c)

            # 5. Execute Baseline D (Simple impulse + identity measurement)
            traj_d = ProbeExecutor.execute(
                firewall, probe_d, total_action_ch,
                pre_steps=pre_steps, post_steps=forecast_horizon, reset_seed=seed
            )
            y_target_d = traj_d.post_readings[target_channel][:forecast_horizon]
            raw_last_d = traj_d.probe_readings[target_channel][-1] if len(traj_d.probe_readings[target_channel]) > 0 else traj_d.pre_readings[target_channel][-1]
            err_d = compute_nmse(y_target_d, np.full_like(y_target_d, raw_last_d))
            base_d_errors.append(err_d)

        # Average metrics
        nmse_cand = float(np.mean(cand_errors))
        nmse_a = float(np.mean(base_a_errors))
        nmse_b = float(np.mean(base_b_errors))
        nmse_c = float(np.mean(base_c_errors))
        nmse_d = float(np.mean(base_d_errors))

        # Information Gain Delta I relative to Passive Baseline A
        info_gain = float(np.clip((nmse_a - nmse_cand) / (nmse_a + 1e-6), -2.0, 2.0))
        diff_b = float(np.clip((nmse_b - nmse_cand) / (nmse_b + 1e-6), -2.0, 2.0))
        diff_c = float(np.clip((nmse_c - nmse_cand) / (nmse_c + 1e-6), -2.0, 2.0))

        # Robustness across seeds (inverse std of errors)
        robustness = float(1.0 / (np.std(cand_errors) + 0.1))

        return {
            "nmse_candidate": nmse_cand,
            "nmse_baseline_a": nmse_a,
            "nmse_baseline_b": nmse_b,
            "nmse_baseline_c": nmse_c,
            "nmse_baseline_d": nmse_d,
            "info_gain": info_gain,
            "diff_b": diff_b,
            "diff_c": diff_c,
            "robustness": robustness,
        }

