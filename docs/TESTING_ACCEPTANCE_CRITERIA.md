# SENSEFORGE: Testing and Acceptance Criteria

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Test Suite Architecture

To ensure experimental integrity and prevent regression, SENSEFORGE mandates five distinct levels of automated verification:

| Test Level | Scope | Primary Objective |
| :--- | :--- | :--- |
| **L1: Unit & Numerical Safety** | Core mathematical functions, safe division, AST evaluation, RNG seeding. | Guarantee deterministic replay, absence of NaN/Inf, and numerical stability. |
| **L2: Firewall Security & Anti-Leakage** | Observation Firewall boundary, exception paths, serialization, introspection. | Prove impossible to inspect hidden variables or bypass allowed channels. |
| **L3: Evolutionary & Search Invariants** | Mutation, crossover, expression depth limits, Pareto domination ranking. | Verify grammar correctness, syntactic validity, and complexity capping. |
| **L4: Statistical Falsification** | Null hypothesis surrogates, Wilcoxon signed-rank tests, p-value calculations. | Guarantee that no candidate is accepted without passing statistical hurdles. |
| **L5: End-to-End System Integration** | World generation $\to$ Firewall $\to$ Discovery $\to$ Falsification $\to$ Ledger $\to$ WebSocket. | Verify complete autonomous workflow execution. |

---

## 2. Formal Acceptance Criteria by Module

### M01: WORLDFOUNDRY
- [ ] **AC-1.1:** Generating an environment with seed $S$ yields identical observation trajectories across repeated runs (tolerance: $0.0$).
- [ ] **AC-1.2:** Supports at least 3 distinct environment families (`CoupledOscillators`, `ReactionDiffusion`, `ThermodynamicSwarm`).
- [ ] **AC-1.3:** State transitions remain numerically stable over 10,000 continuous time steps without numerical overflow or divergence.

### M02: OBSERVATION FIREWALL
- [ ] **AC-2.1:** Any attempt to access `env._state` or unexposed attributes through public firewall methods raises an error or is blocked.
- [ ] **AC-2.2:** Returned observation objects contain exclusively permitted channel indices and are immutable (deep-copied).
- [ ] **AC-2.3:** Simulator exceptions caught by the firewall are stripped of internal variable names and memory addresses.

### M03: INSTRUMENT GENOME
- [ ] **AC-3.1:** Arbitrary syntactically valid AST expressions evaluate to finite float arrays with zero unhandled exceptions.
- [ ] **AC-3.2:** Division by zero returns bounded epsilon-regularized values without crashing.
- [ ] **AC-3.3:** Maximum expression tree depth is strictly enforced (e.g., depth $\le 6$).

### M04: PROBE DESIGNER
- [ ] **AC-4.1:** All probe outputs respect hard intervention amplitude bounds $[-u_{\max}, u_{\max}]$.
- [ ] **AC-4.2:** Cumulative probe energy $\sum |u|^2$ is verified against budget limits.

### M05: DISCOVERY FORGE
- [ ] **AC-5.1:** Multi-objective selection produces a non-dominated Pareto frontier where no candidate is strictly dominated by another.
- [ ] **AC-5.2:** Evolutionary loop executes autonomously without external API calls or human input.

### M06: FALSIFICATION CHAMBER
- [ ] **AC-6.1:** Candidates that perform well on training seeds but fail on held-out seeds are classified as `REJECTED`.
- [ ] **AC-6.2:** Candidates whose predictive gain does not exceed shuffled null surrogates ($p \ge 0.01$) are rejected.
- [ ] **AC-6.3:** Outperforms raw observation baseline and uniform lag embedding baseline before receiving provisional discovery status.

### M07: TRANSFER LAB
- [ ] **AC-7.1:** Correctly tests candidates across distinct environment families and records cross-family transfer scores.

### M08: DISCOVERY LEDGER
- [ ] **AC-8.1:** SQLite ledger records every evaluation, candidate AST string, fitness vector, and timestamp.
- [ ] **AC-8.2:** Any recorded discovery can be replayed from the database with exact numerical replication.

### M09: RESEARCH OBSERVATORY
- [ ] **AC-8.1:** Web client connects via WebSocket, renders live environment state and observation stream, and displays discovered instruments in real-time.

