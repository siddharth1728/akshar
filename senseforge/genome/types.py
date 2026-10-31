"""
SENSEFORGE M03: Measurement DSL Type System
Defines explicit types and semantic validation rules for mathematical expressions.
"""

from enum import Enum
from typing import Dict, Any


class DataType(Enum):
    SCALAR = "SCALAR"
    SERIES = "SERIES"


class TypeValidationError(Exception):
    """Raised when an expression AST violates type consistency rules."""
    pass


def validate_unary_op_type(op_name: str, arg_type: DataType) -> DataType:
    """
    Validates operand type for unary operators and returns the resulting type.
    """
    if op_name in {"Diff", "Lag", "RollingMean", "RollingVar"}:
        if arg_type != DataType.SERIES:
            raise TypeValidationError(f"Operator '{op_name}' requires a SERIES input, but received {arg_type.value}")
        return DataType.SERIES

    elif op_name in {"Mean", "Variance"}:
        if arg_type != DataType.SERIES:
            raise TypeValidationError(f"Operator '{op_name}' requires a SERIES input to collapse, but received {arg_type.value}")
        return DataType.SCALAR

    elif op_name in {"Abs", "Tanh", "Sigmoid", "Clip"}:
        # Mathematical maps preserve input type (elementwise)
        return arg_type

    else:
        raise TypeValidationError(f"Unknown unary operator: {op_name}")


def validate_binary_op_type(op_name: str, left_type: DataType, right_type: DataType) -> DataType:
    """
    Validates operand types for binary operators and returns the resulting type.
    """
    if op_name in {"Covariance", "Correlation"}:
        if left_type != DataType.SERIES or right_type != DataType.SERIES:
            raise TypeValidationError(
                f"Operator '{op_name}' requires two SERIES inputs, but received ({left_type.value}, {right_type.value})"
            )
        return DataType.SCALAR

    elif op_name in {"Add", "Sub", "Mul", "DivSafe"}:
        # Arithmetic broadcasting:
        # SERIES op SERIES -> SERIES
        # SERIES op SCALAR -> SERIES
        # SCALAR op SERIES -> SERIES
        # SCALAR op SCALAR -> SCALAR
        if left_type == DataType.SERIES or right_type == DataType.SERIES:
            return DataType.SERIES
        return DataType.SCALAR

    else:
        raise TypeValidationError(f"Unknown binary operator: {op_name}")

