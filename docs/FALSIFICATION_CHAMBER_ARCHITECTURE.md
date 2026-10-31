# SENSEFORGE: Falsification Chamber Architecture (M06)

**Version:** 0.3.0-alpha  
**Module:** M06 FALSIFICATION CHAMBER  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Architectural Philosophy

The primary objective of the Falsification Chamber is **adversarial refutation**. In automated scientific discovery, search heuristics naturally exploit peculiarities, noise correlations, and in-sample artifacts.

Module M06 operates strictly downstream of candidate selection, acting as an independent, unsympathetic falsifier:

```
[ Frozen Candidate Ψ = (Φ, Π) ]
               │
               ▼
┌────────────────────────────────────────────────────────┐
│               M06 FALSIFICATION CHAMBER                │
│                                                        │
│  [ Baseline Repertoire ]                               │
│  ├── Baseline A: Passive Observation (Zero Action)     │
│  ├── Baseline B: Conventional Rolling Statistics       │
│  ├── Baseline C: Random Intervention Ensemble (K ≥ 5)  │
│  ├── Baseline D: Simple Impulse Heuristic              │
│  ├── Baseline E: Evolved Pair (Candidate)              │
│  ├── Ablation F: Raw Obs + Evolved Probe               │
│  └── Ablation G: Evolved Obs + Random Probe            │
│                                                        │
│  [ Statistical Inference Pipeline ]                    │
│  ├── Paired Seed Differences (Δ_i = L_base - L_cand)   │
│  ├── Empirical Bootstrap 95% Confidence Intervals      │
│  ├── Non-Parametric Wilcoxon Signed-Rank Test          │
│  ├── Holm-Bonferroni Family-Wise Error Correction      │
│  └── Standardized Cohen's d Effect Size                │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
[ Fail Confirmatory / Ablation ]   [ Pass Confirmatory Criteria ]
             │                                   │
             ▼                                   ▼
        [ REJECTED ]                   [ PROVISIONAL_DISCOVERY ]
```

---

## 2. Component Ablations (Baselines F and G)

To determine which component of $\Psi = (\Phi, \Pi)$ is responsible for performance:
- **Ablation F ($\text{Channel}(0) + \Pi$):** Replaces the evolved mathematical operator with the raw instantaneous observation channel, keeping the evolved probe $\Pi$. If Ablation F performs as well as Candidate E, then **the operator $\Phi$ is redundant** and adds no value beyond raw observation.
- **Ablation G ($\Phi + \Pi_{\text{random}}$):** Retains the evolved operator $\Phi$ but couples it with an arbitrary random perturbation. If Candidate E does not beat Ablation G, then **the probe $\Pi$ is not tuned to the measurement**.
