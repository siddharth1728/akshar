# SENSEFORGE: Instrument Genome Specification (M03)

**Version:** 0.1.0  
**Phase:** 02 Development  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Ontological Definition of an Instrument Genome

An **Instrument Genome** represents a candidate scientific observation apparatus. In SENSEFORGE, an instrument is not a passive statistical weight vector; it is a **symbolic mathematical expression tree** that operates over observation time series emitted through the Observation Firewall.

Each candidate $\Psi \in \mathcal{G}$ is defined as a tuple:

$$\Psi = \left\langle \text{id}, \; \mathcal{T}, \; \mathcal{C}(\mathcal{T}), \; \Omega_{\text{req}}, \; \tau_{\max}, \; \mathcal{H}_{\text{parents}}, \; \mathcal{H}_{\text{mutations}}, \; s_{\text{gen}} \right\rangle$$

where:
- $\text{id} \in \Sigma^*$: Globally unique identifier (e.g., `inst_a768c2f17008`).
- $\mathcal{T}$: Strongly-typed Abstract Syntax Tree root node (`ExprNode`).
- $\mathcal{C}(\mathcal{T}) = |\text{nodes}(\mathcal{T})| + \text{depth}(\mathcal{T})$: Structural Kolmogorov-like complexity metric.
- $\Omega_{\text{req}} \subset \mathbb{N}$: Minimal set of observation channel indices required to evaluate $\mathcal{T}$.
- $\tau_{\max} \in \mathbb{N}$: Maximum temporal historical lag needed for evaluation.
- $\mathcal{H}_{\text{parents}}$: Tuple of parent genome identifiers.
- $\mathcal{H}_{\text{mutations}}$: Sequence of applied genetic variation tags (`MUTATE_SUBTREE`, `CROSSOVER`, etc.).
- $s_{\text{gen}} \in \mathbb{Z}$: Deterministic pseudo-random generation seed.

---

## 2. Genetic Variation Operators

To autonomously explore the measurement hypothesis space without hardcoded biases or pre-injected formulas, SENSEFORGE implements four variation mechanisms in `GenomeFactory`:

### 2.1 Random Typed Generation
Given target type $\sigma \in \{\text{SCALAR}, \text{SERIES}\}$ and depth bound $D_{\max}$, expressions are grown recursively. Terminal leaves (channels or constants) are chosen with probability increasing with depth to strictly bound tree height.

### 2.2 Subtree Mutation
Selects a random node $u \in \mathcal{T}$ and replaces it with a newly synthesized subtree $u'$ of identical type $\text{Type}(u') = \text{Type}(u)$ whose depth satisfies $\text{depth}(u') \le D_{\max} - \text{depth}(\text{path}(root, u))$.

### 2.3 Operator Mutation
Swaps an internal node's mathematical primitive with an alternative of identical arity and compatible type semantics (e.g., swapping `Add` for `Mul`, or `Tanh` for `Sigmoid`).

### 2.4 Type-Preserving Crossover
Given parent genomes $\Psi_A$ and $\Psi_B$:
1. Collects all subtrees in $\Psi_A$ and $\Psi_B$ categorized by return type ($\text{SERIES}$ or $\text{SCALAR}$).
2. Identifies common type intersection.
3. Swaps type-compatible subtrees to produce two valid offspring $\Psi_{O1}, \Psi_{O2}$ without inducing type errors.

---

## 3. Canonical Serialization & Provenance Tracking

Every instrument genome serializes into a canonical, deterministic JSON representation suitable for SQLite ledger persistence:

```json
{
  "dsl_version": "senseforge.dsl.v1",
  "genome_id": "inst_a768c2f17008",
  "data_type": "SERIES",
  "complexity": 13,
  "depth": 5,
  "node_count": 8,
  "required_channels": [0, 1],
  "max_temporal_lag": 3,
  "generation_seed": 101,
  "parent_ids": [],
  "mutation_history": ["RANDOM_INIT"],
  "expression_ast": {
    "op": "Sub",
    "left": {
      "op": "Covariance",
      "left": {
        "op": "DivSafe",
        "left": {"op": "Channel", "channel_idx": 1},
        "right": {"op": "Constant", "value": 1.222}
      },
      "right": {
        "op": "Diff",
        "child": {"op": "Channel", "channel_idx": 0},
        "param": 3
      }
    },
    "right": {
      "op": "Tanh",
      "child": {"op": "Channel", "channel_idx": 1}
    }
  },
  "expression_str": "Sub(Covariance(DivSafe(Channel(1), Const(1.2220)), Diff(Channel(0), 3)), Tanh(Channel(1)))"
}
```
Reconstruction from this dictionary is deterministic and byte-for-byte identical.

