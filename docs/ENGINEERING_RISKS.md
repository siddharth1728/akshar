# SENSEFORGE: Unresolved Scientific and Engineering Risks

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Scientific Risks & Mitigation Strategies

### Risk 1: The "Trivial Invariant" Fallacy
- **Description:** An evolutionary search over mathematical operators can easily converge on constant invariants (e.g., $x - x = 0$) or degenerate identities that trivially minimize error variances while conveying zero actual information about latent environmental state.
- **Mitigation:**
  - Mandate **Mutual Information or Predictive Information Gain** ($\Delta \mathcal{I} > 0$) rather than raw loss minimization.
  - Require that candidate operators retain non-zero variance over the observation sequence ($\text{Var}(\Phi(y)) > \epsilon$).
  - Measure prediction improvement on future target transitions ($\vec{y}_{t+1:t+H}$) conditioned on the candidate operator.

### Risk 2: Overfitting to Finite Simulator Runs
- **Description:** A candidate expression tree with sufficient depth can memorize trajectory quirks of a specific random seed, appearing predictive while failing to represent any physical property of the system.
- **Mitigation:**
  - Strict 30-seed held-out evaluation across independently drawn initial conditions.
  - Non-parametric permutation and phase-randomized surrogate testing to establish empirical null distributions.
  - Severe complexity penalties in Pareto ranking ($\mathcal{C}(\Phi)$).

### Risk 3: Ineffective Random Probes
- **Description:** Unstructured random actions may fail to perturb the system into states that distinguish competing hypotheses, acting merely as noise.
- **Mitigation:**
  - Co-evolve structured probe primitives (Dirac pulses, sinusoidal frequency sweeps, step-voltage jumps) that systematically excite natural resonant frequencies and non-linear limits of the dynamical system.

---

## 2. Engineering Risks & Host Platform Constraints

### Risk 4: Windows 11 Smart App Control (SAC) & Compiler Constraints
- **Discovery during environment audit:**
  - The host machine enforces **Smart App Control** (`VerifiedAndReputablePolicyState: 1`), which blocks unsigned third-party executables downloaded to user folders (specifically returning OS error 4551 on `cargo.exe`).
  - Native MSVC Build Tools (`link.exe`) are not installed on the system.
- **Engineering Response & Dual-Engine Architecture:**
  - We maintain standard Rust source definitions in `crates/worldfoundry/` with full Cargo configurations for portable multi-platform deployment and PyO3 bindings.
  - Concurrently, we implement a 100% pure, vectorized Python reference engine (`senseforge.core.worldfoundry`) powered by pre-installed, signed BLAS/LAPACK binaries (`numpy` and `scipy`).
  - This guarantees that SENSEFORGE runs with high performance, strict determinism, and zero environment barriers on the current host while preserving the full Rust architecture for environments where MSVC/cargo are provisioned.

### Risk 5: Numerical Divergence in Stiff ODE Integration
- **Description:** Coupled non-linear oscillators and reaction-diffusion equations can experience numerical explosions if Euler time steps are too coarse.
- **Mitigation:**
  - Utilize adaptive or bounded symplectic Runge-Kutta 4th order (RK4) integration for mechanical systems and operator-splitting / implicit diffusion schemes for reaction-diffusion fields.
  - Implement numerical clipping and divergence detection within the simulation loop, gracefully restarting runs with penalized fitness rather than crashing.

### Risk 6: Bloat and Combinatorial Explosion in Symbolic ASTs
- **Description:** Genetic programming naturally tends towards exponential expression growth ("code bloat") where redundant trees slow down evaluation.
- **Mitigation:**
  - Hard AST depth caps ($D \le 6$).
  - Constant folding and algebraic simplification before evaluation.
  - Pareto multi-objective selection prioritizing minimal node count.

