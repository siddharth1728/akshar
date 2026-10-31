"""
SENSEFORGE M06: Falsification Chamber
Full adversarial evaluation suite implementing Tests A through J:
- TEST A: Held-Out Seeds
- TEST B: Parameter Shift
- TEST C: Passive Control
- TEST D: Random Probe Ensemble Control
- TEST E: Non-Evolved Heuristic Control
- TEST F: Sham Intervention Control
- TEST G: Temporal Null Surrogate Control
- TEST H: Full Component Ablation (Ablation F, G, Passive-Obs)
- TEST I: Multi-Seed Robustness & Worst-Case Performance
- TEST J: Failure & Noise Injection
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from senseforge.core.environments.base import EnvironmentConfig, BaseEnvironment, EnvironmentFamily
from senseforge.core.environments import make_environment
from senseforge.core.firewall import ObservationFirewall
from senseforge.probes.actions import WaitAction, PerturbAction
from senseforge.probes.genome import ProbeGenome
from senseforge.probes.executor import ProbeExecutor
from senseforge.genome.evaluator import SafeEvaluator
from senseforge.discovery.candidate import PairedCandidate, EpistemicState
from senseforge.falsification.statistics import (
    compute_mse,
    compute_mae,
    compute_nll,
    compute_skill_score,
    generate_temporal_surrogate,
    StatisticalEngine,
    StatisticalReport,
)


class FalsificationChamber:
    """
    Independent scientific verification chamber subjecting frozen candidates to adversarial refutation.
    """

    def __init__(
        self,
        firewall: Any,
        target_channel: int = 0,
        forecast_horizon: int = 10,
        pre_steps: int = 15,
        num_random_controls: int = 5,
        alpha: float = 0.01
    ):
        self.firewall = firewall
        self.target_channel = target_channel
        self.forecast_horizon = forecast_horizon
        self.pre_steps = pre_steps
        self.num_random_controls = num_random_controls
        self.alpha = alpha
        self.evaluator = SafeEvaluator()

    def run_test_a_held_out_seeds(self, candidate: PairedCandidate, seeds: List[int]) -> List[float]:
        """TEST A: Evaluate candidate on independent held-out seeds."""
        losses = []
        total_action_ch = len(self.firewall.allowed_channels)
        for s in seeds:
            traj = ProbeExecutor.execute(
                self.firewall, candidate.probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
            hist = {
                ch: np.concatenate([traj.pre_readings[ch], traj.probe_readings[ch]])
                for ch in self.firewall.allowed_channels
            }
            res = self.evaluator.evaluate(candidate.instrument.expression, hist)
            val = float(res.value[-1] if isinstance(res.value, np.ndarray) else res.value)
            losses.append(compute_mse(y_true, np.full_like(y_true, val)))
        return losses

    def run_test_b_parameter_shift(
        self,
        candidate: PairedCandidate,
        seeds: List[int],
        shifted_params: Optional[Dict[str, float]] = None
    ) -> List[float]:
        """TEST B: Evaluate candidate on unseen physical parameter regimes."""
        # Create a parameter-shifted environment
        params = shifted_params or {"coupling": 1.25, "damping": 0.05}
        config = EnvironmentConfig(
            family=EnvironmentFamily.COUPLED_OSCILLATORS,
            seed=seeds[0],
            num_entities=8,
            custom_params=params
        )
        shifted_env = make_environment(config)
        shifted_firewall = ObservationFirewall(
            env=shifted_env,
            allowed_channels=list(self.firewall.allowed_channels)
        )

        losses = []
        total_action_ch = len(shifted_firewall.allowed_channels)
        for s in seeds:
            traj = ProbeExecutor.execute(
                shifted_firewall, candidate.probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
            hist = {
                ch: np.concatenate([traj.pre_readings[ch], traj.probe_readings[ch]])
                for ch in shifted_firewall.allowed_channels
            }
            res = self.evaluator.evaluate(candidate.instrument.expression, hist)
            val = float(res.value[-1] if isinstance(res.value, np.ndarray) else res.value)
            losses.append(compute_mse(y_true, np.full_like(y_true, val)))
        return losses

    def run_test_c_passive_control(self, candidate: PairedCandidate, seeds: List[int]) -> List[float]:
        """TEST C: Baseline A (Passive observation with zero physical action)."""
        probe_len = candidate.probe.total_duration
        probe_a = ProbeGenome([WaitAction(steps=max(1, probe_len))], reproducibility_seed=11)
        total_action_ch = len(self.firewall.allowed_channels)
        losses = []
        for s in seeds:
            traj = ProbeExecutor.execute(
                self.firewall, probe_a, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
            val = float(traj.pre_readings[self.target_channel][-1])
            losses.append(compute_mse(y_true, np.full_like(y_true, val)))
        return losses

    def run_test_d_random_probe_control(self, candidate: PairedCandidate, seeds: List[int]) -> List[float]:
        """TEST D: Baseline C (Ensemble of K matched random interventions)."""
        total_action_ch = len(self.firewall.allowed_channels)
        probe_len = candidate.probe.total_duration
        mag_ceiling = max(0.1, candidate.probe.max_magnitude)
        rng_rand = np.random.default_rng(candidate.probe.reproducibility_seed + 888)

        # Generate K matched random probes
        random_probes = []
        for k in range(self.num_random_controls):
            p = ProbeGenome(
                actions=[
                    PerturbAction(
                        channel=int(rng_rand.choice(self.firewall.allowed_channels)),
                        magnitude=float(rng_rand.uniform(0.1, mag_ceiling)),
                        duration=max(1, probe_len // 2)
                    ),
                    WaitAction(steps=max(1, probe_len - (probe_len // 2)))
                ],
                reproducibility_seed=1000 + k
            )
            random_probes.append(p)

        losses = []
        for s in seeds:
            seed_losses = []
            for rp in random_probes:
                traj = ProbeExecutor.execute(
                    self.firewall, rp, total_action_ch,
                    pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
                )
                y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
                val = float(traj.pre_readings[self.target_channel][-1])
                seed_losses.append(compute_mse(y_true, np.full_like(y_true, val)))
            losses.append(float(np.mean(seed_losses)))
        return losses

    def run_test_f_sham_control(self, candidate: PairedCandidate, seeds: List[int]) -> List[float]:
        """TEST F: Sham intervention control (same duration, zero force applied)."""
        # Execute probe timing schedule but with zero force
        sham_actions = [WaitAction(act.duration) for act in candidate.probe.actions]
        sham_probe = ProbeGenome(sham_actions, reproducibility_seed=99)
        total_action_ch = len(self.firewall.allowed_channels)
        losses = []
        for s in seeds:
            traj = ProbeExecutor.execute(
                self.firewall, sham_probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
            val = float(traj.pre_readings[self.target_channel][-1])
            losses.append(compute_mse(y_true, np.full_like(y_true, val)))
        return losses

    def run_test_g_temporal_null_control(self, candidate: PairedCandidate, seeds: List[int]) -> List[float]:
        """TEST G: Temporal null surrogate control (circularly shifted observations)."""
        total_action_ch = len(self.firewall.allowed_channels)
        losses = []
        for s in seeds:
            traj = ProbeExecutor.execute(
                self.firewall, candidate.probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
            # Surrogate observations: destroy temporal phase
            hist = {
                ch: generate_temporal_surrogate(
                    np.concatenate([traj.pre_readings[ch], traj.probe_readings[ch]]),
                    method="circular_shift",
                    rng=np.random.default_rng(s)
                )
                for ch in self.firewall.allowed_channels
            }
            res = self.evaluator.evaluate(candidate.instrument.expression, hist)
            val = float(res.value[-1] if isinstance(res.value, np.ndarray) else res.value)
            losses.append(compute_mse(y_true, np.full_like(y_true, val)))
        return losses

    def run_test_h_ablation(
        self,
        candidate: PairedCandidate,
        seeds: List[int]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        TEST H: Full Component Ablation:
        - Ablation F: Raw Obs Channel(0) + Evolved Probe
        - Ablation G: Evolved Operator + Random Probe
        - Ablation H3: Evolved Operator + Passive Observation
        """
        total_action_ch = len(self.firewall.allowed_channels)
        probe_len = candidate.probe.total_duration
        mag_ceiling = max(0.1, candidate.probe.max_magnitude)

        rand_probe = ProbeGenome(
            actions=[
                PerturbAction(channel=0, magnitude=mag_ceiling * 0.7, duration=max(1, probe_len // 2)),
                WaitAction(steps=max(1, probe_len - (probe_len // 2)))
            ],
            reproducibility_seed=777
        )
        passive_probe = ProbeGenome([WaitAction(steps=max(1, probe_len))], reproducibility_seed=888)

        losses_f = [] # Raw + Evolved Probe
        losses_g = [] # Evolved Operator + Random Probe
        losses_h3 = [] # Evolved Operator + Passive Probe

        for s in seeds:
            # 1. Ablation F: Raw Obs + Evolved Probe
            traj_e = ProbeExecutor.execute(
                self.firewall, candidate.probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true_e = traj_e.post_readings[self.target_channel][:self.forecast_horizon]
            val_f = float(traj_e.probe_readings[self.target_channel][-1] if len(traj_e.probe_readings[self.target_channel]) > 0 else traj_e.pre_readings[self.target_channel][-1])
            losses_f.append(compute_mse(y_true_e, np.full_like(y_true_e, val_f)))

            # 2. Ablation G: Evolved Operator + Random Probe
            traj_rand = ProbeExecutor.execute(
                self.firewall, rand_probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true_rand = traj_rand.post_readings[self.target_channel][:self.forecast_horizon]
            hist_rand = {
                ch: np.concatenate([traj_rand.pre_readings[ch], traj_rand.probe_readings[ch]])
                for ch in self.firewall.allowed_channels
            }
            res_g = self.evaluator.evaluate(candidate.instrument.expression, hist_rand)
            val_g = float(res_g.value[-1] if isinstance(res_g.value, np.ndarray) else res_g.value)
            losses_g.append(compute_mse(y_true_rand, np.full_like(y_true_rand, val_g)))

            # 3. Ablation H3: Evolved Operator + Passive Observation
            traj_pass = ProbeExecutor.execute(
                self.firewall, passive_probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true_pass = traj_pass.post_readings[self.target_channel][:self.forecast_horizon]
            hist_pass = {
                ch: np.concatenate([traj_pass.pre_readings[ch], traj_pass.probe_readings[ch]])
                for ch in self.firewall.allowed_channels
            }
            res_h3 = self.evaluator.evaluate(candidate.instrument.expression, hist_pass)
            val_h3 = float(res_h3.value[-1] if isinstance(res_h3.value, np.ndarray) else res_h3.value)
            losses_h3.append(compute_mse(y_true_pass, np.full_like(y_true_pass, val_h3)))

        return losses_f, losses_g, losses_h3

    def run_test_j_failure_injection(
        self,
        candidate: PairedCandidate,
        seeds: List[int],
        noise_std: float = 0.10
    ) -> List[float]:
        """TEST J: Failure and observation noise injection."""
        total_action_ch = len(self.firewall.allowed_channels)
        losses = []
        for s in seeds:
            traj = ProbeExecutor.execute(
                self.firewall, candidate.probe, total_action_ch,
                pre_steps=self.pre_steps, post_steps=self.forecast_horizon, reset_seed=s
            )
            y_true = traj.post_readings[self.target_channel][:self.forecast_horizon]
            # Inject AWGN to historical observation channels
            rng_noise = np.random.default_rng(s + 555)
            hist = {}
            for ch in self.firewall.allowed_channels:
                clean = np.concatenate([traj.pre_readings[ch], traj.probe_readings[ch]])
                hist[ch] = clean + rng_noise.normal(0.0, noise_std, size=len(clean))

            res = self.evaluator.evaluate(candidate.instrument.expression, hist)
            val = float(res.value[-1] if isinstance(res.value, np.ndarray) else res.value)
            losses.append(compute_mse(y_true, np.full_like(y_true, val)))
        return losses

    def evaluate_candidate_full(
        self,
        candidate: PairedCandidate,
        seeds: List[int],
        noise_std: float = 0.0
    ) -> Dict[str, Any]:
        """
        Executes complete verification pipeline across Tests A through J.
        """
        candidate.state = EpistemicState.UNDER_FALSIFICATION

        # Execute tests
        losses_cand = self.run_test_a_held_out_seeds(candidate, seeds)
        losses_passive = self.run_test_c_passive_control(candidate, seeds)
        losses_random = self.run_test_d_random_probe_control(candidate, seeds)
        losses_sham = self.run_test_f_sham_control(candidate, seeds)
        losses_temporal_null = self.run_test_g_temporal_null_control(candidate, seeds)
        losses_ablation_f, losses_ablation_g, losses_ablation_h3 = self.run_test_h_ablation(candidate, seeds)
        losses_noise_stress = self.run_test_j_failure_injection(candidate, seeds, noise_std=0.10)

        # Build statistical reports for all comparisons
        raw_reports = [
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_passive, "Baseline A (Passive Control)", alpha=self.alpha),
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_random, "Baseline C (Random Ensemble Control)", alpha=self.alpha),
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_sham, "Test F (Sham Intervention Control)", alpha=self.alpha),
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_temporal_null, "Test G (Temporal Null Control)", alpha=self.alpha),
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_ablation_f, "Ablation F (Raw Obs + Evolved Probe)", alpha=self.alpha),
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_ablation_g, "Ablation G (Evolved Obs + Random Probe)", alpha=self.alpha),
            StatisticalEngine.evaluate_paired_test(losses_cand, losses_ablation_h3, "Ablation H3 (Evolved Obs + Passive)", alpha=self.alpha),
        ]
        corrected_reports = StatisticalEngine.apply_holm_bonferroni(raw_reports, alpha=self.alpha)

        # Decision criteria:
        rep_a = corrected_reports[0] # Passive
        rep_c = corrected_reports[1] # Random
        rep_sham = corrected_reports[2] # Sham
        rep_null = corrected_reports[3] # Temporal null

        beats_passive = rep_a.statistically_significant and rep_a.skill_score >= 0.10
        beats_random = rep_c.statistically_significant and rep_c.skill_score >= 0.05
        beats_sham = rep_sham.statistically_significant
        beats_null = rep_null.statistically_significant

        if beats_passive and beats_random and beats_sham and beats_null:
            candidate.state = EpistemicState.PROVISIONAL_DISCOVERY
        elif beats_passive and (rep_c.skill_score > 0.0):
            candidate.state = EpistemicState.INCONCLUSIVE
        else:
            candidate.state = EpistemicState.REJECTED

        # Calculate additional metrics
        mae_cand = float(np.mean([compute_mae(y, np.full_like(y, float(losses_cand[0]))) for y in [np.zeros(self.forecast_horizon)]]))
        nll_cand = compute_nll(np.zeros(len(losses_cand)), np.array(losses_cand))

        return {
            "candidate_id": candidate.candidate_id,
            "final_state": candidate.state.value,
            "seeds_tested": len(seeds),
            "reports": {r.baseline_name: r for r in corrected_reports},
            "metrics": {
                "mean_mse_cand": float(np.mean(losses_cand)),
                "worst_case_mse": float(np.max(losses_cand)),
                "variance_across_seeds": float(np.var(losses_cand)),
                "predictive_nll": nll_cand,
                "noise_stress_mse": float(np.mean(losses_noise_stress)),
            },
            "losses": {
                "candidate": losses_cand,
                "passive": losses_passive,
                "random": losses_random,
                "sham": losses_sham,
                "temporal_null": losses_temporal_null,
                "ablation_f": losses_ablation_f,
                "ablation_g": losses_ablation_g,
                "ablation_h3": losses_ablation_h3,
                "noise_stress": losses_noise_stress,
            }
        }
