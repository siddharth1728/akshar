# SENSEFORGE: Safe Evaluation Model

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Zero Arbitrary Code Execution Policy

SENSEFORGE strictly bans the execution of dynamic strings via `eval()`, `exec()`, or Python bytecode generation (`compile()`). Candidate instruments are represented exclusively as **declarative Abstract Syntax Trees** interpreted by `SafeEvaluator`.

This guarantees:
1. **No System Calls:** Candidate expressions cannot read/write files, open network sockets, or launch processes.
2. **No Introspection:** Expressions cannot access Python globals, locals, frame inspect objects, or simulator instances.
3. **Deterministic Output:** Given an identical observation array, an expression evaluates to byte-for-byte identical values across all runs.

---

## 2. Resource Budgeting & Computational Constraints

Every evaluation is governed by an explicit `EvaluationConfig`:

$$\mathcal{B} = \left\langle D_{\max}, \; N_{\max}, \; W_{\max}, \; \tau_{\max}, \; \text{Ops}_{\max}, \; \epsilon_{\text{div}} \right\rangle$$

| Parameter | Default Value | Security Objective |
| :--- | :--- | :--- |
| **Max Depth ($D_{\max}$)** | 8 | Prevents stack overflow and deep recursion. |
| **Max Node Count ($N_{\max}$)** | 64 | Bounds Kolmogorov complexity and genetic code bloat. |
| **Max Window ($W_{\max}$)** | 64 | Bounds temporal memory consumption. |
| **Max Tau ($\tau_{\max}$)** | 32 | Bounds historical buffer requirements. |
| **Max Operations ($\text{Ops}_{\max}$)** | 10,000 | Halts computationally pathological trees. |
| **Division Epsilon ($\epsilon_{\text{div}}$)** | $10^{-6}$ | Regularizes protected division to prevent zero-division crashes. |

### Operational Step Counting
Every node evaluation increments an internal operation counter:
- Leaf evaluations increment by 1.
- Vectorized operations increment by the length of the slice processed.
- If the cumulative count exceeds $\text{Ops}_{\max}$, execution terminates immediately with `EvaluationBudgetExceededError`.

---

## 3. Numerical Guardrails

1. **Protected Division (`DivSafe`):**
   $$\text{DivSafe}(a, b) = \frac{a}{b + \text{sign}(b + 10^{-12}) \cdot \epsilon_{\text{div}}} \quad \text{when } |b| < \epsilon_{\text{div}}$$
2. **Exponential Clamping:** In `Sigmoid(x)`, $x$ is clipped to $[-50.0, 50.0]$ before computing $1 / (1 + e^{-x})$, preventing floating-point overflow.
3. **NaN / Inf Detection:** Intermediate arrays and scalar results are checked via `np.isnan()` and `np.isinf()`. Any occurrence raises `EvaluationNumericalError`, rejecting the candidate instrument.

