"""
SENSEFORGE M03: Instrument Genome
Represents evolvable measurement operators with genetic variation operators:
random generation, subtree mutation, operator mutation, constant mutation,
and validity-preserving crossover.
"""

from typing import List, Tuple, Set, Optional, Dict, Any
import uuid
import copy
import numpy as np

from senseforge.genome.types import DataType, TypeValidationError
from senseforge.genome.ast import (
    ExprNode,
    ChannelNode,
    ConstantNode,
    UnaryOpNode,
    BinaryOpNode,
    ast_from_dict,
)
from senseforge.genome.evaluator import EvaluationConfig


class InstrumentGenome:
    """
    Candidate measurement instrument genome containing the mathematical operator AST
    and complete provenance tracking.
    """

    def __init__(
        self,
        expression: ExprNode,
        generation_seed: int,
        genome_id: Optional[str] = None,
        parent_ids: Optional[Tuple[str, ...]] = None,
        mutation_history: Optional[List[str]] = None,
    ):
        self.genome_id = genome_id or f"inst_{uuid.uuid4().hex[:12]}"
        self.expression = expression
        self.generation_seed = generation_seed
        self.parent_ids = parent_ids or ()
        self.mutation_history = mutation_history or []
        self.evaluation_history: List[Dict[str, Any]] = []

    @property
    def data_type(self) -> DataType:
        return self.expression.data_type

    @property
    def depth(self) -> int:
        return self.expression.depth

    @property
    def node_count(self) -> int:
        return self.expression.node_count

    @property
    def complexity(self) -> int:
        """Structural complexity: node count + tree depth."""
        return self.expression.node_count + self.expression.depth

    @property
    def required_channels(self) -> Set[int]:
        return self.expression.required_channels

    @property
    def max_temporal_lag(self) -> int:
        return self.expression.max_temporal_lag

    def clone(self) -> "InstrumentGenome":
        """Deep clone with new ID and parent linkage."""
        cloned = copy.deepcopy(self)
        cloned.genome_id = f"inst_{uuid.uuid4().hex[:12]}"
        cloned.parent_ids = (self.genome_id,)
        return cloned

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Canonical dictionary representation for SQLite persistence and JSON serialization."""
        return {
            "dsl_version": "senseforge.dsl.v1",
            "genome_id": self.genome_id,
            "data_type": self.data_type.value,
            "complexity": self.complexity,
            "depth": self.depth,
            "node_count": self.node_count,
            "required_channels": sorted(list(self.required_channels)),
            "max_temporal_lag": self.max_temporal_lag,
            "generation_seed": self.generation_seed,
            "parent_ids": list(self.parent_ids),
            "mutation_history": self.mutation_history,
            "expression_ast": self.expression.to_canonical_dict(),
            "expression_str": self.expression.to_canonical_str(),
        }

    @classmethod
    def from_canonical_dict(cls, d: Dict[str, Any]) -> "InstrumentGenome":
        """Reconstructs candidate from canonical dictionary."""
        expr = ast_from_dict(d["expression_ast"])
        inst = cls(
            expression=expr,
            generation_seed=d["generation_seed"],
            genome_id=d["genome_id"],
            parent_ids=tuple(d.get("parent_ids", ())),
            mutation_history=d.get("mutation_history", []),
        )
        return inst


# --- Evolutionary Generation & Variation Engine ---

class GenomeFactory:
    """Generates and mutates InstrumentGenomes under strict type and depth constraints."""

    UNARY_SERIES_OPS = ["Diff", "Lag", "RollingMean", "RollingVar", "Abs", "Tanh", "Sigmoid", "Clip"]
    UNARY_COLLAPSE_OPS = ["Mean", "Variance"]
    BINARY_ARITHMETIC_OPS = ["Add", "Sub", "Mul", "DivSafe"]
    BINARY_SERIES_COLLAPSE_OPS = ["Covariance", "Correlation"]

    @classmethod
    def generate_random_ast(
        cls,
        target_type: DataType,
        allowed_channels: List[int],
        max_depth: int,
        rng: np.random.Generator,
        current_depth: int = 1
    ) -> ExprNode:
        """
        Recursively builds a typed, valid AST tree up to max_depth.
        """
        if current_depth >= max_depth:
            # Must return a leaf/terminal
            if target_type == DataType.SERIES:
                ch = int(rng.choice(allowed_channels))
                return ChannelNode(channel_idx=ch)
            else:
                val = float(rng.uniform(-2.0, 2.0))
                return ConstantNode(value=val)

        # Decide whether to place a leaf or an internal operator
        # P(terminal) increases as depth approaches max_depth
        p_terminal = 0.2 + 0.6 * (current_depth / max_depth)
        if rng.random() < p_terminal and current_depth > 1:
            if target_type == DataType.SERIES:
                ch = int(rng.choice(allowed_channels))
                return ChannelNode(channel_idx=ch)
            else:
                val = float(rng.uniform(-2.0, 2.0))
                return ConstantNode(value=val)

        if target_type == DataType.SERIES:
            # Can be: UnaryOp on SERIES, or BinaryOp (SERIES x SERIES, or SERIES x SCALAR)
            choice = rng.choice(["unary_series", "binary_arithmetic"])
            if choice == "unary_series":
                op = str(rng.choice(cls.UNARY_SERIES_OPS))
                child = cls.generate_random_ast(DataType.SERIES, allowed_channels, max_depth, rng, current_depth + 1)
                param = None
                if op in {"Diff", "Lag"}:
                    param = int(rng.integers(1, 5))
                elif op in {"RollingMean", "RollingVar"}:
                    param = int(rng.integers(3, 16))
                elif op == "Clip":
                    param = [-2.0, 2.0]
                return UnaryOpNode(op_name=op, child=child, param=param)

            else:
                op = str(rng.choice(cls.BINARY_ARITHMETIC_OPS))
                # For arithmetic to produce SERIES, at least one argument must be SERIES
                left_type = DataType.SERIES if rng.random() < 0.7 else DataType.SCALAR
                right_type = DataType.SERIES if left_type == DataType.SCALAR else (DataType.SERIES if rng.random() < 0.5 else DataType.SCALAR)
                left = cls.generate_random_ast(left_type, allowed_channels, max_depth, rng, current_depth + 1)
                right = cls.generate_random_ast(right_type, allowed_channels, max_depth, rng, current_depth + 1)
                return BinaryOpNode(op_name=op, left=left, right=right)

        else: # target_type == DataType.SCALAR
            choice = rng.choice(["constant", "unary_collapse", "binary_collapse", "binary_arithmetic"])
            if choice == "constant":
                val = float(rng.uniform(-2.0, 2.0))
                return ConstantNode(value=val)

            elif choice == "unary_collapse":
                op = str(rng.choice(cls.UNARY_COLLAPSE_OPS))
                child = cls.generate_random_ast(DataType.SERIES, allowed_channels, max_depth, rng, current_depth + 1)
                return UnaryOpNode(op_name=op, child=child)

            elif choice == "binary_collapse":
                op = str(rng.choice(cls.BINARY_SERIES_COLLAPSE_OPS))
                left = cls.generate_random_ast(DataType.SERIES, allowed_channels, max_depth, rng, current_depth + 1)
                right = cls.generate_random_ast(DataType.SERIES, allowed_channels, max_depth, rng, current_depth + 1)
                return BinaryOpNode(op_name=op, left=left, right=right)

            else:
                op = str(rng.choice(cls.BINARY_ARITHMETIC_OPS))
                left = cls.generate_random_ast(DataType.SCALAR, allowed_channels, max_depth, rng, current_depth + 1)
                right = cls.generate_random_ast(DataType.SCALAR, allowed_channels, max_depth, rng, current_depth + 1)
                return BinaryOpNode(op_name=op, left=left, right=right)

    @classmethod
    def create_random_genome(
        cls,
        seed: int,
        allowed_channels: List[int],
        target_type: DataType = DataType.SERIES,
        max_depth: int = 5
    ) -> InstrumentGenome:
        """Creates a fresh, random, validated candidate genome."""
        rng = np.random.default_rng(seed)
        tree = cls.generate_random_ast(target_type, allowed_channels, max_depth, rng)
        return InstrumentGenome(
            expression=tree,
            generation_seed=seed,
            mutation_history=["RANDOM_INIT"],
        )

    # --- Genetic Mutations ---

    @classmethod
    def mutate_constant(cls, genome: InstrumentGenome, rng: np.random.Generator) -> InstrumentGenome:
        """Perturbs a constant node within the tree with Gaussian noise."""
        cloned = genome.clone()
        constants = []

        def find_constants(node: ExprNode):
            if isinstance(node, ConstantNode):
                constants.append(node)
            elif isinstance(node, UnaryOpNode):
                find_constants(node.child)
            elif isinstance(node, BinaryOpNode):
                find_constants(node.left)
                find_constants(node.right)

        find_constants(cloned.expression)
        if constants:
            target = rng.choice(constants)
            target.value = float(np.clip(target.value + rng.normal(0.0, 0.2), -10.0, 10.0))
            cloned.mutation_history.append("MUTATE_CONSTANT")
        return cloned

    @classmethod
    def mutate_operator(cls, genome: InstrumentGenome, rng: np.random.Generator) -> InstrumentGenome:
        """Swaps an operator for an arity- and type-compatible alternative."""
        cloned = genome.clone()
        candidates = []

        def find_operators(node: ExprNode):
            if isinstance(node, (UnaryOpNode, BinaryOpNode)):
                candidates.append(node)
            if isinstance(node, UnaryOpNode):
                find_operators(node.child)
            elif isinstance(node, BinaryOpNode):
                find_operators(node.left)
                find_operators(node.right)

        find_operators(cloned.expression)
        if candidates:
            target = rng.choice(candidates)
            if isinstance(target, BinaryOpNode) and target.op_name in cls.BINARY_ARITHMETIC_OPS:
                choices = [op for op in cls.BINARY_ARITHMETIC_OPS if op != target.op_name]
                target.op_name = str(rng.choice(choices))
                cloned.mutation_history.append(f"MUTATE_OP({target.op_name})")
            elif isinstance(target, UnaryOpNode) and target.op_name in {"Abs", "Tanh", "Sigmoid"}:
                choices = [op for op in ["Abs", "Tanh", "Sigmoid"] if op != target.op_name]
                target.op_name = str(rng.choice(choices))
                cloned.mutation_history.append(f"MUTATE_OP({target.op_name})")
        return cloned

    @classmethod
    def mutate_subtree(
        cls,
        genome: InstrumentGenome,
        allowed_channels: List[int],
        max_depth: int,
        rng: np.random.Generator
    ) -> InstrumentGenome:
        """Replaces a randomly chosen sub-node with a newly generated typed subtree."""
        cloned = genome.clone()
        subtrees = []

        def collect_nodes(node: ExprNode, parent: Optional[ExprNode] = None, slot: Optional[str] = None):
            subtrees.append((node, parent, slot))
            if isinstance(node, UnaryOpNode):
                collect_nodes(node.child, node, "child")
            elif isinstance(node, BinaryOpNode):
                collect_nodes(node.left, node, "left")
                collect_nodes(node.right, node, "right")

        collect_nodes(cloned.expression)
        node, parent, slot = subtrees[int(rng.integers(0, len(subtrees)))]
        remaining_depth = max(2, max_depth - (cloned.depth - node.depth))
        new_sub = cls.generate_random_ast(node.data_type, allowed_channels, remaining_depth, rng)

        if parent is None:
            cloned.expression = new_sub
        else:
            setattr(parent, slot, new_sub)

        cloned.mutation_history.append("MUTATE_SUBTREE")
        return cloned

    # --- Genetic Crossover ---

    @classmethod
    def crossover(
        cls,
        parent_a: InstrumentGenome,
        parent_b: InstrumentGenome,
        rng: np.random.Generator
    ) -> Tuple[InstrumentGenome, InstrumentGenome]:
        """
        Type-preserving subtree crossover: selects type-compatible subtrees from
        both parents and exchanges them.
        """
        offspring_a = parent_a.clone()
        offspring_b = parent_b.clone()

        def collect_nodes_by_type(node: ExprNode, parent=None, slot=None, acc=None):
            if acc is None:
                acc = {DataType.SERIES: [], DataType.SCALAR: []}
            acc[node.data_type].append((node, parent, slot))
            if isinstance(node, UnaryOpNode):
                collect_nodes_by_type(node.child, node, "child", acc)
            elif isinstance(node, BinaryOpNode):
                collect_nodes_by_type(node.left, node, "left", acc)
                collect_nodes_by_type(node.right, node, "right", acc)
            return acc

        nodes_a = collect_nodes_by_type(offspring_a.expression)
        nodes_b = collect_nodes_by_type(offspring_b.expression)

        # Pick a data type that both parents have nodes for
        avail_types = [t for t in [DataType.SERIES, DataType.SCALAR] if nodes_a[t] and nodes_b[t]]
        if not avail_types:
            # Fallback if no matching types (rare)
            return offspring_a, offspring_b

        chosen_type = rng.choice(avail_types)
        node_a, parent_a_node, slot_a = nodes_a[chosen_type][int(rng.integers(0, len(nodes_a[chosen_type])))]
        node_b, parent_b_node, slot_b = nodes_b[chosen_type][int(rng.integers(0, len(nodes_b[chosen_type])))]

        # Clone subtrees before exchange
        sub_a_clone = node_a.clone()
        sub_b_clone = node_b.clone()

        if parent_a_node is None:
            offspring_a.expression = sub_b_clone
        else:
            setattr(parent_a_node, slot_a, sub_b_clone)

        if parent_b_node is None:
            offspring_b.expression = sub_a_clone
        else:
            setattr(parent_b_node, slot_b, sub_a_clone)

        offspring_a.parent_ids = (parent_a.genome_id, parent_b.genome_id)
        offspring_b.parent_ids = (parent_a.genome_id, parent_b.genome_id)
        offspring_a.mutation_history.append("CROSSOVER")
        offspring_b.mutation_history.append("CROSSOVER")

        return offspring_a, offspring_b

