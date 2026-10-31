"""
SENSEFORGE M03: Measurement Abstract Syntax Tree (AST)
Typed, composable mathematical expression nodes for scientific instrumentation.
"""

from abc import ABC, abstractmethod
from typing import Set, Dict, Any, List, Optional
import copy
from senseforge.genome.types import (
    DataType,
    TypeValidationError,
    validate_unary_op_type,
    validate_binary_op_type,
)


class ExprNode(ABC):
    """Abstract base class for all expression tree nodes."""

    @property
    @abstractmethod
    def data_type(self) -> DataType:
        """Returns the inferred return type of this sub-expression."""
        pass

    @property
    @abstractmethod
    def depth(self) -> int:
        """Tree depth of this sub-expression (1 for leaf)."""
        pass

    @property
    @abstractmethod
    def node_count(self) -> int:
        """Total number of nodes in this subtree."""
        pass

    @property
    @abstractmethod
    def required_channels(self) -> Set[int]:
        """Set of observation channel indices referenced by this subtree."""
        pass

    @property
    @abstractmethod
    def max_temporal_lag(self) -> int:
        """Maximum historical steps required by this subtree."""
        pass

    @abstractmethod
    def to_canonical_dict(self) -> Dict[str, Any]:
        """Serializes node to a canonical dictionary representation."""
        pass

    @abstractmethod
    def to_canonical_str(self) -> str:
        """S-expression style string representation."""
        pass

    def clone(self) -> "ExprNode":
        """Deep clone of this expression tree."""
        return copy.deepcopy(self)


# --- Terminals ---

class ChannelNode(ExprNode):
    """Selects an observation channel time-series."""

    def __init__(self, channel_idx: int):
        if not isinstance(channel_idx, int) or channel_idx < 0:
            raise ValueError(f"Invalid channel_idx: {channel_idx}")
        self.channel_idx = channel_idx

    @property
    def data_type(self) -> DataType:
        return DataType.SERIES

    @property
    def depth(self) -> int:
        return 1

    @property
    def node_count(self) -> int:
        return 1

    @property
    def required_channels(self) -> Set[int]:
        return {self.channel_idx}

    @property
    def max_temporal_lag(self) -> int:
        return 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"op": "Channel", "channel_idx": self.channel_idx}

    def to_canonical_str(self) -> str:
        return f"Channel({self.channel_idx})"


class ConstantNode(ExprNode):
    """Scalar constant."""

    def __init__(self, value: float):
        val = float(value)
        if not (-1e6 <= val <= 1e6):
            raise ValueError(f"Constant value out of bounds: {val}")
        self.value = val

    @property
    def data_type(self) -> DataType:
        return DataType.SCALAR

    @property
    def depth(self) -> int:
        return 1

    @property
    def node_count(self) -> int:
        return 1

    @property
    def required_channels(self) -> Set[int]:
        return set()

    @property
    def max_temporal_lag(self) -> int:
        return 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"op": "Constant", "value": round(self.value, 6)}

    def to_canonical_str(self) -> str:
        return f"Const({self.value:.4f})"


# --- Unary / Temporal Operators ---

class UnaryOpNode(ExprNode):
    """Base class for unary operations."""

    def __init__(self, op_name: str, child: ExprNode, param: Optional[Any] = None):
        self.op_name = op_name
        self.child = child
        self.param = param
        self._data_type = validate_unary_op_type(op_name, child.data_type)

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @property
    def depth(self) -> int:
        return 1 + self.child.depth

    @property
    def node_count(self) -> int:
        return 1 + self.child.node_count

    @property
    def required_channels(self) -> Set[int]:
        return self.child.required_channels

    @property
    def max_temporal_lag(self) -> int:
        lag = self.child.max_temporal_lag
        if self.op_name in {"Diff", "Lag"} and isinstance(self.param, int):
            lag += self.param
        elif self.op_name in {"RollingMean", "RollingVar"} and isinstance(self.param, int):
            lag += self.param
        return lag

    def to_canonical_dict(self) -> Dict[str, Any]:
        d = {"op": self.op_name, "child": self.child.to_canonical_dict()}
        if self.param is not None:
            d["param"] = self.param
        return d

    def to_canonical_str(self) -> str:
        if self.param is not None:
            return f"{self.op_name}({self.child.to_canonical_str()}, {self.param})"
        return f"{self.op_name}({self.child.to_canonical_str()})"


# --- Binary Operators ---

class BinaryOpNode(ExprNode):
    """Base class for binary operations."""

    def __init__(self, op_name: str, left: ExprNode, right: ExprNode, param: Optional[Any] = None):
        self.op_name = op_name
        self.left = left
        self.right = right
        self.param = param
        self._data_type = validate_binary_op_type(op_name, left.data_type, right.data_type)

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @property
    def depth(self) -> int:
        return 1 + max(self.left.depth, self.right.depth)

    @property
    def node_count(self) -> int:
        return 1 + self.left.node_count + self.right.node_count

    @property
    def required_channels(self) -> Set[int]:
        return self.left.required_channels.union(self.right.required_channels)

    @property
    def max_temporal_lag(self) -> int:
        return max(self.left.max_temporal_lag, self.right.max_temporal_lag)

    def to_canonical_dict(self) -> Dict[str, Any]:
        d = {
            "op": self.op_name,
            "left": self.left.to_canonical_dict(),
            "right": self.right.to_canonical_dict(),
        }
        if self.param is not None:
            d["param"] = self.param
        return d

    def to_canonical_str(self) -> str:
        return f"{self.op_name}({self.left.to_canonical_str()}, {self.right.to_canonical_str()})"


# --- AST Serialization & Reconstruction ---

def ast_from_dict(d: Dict[str, Any]) -> ExprNode:
    """Reconstructs a strongly-typed ExprNode tree from canonical JSON dictionary."""
    if not isinstance(d, dict) or "op" not in d:
        raise ValueError(f"Invalid AST node dictionary: {d}")

    op = d["op"]

    if op == "Channel":
        return ChannelNode(channel_idx=d["channel_idx"])

    elif op == "Constant":
        return ConstantNode(value=d["value"])

    elif op in {"Diff", "Lag", "RollingMean", "RollingVar"}:
        child = ast_from_dict(d["child"])
        param = d.get("param", 1)
        return UnaryOpNode(op_name=op, child=child, param=param)

    elif op in {"Mean", "Variance", "Abs", "Tanh", "Sigmoid"}:
        child = ast_from_dict(d["child"])
        return UnaryOpNode(op_name=op, child=child)

    elif op == "Clip":
        child = ast_from_dict(d["child"])
        param = d.get("param", [-1.0, 1.0])
        return UnaryOpNode(op_name=op, child=child, param=param)

    elif op in {"Add", "Sub", "Mul", "DivSafe", "Covariance", "Correlation"}:
        left = ast_from_dict(d["left"])
        right = ast_from_dict(d["right"])
        param = d.get("param")
        return BinaryOpNode(op_name=op, left=left, right=right, param=param)

    else:
        raise ValueError(f"Unrecognized AST operator: {op}")
