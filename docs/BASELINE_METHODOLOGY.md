# SENSEFORGE: Baseline Methodology & Comparative Controls

**Version:** 0.2.0-alpha  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. The Five Comparative Baselines

To guard against false claims of scientific discovery, every candidate $\Psi = (\Phi, \Pi)$ is continuously falsified against four reference baselines evaluated on identical seeds and computational budgets:

### Baseline A: Passive Observation
- **Intervention:** Zero action ($\vec{u}_t = \vec{0}$) for the full episode duration.
- **Hypothesis Tested:** Does actively perturbing the system provide an advantage over passively watching natural decay?

### Baseline B: Conventional Statistical Summaries
- **Intervention:** Zero action ($\vec{u}_t = \vec{0}$).
- **Feature Extractor:** Moving average ($\text{MA}_5$), moving variance, and delay coordinates over raw channels.
- **Hypothesis Tested:** Can the candidate outperform standard time-series signal processing methods?

### Baseline C: Random Valid Perturbations
- **Intervention:** Random action sequence matching the duration and energy ceiling of the candidate probe.
- **Hypothesis Tested:** Is the discovery due to the *structured timing and direction* of the probe, or simply white noise excitation?

### Baseline D: Simple Non-Evolved Instrument
- **Intervention:** Standard single-step impulse pulse.
- **Measurement:** Instantaneous raw observation channel.
- **Hypothesis Tested:** Does the co-evolved composite instrument outperform trivial engineering heuristics?

### Baseline E: Co-Evolved Discovery Candidate $\Psi = (\Phi, \Pi)$
- The autonomous pairing of evolved measurement operator $\Phi$ and structured probe sequence $\Pi$.

---

## 2. Epistemic Classification Thresholds

| Classification | Mandatory Empirical Criteria |
| :--- | :--- |
| `REJECTED` | $\Delta \mathcal{I} \le 0.0$ (Candidate fails to improve over passive baseline). |
| `INCONCLUSIVE` | $\Delta \mathcal{I} > 0.0$ but $\Delta_C \le 0.05$ (Improvement does not significantly exceed random noise). |
| `PROVISIONAL_DISCOVERY` | $\Delta \mathcal{I} > 0.10$ AND $\Delta_C > 0.05$ across all held-out evaluation seeds with $\text{Robustness} > 1.0$. |
| `GENERALIZED_DISCOVERY` | Reserved for Phase 04 cross-family transfer across distinct physical analogies. |

