# SENSEFORGE: Measurement AST Type System

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Type Space

The SENSEFORGE measurement language defines two fundamental data types:

$$\mathcal{T} = \{\text{SCALAR}, \text{SERIES}\}$$

- **`SCALAR` ($\mathbb{R}$):** A zero-dimensional continuous real number (e.g., summary statistics, constant scale factors, correlation coefficients).
- **`SERIES` ($\mathbb{R}^T$):** A one-dimensional, time-ordered sequence of real values corresponding to observation steps.

---

## 2. Typing Judgment Rules

We formalize typing using standard deduction rules:

### Terminals

$$\frac{i \in \mathbb{N}}{\Gamma \vdash \text{Channel}(i) : \text{SERIES}} \quad (\text{T-Channel})$$

$$\frac{c \in \mathbb{R}}{\Gamma \vdash \text{Constant}(c) : \text{SCALAR}} \quad (\text{T-Constant})$$

### Temporal Operations

$$\frac{\Gamma \vdash e : \text{SERIES} \quad \tau \in \mathbb{N}^+}{\Gamma \vdash \text{Diff}(e, \tau) : \text{SERIES}} \quad (\text{T-Diff})$$

$$\frac{\Gamma \vdash e : \text{SERIES} \quad \tau \in \mathbb{N}^+}{\Gamma \vdash \text{Lag}(e, \tau) : \text{SERIES}} \quad (\text{T-Lag})$$

$$\frac{\Gamma \vdash e : \text{SERIES} \quad w \in \mathbb{N}^+}{\Gamma \vdash \text{RollingMean}(e, w) : \text{SERIES}} \quad (\text{T-RollingMean})$$

### Statistical Collapsing

$$\frac{\Gamma \vdash e : \text{SERIES}}{\Gamma \vdash \text{Mean}(e) : \text{SCALAR}} \quad (\text{T-Mean})$$

$$\frac{\Gamma \vdash e_1 : \text{SERIES} \quad \Gamma \vdash e_2 : \text{SERIES}}{\Gamma \vdash \text{Covariance}(e_1, e_2) : \text{SCALAR}} \quad (\text{T-Covariance})$$

### Arithmetic Broadcasting

$$\frac{\Gamma \vdash e_1 : \sigma \quad \Gamma \vdash e_2 : \sigma}{\Gamma \vdash \text{Op}(e_1, e_2) : \sigma} \quad \text{for } \text{Op} \in \{\text{Add}, \text{Sub}, \text{Mul}, \text{DivSafe}\}$$

$$\frac{\Gamma \vdash e_1 : \text{SERIES} \quad \Gamma \vdash e_2 : \text{SCALAR}}{\Gamma \vdash \text{Op}(e_1, e_2) : \text{SERIES}}$$

$$\frac{\Gamma \vdash e_1 : \text{SCALAR} \quad \Gamma \vdash e_2 : \text{SERIES}}{\Gamma \vdash \text{Op}(e_1, e_2) : \text{SERIES}}$$

---

## 3. Type Safety Theorem

> **Type Soundness Theorem:** If an AST expression tree $\mathcal{T}$ is well-typed under $\Gamma$ ($\Gamma \vdash \mathcal{T} : \sigma$), and every observation channel referenced by $\mathcal{T}$ provides a finite, non-empty 1D array of float64 values, then evaluation of $\mathcal{T}$ via `SafeEvaluator` is guaranteed to terminate and produce a result of type $\sigma$ without unhandled runtime exceptions.

*Proof:* Evaluator node dispatch implements an inductive structural match over $\mathcal{T}$. Since every node constructor enforces typing rules during AST instantiation (`validate_unary_op_type`, `validate_binary_op_type`), untyped expressions cannot be instantiated.

