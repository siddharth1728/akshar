# SENSEFORGE: Comprehensive Scientific Audit of Phase 03

**Audit Date:** 2026-10-31  
**Auditor:** Principal Research Architect & Scientific Integrity Lead  
**Document Classification:** Pre-Implementation Mandatory Audit (Phase 04)  
**Status:** COMPLETE — Implementation and Methodological Defects Identified  

---

## 1. Executive Summary & Audit Mandate

In accordance with the Phase 04 directive, this audit traces every reported numerical result and methodological claim from Phase 03 directly back to its source code in `senseforge/discovery/`, `senseforge/probes/`, and `scripts/milestone_03_verify.py`.

The audit reveals that while the procedural simulation (M01), observation firewall (M02), and AST evaluator (M03) are architecturally sound, the evolutionary scoring loop in Phase 03 suffered from **five critical scientific and methodological defects**:
1. Target Trajectory Mismatch between candidate and baselines.
2. Trivial Identity Collapse of measurement operators.
3. Conflation of Normalized Skill Score with Shannon Mutual Information.
4. Conflation of Parameter Count / Duration with Algorithmic Complexity.
5. In-Sample Validation Bias (evaluating on search seeds).

These defects are documented below with mathematical proofs, source-code citations, and corrective requirements.

---

## 2. In-Depth Investigation of the Seven Specific Audit Items

### Item 1: Reported Information Gain Values Around +0.838
- **Source Code Trace:** `senseforge/discovery/baselines.py`, lines 135–138:
  ```python
  info_gain = float(np.clip((nmse_a - nmse_cand) / (nmse_a + 1e-6), -2.0, 2.0))
  ```
- **Finding:**
  1. The metric was calculated as $(NMSE_A - NMSE_{cand}) / NMSE_A$.
  2. In `baselines.py`, $NMSE_{cand}$ was evaluated on the *post-intervention trajectory* $y_{\text{post}}$ following probe $\Pi$.
  3. Conversely, $NMSE_A$ was evaluated on an *unperturbed passive trajectory* $y_{\text{post}, A}$.
  4. In `CoupledOscillators`, an unperturbed oscillator undergoing nonlinear damping has a decaying trajectory whose variance is small, making the denominator $Var(y_{\text{true}}) + 10^{-8}$ small and inflating $NMSE_A$ to values $\approx 10.0$.
  5. The candidate's point forecast residual happened to produce $NMSE_{cand} \approx 1.62$.
  6. Thus:
     $$\frac{10.0 - 1.62}{10.0} = 0.838$$
  7. **Conclusion:** The score $+0.838$ was a mathematical artifact of comparing Normalized Mean Squared Errors across two completely different physical trajectories. It is NOT Shannon Mutual Information, nor is it a valid paired prediction score.

---

### Item 2: Reported Improvements Over Passive and Random Controls
- **Source Code Trace:** `senseforge/discovery/baselines.py`, lines 58–73 and 106–122.
- **Finding:**
  1. **Passive Control (Baseline A):** The passive control used all `WaitAction` steps. But because the target $y_{\text{target}}$ for Candidate E was the response to perturbation $\Pi$, Baseline A was never asked to predict the response to $\Pi$; it predicted unperturbed relaxation.
  2. **Random Control (Baseline C):** A single random probe `probe_c` was instantiated per seed using `reproducibility_seed = candidate.probe.reproducibility_seed`. No ensemble averaging or variance estimation was performed.
  3. Because the random probe had arbitrary timing and single-channel pulses, its point forecast residual had high variance. The candidate was declared superior based on a single sample comparison without hypothesis testing or statistical confidence intervals.

---

### Item 3: Multi-Seed Robustness Value of 5.3888
- **Source Code Trace:** `senseforge/discovery/baselines.py`, lines 143–144:
  ```python
  robustness = float(1.0 / (np.std(cand_errors) + 0.1))
  ```
- **Finding:**
  1. The metric was defined purely as $\frac{1}{\text{std}(NMSE) + 0.1}$ across 3 seeds (`[101, 202, 303]`).
  2. If the errors were $[1.60, 1.62, 1.61]$, the standard deviation was $\approx 0.085$.
  3. Then:
     $$\frac{1}{0.085 + 0.1} \approx 5.3888$$
  4. **Pathology:** This metric rewards low variance of error, even if the error itself is catastrophic. A candidate that fails equally on all seeds receives a high "robustness" score.
  5. **Correction:** Robustness must be measured as lower-bound statistical performance under uncertainty (e.g., lower bound of the 95% bootstrap confidence interval of skill score across seeds).

---

### Item 4: Population Mean Fitness Improving Until Generation 2 and Declining in Generation 3
- **Reported Data:** Gen 0: $-1.5338$, Gen 1: $-1.0614$, Gen 2: $-0.3848$, Gen 3: $-0.6659$.
- **Source Code Trace:** `senseforge/discovery/forge.py`, lines 164–215.
- **Finding:**
  1. `DiscoveryForge` uses NSGA-II non-dominated sorting across 5 objectives.
  2. In Generation 2, elitist selection preserved top candidates, raising the mean.
  3. In Generation 3, tournament selection selected diverse boundary points on the Pareto frontier (candidates with low energy cost or low complexity, but negative info gain).
  4. Crossover (`GenomeFactory.crossover`) and subtree mutation (`mutate_subtree`) produced exploratory offspring with un-tuned constants, generating large negative skill scores (clipped to $-2.0$).
  5. Because the population size was small ($N=12$), a few exploratory candidates with $-2.0$ dragged the arithmetic mean from $-0.38$ down to $-0.66$.
  6. **Conclusion:** This decline was natural genetic drift and exploration on a multi-objective Pareto frontier, not a bug in the evolutionary loop itself.

---

### Item 5: Relationship Between Complexity 14 and AST Depth 1
- **Candidate Profile:**
  - Expression: `Channel(0)` (AST Depth: 1, Node Count: 1)
  - Action Sequence: `['Perturb', 'ReversePerturb', 'ReversePerturb']` (Duration: 12 steps)
  - Reported Complexity: 14
- **Source Code Trace:**
  - In `senseforge/genome/candidate.py`:
    ```python
    @property
    def complexity(self) -> int:
        return self.expression.node_count + self.expression.depth
    ```
    For `Channel(0)`: `node_count = 1`, `depth = 1` $\implies \text{instrument complexity} = 2$.
  - In `senseforge/discovery/candidate.py`:
    ```python
    @property
    def complexity(self) -> int:
        return self.instrument.complexity + self.probe.total_duration
    ```
    Total duration = $12$. Total candidate complexity = $2 + 12 = 14$.
- **Finding:**
  The calculation was algebraically consistent with the code, but conceptually flawed. Adding AST node counts (symbolic dimension) directly to discrete simulation steps (temporal dimension) conflates syntactic expression complexity with physical experiment duration. They must be tracked as independent objective dimensions.

---

### Item 6: Distinction Between Four Control Baselines and Evolved Candidate
- **Audit Table:**

| Baseline | Measurement $\Phi$ | Intervention $\Pi$ | Ground Truth Target $y$ | Evaluation Flaw in Phase 03 |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline A (Passive)** | Raw last obs | None (Wait only) | Unperturbed trajectory | Target trajectory differed from Candidate E |
| **Baseline B (Conventional)** | Moving Average 5 | None (Wait only) | Unperturbed trajectory | Target trajectory differed from Candidate E |
| **Baseline C (Random Probe)** | Raw last obs | Random pulse sequence | Perturbed by random probe | Only 1 random probe sampled; target differed |
| **Baseline D (Impulse)** | Raw probe obs | Single impulse pulse | Perturbed by impulse | Target differed from Candidate E |
| **Candidate E (Evolved)** | Evolved AST | Evolved Probe | Perturbed by evolved probe | Self-referential target |

- **Fatal Defect:** Every baseline was predicting a *different* target trajectory! A valid scientific test requires holding the target constant or evaluating predictability of an independent invariant property across identical initial conditions.

---

### Item 7: Observation, Duration, and Intervention Budgets
- **Finding:**
  1. **Duration:** Candidate probe durations varied between 4 and 16 steps depending on random generation. Baseline A matched the candidate duration, but Baseline D was fixed.
  2. **Energy Ceiling:** Probe energy was capped at 25.0, but candidates used anywhere from 1.0 to 18.0 energy, while Baseline C did not match the exact instantaneous energy profile.
  3. **Observation Access:** The Observation Firewall strictly prevented access to private simulator state. Both candidate and baselines received only permitted channel arrays. There was zero simulator attribute leakage.

---

## 3. Discovered Implementation Defects & Corrective Actions

| Defect ID | Description | Impact | Required Correction in Phase 04 |
| :--- | :--- | :--- | :--- |
| **DEF-01** | Different ground-truth targets for candidate and baselines in `baselines.py`. | Invalidates all relative skill scores. | Re-design evaluation protocol: all models must forecast the exact same observation target or latent dynamical response under controlled interventions. |
| **DEF-02** | Single random probe in Baseline C. | High variance, lack of statistical power. | Implement an ensemble of $K \ge 10$ matched random probes with duration and energy ceilings. |
| **DEF-03** | Conflating prediction skill with mutual information. | Scientific misnomer violating DPI. | Explicitly report Normalized Predictive Skill Score ($\Delta \text{Skill}$), MSE, and MAE. Reserve mutual information for formal entropy estimators. |
| **DEF-04** | Combining AST complexity and probe duration into a single scalar. | Obscures separate physical and symbolic costs. | Separate into `symbolic_complexity` ($\text{nodes} + \text{depth}$) and `experimental_cost` ($\text{duration} + \text{energy}$). |
| **DEF-05** | Reuse of evaluation seeds `[101, 202, 303]` during search. | In-sample selection bias. | Implement 3-tier strictly disjoint seed partitions: Exploration, Validation, and Locked Test ($N \ge 30$). |
| **DEF-06** | Lack of component ablations. | Cannot isolate whether $\Phi$ or $\Pi$ drives performance. | Implement Baseline F ($\text{Raw} + \Pi$) and Baseline G ($\Phi + \Pi_{\text{rand}}$). |

---

## 4. Conclusion

The Phase 03 results must be treated as **exploratory search artifacts** rather than verified scientific discoveries. The Falsification Chamber (M06) and Transfer Lab (M07) in Phase 04 must implement strict baseline reconstruction, component ablations, locked confirmatory testing ($N \ge 30$), and cross-family transfer without data leakage.
