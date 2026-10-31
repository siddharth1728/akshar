# SENSEFORGE: Experimental Protocol and Falsification Standards

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Ground Rules for Scientific Integrity

To prevent the common failure modes of automated discovery—such as data leakage, overfitting to noise, circular verification, and confirmation bias—all SENSEFORGE experiments must adhere strictly to the following five operational rules:

1. **Firewall Isolation:** The discovery loop must never inspect, receive, or reference private environment state, random seeds, hidden parameters, or future time steps. All interactions must proceed through typed, opaque observation vectors and probe actions.
2. **Deterministic Replayability:** Every experiment must be fully reproducible from a single composite specification: `(Environment_ID, Environment_Seed, Instrument_Genome, Probe_Genome, Evaluation_Config)`.
3. **Mandatory Baseline Comparison:** No candidate instrument may be accepted unless it demonstrates statistically superior performance over three standard baselines:
   - **Baseline 0 (Raw Observation Identity):** Predicting directly from the instantaneous raw measurement $\Omega_0(S_t)$.
   - **Baseline 1 (Uniform Lag Embedding):** Classical Takens-style delay coordinates $[y_t, y_{t-\tau}, \dots, y_{t-(k-1)\tau}]$.
   - **Baseline 2 (Linear Autoregressive/PCA Model):** Standard ridge regression on lagged raw channels.
4. **Permutation & Null Hypothesis Testing:** Every candidate must be evaluated against a phase-randomized or observation-shuffled null surrogate to verify that performance gain is not due to random correlation.
5. **Epistemic Labeling:** Discoveries must be classified according to empirical evidence:
   - `REJECTED`: Fails out-of-sample or null-model tests ($p \ge 0.01$).
   - `INCONCLUSIVE`: Demonstrates marginal improvement but fails complexity penalty or robustness bounds.
   - `PROVISIONAL_DISCOVERY`: Passes all in-family held-out seeds with statistically significant information gain ($p < 0.01$).
   - `GENERALIZED_DISCOVERY`: Passes out-of-family transfer evaluation in at least one distinct environment family without retraining.

---

## 2. Quantitative Evaluation Metrics

### 2.1 Information Gain Metric ($\Delta \mathcal{I}$)
We evaluate the predictive utility of an instrument $\Psi = (\Phi, \Pi)$ by measuring the reduction in forecast uncertainty over future observation trajectories $\vec{y}_{t+1:t+H}$:

$$\Delta \mathcal{I}(\Psi) = \frac{\mathcal{L}_{\text{baseline}} - \mathcal{L}_{\Psi}}{\mathcal{L}_{\text{baseline}}}$$

where $\mathcal{L}$ is normalized mean squared error (NMSE) or negative log-likelihood under a Gaussian process or ridge regressor trained strictly on historical observations emitted by $\Psi$.

### 2.2 Complexity Regularization & Pareto Ranking
To prevent operator bloat, the fitness function incorporates a Pareto-optimal multi-objective formulation:

$$\mathcal{F}(\Psi) = \left( \Delta \mathcal{I}(\Psi), \; -\mathcal{C}(\Phi), \; -\mathcal{E}(\Pi), \; \mathcal{R}(\Psi) \right)$$

where:
- $\mathcal{C}(\Phi)$: Syntactic complexity (node count + operation depth of the expression DAG).
- $\mathcal{E}(\Pi)$: Energetic cost of the probe sequence (cumulative action amplitude).
- $\mathcal{R}(\Psi)$: Robustness score across noise-perturbed observation regimes.

### 2.3 Statistical Significance Criteria
- **Sample Size:** $N \ge 30$ independent rollouts across held-out seeds.
- **Hypothesis Test:** Wilcoxon signed-rank test comparing candidate residuals against baseline residuals.
- **Significance Threshold:** $\alpha = 0.01$ with Bonferroni correction for multiple hypothesis testing across generations.

---

## 3. Four-Phase Validation Pipeline

```
[ Candidate Instrument Genome Ψ ]
             │
             ▼
[ Phase 1: In-Sample Fitness (Screening) ] ──── Fail ───► [ REJECT: Insufficient Signal ]
             │ Pass
             ▼
[ Phase 2: Held-Out Seed Generalization ] ──── Fail ───► [ REJECT: Overfit to Initial Conditions ]
             │ Pass
             ▼
[ Phase 3: Null Hypothesis & Permutation ] ─── Fail ───► [ REJECT: Spurious Correlation ]
             │ Pass
             ▼
[ Phase 4: Cross-Family Transfer Testing ] ─── Fail ───► [ CLASSIFY: In-Family Provisional Discovery ]
             │ Pass
             ▼
[ CLASSIFY: Cross-Family Generalized Discovery ]
```

