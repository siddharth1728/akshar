"""
Scientific, Property, and Metamorphic Tests for InstrumentGenome & Measurement DSL (M03)
"""

import pytest
import numpy as np

from senseforge.genome.types import DataType, TypeValidationError
from senseforge.genome.ast import (
    ChannelNode,
    ConstantNode,
    UnaryOpNode,
    BinaryOpNode,
    ast_from_dict,
)
from senseforge.genome.evaluator import (
    SafeEvaluator,
    EvaluationConfig,
    EvaluationResult,
    EvaluationBudgetExceededError,
    EvaluationNumericalError,
    EvaluationError,
)
from senseforge.genome.candidate import (
    InstrumentGenome,
    GenomeFactory,
)
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.worldfoundry import WorldFoundry


# --- 1. Type Correctness & Semantic Validation ---

def test_ast_type_validation_diff_requires_series():
    """Diff operator applied to a SCALAR constant must raise TypeValidationError."""
    const = ConstantNode(3.14)
    with pytest.raises(TypeValidationError, match="requires a SERIES"):
        UnaryOpNode(op_name="Diff", child=const)


def test_ast_type_validation_covariance_requires_two_series():
    """Covariance between a SERIES and a SCALAR must raise TypeValidationError."""
    ch = ChannelNode(0)
    const = ConstantNode(1.0)
    with pytest.raises(TypeValidationError, match="requires two SERIES"):
        BinaryOpNode(op_name="Covariance", left=ch, right=const)


def test_ast_arithmetic_broadcasting_type_inference():
    """SERIES + SCALAR produces SERIES; SCALAR + SCALAR produces SCALAR."""
    ch = ChannelNode(0)
    const = ConstantNode(2.5)
    add_series = BinaryOpNode("Add", ch, const)
    assert add_series.data_type == DataType.SERIES

    add_scalar = BinaryOpNode("Add", const, const)
    assert add_scalar.data_type == DataType.SCALAR


# --- 2. Random Generation & Structural Limits ---

@pytest.mark.parametrize("target_type", [DataType.SERIES, DataType.SCALAR])
def test_random_genome_generation(target_type: DataType):
    """Random genomes generated across seeds must strictly respect type and max_depth."""
    allowed = [0, 1, 2]
    for seed in range(20):
        genome = GenomeFactory.create_random_genome(
            seed=seed,
            allowed_channels=allowed,
            target_type=target_type,
            max_depth=5
        )
        assert genome.data_type == target_type
        assert genome.depth <= 5
        assert genome.complexity > 0
        for ch in genome.required_channels:
            assert ch in allowed


# --- 3. Genetic Mutations ---

def test_genetic_mutations_preserve_validity():
    """All three mutation types must preserve valid AST structure and types."""
    rng = np.random.default_rng(42)
    allowed = [0, 1]
    genome = GenomeFactory.create_random_genome(100, allowed, DataType.SERIES, max_depth=4)

    # 1. Mutate constant
    mut_const = GenomeFactory.mutate_constant(genome, rng)
    assert mut_const.data_type == genome.data_type

    # 2. Mutate operator
    mut_op = GenomeFactory.mutate_operator(genome, rng)
    assert mut_op.data_type == genome.data_type

    # 3. Mutate subtree
    mut_sub = GenomeFactory.mutate_subtree(genome, allowed, max_depth=5, rng=rng)
    assert mut_sub.data_type == genome.data_type
    assert mut_sub.depth <= 5


# --- 4. Crossover Validity ---

def test_crossover_produces_valid_offspring():
    """Crossover between two parents must produce two structurally and type-valid offspring."""
    rng = np.random.default_rng(777)
    allowed = [0, 1]
    parent_a = GenomeFactory.create_random_genome(1, allowed, DataType.SERIES, max_depth=4)
    parent_b = GenomeFactory.create_random_genome(2, allowed, DataType.SERIES, max_depth=4)

    off_a, off_b = GenomeFactory.crossover(parent_a, parent_b, rng)
    assert off_a.data_type == DataType.SERIES
    assert off_b.data_type == DataType.SERIES
    assert off_a.genome_id != parent_a.genome_id
    assert off_b.genome_id != parent_b.genome_id
    assert parent_a.genome_id in off_a.parent_ids


# --- 5. Deterministic Evaluation ---

def test_deterministic_evaluation():
    """Evaluating identical AST over identical inputs yields byte-for-byte identical output."""
    obs = {
        0: np.linspace(0.0, 10.0, 50),
        1: np.sin(np.linspace(0.0, 10.0, 50))
    }
    # AST: Diff(Channel(0), 1) + Channel(1) * 2.0
    expr = BinaryOpNode(
        "Add",
        UnaryOpNode("Diff", ChannelNode(0), param=1),
        BinaryOpNode("Mul", ChannelNode(1), ConstantNode(2.0))
    )

    evaluator = SafeEvaluator()
    res1 = evaluator.evaluate(expr, obs)
    res2 = evaluator.evaluate(expr, obs)

    np.testing.assert_array_equal(res1.value, res2.value)
    assert res1.ops_performed == res2.ops_performed


# --- 6. Numerical Safeguards (Protected Division & Safeguards) ---

def test_protected_division_zero_denominator():
    """Protected division by zero must not raise FloatingPointError or produce NaN/Inf."""
    obs = {0: np.array([1.0, 2.0, 3.0]), 1: np.array([0.0, 0.0, 0.0])}
    expr = BinaryOpNode("DivSafe", ChannelNode(0), ChannelNode(1))

    evaluator = SafeEvaluator()
    res = evaluator.evaluate(expr, obs)
    assert isinstance(res.value, np.ndarray)
    assert not np.isnan(res.value).any()
    assert not np.isinf(res.value).any()


def test_rejection_of_nan_input():
    """Observation containing NaN must trigger EvaluationNumericalError."""
    obs = {0: np.array([1.0, float("nan"), 3.0])}
    expr = ChannelNode(0)
    evaluator = SafeEvaluator()
    with pytest.raises(EvaluationNumericalError):
        evaluator.evaluate(expr, obs)


# --- 7. Resource Budget Enforcement ---

def test_operation_budget_exceeded():
    """An expression that triggers too many operations must be aborted with budget error."""
    # Long observation series with low op budget
    obs = {0: np.ones(5000)}
    expr = UnaryOpNode("RollingMean", ChannelNode(0), param=10)

    strict_evaluator = SafeEvaluator(EvaluationConfig(max_ops=500))
    with pytest.raises(EvaluationBudgetExceededError):
        strict_evaluator.evaluate(expr, obs)


# --- 8. Canonical Serialization & Reconstruction ---

def test_canonical_json_roundtrip():
    """Genomes serialized to canonical dictionary must reconstruct with identical structure."""
    allowed = [0, 1]
    original = GenomeFactory.create_random_genome(888, allowed, DataType.SERIES, max_depth=4)
    d = original.to_canonical_dict()

    reconstructed = InstrumentGenome.from_canonical_dict(d)
    assert reconstructed.genome_id == original.genome_id
    assert reconstructed.data_type == original.data_type
    assert reconstructed.complexity == original.complexity
    assert reconstructed.to_canonical_dict() == d


# --- 9. Metamorphic Mathematical Tests ---

def test_metamorphic_diff_of_constant_is_zero():
    """METAMORPHIC: The Diff operator of any constant series must be exactly zero."""
    obs = {0: np.full(50, 42.0)}
    expr = UnaryOpNode("Diff", ChannelNode(0), param=1)
    evaluator = SafeEvaluator()
    res = evaluator.evaluate(expr, obs)
    # Beyond index tau=1, difference of constant is 0.0
    np.testing.assert_array_equal(res.value[1:], np.zeros(49))


def test_metamorphic_subtraction_self_is_zero():
    """METAMORPHIC: Any expression subtracted from itself must equal zero."""
    obs = {0: np.random.default_rng(42).normal(size=50)}
    expr = BinaryOpNode("Sub", ChannelNode(0), ChannelNode(0))
    evaluator = SafeEvaluator()
    res = evaluator.evaluate(expr, obs)
    np.testing.assert_allclose(res.value, np.zeros(50), atol=1e-12)


def test_metamorphic_mean_of_constant():
    """METAMORPHIC: Mean of a constant series must equal the constant."""
    val = 17.5
    obs = {0: np.full(100, val)}
    expr = UnaryOpNode("Mean", ChannelNode(0))
    evaluator = SafeEvaluator()
    res = evaluator.evaluate(expr, obs)
    assert pytest.approx(res.value) == val


def test_metamorphic_variance_of_constant():
    """METAMORPHIC: Variance of a constant series must be 0.0."""
    obs = {0: np.full(100, 99.0)}
    expr = UnaryOpNode("Variance", ChannelNode(0))
    evaluator = SafeEvaluator()
    res = evaluator.evaluate(expr, obs)
    assert pytest.approx(res.value, abs=1e-12) == 0.0


# --- 10. Observation-Only Operation with WorldFoundry ---

def test_evaluation_over_procedural_worldfoundry_observations():
    """
    Evaluates dynamically evolved candidate instruments over real procedural
    observations emitted from an active WorldFoundry environment.
    """
    firewall = WorldFoundry.spawn_sandboxed_environment(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=123,
        allowed_channels=[0, 1],
        num_entities=8
    )

    # Collect 30 time steps of observations through the firewall
    buffer_ch0 = []
    buffer_ch1 = []
    for _ in range(30):
        frame = firewall.probe([0.1, -0.1])
        buffer_ch0.append(frame.readings[0])
        buffer_ch1.append(frame.readings[1])

    obs = {
        0: np.array(buffer_ch0),
        1: np.array(buffer_ch1)
    }

    # Generate 10 random candidates and evaluate each on procedural observations
    evaluator = SafeEvaluator()
    for seed in range(10):
        candidate = GenomeFactory.create_random_genome(
            seed=seed,
            allowed_channels=[0, 1],
            target_type=DataType.SERIES,
            max_depth=4
        )
        res = evaluator.evaluate(candidate.expression, obs)
        assert isinstance(res, EvaluationResult)
        assert res.data_type == DataType.SERIES
        assert len(res.value) == 30
        assert not np.isnan(res.value).any()

