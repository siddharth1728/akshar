# SENSEFORGE: Discovery Forge Architecture (M05)

**Version:** 0.2.0-alpha  
**Module:** M05 DISCOVERYFORGE  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Dual-Genome Co-Evolution Paradigm

Module M05 (`DISCOVERYFORGE`) maintains the co-evolution of two symbiotic populations:

$$\text{Population A (Operators)}: \{\Phi_1, \dots, \Phi_N\} \quad \times \quad \text{Population B (Probes)}: \{\Pi_1, \dots, \Pi_N\}$$

bound into paired discovery candidates:

$$\Psi_i = \left(\Phi_i, \; \Pi_i\right)$$

```
                                [ DISCOVERY FORGE ENGINE ]
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
          [ Population A: Operators (Φ) ]               [ Population B: Probes (Π) ]
          - Typed Expression Trees                      - Action Primitives
          - Subtree Mutation                            - Sequence Mutation
          - Operator Swaps                              - Magnitude / Timing Jitter
                      │                                             │
                      └──────────────────────┬──────────────────────┘
                                             ▼
                             [ Paired Candidate: Ψ = (Φ, Π) ]
                                             │
                                             ▼
                          [ Baseline Evaluator across Held-Out Seeds ]
                          ├── vs Baseline A (Passive Observation)
                          ├── vs Baseline B (Conventional Summaries)
                          ├── vs Baseline C (Random Probe Control)
                          └── vs Baseline D (Simple Impulse Probe)
                                             │
                                             ▼
                             [ Multi-Objective Pareto Sorting ]
                             ├── Objective 1: Info Gain (ΔI)
                             ├── Objective 2: Gain over Random (Δ_C)
                             ├── Objective 3: Multi-Seed Robustness
                             ├── Objective 4: Complexity Regularization
                             └── Objective 5: Energy Efficiency
                                             │
                                             ▼
                              [ Bounded Pareto Archive (N ≤ 50) ]
```

---

## 2. Multi-Objective Pareto Optimization (NSGA-II)

Arbitrary scalar fitness weighting inevitably leads to pathological compromises (e.g., sacrificing all predictive accuracy to minimize expression length). SENSEFORGE adopts **Fast Non-Dominated Sorting (NSGA-II)** with:

1. **Non-Dominated Front Partitioning ($F_0, F_1, \dots$):** Front $F_0$ contains all mutually non-dominated solutions.
2. **Crowding Distance Diversity:** Candidates on sparse regions of the objective surface are prioritized to prevent premature convergence on a single sub-optimal strategy.
3. **Bounded Pareto Archive:** Preserves the global Pareto discovery frontier across generations.

