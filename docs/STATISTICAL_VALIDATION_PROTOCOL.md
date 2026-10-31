# SENSEFORGE: Statistical Validation Protocol & Inference Standards

**Version:** 0.3.0-alpha  
**Module:** M06 FALSIFICATION CHAMBER  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Estimator Definitions

### 1.1 Normalized Predictive Skill Score ($\Delta \text{Skill}$)

$$\Delta \text{Skill}(\Psi \mid \mathcal{B}) = \frac{\bar{\mathcal{L}}_{\mathcal{B}} - \bar{\mathcal{L}}_{\Psi}}{\bar{\mathcal{L}}_{\mathcal{B}} + \epsilon}$$

where $\mathcal{L}$ is Mean Squared Error (MSE) over the post-intervention observation trajectory.
- $\Delta \text{Skill} > 0$: Candidate outperforms baseline $\mathcal{B}$.
- $\Delta \text{Skill} = 1$: Perfect forecast ($\mathcal{L}_{\Psi} = 0$).
- $\Delta \text{Skill} < 0$: Candidate performs worse than baseline $\mathcal{B}$.

---

## 2. Hypothesis Testing & Uncertainty Quantification

### 2.1 Paired Wilcoxon Signed-Rank Test
Given paired error vectors $\{(\mathcal{L}_{\mathcal{B}, i}, \mathcal{L}_{\Psi, i})\}_{i=1}^N$ across $N \ge 30$ independent confirmatory seeds:
$$H_0: \text{Median}(\mathcal{L}_{\mathcal{B}} - \mathcal{L}_{\Psi}) \le 0 \quad \text{vs.} \quad H_1: \text{Median}(\mathcal{L}_{\mathcal{B}} - \mathcal{L}_{\Psi}) > 0$$
Evaluated with significance threshold $\alpha = 0.01$.

### 2.2 Holm-Bonferroni Multiple Comparison Correction
For $M=6$ simultaneous baseline and ablation comparisons:
$$p_{(k)} \le \frac{\alpha}{M - k + 1}$$
Guarantees Family-Wise Error Rate (FWER) control $\le 0.01$.

### 2.3 Non-Parametric Bootstrap Confidence Intervals (95% CI)
Computes $B=1000$ empirical resamples of mean paired differences $\Delta = \mathcal{L}_{\mathcal{B}} - \mathcal{L}_{\Psi}$.
A candidate is considered robust only if the lower bound satisfies:
$$\text{CI}_{95, \text{lower}} > 0.0$$
