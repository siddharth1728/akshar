# SENSEFORGE: Phase 01 Boundary Hardening & Audit Report

**Version:** 0.1.0  
**Phase:** 01 Hardening  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Audit Findings: Limitations of In-Process Isolation

During our rigorous audit of Phase 01, we evaluated the security guarantees of the initial Python `ObservationFirewall`. While effective against casual introspection, an in-process firewall in Python has fundamental epistemological limits:

1. **Shared Process Heap:** Any code running in the same Python process interpreter can theoretically invoke `gc.get_objects()`, crawl memory references, or inspect execution frames via `sys._getframe()`.
2. **Object Introspection Bypasses:** Although `__getattr__` was overridden, `object.__getattribute__` or direct C-extension pointers could access private mangled attributes (`_ObservationFirewall__env`).
3. **Serialization Vulnerabilities:** While `__reduce__` blocked pickling on the firewall object, global module state or uncollected garbage could be inspected.

### Rust Toolchain Host Audit
- **Status:** Unverified / Non-operational for execution on this host.
- **Evidence:** Running `cargo.exe` triggers Windows 11 Smart App Control (SAC) policy block (`os error 4551`). Additionally, MSVC build tools (`link.exe`) are not provisioned on the host.
- **Action:** In accordance with the non-negotiable directive, host security restrictions were **not bypassed or disabled**. Rust crate sources are maintained in `crates/worldfoundry/` as portable specifications, while Python serves as the verified reference execution engine.

---

## 2. Hardened Architecture: Process-Separated Boundary

To achieve true, unbreachable physical isolation between the simulation and the discovery agent, we engineered an **OS-level Process-Separated Architecture**:

```
┌───────────────────────────────────────────────┐
│              WORLD PROCESS                    │
│  - Holds BaseEnvironment instance             │
│  - Private positions, velocities, parameters  │
│  - Executes RK4 / Gray-Scott dynamics         │
│  - Strictly isolated memory heap              │
└───────────────────────┬───────────────────────┘
                        │ Standard Streams Pipe (IPC)
                        │ Versioned JSON-Lines Protocol (senseforge.ipc.v1)
                        ▼
┌───────────────────────────────────────────────┐
│            DISCOVERY PROCESS                  │
│  - ProcessObservationFirewall Client          │
│  - Zero pointers to simulator objects         │
│  - Verifies sequence numbers & chained hashes │
│  - Evaluates candidate instrument genomes     │
└───────────────────────────────────────────────┘
```

### Threat Model & Countermeasures

| Threat Vector | Attack Mechanism | Countermeasure in SENSEFORGE |
| :--- | :--- | :--- |
| **Heap Scraping** | Calling `gc.get_objects()` to find simulation state in memory. | World Process runs in a separate OS process; heap memory is physically isolated by the OS kernel. |
| **Tampered / Stale Frames** | Replay of historical frames or out-of-order execution. | Monotonic sequence counters (`seq`) and chained canonical SHA-256 hashes (`prev_frame_hash`). |
| **Unauthorized Probing** | Sending extreme, NaN, or Inf action values. | Strict Pydantic model validation (`extra="forbid"`) and hard action clamping to $[-u_{\max}, u_{\max}]$. |
| **Exception Leakage** | Triggering simulator errors to reveal internal parameter names in stack traces. | World Process sanitizes all exceptions into generic `EnvErrorResponse` tokens (`EXECUTION_ERROR`). |
| **Process Termination** | Subprocess crashes or is forcefully terminated. | Discovery client detects termination, surfaces `ProcessBoundaryTerminatedError`, and enables clean restarts. |

---

## 3. Communication Protocol Specification (`senseforge.ipc.v1`)

All messages crossing the boundary are single-line JSON objects adhering strictly to schema:
- `SPAWN`: Initializes an environment family with randomized seed and permitted channel indices.
- `OBSERVE`: Requests instantaneous readings for permitted channels only.
- `PROBE`: Applies bounded perturbation vector and steps the simulation.
- `RESET`: Resets initial conditions.
- `PING`: Verifies worker health.
- `SHUTDOWN`: Gracefully terminates the worker process.

Every response frame incorporates a chained canonical hash:
$$\text{Hash}_t = \text{SHA256}\left(\text{JSON}_{\text{canonical}}(\text{env\_id}, \text{seq}, \text{step}, t, \vec{y}_t, \text{Hash}_{t-1})\right)$$

---

## 4. Adversarial Verification Test Suite

The test suite in [`tests/test_process_firewall.py`](file:///c:/akshar/tests/test_process_firewall.py) verifies:
- `test_process_firewall_basic_lifecycle`: Clean IPC communication.
- `test_heap_isolation_no_simulation_objects_in_discovery_memory`: Zero simulation classes exist in the Discovery process heap.
- `test_rejection_of_unauthorized_extra_fields`: Extra JSON fields are rejected by the protocol.
- `test_adversarial_action_nan_inf_rejection`: Unsafe numerical probe vectors are rejected.
- `test_replay_attack_detection`: Replayed sequence numbers are detected and rejected.
- `test_process_crash_detection`: Process death is caught without hanging.
- `test_restart_after_crash`: Clean re-initialization after process death.

**Result:** 7 of 7 adversarial tests passed.

