# SENSEFORGE: Research Landscape and Prior-Art Investigation

**Version:** 0.1.0  
**Domain:** Autonomous Invention of Measurement Mechanisms  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Executive Summary & Epistemological Stance

Scientific discovery fundamentally hinges on **measurement**: the operational mapping between an unobserved (or partially observed) physical or computational substrate and symbolic, quantifiable representations. Conventional computational science and automated discovery programs generally presuppose the observation vocabulary—assuming sensors, tabular variables, coordinate frames, or raw sensory tensors are fixed *a priori*. 

**SENSEFORGE** investigates the computational possibility of **autonomous measurement invention**: whether an artificial system, bound by an information-restricted interface, can formulate novel mathematical operators and active experimental probes to reveal hidden dynamics that are unresolvable within its primitive observation vocabulary.

This document grounds SENSEFORGE across nine major research lineages, identifying specific milestones, foundational literature, methodological boundaries, and structural limitations of current paradigms.

---

## 2. Taxonomy of Related Research Lineages

```
                                  [ AUTONOMOUS DISCOVERY SPECTRUM ]
                                                 │
        ┌────────────────────────┬───────────────┴───────────────┬────────────────────────┐
        ▼                        ▼                               ▼                        ▼
[Symbolic Regression &    [Active Perception &             [Evolutionary Feature    [Automated Scientific
 Equation Discovery]      Experimental Design]             Construction & Search]   Discovery & Causal Systems]
 ├── Bacon / AI Feynman    ├── Active Learning (Settles)   ├── GP Feature Synthesis ├── "Robot Scientist" Adam/Eve
 ├── PySR / Symbolic GP    ├── Causal Discovery (Pearl)    ├── Novelty Search       ├── Causal State Splitting
 └── SINDy (Brunton et al) └── Bayesian Experimental Des.   └── MAP-Elites           └── Epistemic Curiosity (Friston)
```

### 2.1 Symbolic Regression & Equation Discovery

#### Foundational Works:
1. **Langley, P., Simon, H. A., Bradshaw, G. L., & Zytkow, J. M. (1987).** *Scientific Discovery: Computational Explorations of the Creative Processes.* MIT Press. (The BACON project family).
2. **Schmidt, M., & Lipson, H. (2009).** *Distilling Free-Form Natural Laws from Experimental Data.* Science, 324(5923), 81–85.
3. **Brunton, S. L., Proctor, J. L., & Kutz, J. N. (2016).** *Discovering governing equations from data by sparse identification of nonlinear dynamical systems (SINDy).* PNAS, 113(15), 3932–3937.
4. **Udrescu, S. M., & Tegmark, M. (2020).** *AI Feynman: A physics-inspired method for symbolic regression.* Science Advances, 6(16), eaay2631.
5. **Cranmer, M. (2023).** *Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl.* arXiv:2305.01582.

#### Paradigmatic Assumptions & Limitations:
- **Fixed Observable Basis:** Symbolic regression systems assume that the state variables (e.g., position $x$, velocity $v$, temperature $T$) are already isolated, digitized, and provided as clean columns.
- **Passive Ingestion:** The algorithm fits relationships $\dot{x} = f(x)$ or $y = f(x_1, \dots, x_k)$ over passively collected trajectories. It cannot construct a physical apparatus or introduce novel probe sequences to tease apart degenerate or aliased states.
- **Inability to Invent Operators:** The grammar consists of standard analytical primitives ($+, -, \times, \div, \sin, \cos, \exp$), fitting equations over *pre-existing* measurements rather than discovering what constitutes a measurement.

---

### 2.2 Automated Scientific Discovery ("Robot Scientists")

#### Foundational Works:
1. **King, R. D., Rowland, J., Oliver, S. G., et al. (2004).** *The Automation of Science.* Science, 324(5923), 85–89. (The *Adam* and *Eve* systems).
2. **Sparkes, A., Aubrey, W., Byrne, E., et al. (2010).** *Towards Robot Scientists for autonomous scientific discovery.* Autom. Exp., 2(1).
3. **Burger, P. B., et al. (2020).** *A mobile robotic chemist.* Nature, 583, 237–241.

#### Paradigmatic Assumptions & Limitations:
- **Predefined Ontologies:** Robot scientists operate on explicit logical ontologies (e.g., yeast functional genomics, chemical compound libraries). Hypotheses are propositions within a predefined relational database (e.g., "Gene $G$ encodes Enzyme $E$").
- **Rigid Physical Measurement Assays:** The assay mechanisms (optical density, mass spectrometry, fluorescence) are engineered by human instrument makers. The system chooses which well to pipet, but cannot invent a new physical or mathematical measurement paradigm.

---

### 2.3 Active Perception & Active Experimental Design

#### Foundational Works:
1. **Bajcsy, R. (1988).** *Active Perception.* Proceedings of the IEEE, 76(8), 996–1005.
2. **Settles, B. (2009).** *Active Learning Literature Survey.* University of Wisconsin-Madison, Computer Sciences Technical Report 1648.
3. **Chaloner, K., & Verdinelli, I. (1995).** *Bayesian experimental design: A review.* Statistical Science, 273–304.
4. **Friston, K., Mattout, J., Trujillo-Barreto, N., Ashburner, J., & Penny, W. (2007).** *Variational free energy and the hypothesis testing brain.* NeuroImage, 36(4), 1271–1292.

#### Paradigmatic Assumptions & Limitations:
- Active learning optimizes sampling trajectories ($x^* = \arg\max \mathbb{I}(y; \theta | x)$) over known input spaces.
- Active perception typically repositions a camera or sensor without changing the mathematical definition of what constitutes an observation channel.

---

### 2.4 Evolutionary Feature Construction & Genetic Programming

#### Foundational Works:
1. **Koza, J. R. (1992).** *Genetic Programming: On the Programming of Computers by Means of Natural Selection.* MIT Press.
2. **Smith, M. G., & Bull, L. (2005).** *Genetic programming with a genetic algorithm for feature construction and selection.* Genetic Programming and Evolvable Machines, 6(3), 265–281.
3. **Tran, B., Xue, B., & Zhang, M. (2016).** *Genetic programming for feature construction and selection in classification on high-dimensional data.* Pattern Recognition, 49, 142–156.

#### Paradigmatic Assumptions & Limitations:
- Feature construction builds composite algebraic trees to maximize a static supervised classification or regression metric (e.g., accuracy, $R^2$).
- Lacks **active probing**: standard feature synthesis does not pair mathematical operators with interventions in the environment.
- Suffers from bloat and over-fitting to narrow sample distributions unless constrained by formal falsification, null-hypothesis testing, and cross-family transfer.

---

### 2.5 Novelty Search, Quality Diversity, and Artificial Life

#### Foundational Works:
1. **Lehman, J., & Stanley, K. O. (2011).** *Abandoning objectives: Evolution through the search for novelty alone.* Evolutionary Computation, 19(2), 189–223.
2. **Pugh, J. K., Soros, L. B., & Stanley, K. O. (2016).** *Quality diversity: A new frontier for evolutionary computation.* Frontiers in Robotics and AI, 3, 40.
3. **Langton, C. G. (1997).** *Artificial Life: An Overview.* MIT Press.

#### Paradigmatic Assumptions & Limitations:
- Novelty search relies on an experimenter-defined **behavior characterization (BC)** vector. The human defines what constitutes "behavior"; the algorithm merely fills the archive.
- In SENSEFORGE, the system itself must discover the behavior characterizations by evolving measurement operators.

---

### 2.6 Information Theory & Causal Discovery

#### Foundational Works:
1. **Pearl, J. (2009).** *Causality: Models, Reasoning, and Inference.* Cambridge University Press.
2. **Schreiber, T. (2000).** *Measuring information transfer.* Physical Review Letters, 85(2), 461.
3. **Shalizi, C. R., & Crutchfield, J. P. (2001).** *Computational mechanics: Pattern and prediction, structure and randomness.* Journal of Statistical Physics, 104(3), 817–879.
4. **Peters, J., Janzing, D., & Schölkopf, B. (2017).** *Elements of Causal Inference: Foundations and Learning Algorithms.* MIT Press.

#### Paradigmatic Assumptions & Limitations:
- Causal discovery (e.g., PC algorithm, FCI, GES) infers DAG structures over observed random variables. Interventions ($do(X=x)$) require that $X$ is already an accessible, manipulable node.
- If the true causal driver is an unobserved dynamical property or an invariant that requires temporal integration, standard causal inference fails due to latent confounders.

---

## 3. Comparative Matrix: Prior Art vs. SENSEFORGE

| Framework | Environment Generation | Observation Interface | Operator Synthesis | Active Probe Synthesis | Falsification / Null Models | Cross-Family Transfer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BACON / AI Feynman** | None (Static) | Static / Fixed | Predefined arithmetic | None (Passive) | Goodness-of-fit | N/A |
| **SINDy** | Continuous ODE/PDE data | Static coordinates | Linear sparse dictionary | None (Passive) | Cross-validation | N/A |
| **Robot Scientist (King et al.)** | Wet-lab biology | Fixed lab assays | Logic predicates | Predefined test selection | Experimental replicates | Domain specific |
| **Active Learning (Settles)** | Static dataset/pool | Fixed feature vectors | None | Point query selection | Statistical margin | N/A |
| **GP Feature Construction** | Static tabular | Fixed table columns | Tree-based algebraic | None (Passive) | Train/Test split | Poor / Overfits |
| **Novelty Search / QD** | Simulated simulator | Fixed behavior vector | None | Policy evolution | Archive distance | Within-distribution |
| **SENSEFORGE (This Work)** | **Autonomous procedural (M01)** | **Strict firewall boundary (M02)** | **Typed symbolic DSL (M03/M05)** | **Intervention probe sequences (M04)** | **Held-out seeds + Permutation tests (M06)** | **Multi-family generalization (M07)** |

---

## 4. Key Gaps in Current Literature

1. **The "Pre-Given Measurement" Fallacy:** Machine learning almost exclusively operates post-measurement. The question of *how* raw interactions with an alien environment can be systematically aggregated into informative, invariant, or predictive scalar/vector quantities remains largely unaddressed.
2. **The Passive-Active Decoupling:** Equation discovery is predominantly passive; active learning is predominantly fixed-feature. Systems that concurrently invent a *measurement metric* and an *experimental excitation protocol* to validate it do not exist in standard toolkits.
3. **Lack of Information Firewalls:** Existing benchmarks frequently leak environmental internals (e.g., simulator physics pointers, global energy variables) into the feature selection loop, corrupting the validity of autonomous discovery claims.

---

## 5. Conclusion

SENSEFORGE establishes a distinct niche at the intersection of symbolic expression synthesis, active experimental design, and procedural dynamical systems. By strictly enforcing an Observation Firewall and mandating falsification through held-out permutation tests and cross-family transfer, SENSEFORGE aims to empirically test whether autonomous systems can bootstrap their own observational vocabularies from first principles.

