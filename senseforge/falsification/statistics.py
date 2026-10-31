"""
SENSEFORGE M06: Statistical Inference & Metric Calculation Engine
Implements MSE, MAE, predictive Negative Log-Likelihood, paired Wilcoxon tests,
bootstrap 95% confidence intervals, Cohen's d effect sizes, Holm-Bonferroni correction,
and temporal surrogate generators (circular time-shift / phase randomization).
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats
from dataclasses import dataclass


def compute_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Squared Error."""
    return float(np.mean((y_true - y_pred) ** 2))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_nll(y_true: np.ndarray, y_pred: np.ndarray, residual_var: Optional[float] = None) -> float:
    """
    Predictive Gaussian Negative Log-Likelihood (NLL):
    NLL = 0.5 * ln(2 * pi * sigma^2) + (y - y_hat)^2 / (2 * sigma^2)
    """
    res = y_true - y_pred
    var = residual_var if (residual_var is not None and residual_var > 1e-8) else max(1e-6, float(np.var(res)))
    nll = 0.5 * np.log(2.0 * np.pi * var) + np.mean(res ** 2) / (2.0 * var)
    return float(nll)


def compute_skill_score(base_loss: float, cand_loss: float) -> float:
    """
    Normalized Predictive Skill Score (Delta Skill):
    Positive score indicates candidate outperforms baseline.
    """
    return float((base_loss - cand_loss) / (base_loss + 1e-8))


def generate_temporal_surrogate(
    series: np.ndarray,
    method: str = "circular_shift",
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """
    Generates temporal null surrogate preserving first/second order statistics:
    - circular_shift: circular roll of time index destroying phase coherence with external inputs
    - phase_randomize: randomizes Fourier phase angles while preserving the exact power spectrum.
    """
    r = rng or np.random.default_rng(42)
    n = len(series)
    if n < 4:
        return series.copy()

    if method == "circular_shift":
        shift = int(r.integers(1, n - 1))
        return np.roll(series, shift)

    elif method == "phase_randomize":
        # Fourier phase randomization preserving amplitude spectrum
        fft_coeffs = np.fft.rfft(series)
        amplitudes = np.abs(fft_coeffs)
        # Random phase angles uniform in [-pi, pi]
        random_phases = r.uniform(-np.pi, np.pi, size=len(fft_coeffs))
        # Keep DC component and Nyquist component (if present) real
        random_phases[0] = 0.0
        if n % 2 == 0:
            random_phases[-1] = 0.0
        surrogate_fft = amplitudes * np.exp(1j * random_phases)
        return np.fft.irfft(surrogate_fft, n=n)

    else:
        raise ValueError(f"Unknown surrogate method: {method}")


@dataclass(frozen=True)
class StatisticalReport:
    """Rigorous empirical validation report for candidate vs baseline."""
    baseline_name: str
    n_seeds: int
    mean_baseline_loss: float
    mean_candidate_loss: float
    skill_score: float              # Delta Skill: (L_base - L_cand) / L_base
    cohens_d: float                 # Effect size
    p_value: float                  # Wilcoxon signed-rank p-value
    p_value_corrected: float        # Holm-Bonferroni corrected p-value
    ci_95_lower: float              # 95% Bootstrap CI lower bound
    ci_95_upper: float              # 95% Bootstrap CI upper bound
    statistically_significant: bool # True if p_corrected < alpha and CI_lower > 0


class StatisticalEngine:
    """Performs statistical inference over paired seed-level evaluation vectors."""

    @staticmethod
    def compute_bootstrap_ci(
        diffs: np.ndarray,
        num_resamples: int = 1000,
        alpha: float = 0.05,
        rng: Optional[np.random.Generator] = None
    ) -> Tuple[float, float]:
        """Computes empirical bootstrap confidence interval for mean difference."""
        r = rng or np.random.default_rng(42)
        n = len(diffs)
        if n < 2:
            return float(diffs[0]), float(diffs[0])

        boot_means = np.zeros(num_resamples)
        for i in range(num_resamples):
            sample = r.choice(diffs, size=n, replace=True)
            boot_means[i] = np.mean(sample)

        lower = float(np.percentile(boot_means, 100 * (alpha / 2)))
        upper = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
        return lower, upper

    @staticmethod
    def compute_cohens_d(cand_losses: np.ndarray, base_losses: np.ndarray) -> float:
        """
        Paired Cohen's d: positive d means candidate loss is lower than baseline loss.
        """
        diffs = base_losses - cand_losses
        sd = np.std(diffs, ddof=1)
        if sd < 1e-8:
            return 0.0
        return float(np.mean(diffs) / sd)

    @classmethod
    def evaluate_paired_test(
        cls,
        cand_losses: List[float],
        base_losses: List[float],
        baseline_name: str,
        alpha: float = 0.01,
        rng: Optional[np.random.Generator] = None
    ) -> StatisticalReport:
        """
        Executes paired non-parametric Wilcoxon signed-rank test, Cohen's d, and bootstrap CI.
        """
        c_arr = np.asarray(cand_losses, dtype=np.float64)
        b_arr = np.asarray(base_losses, dtype=np.float64)
        n = len(c_arr)
        assert len(b_arr) == n, "Candidate and baseline loss arrays must have identical length"

        diffs = b_arr - c_arr  # Positive diff = candidate outperforms baseline
        mean_base = float(np.mean(b_arr))
        mean_cand = float(np.mean(c_arr))
        skill = compute_skill_score(mean_base, mean_cand)

        d = cls.compute_cohens_d(c_arr, b_arr)
        ci_low, ci_high = cls.compute_bootstrap_ci(diffs, num_resamples=1000, alpha=alpha, rng=rng)

        # Wilcoxon signed-rank test
        if np.allclose(diffs, 0.0):
            p_val = 1.0
        else:
            try:
                res = stats.wilcoxon(b_arr, c_arr, alternative="greater")
                p_val = float(res.pvalue)
            except Exception:
                p_val = 1.0

        return StatisticalReport(
            baseline_name=baseline_name,
            n_seeds=n,
            mean_baseline_loss=mean_base,
            mean_candidate_loss=mean_cand,
            skill_score=skill,
            cohens_d=d,
            p_value=p_val,
            p_value_corrected=p_val,
            ci_95_lower=ci_low,
            ci_95_upper=ci_high,
            statistically_significant=bool(p_val < alpha and ci_low > 0.0),
        )

    @staticmethod
    def apply_holm_bonferroni(reports: List[StatisticalReport], alpha: float = 0.01) -> List[StatisticalReport]:
        """
        Applies Holm-Bonferroni step-down correction for multiple comparisons.
        """
        m = len(reports)
        if m == 0:
            return []

        sorted_indices = sorted(range(m), key=lambda i: reports[i].p_value)
        corrected_reports = list(reports)

        for rank, idx in enumerate(sorted_indices):
            rep = reports[idx]
            adj_p = min(1.0, rep.p_value * (m - rank))
            sig = bool(adj_p < alpha and rep.ci_95_lower > 0.0)

            corrected_reports[idx] = StatisticalReport(
                baseline_name=rep.baseline_name,
                n_seeds=rep.n_seeds,
                mean_baseline_loss=rep.mean_baseline_loss,
                mean_candidate_loss=rep.mean_candidate_loss,
                skill_score=rep.skill_score,
                cohens_d=rep.cohens_d,
                p_value=rep.p_value,
                p_value_corrected=adj_p,
                ci_95_lower=rep.ci_95_lower,
                ci_95_upper=rep.ci_95_upper,
                statistically_significant=sig,
            )

        return corrected_reports
