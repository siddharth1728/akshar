# SENSEFORGE: Probe Genome Specification (M04)

**Version:** 0.2.0-alpha  
**Module:** M04 PROBEDESIGNER  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Ontological Definition of the Probe Genome (Π)

In scientific experimentation, observation is not merely a receptive act; it is an **active perturbation-response dialogue**. The Probe Genome ($\Pi$) formalizes the experimental intervention protocol applied to an environment.

Each candidate probe $\Pi$ is mathematically defined as:

$$\Pi = \left\langle \text{id}, \; \mathcal{A}, \; T_{\Pi}, \; \mathcal{E}_{\Pi}, \; u_{\max}, \; \Omega_{\text{act}}, \; \mathcal{H}_{\text{parents}}, \; g, \; \mathcal{H}_{\text{mut}}, \; s_{\text{gen}} \right\rangle$$

where:
- $\text{id} \in \Sigma^*$: Globally unique probe identifier (e.g., `probe_4821ca9012bf`).
- $\mathcal{A} = (a_1, a_2, \dots, a_k)$: Bounded sequence of typed action primitives.
- $T_{\Pi} = \sum_{i=1}^k \text{duration}(a_i)$: Total discrete time steps consumed by the unrolled schedule ($T_{\Pi} \le T_{\max}$).
- $\mathcal{E}_{\Pi} = \sum_{t=1}^{T_{\Pi}} \|\vec{u}_t\|^2$: Cumulative energetic expenditure of the intervention ($\mathcal{E}_{\Pi} \le \mathcal{E}_{\max}$).
- $u_{\max} = \max_t \|\vec{u}_t\|_\infty$: Peak intervention amplitude ($u_{\max} \le u_{\text{ceiling}}$).
- $\Omega_{\text{act}} \subset \mathbb{N}$: Subsets of actuator/intervention ports manipulated.
- $\mathcal{H}_{\text{parents}}$: Tuple of parent probe identifiers.
- $g \in \mathbb{N}$: Generational index.
- $\mathcal{H}_{\text{mut}}$: Audit trail of genetic variation operations applied.
- $s_{\text{gen}} \in \mathbb{Z}$: Deterministic random seed.

---

## 2. Typed Experimental Action Primitives

| Primitive | Parameters | Duration ($\Delta t$) | Energy Cost ($\Delta \mathcal{E}$) | Physical Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `WaitAction` | `steps: int` | `steps` | $0.0$ | Passive relaxation; permits natural unforced dynamics. |
| `ObserveAction` | `steps: int` | `steps` | $0.0$ | Dedicated observation window. |
| `PerturbAction` | `ch, mag, dur` | `dur` | $\text{mag}^2 \times \text{dur}$ | Constant directional force injection on actuator channel `ch`. |
| `ReversePerturbAction` | `ch, mag, dur` | `dur` | $\text{mag}^2 \times \text{dur}$ | Inverted force injection ($-\text{mag}$) to expose hysteresis/asymmetry. |
| `RepeatAction` | `action, count` | $\text{dur} \times \text{count}$ | $\mathcal{E}_{\text{sub}} \times \text{count}$ | Periodic excitation testing resonant modes. |

---

## 3. Evolutionary Variation Operators

1. **Random Generation (`create_random_probe`):** Synthesizes balanced sequences of wait steps and bounded perturbations within hard energy ceilings.
2. **Magnitude Mutation (`mutate_magnitude`):** Applies Gaussian noise to perturbation amplitudes ($\sigma = 0.15$), clamping within $[-u_{\text{ceiling}}, u_{\text{ceiling}}]$.
3. **Timing Mutation (`mutate_timing`):** Jitters durations and pauses to test response decay times.
4. **Sequence Mutation (`mutate_sequence`):** Inserts, deletes, or swaps action primitives.
5. **Crossover (`crossover`):** Splices action subsequences between two parent probes with automatic budget truncation.
6. **Simplification (`simplify_probe`):** Merges adjacent identical actions (e.g. consecutive waits) to eliminate redundancy.

