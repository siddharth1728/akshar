# SENSEFORGE: Statistical Analysis Methodology (Phase 04)

**Project:** SENSEFORGE  
**Classification:** Experimental Computational Science / Artificial Intelligence Research  
**Version:** `0.3.0-alpha`  
**Module:** M06 Statistical Engine (`senseforge/falsification/statistics.py`)  
**Status:** FULLY IMPLEMENTED & VERIFIED  

---

## 1. Mathematical Formulas & Estimators

All statistical evaluations in SENSEFORGE are grounded in formal mathematical definitions implemented in [`senseforge/falsification/statistics.py`](file:///c:/akshar/senseforge/falsification/statistics.py).

### 1.1 Loss Functions

Given ground truth observations $\mathbf{y} = (y_1, y_2, \dots, y_H)$ and model predictions $\widehat{\mathbf{y}} = (\widehat{y}_1, \widehat{y}_2, \dots, \widehat{y}_H)$ over forecast horizon $H$:

#### Mean Squared Error (MSE):
$$\text{MSE}(\mathbf{y}, \widehat{\mathbf{y}}) = \frac{1}{H} \sum_{t=1}^H (y_t - \widehat{y}_t)^2$$

#### Mean Absolute Error (MAE):
$$\text{MAE}(\mathbf{y}, \widehat{\mathbf{y}}) = \frac{1}{H} \sum_{t=1}^H |y_t - \widehat{y}_t|$$

#### Predictive Negative Log-Likelihood (NLL):
Assuming Gaussian predictive residuals with variance $\sigma^2$:
$$\text{NLL}(\mathbf{y}, \widehat{\mathbf{y}}; \sigma^2) = \frac{H}{2} \ln(2\pi \sigma^2) + \frac{1}{2\sigma^2} \sum_{t=1}^H (y_t - \widehat{y}_t)^2$$

### 1.2 Normalized Predictive Skill Score ($SS$):
To prevent scale dependency across environments and channel units, skill is evaluated relative to an explicit control baseline (e.g. Baseline A):
$$SS(\text{Candidate}, \text{Baseline}) = 1 - \frac{\overline{\text{Loss}}_{\text{Candidate}}}{\overline{\text{Loss}}_{\text{Baseline}} + \epsilon}$$
- $SS = 1.0$: Perfect zero-error forecast.
- $SS > 0.0$: Candidate outperforms baseline.
- $SS = 0.0$: Candidate is identical to baseline.
- $SS < 0.0$: Candidate is worse than baseline.

---

## 2. Hypothesis Testing & Effect Size Estimation

### 2.1 Paired Differences Formulation
Let $s_i \in \mathcal{S}$ denote independent evaluation seed $i \in \{1, \dots, N\}$. For each seed, let:
$$L_{\text{cand}}(s_i) = \text{MSE}(\Psi, s_i), \quad L_{\text{base}}(s_i) = \text{MSE}(\text{Baseline}, s_i)$$
The paired performance delta is:
$$\Delta_i = L_{\text{base}}(s_i) - L_{\text{cand}}(s_i)$$
A positive $\Delta_i > 0$ indicates the candidate achieved lower loss on seed $s_i$.

### 2.2 Non-Parametric Wilcoxon Signed-Rank Test
Because simulation losses across dynamical regimes are typically non-Gaussian and heavy-tailed, parametric Student's $t$-tests are invalid.

We employ the two-sided **Wilcoxon signed-rank test** on differences $D_i = L_{\text{cand}}(s_i) - L_{\text{base}}(s_i)$:
1. Filter out ties ($D_i = 0$).
2. Rank absolute differences $|D_i|$ in ascending order: $R_i = \text{Rank}(|D_i|)$.
3. Compute test statistic:
   $$W^+ = \sum_{D_i > 0} R_i, \quad W^- = \sum_{D_i < 0} R_i$$
   $$W = \min(W^+, W^-)$$
4. For $N \ge 20$, compute the asymptotic standard normal statistic:
   $$z = \frac{W - \frac{N(N+1)}{4}}{\sqrt{\frac{N(N+1)(2N+1)}{24}}}, \quad p = 2 \cdot (1 - \Phi(|z|))$$
   For one-sided testing (candidate superior to baseline), $p = 1 - \Phi(z_{\text{signed}})$.

### 2.3 Standardized Cohen's $d$ Effect Size
To measure the magnitude of improvement independent of sample size:
$$d = \frac{\overline{\Delta}}{s_{\Delta}}$$
Where $\overline{\Delta} = \frac{1}{N}\sum_{i=1}^N \Delta_i$ and $s_{\Delta} = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (\Delta_i - \overline{\Delta})^2}$.
- $|d| \ge 0.2$: Small effect
- $|d| \ge 0.5$: Medium effect
- $|d| \ge 0.8$: Large effect
- $|d| \ge 1.5$: Decisive effect

### 2.4 Empirical Bootstrap Confidence Intervals ($B = 1000$)
To avoid parametric assumptions for confidence intervals, the $95\%$ confidence interval of the mean difference $\overline{\Delta}$ is computed via non-parametric bootstrapping:
1. Sample $N$ items with replacement from $\{\Delta_1, \dots, \Delta_N\}$ to obtain bootstrap sample $\boldsymbol{\Delta}^{*b}$.
2. Compute sample mean $\overline{\Delta}^{*b}$.
3. Repeat $B = 1000$ times.
4. Set $\text{CI}_{95\%} = \left[ Q_{0.025}(\overline{\boldsymbol{\Delta}}^*), Q_{0.975}(\overline{\boldsymbol{\Delta}}^*) \right]$.

---

## 3. Multiple Comparison Correction: Holm-Bonferroni Method

When testing a candidate against $M$ simultaneous baselines (Baselines A, C, Sham, Temporal Null, Ablations F, G, H3; $M = 7$), uncorrected significance testing leads to severe Family-Wise Error Rate (FWER) inflation.

The **Holm-Bonferroni step-down procedure** controls the FWER at level $\alpha = 0.01$:
1. Sort raw $p$-values in ascending order: $p_{(1)} \le p_{(2)} \le \dots \le p_{(M)}$.
2. For each step $k \in \{1, \dots, M\}$:
   $$\alpha_k = \frac{\alpha}{M - k + 1}$$
3. Adjusted $p$-value:
   $$p_{(k)}^{\text{adj}} = \min\left(1.0, \max_{j \le k} \left( (M - j + 1) \cdot p_{(j)} \right)\right)$$
4. If $p_{(k)} \le \alpha_k$, comparison $k$ is declared statistically significant; otherwise, stop and reject significance for all remaining $j \ge k$.
