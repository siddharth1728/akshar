# SENSEFORGE: Probing Protocol & Episode Isolation

**Version:** 0.2.0-alpha  
**Module:** M04 PROBEDESIGNER  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Episode Isolation Principle

A fundamental rule of scientific discovery is that **an experimental test must not contaminate the initial conditions of a subsequent test**. 

If Candidate $\Psi_1$ displaces an oscillator to an extreme position, Candidate $\Psi_2$ must not inherit that displaced initial state unless testing hysteresis.

### The Execution Lifecycle

Every probe evaluation follows a strict three-phase lifecycle executed by `ProbeExecutor`:

```
[ RESET ENVIRONMENT ] ───► Clean Seed S_0 (Zero Contamination)
         │
         ▼
[ PHASE 1: PRE-INTERVENTION ] ───► T_pre steps of zero-force relaxation (Base Dynamics)
         │
         ▼
[ PHASE 2: ACTIVE PROBE ] ───────► T_probe steps unrolling ProbeGenome action schedule
         │
         ▼
[ PHASE 3: POST-INTERVENTION ] ──► T_post steps relaxation (Transient decay & State Forecast)
```

---

## 2. Hard Action Guardrails

The Observation Firewall enforces:
1. **Dimension Clamping:** Intervention vectors are clamped to the exact number of active actuator ports.
2. **Magnitude Capping:** Any action exceeding $u_{\text{max}}$ is strictly clipped to $[-u_{\text{max}}, u_{\text{max}}]$.
3. **NaN/Inf Interception:** Action vectors containing `NaN` or `Inf` are rejected by Pydantic protocol models before reaching the simulation.
4. **Energy Ceiling:** Cumulative energy $\sum \|\vec{u}_t\|^2$ is enforced by `enforce_budget`.

