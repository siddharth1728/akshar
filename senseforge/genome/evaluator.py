"""
SENSEFORGE M03: Safe AST Evaluator
Executes measurement expression trees deterministically without eval/exec.
Enforces structural caps, computational budgets, and numerical safeguards.
"""

from typing import Dict, Any, Union, Optional
import numpy as np
from dataclasses import dataclass
from senseforge.genome.types import DataType, TypeValidationError
from senseforge.genome.ast import ExprNode, ChannelNode, ConstantNode, UnaryOpNode, BinaryOpNode


class EvaluationError(Exception):
    """Base exception for expression evaluation failures."""
    pass


class EvaluationBudgetExceededError(EvaluationError):
    """Raised when an expression exceeds its allotted operation budget."""
    pass


class EvaluationNumericalError(EvaluationError):
    """Raised when an evaluation produces NaN, Inf, or invalid numerical outputs."""
    pass


@dataclass(frozen=True)
class EvaluationConfig:
    max_depth: int = 8
    max_nodes: int = 64
    max_window: int = 64
    max_tau: int = 32
    max_ops: int = 10_000
    div_eps: float = 1e-6


@dataclass(frozen=True)
class EvaluationResult:
    data_type: DataType
    value: Union[float, np.ndarray]
    ops_performed: int
    temporal_steps_used: int


class SafeEvaluator:
    """
    Sandboxed AST interpreter executing typed expressions over observation arrays.
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()
        self._ops_count = 0

    def evaluate(
        self,
        expr: ExprNode,
        observations: Dict[int, np.ndarray]
    ) -> EvaluationResult:
        """
        Safely evaluates an expression against observation time-series channels.
        observations: mapping from channel_idx to 1D float array of time-ordered observations.
        """
        # 1. Structural pre-validation
        if expr.depth > self.config.max_depth:
            raise EvaluationError(f"Expression depth {expr.depth} exceeds max_depth {self.config.max_depth}")
        if expr.node_count > self.config.max_nodes:
            raise EvaluationError(f"Expression size {expr.node_count} nodes exceeds max_nodes {self.config.max_nodes}")

        # Check channel availability
        for ch in expr.required_channels:
            if ch not in observations:
                raise EvaluationError(f"Required channel {ch} missing from observation buffer")
            if len(observations[ch]) == 0:
                raise EvaluationError(f"Observation channel {ch} is empty")

        # Determine time series length
        sample_ch = next(iter(expr.required_channels)) if expr.required_channels else None
        t_len = len(observations[sample_ch]) if sample_ch is not None else 1

        if expr.max_temporal_lag >= t_len and expr.data_type == DataType.SERIES:
            raise EvaluationError(
                f"Expression requires lag {expr.max_temporal_lag}, but observation length is only {t_len}"
            )

        self._ops_count = 0
        raw_val = self._eval_node(expr, observations)

        # 2. Numerical validation
        if isinstance(raw_val, np.ndarray):
            if np.isnan(raw_val).any() or np.isinf(raw_val).any():
                raise EvaluationNumericalError("Evaluation produced NaN or infinite values in series result")
        elif isinstance(raw_val, (float, np.floating)):
            if np.isnan(raw_val) or np.isinf(raw_val):
                raise EvaluationNumericalError("Evaluation produced NaN or infinite scalar result")
            raw_val = float(raw_val)

        return EvaluationResult(
            data_type=expr.data_type,
            value=raw_val,
            ops_performed=self._ops_count,
            temporal_steps_used=t_len,
        )

    def _tick_op(self, count: int = 1):
        self._ops_count += count
        if self._ops_count > self.config.max_ops:
            raise EvaluationBudgetExceededError(
                f"Evaluation exceeded computational budget of {self.config.max_ops} operations"
            )

    def _eval_node(
        self,
        node: ExprNode,
        observations: Dict[int, np.ndarray]
    ) -> Union[float, np.ndarray]:
        self._tick_op(1)

        if isinstance(node, ChannelNode):
            return np.array(observations[node.channel_idx], dtype=np.float64)

        elif isinstance(node, ConstantNode):
            return float(node.value)

        elif isinstance(node, UnaryOpNode):
            child_val = self._eval_node(node.child, observations)
            op = node.op_name

            if op == "Diff":
                tau = int(node.param) if node.param is not None else 1
                if not isinstance(child_val, np.ndarray) or len(child_val) <= tau:
                    raise EvaluationError("Diff requires SERIES array longer than tau")
                self._tick_op(len(child_val))
                diff_res = np.zeros_like(child_val)
                diff_res[tau:] = child_val[tau:] - child_val[:-tau]
                return diff_res

            elif op == "Lag":
                tau = int(node.param) if node.param is not None else 1
                if not isinstance(child_val, np.ndarray) or len(child_val) <= tau:
                    raise EvaluationError("Lag requires SERIES array longer than tau")
                self._tick_op(len(child_val))
                lag_res = np.zeros_like(child_val)
                lag_res[tau:] = child_val[:-tau]
                lag_res[:tau] = child_val[0]  # Edge fill with initial value
                return lag_res

            elif op == "RollingMean":
                w = int(node.param) if node.param is not None else 5
                if not isinstance(child_val, np.ndarray) or len(child_val) == 0:
                    raise EvaluationError("RollingMean requires non-empty SERIES array")
                self._tick_op(len(child_val) * 2)
                # Compute cumulative moving average with boundary padding
                cs = np.cumsum(np.insert(child_val, 0, 0.0))
                w_eff = np.minimum(np.arange(1, len(child_val) + 1), w)
                idx_low = np.maximum(0, np.arange(len(child_val)) - w + 1)
                idx_high = np.arange(1, len(child_val) + 1)
                return (cs[idx_high] - cs[idx_low]) / w_eff

            elif op == "RollingVar":
                w = int(node.param) if node.param is not None else 5
                if not isinstance(child_val, np.ndarray) or len(child_val) == 0:
                    raise EvaluationError("RollingVar requires non-empty SERIES array")
                self._tick_op(len(child_val) * 4)
                # Rolling variance via E[X^2] - (E[X])^2
                mean_x = self._eval_node(UnaryOpNode("RollingMean", node.child, w), observations)
                mean_x2 = self._eval_node(
                    UnaryOpNode("RollingMean", BinaryOpNode("Mul", node.child, node.child), w),
                    observations
                )
                var = np.maximum(0.0, mean_x2 - (mean_x ** 2))
                return var

            elif op == "Mean":
                if not isinstance(child_val, np.ndarray) or len(child_val) == 0:
                    raise EvaluationError("Mean requires non-empty SERIES")
                self._tick_op(len(child_val))
                return float(np.mean(child_val))

            elif op == "Variance":
                if not isinstance(child_val, np.ndarray) or len(child_val) == 0:
                    raise EvaluationError("Variance requires non-empty SERIES")
                self._tick_op(len(child_val))
                return float(np.var(child_val))

            elif op == "Abs":
                self._tick_op(len(child_val) if isinstance(child_val, np.ndarray) else 1)
                return np.abs(child_val)

            elif op == "Tanh":
                self._tick_op(len(child_val) if isinstance(child_val, np.ndarray) else 1)
                return np.tanh(child_val)

            elif op == "Sigmoid":
                self._tick_op(len(child_val) if isinstance(child_val, np.ndarray) else 1)
                clipped = np.clip(child_val, -50.0, 50.0)
                return 1.0 / (1.0 + np.exp(-clipped))

            elif op == "Clip":
                min_v, max_v = node.param if node.param is not None else (-1.0, 1.0)
                self._tick_op(len(child_val) if isinstance(child_val, np.ndarray) else 1)
                return np.clip(child_val, min_v, max_v)

            else:
                raise EvaluationError(f"Unsupported unary operator: {op}")

        elif isinstance(node, BinaryOpNode):
            left_val = self._eval_node(node.left, observations)
            right_val = self._eval_node(node.right, observations)
            op = node.op_name

            if op == "Add":
                self._tick_op(max(np.size(left_val), np.size(right_val)))
                return left_val + right_val

            elif op == "Sub":
                self._tick_op(max(np.size(left_val), np.size(right_val)))
                return left_val - right_val

            elif op == "Mul":
                self._tick_op(max(np.size(left_val), np.size(right_val)))
                return left_val * right_val

            elif op == "DivSafe":
                self._tick_op(max(np.size(left_val), np.size(right_val)))
                eps = self.config.div_eps
                # Regularized denominator: sign(denom) * eps added when abs(denom) is near zero
                if isinstance(right_val, np.ndarray):
                    denom = np.where(np.abs(right_val) < eps, np.sign(right_val + 1e-12) * eps, right_val)
                else:
                    denom = right_val if abs(right_val) >= eps else (np.sign(right_val + 1e-12) * eps)
                return left_val / denom

            elif op == "Covariance":
                if not (isinstance(left_val, np.ndarray) and isinstance(right_val, np.ndarray)):
                    raise EvaluationError("Covariance requires two SERIES arrays")
                n = min(len(left_val), len(right_val))
                if n < 2:
                    return 0.0
                self._tick_op(n * 2)
                cov = np.cov(left_val[:n], right_val[:n])[0, 1]
                return float(cov)

            elif op == "Correlation":
                if not (isinstance(left_val, np.ndarray) and isinstance(right_val, np.ndarray)):
                    raise EvaluationError("Correlation requires two SERIES arrays")
                n = min(len(left_val), len(right_val))
                if n < 2:
                    return 0.0
                self._tick_op(n * 4)
                v1 = np.var(left_val[:n])
                v2 = np.var(right_val[:n])
                if v1 < 1e-12 or v2 < 1e-12:
                    return 0.0
                corr = np.corrcoef(left_val[:n], right_val[:n])[0, 1]
                if np.isnan(corr):
                    return 0.0
                return float(np.clip(corr, -1.0, 1.0))

            else:
                raise EvaluationError(f"Unsupported binary operator: {op}")

        else:
            raise EvaluationError(f"Unknown node type: {type(node)}")

