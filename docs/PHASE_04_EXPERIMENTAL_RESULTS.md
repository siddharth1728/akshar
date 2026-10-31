# SENSEFORGE: Phase 04 Experimental Results & Falsification Evidence

**Version:** 0.3.0-alpha  
**Phase:** 04 (Falsification Chamber & Transfer Lab)  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Executive Summary & Epistemic Honesty

In accordance with scientific integrity guidelines:
> **A negative experimental outcome is a successful scientific outcome when the protocol was properly designed, audited, and executed.**

In Phase 04, we audited Phase 03's preliminary candidates and evaluated a frozen discovery candidate through the **Sealed Confirmatory Partition ($N=35$ independent seeds)** and the **Cross-Family Transfer Lab**.

The evaluated candidate **failed both confirmatory testing and cross-family transfer**, and was rigorously **FALSIFIED** and **REJECTED**.

---

## 2. Sealed Confirmatory Results ($N = 35$ Seeds)

- **Candidate ID:** `pair_493039af2be7`
- **Config Hash:** `8a60b548cbfb63c9fc4dfaad713775bf2ea7912dfaf034fb8aa1871c89c5369e`
- **Operator ($\Phi$):** `Sub(Const(-0.8227), DivSafe(Channel(1), Const(1.2220)))`
- **Probe Schedule ($\Pi$):** `['Wait', 'Perturb', 'ReversePerturb']`
- **Partition:** Confirmatory Seeds `9000` through `9034` ($N=35$).

### Confirmatory Telemetry Table:

| Comparator | Skill Score ($\Delta \text{Skill}$) | Cohen's $d$ | Corrected $p$ (Holm) | Significance ($\alpha=0.01$) | Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Baseline A (Passive)** | $-2560.47$ | $-1.58$ | $1.0000$ | Not Significant | **FAILED** |
| **Baseline B (Conventional Stats)** | $-2118.26$ | $-1.58$ | $1.0000$ | Not Significant | **FAILED** |
| **Baseline C (Random Ensemble $K=5$)** | $-2573.81$ | $-1.58$ | $1.0000$ | Not Significant | **FAILED** |
| **Baseline D (Impulse Heuristic)** | $-11487.98$ | $-1.58$ | $1.0000$ | Not Significant | **FAILED** |
| **Ablation F (Raw Obs + Evolved Probe)** | $-11453.76$ | $-1.58$ | $1.0000$ | Not Significant | **FAILED** |
| **Ablation G (Evolved Obs + Random Probe)** | $-0.0004$ | $-2.91$ | $1.0000$ | Not Significant | **FAILED** |

### Post-Confirmatory Epistemic Status: `REJECTED`

---

## 3. Cross-Family Transfer Telemetry

### Target 1: Reaction-Diffusion (Gray-Scott Field)
- **Target Skill Score:** $-21767.55$
- **Transfer Degradation Ratio (TDR):** $0.0000$
- **Corrected $p$-value:** $1.0000$
- **Classification:** **`FAILED_TRANSFER`**

### Target 2: Thermodynamic Swarm (N-Body Particulate System)
- **Target Skill Score:** $-5878.40$
- **Transfer Degradation Ratio (TDR):** $0.0000$
- **Corrected $p$-value:** $1.0000$
- **Classification:** **`FAILED_TRANSFER`**

---

## 4. Scientific Significance of the Result

1. **Successful Rejection of Search Overfitting:** The candidate appeared promising under in-sample selection, but completely collapsed under $N=35$ unseen confirmatory seeds and ensemble random controls.
2. **Verification of the Falsification Chamber:** The machinery proved capable of detecting overfitted mathematical artifacts and rejecting them decisively without confirmation bias.
3. **Audit-Grade Provenance:** The complete experiment was cryptographically signed and recorded in `confirmatory_manifest.json` (`d2733ed128b292c307cf18e69d5a130ed84787fdaedb33dc1d651f5a3987fdd6`).
