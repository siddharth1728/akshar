# SENSEFORGE: Evolutionary Objectives & Information Theory

**Version:** 0.2.0-alpha  
**Module:** M05 DISCOVERYFORGE  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Information-Theoretic Foundations

A central tenet of the SENSEFORGE methodology is the **Data Processing Inequality (DPI)**:

> **Information Theoretic Constraint:** For any Markov chain $X \to Y \to Z$, the mutual information satisfies:
> $$\mathbb{I}(X; Z) \le \mathbb{I}(X; Y)$$
> A deterministic mathematical transformation $\Phi(Y)$ over historical observations cannot create new Shannon information about the latent environmental state $S_t$.

### Why Experimental Probing is Mandatory

While passive feature engineering cannot increase mutual information, **active interventions ($do(A = \vec{u})$) fundamentally alter the conditional distribution of future states**:

$$\mathbb{P}(S_{t+1} \mid do(A = \vec{u}), S_t) \neq \mathbb{P}(S_{t+1} \mid S_t)$$

Controlled physical probes excite unobserved dynamical modes (e.g., non-linear resonance, damping asymmetry, boundary elasticity) that are completely dormant during passive observation.

Therefore:
1. **The Probe ($\Pi$)** creates the physical excitation that exposes latent state variables.
2. **The Measurement Operator ($\Phi$)** synthesizes the receptive filter that captures that excitation.

---

## 2. Multi-Objective Evaluation Dimensions

Every candidate $\Psi = (\Phi, \Pi)$ is evaluated on five independent objectives:

1. **Predictive Information Gain ($\Delta \mathcal{I}$):**
   $$\Delta \mathcal{I}(\Psi) = \frac{\text{NMSE}_{\text{passive}} - \text{NMSE}_{\Psi}}{\text{NMSE}_{\text{passive}} + 10^{-6}}$$
2. **Random Control Differential ($\Delta_C$):**
   $$\Delta_C(\Psi) = \frac{\text{NMSE}_{\text{random\_probe}} - \text{NMSE}_{\Psi}}{\text{NMSE}_{\text{random\_probe}} + 10^{-6}}$$
   Ensures that performance is due to *structured experimental design*, not mere random excitation.
3. **Cross-Seed Robustness ($\mathcal{R}$):**
   $$\mathcal{R}(\Psi) = \frac{1}{\text{std}_{s \in \mathcal{S}_{\text{eval}}}(\text{NMSE}(s)) + 0.1}$$
4. **Structural Simplicity ($-\mathcal{C}$):**
   $$-\mathcal{C}(\Psi) = -\left(\text{node\_count}(\Phi) + \text{depth}(\Phi) + T_{\Pi}\right)$$
5. **Energetic Efficiency ($-\mathcal{E}$):**
   $$-\mathcal{E}(\Pi) = -\sum_{t=1}^{T_{\Pi}} \|\vec{u}_t\|^2$$

