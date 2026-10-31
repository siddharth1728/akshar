# SENSEFORGE: System Architecture and Dependency Specification

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. High-Level Modular Decomposition

SENSEFORGE is architected as a set of nine decoupled, rigorously bounded modules (M01 to M09), spanning simulation, information boundaries, symbolic representation, evolutionary search, falsification, transfer evaluation, and visual instrumentation.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SENSEFORGE ARCHITECTURE                         │
└──────────────────────────────────────────────────────────────────────────────┘

                               [ M01 WORLDFOUNDRY ]
                  Procedural Generation of Dynamical Systems
                     ├── Coupled Non-linear Oscillators
                     ├── Dissipative Reaction-Diffusion Cellular Automata
                     └── Particle Thermodynamic Swarms
                                      │
                                      ▼ [Internal Hidden State: S_t, Parameters, Seed]
                     ┌──────────────────────────────────┐
                     │    M02 OBSERVATION FIREWALL      │
                     │  - Opaque Projection Ω(S_t)      │
                     │  - Action Gatekeeper             │
                     │  - Non-leaking Exception Barrier │
                     └──────────────────────────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │ Observable Frames y_t                             │ Probe Response
            ▼                                                   ▼
┌───────────────────────┐                             ┌───────────────────────┐
│  M03 INSTRUMENT GENOME│                             │   M04 PROBE DESIGNER  │
│  - Operator AST       │◄────────────────────────────┤  - Intervention Seq.  │
│  - Type Checker       │                             │  - Perturbation Timing│
│  - Safe Sandbox Exec  │                             └───────────────────────┘
└───────────┬───────────┘                                         ▲
            │ Candidate Instrument Ψ = (Φ, Π)                     │
            ▼                                                     │
┌───────────────────────┐                             ┌───────────┴───────────┐
│  M05 DISCOVERY FORGE  │                             │   M07 TRANSFER LAB    │
│  - Pareto Genetic Alg │                             │  - Cross-Family Eval  │
│  - Complexity Penalty │                             │  - Invariance Testing │
│  - Archive & Diversity│                             └───────────────────────┘
└───────────┬───────────┘                                         ▲
            │ Candidates                                          │ Verified Invariants
            ▼                                                     │
┌───────────────────────┐                                         │
│   M06 FALSIFICATION   │─────────────────────────────────────────┘
│   - Held-Out Seeds    │
│   - Permutation Nulls │
│   - Delay Baselines   │
└───────────┬───────────┘
            │ Verified / Rejected Ledgers
            ▼
┌───────────────────────┐                             ┌───────────────────────┐
│  M08 DISCOVERY LEDGER │◄────────────────────────────┤ M09 RESEARCH          │
│  - SQLite Schema      │      WebSocket / JSON API   │     OBSERVATORY       │
│  - Provenance Tree    │────────────────────────────►│  - React / TypeScript │
│  - Replay Validation  │                             │  - WebGL2 / GLSL      │
└───────────────────────┘                             └───────────────────────┘
```

---

## 2. Module Specifications (M01 – M09)

### M01: WORLDFOUNDRY (Procedural Simulation Engine)
- **Role:** Generates synthetic dynamical environments $\mathcal{E}$ across diverse physical analogues.
- **Environment Families:**
  1. `CoupledOscillators`: Non-linear, chaotic Duffing-van der Pol lattice with non-linear spring constants and variable damping.
  2. `ReactionDiffusion`: 1D/2D Gray-Scott or FitzHugh-Nagumo reaction grids exhibiting traveling wave fronts, spot formation, and excitability.
  3. `ThermodynamicSwarm`: Bounded N-body particle system with multi-species potential fields and non-conservative boundary friction.
- **Invariants:** 100% deterministic simulation step given `(Family, Seed, ParameterVector)`.
- **Private State:** Positions, velocities, hidden activator/inhibitor concentrations, coupling matrices, and future trajectory buffers are marked strictly private.

### M02: OBSERVATION FIREWALL (Cryptographic Information Boundary)
- **Role:** Ensures the discovery process cannot access latent environment variables through any channel (memory reflection, object attributes, exception strings, JSON serialization, or timing leaks).
- **Enforcement Mechanisms:**
  - Opaque observation envelope: returns strictly frozen float arrays `y_t \in \mathbb{R}^k`.
  - Action validation: only permitted probe vectors within predefined bounds $[-u_{\max}, u_{\max}]$ are admitted.
  - Exception sanitization: error traces from inside the simulator are stripped of internal parameter names and state values.
  - Audit logging: hashes every interaction frame for reproducibility.

### M03: INSTRUMENT GENOME (Symbolic Operator Representation)
- **Role:** Represents candidate measurement operators as typed Abstract Syntax Trees (AST) or Directed Acyclic Graphs (DAG).
- **DSL Primitives:**
  - Arithmetic: `Add`, `Sub`, `Mul`, `SafeDiv`, `Neg`, `Abs`
  - Temporal: `Lag(tau)`, `Diff(tau)`, `Integral(window)`, `EMA(alpha)`
  - Statistical: `RollingMean(window)`, `RollingVariance(window)`, `RollingQuantile(q, window)`
  - Cross-channel: `DotProduct(c1, c2)`, `CrossRatio(c1, c2, eps)`
  - Non-linear: `Tanh`, `Sigmoid`, `Relu`, `Softplus`
- **Execution:** Strongly typed, bounded recursion depth ($D \le 6$), memory-capped, deterministic, free of external side-effects.

### M04: PROBE DESIGNER (Controlled Experimental Design)
- **Role:** Generates structured intervention schedules $\Pi = (a_1, a_2, \dots, a_\tau)$ to disturb the environment and reveal hidden modes.
- **Probe Types:**
  - `DiracPulse(amplitude, channel, step)`
  - `SinusoidalSweep(f_start, f_end, amplitude, channel)`
  - `StepResponse(step_value, duration, channel)`
  - `StateTriggeredPulse(channel, threshold, pulse_value)`

### M05: DISCOVERY FORGE (Evolutionary Synthesis Engine)
- **Role:** Searches the combinatorial space of measurement operators and probe designs.
- **Mechanism:** Multi-objective genetic algorithm (NSGA-II / Pareto MAP-Elites) optimizing for:
  1. Incremental predictive information ($\Delta \mathcal{I}$).
  2. Operator simplicity ($-\mathcal{C}(\Phi)$).
  3. Probe energy efficiency ($-\mathcal{E}(\Pi)$).
  4. Behavioral novelty relative to historical archive.

### M06: FALSIFICATION CHAMBER (Adversarial Verification)
- **Role:** Subject candidate instruments to falsification.
- **Protocol:**
  1. **Held-Out Evaluation:** 30 unseen seeds from the same environment family.
  2. **Surrogate Null Tests:** Phase-randomized Fourier surrogates and shuffled time-series to test whether performance gain exceeds chance ($p < 0.01$).
  3. **Baseline Differential:** Direct comparison against Takens delay embeddings and Ridge AR baselines.
  4. **Noise Stress Test:** Injects additive white Gaussian noise (AWGN) to assess degradation curves.

### M07: TRANSFER LAB (Generalization Testing)
- **Role:** Evaluates whether an operator discovered in family $\mathcal{F}_A$ captures generalized dynamical laws applicable in $\mathcal{F}_B$.
- **Metric:** Measurement Transferability Index (MTI):
  $$\text{MTI}(\Phi, \mathcal{F}_A \to \mathcal{F}_B) = \frac{\Delta \mathcal{I}(\Phi \mid \mathcal{F}_B)}{\Delta \mathcal{I}(\Phi \mid \mathcal{F}_A)}$$

### M08: DISCOVERY LEDGER (SQLite Persistence)
- **Role:** Immutable audit trail recording every experiment, candidate AST, probe schedule, fitness vector, falsification outcome, and seed configuration.
- **Schema:** Strict relational structure ensuring zero unrecorded discoveries.

### M09: RESEARCH OBSERVATORY (Web Interface)
- **Role:** Interactive scientific instrumentation cockpit.
- **Components:**
  - High-fps WebGL2 canvas rendering phase space and simulated fields.
  - Interactive AST expression viewer.
  - Live Pareto discovery frontier.
  - Falsification hypothesis test reports.
  - Full experiment control (Generate, Evolve, Pause, Falsify, Transfer, Export).

---

## 3. Directory Layout

```
c:\akshar\
├── docs/
│   ├── RESEARCH_LANDSCAPE.md
│   ├── ORIGINALITY_HYPOTHESIS.md
│   ├── RESEARCH_QUESTIONS.md
│   ├── EXPERIMENTAL_PROTOCOL.md
│   ├── ARCHITECTURE.md
│   ├── MODULE_SPECIFICATION.md
│   ├── TESTING_ACCEPTANCE_CRITERIA.md
│   └── ENGINEERING_RISKS.md
├── crates/
│   └── worldfoundry/
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs
│           ├── firewall.rs
│           ├── environments/
│           │   ├── mod.rs
│           │   ├── coupled_oscillators.rs
│           │   ├── reaction_diffusion.rs
│           │   └── thermodynamic_swarm.rs
│           └── measurements.rs
├── senseforge/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── firewall.py
│   │   ├── worldfoundry.py
│   │   └── environments/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── coupled_oscillators.py
│   │       ├── reaction_diffusion.py
│   │       └── thermodynamic_swarm.py
│   ├── genome/
│   │   ├── __init__.py
│   │   ├── dsl.py
│   │   ├── types.py
│   │   ├── parser.py
│   │   └── evaluator.py
│   ├── probes/
│   │   ├── __init__.py
│   │   └── designer.py
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── forge.py
│   │   ├── population.py
│   │   └── pareto.py
│   ├── falsification/
│   │   ├── __init__.py
│   │   ├── chamber.py
│   │   ├── baselines.py
│   │   └── surrogates.py
│   ├── transfer/
│   │   ├── __init__.py
│   │   └── lab.py
│   ├── ledger/
│   │   ├── __init__.py
│   │   ├── schema.sql
│   │   └── db.py
│   └── server/
│       ├── __init__.py
│       ├── app.py
│       ├── routes.py
│       └── websocket.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── SimulationCanvas.tsx
│       │   ├── DiscoveryFrontier.tsx
│       │   ├── AstViewer.tsx
│       │   ├── FalsificationPanel.tsx
│       │   └── LedgerHistory.tsx
│       └── shaders/
│           ├── particle.vert.glsl
│           └── field.frag.glsl
├── tests/
│   ├── test_firewall.py
│   ├── test_worldfoundry.py
│   ├── test_dsl.py
│   ├── test_falsification.py
│   └── test_end_to_end.py
└── scripts/
    ├── run_all_tests.ps1
    └── start_system.ps1
```

