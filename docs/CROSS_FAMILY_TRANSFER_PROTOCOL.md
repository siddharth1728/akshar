# SENSEFORGE: Cross-Family Transfer Protocol

**Version:** 0.3.0-alpha  
**Module:** M07 TRANSFER LAB  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Supported Dynamical Families

| Family | Physical Analogy | State Variables | Intervention Ports |
| :--- | :--- | :--- | :--- |
| `coupled_oscillators` | Mechanical lattice | Positions $\vec{x}$, Velocities $\vec{v}$ | Direct external accelerations $\vec{u}$ |
| `reaction_diffusion` | Chemical kinetics | Activator $u$, Inhibitor $v$ | Chemical source/sink injection |
| `thermodynamic_swarm` | Particulate gas | Coordinates $(x, y)$, Velocities $(v_x, v_y)$ | Force injection on guide particle |

---

## 2. Transfer Execution Protocol

1. **Candidate Freezing:** Candidate $\Psi = (\Phi, \Pi)$ is frozen in `FrozenCandidate` with cryptographic signature.
2. **Channel Semantic Check:** `EnvironmentAdapter.validate_compatibility` verifies channel index bounds.
3. **Target Rollout:** Target environments are spawned behind their own Observation Firewalls using dedicated target seeds (e.g. seeds 5000–5019).
4. **Evaluation:** `FalsificationChamber` evaluates Candidate vs Target Baseline A across $N \ge 20$ target rollouts.
5. **Transfer Degradation Ratio (TDR):**
   $$\text{TDR} = \frac{\Delta \text{Skill}_{\text{target}}}{\Delta \text{Skill}_{\text{source}}}$$
