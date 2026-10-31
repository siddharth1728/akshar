# SENSEFORGE: Module Specification and Implementation Plan

**Version:** 0.1.0  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Module Detailed Specifications

### Module M01 — WORLDFOUNDRY (Procedural Simulation Engine)
- **Interface Contract:**
  ```python
  class EnvironmentFamily(Enum):
      COUPLED_OSCILLATORS = "coupled_oscillators"
      REACTION_DIFFUSION = "reaction_diffusion"
      THERMODYNAMIC_SWARM = "thermodynamic_swarm"

  class EnvironmentConfig(BaseModel):
      family: EnvironmentFamily
      seed: int
      step_size: float = 0.01
      noise_std: float = 0.0
      params: Dict[str, float] = Field(default_factory=dict)
  ```
- **Execution Invariant:**
  Calling `env.step(action_vector)` advances internal state by `step_size`.
  All random number generators are seeded per instance.
  Calling `env.reset(seed)` returns the environment to the exact reproducible state.
- **Hidden State Isolation:**
  Internal simulation objects MUST NEVER expose raw state tensors or references to caller. All state transitions happen within private attributes.

---

### Module M02 — OBSERVATION FIREWALL (Cryptographic Information Boundary)
- **Interface Contract:**
  ```python
  class ObservationFrame(BaseModel):
      timestamp: float
      step_index: int
      readings: List[float] # strictly restricted projection
      firewall_hash: str     # SHA256 integrity token

  class ObservationFirewall:
      def __init__(self, env: BaseEnvironment, allowed_channels: List[int]):
          self._env = env
          self._allowed_channels = allowed_channels
          self._total_steps = 0
          
      def observe(self) -> ObservationFrame:
          # Obtains raw internal state, performs strict projection, disposes of internal reference
          ...
          
      def probe(self, action: List[float]) -> ObservationFrame:
          # Clamps action to valid bounds, applies perturbation, returns restricted observation
          ...
  ```
- **Information Leakage Tests:**
  1. Inspecting `dir(firewall)` or `vars(firewall)` does not expose `_env.state`.
  2. Exceptions raised in `_env` are caught, sanitized, and re-emitted as generic `FirewallException`.
  3. No pointer sharing: all observation vectors are deep-copied / cloned as immutable lists or contiguous arrays.

---

### Module M03 — INSTRUMENT GENOME (Symbolic Expression Engine)
- **Grammar Definition:**
  ```
  Expr := Terminal | UnaryOp(Expr) | BinaryOp(Expr, Expr) | WindowOp(Expr, Window)
  Terminal := Channel(idx) | Constant(val)
  UnaryOp := Neg | Abs | SqrtSafe | LogSafe | Tanh | Diff(tau) | Lag(tau)
  BinaryOp := Add | Sub | Mul | DivSafe | Max | Min | DotProduct
  WindowOp := RollingMean | RollingVar | RollingQuantile(q)
  ```
- **Type Rules:**
  - Every expression operates on sliding time windows of length $W \le 128$.
  - Evaluation produces a 1D scalar or time-series vector of float64 values.
  - Safe division guarantees no NaN / Inf output: $\text{DivSafe}(a, b) = \frac{a}{b + \text{sign}(b)\cdot 10^{-6}}$ when $|b| < 10^{-6}$.

---

### Module M04 — PROBE DESIGNER (Controlled Experimental Design)
- **Intervention Protocol:**
  - Probes are bounded schedules: $\Pi = \{(t_i, u_i, c_i)\}_{i=1}^K$ where $t_i$ is offset, $u_i \in [-1.0, 1.0]$ is perturbation value, $c_i$ is target intervention port.
  - Maximum probe duration $\tau \le 50$ steps.
  - Energetic constraint: $\sum |u_i|^2 \le E_{\max}$.

---

### Module M05 — DISCOVERY FORGE (Evolutionary Synthesis)
- **Genetic Algorithm Specification:**
  - Representation: Expression AST + Probe Schedule.
  - Mutations:
    - Point mutation (replace operator or constant).
    - Subtree insertion (grow new functional sub-branch).
    - Subtree deletion (prune to terminal).
    - Probe timing and amplitude jitter.
  - Crossover: Subtree swapping between compatible parent nodes.
  - Multi-objective Pareto selection: Non-dominated sorting with crowding distance (NSGA-II).

---

### Module M06 — FALSIFICATION CHAMBER (Adversarial Testing)
- **Validation Pipeline:**
  1. Candidate evaluated on 30 held-out random seeds.
  2. Candidate compared against linear autoregressive model on raw observations.
  3. Null surrogate testing: 100 random shuffles / phase surrogates.
  4. Bonferroni-corrected p-value calculation ($\alpha = 0.01$).

---

### Module M07 — TRANSFER LAB (Cross-Family Generalization)
- **Transfer Pipeline:**
  1. Freeze candidate operator $\Phi^*$.
  2. Deploy $\Phi^*$ into an unseen environment family (e.g., from `CoupledOscillators` to `ReactionDiffusion`).
  3. Compute $\Delta \mathcal{I}$ relative to in-family baselines.
  4. Classify as `GENERALIZED_DISCOVERY` if $\Delta \mathcal{I} > 0.15$ with $p < 0.01$.

---

### Module M08 — DISCOVERY LEDGER (SQLite Persistence)
- **Relational Schema:**
  - `environments`: id, family, seed, configuration_json, created_at.
  - `candidates`: id, generation, ast_representation, probe_schedule, complexity.
  - `evaluations`: id, candidate_id, environment_id, baseline_error, candidate_error, info_gain, p_value, status.
  - `transfers`: id, candidate_id, source_family, target_family, transfer_score, status.

---

### Module M09 — RESEARCH OBSERVATORY (Web UI & Visual Interface)
- **Architecture:**
  - Backend: FastAPI with asynchronous WebSockets streaming live simulation frames and evolutionary progress at 30-60 Hz.
  - Frontend: React + TypeScript + Tailwind CSS / Deep Graphite theme.
  - Visualizer: Custom HTML5 Canvas / WebGL2 shader pipelines rendering particle swarms, reaction diffusion grids, and live phase-space trajectories.

