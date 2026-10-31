# SENSEFORGE: Locked Evaluation Protocol (Phase 04)

**Project:** SENSEFORGE  
**Classification:** Experimental Computational Science / Artificial Intelligence Research  
**Version:** `0.3.0-alpha`  
**Module:** M06 Partition & Manifest Engines (`senseforge/falsification/partition.py`, `manifest.py`)  
**Status:** FULLY IMPLEMENTED & VERIFIED  

---

## 1. Principles of Pre-Registration & Sealed Partitions

In computational evolutionary research, researchers frequently fall victim to unconscious "leakage": running generations until a candidate performs well on the test set, modifying hyperparameters, and re-running. This is mathematically equivalent to training on the test set.

To establish absolute scientific integrity, SENSEFORGE implements a **3-tier partitioned seed hierarchy**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3-TIER PARTITIONED HIERARCHY                    │
├────────────────────┬───────────┬───────────────┬───────────────────────┤
│ Partition Type     │ Seeds     │ Access Policy │ Permitted Operations  │
├────────────────────┼───────────┼───────────────┼───────────────────────┤
│ 1. SEARCH          │ 1000..1024│ Open / Mutable│ Selection, Crossover  │
│ 2. VALIDATION      │ 2000..2019│ Read-Only     │ Hyperparameter tuning │
│ 3. LOCKED_TEST     │ 9000..9034│ Sealed (One)  │ Single Confirmatory   │
└────────────────────┴───────────┴───────────────┴───────────────────────┘
```

The partitions are verified strictly disjoint:
$$\mathcal{S}_{\text{Search}} \cap \mathcal{S}_{\text{Val}} = \emptyset, \quad \mathcal{S}_{\text{Search}} \cap \mathcal{S}_{\text{Lock}} = \emptyset, \quad \mathcal{S}_{\text{Val}} \cap \mathcal{S}_{\text{Lock}} = \emptyset$$

---

## 2. Statistical Power Analysis & Sample Size Sizing

Before evaluating on the locked partition, the minimum sample size $N$ is computed via statistical power analysis:
- Significance Level: $\alpha = 0.01$ (Two-sided)
- Statistical Power: $1 - \beta = 0.80$
- Minimum Meaningful Effect Size: Cohen's $d \ge 0.60$

Under normal asymptotic assumptions:
$$N \ge \left( \frac{z_{1 - \alpha/2} + z_{1 - \beta}}{d} \right)^2 \approx \left( \frac{2.576 + 0.842}{0.60} \right)^2 = \left( \frac{3.418}{0.60} \right)^2 \approx 32.45$$

Hence, SENSEFORGE enforces:
$$N_{\text{locked}} \ge 30 \quad (\text{Default } N = 35 \text{ seeds})$$

---

## 3. Cryptographic Locking: FrozenCandidate

Before any access to the Locked Test Partition is permitted:
1. **Serialization:** The candidate AST $\Phi$ and probe action list $\Pi$ are serialized to canonical JSON format (sorted keys, no extraneous whitespace).
2. **SHA-256 Hashing:** A configuration hash $H(\Psi)$ is computed:
   $$H(\Psi) = \text{SHA256}(\text{CanonicalJSON}(\Phi) \mathbin{\Vert} \text{CanonicalJSON}(\Pi))$$
3. **Immutability Enforcement:** The candidate object is wrapped in `FrozenCandidate`. Any subsequent mutation of attributes is forbidden.

---

## 4. Retuning Prevention & Enforcement Engine

When `c_part.get_seeds(candidate_id, config_hash)` is invoked:
1. If `candidate_id` is seen for the first time:
   - The partition records the pairing `(candidate_id, config_hash)`.
   - Access to the locked seeds is granted for this one-shot evaluation.
2. If `candidate_id` is queried again with the **exact same** `config_hash`:
   - Access is granted solely for verification / re-run reproducibility.
3. If `candidate_id` is queried with a **modified** `config_hash`:
   - **`PartitionSealedViolation`** is raised immediately:
   > *"Candidate '{id}' attempted to access Locked Partition with modified configuration hash ({hash2} != {hash1}). Retuning on locked test partition is strictly prohibited."*
   - Execution is aborted. No seed leakage can occur.

---

## 5. Audit-Grade Provenance Manifest

Upon completion of the locked confirmatory test, a cryptographically signed manifest is generated:
- Hardware, OS, Python runtime, and package versions.
- Timestamp and environment configuration.
- Candidate ID and SHA-256 configuration hash.
- Full statistical telemetry across all 7 comparator baselines.
- Transfer Lab performance across target environments.
- **`manifest_signature`**: SHA-256 hash over the canonical JSON representation of the entire manifest.
