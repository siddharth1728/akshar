# SENSEFORGE: Formal Research Hypotheses & Falsification Criteria

**Version:** 0.3.0-alpha  
**Phase:** 04 (Falsification Chamber & Transfer Lab)  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Primary Empirical Hypotheses

### Hypothesis 1: Intra-Family Active Measurement Discovery ($H_1$)

> **$H_1$ (Intra-Family Discovery):**  
> Within a procedural environment family $\mathcal{F}$, there exists at least one jointly evolved candidate instrument $\Psi = (\Phi, \Pi)$ whose predictive skill on future observable outcomes $y_{t+1:t+H}$ significantly exceeds that of:
> 1. Passive observation without intervention (Baseline A).
> 2. Conventional raw-channel rolling statistical features (Baseline B).
> 3. Matched random perturbation ensembles with identical energy and duration budgets (Baseline C).
> 4. Fixed heuristic impulse probes (Baseline D).
> 5. Component ablations: raw observation with evolved probe (Baseline F) and evolved operator with random probe (Baseline G).
>
> under a paired two-tailed Wilcoxon signed-rank test ($\alpha = 0.01$, Holm-Bonferroni corrected), with medium-to-large effect size (Cohen's $d \ge 0.50$) and strictly positive lower 95% bootstrap confidence interval, evaluated across at least 30 independent seeds in the Locked Test Partition.

---

### Hypothesis 2: Cross-Environment Generalization and Transfer ($H_2$)

> **$H_2$ (Cross-Environment Transfer):**  
> A subset of validated discovery candidates $\Psi^* \in \mathcal{G}_{\text{prov}}$ retains statistically significant predictive utility ($\Delta \text{Skill}_{\text{target}} \ge 0.10, p < 0.01$) when transferred without retraining or evolutionary modification:
> 1. Into out-of-distribution parameter regimes within the same family (e.g., altered non-linear damping, stiffness, or coupling).
> 2. Into structurally distinct procedural environment families with compatible observation/intervention dimensions (e.g., from Coupled Oscillators to Reaction-Diffusion or Thermodynamic Swarms).

---

## 2. Explicit Falsifiable Null Hypotheses

To prevent confirmation bias, SENSEFORGE explicitly establishes three adversarial null hypotheses:

### Null Hypothesis 1: Random Variation & Budget Artifact ($H_{0-1}$)

> **$H_{0-1}$:** Any observed predictive advantage of candidate $\Psi = (\Phi, \Pi)$ over passive observation is fully explained by random perturbation noise, numerical variance, or energetic budget disparities, such that Candidate E exhibits no statistically significant advantage over matched-energy random probe ensembles (Baseline C, $p \ge 0.01$) or sham interventions (Test F).

### Null Hypothesis 2: In-Sample Overfitting & Test Collapse ($H_{0-2}$)

> **$H_{0-2}$:** Any apparent predictive improvement observed during evolutionary exploration is an artifact of selection on finite training seeds, and the performance advantage drops to zero ($\Delta \text{Skill} \le 0$) when evaluated on the Locked Test Partition ($N \ge 30$).

### Null Hypothesis 3: Simulator-Specific Artifact & Evaluator Leakage ($H_{0-3}$)

> **$H_{0-3}$:** The discovered operator fails to capture any physical invariant, and its performance degrades completely ($\text{TDR} \le 0$) under parameter shifts (Test B), temporal surrogate phase-randomization (Test G), or cross-family transfer (Module M07).

---

## 3. Pre-Registered Falsification Decision Table

| Outcome Metric | Rejection of Null ($H_0$) / Acceptance Criteria | Classification Assigned |
| :--- | :--- | :--- |
| $\Delta \text{Skill}_{\text{locked}} \le 0.0$ or $p_{\text{adj}} \ge 0.01$ | Fails to reject $H_{0-1}$ or $H_{0-2}$. | **`REJECTED`** |
| $\Delta \text{Skill} > 0.0$ but $\le \Delta \text{Skill}_{\text{random}}$ | Advantage is due to generic perturbation, not evolved strategy. | **`REJECTED`** |
| $\Delta \text{Skill} > 0.0$ but $0.01 \le p_{\text{adj}} < 0.05$ | Evidence is statistically inconclusive. | **`INCONCLUSIVE`** |
| $\Delta \text{Skill} \ge 0.10$, $p_{\text{adj}} < 0.01$, $\text{CI}_{95, \text{low}} > 0$, beats Baselines A–G on Locked Partition ($N \ge 30$) | Rejects $H_{0-1}$ and $H_{0-2}$ within source family. | **`PROVISIONAL_DISCOVERY`** |
| Meets Provisional criteria AND transfers to distinct family $\mathcal{F}_{\text{target}}$ with $\Delta \text{Skill}_{\text{target}} \ge 0.10$ and $p < 0.01$ | Rejects $H_{0-3}$; demonstrates general physical invariance. | **`GENERALIZED_DISCOVERY`** |
