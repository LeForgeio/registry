"""
Logical function Pydantic models for Excel-like logical operations.
"""
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class IfRequest(BaseModel):
    """Request for IF operation."""
    condition: bool = Field(..., description="Condition to evaluate")
    value_if_true: Any = Field(..., description="Value if condition is true")
    value_if_false: Any = Field(None, description="Value if condition is false")


class ConditionValuePair(BaseModel):
    """A condition-value pair for IFS."""
    condition: bool = Field(..., description="Condition to evaluate")
    value: Any = Field(..., description="Value if condition is true")


class IfsRequest(BaseModel):
    """Request for IFS operation (multiple conditions)."""
    conditions: List[ConditionValuePair] = Field(..., min_length=1, description="List of condition-value pairs")


class SwitchRequest(BaseModel):
    """Request for SWITCH operation."""
    expression: Any = Field(..., description="Expression to match")
    cases: List[tuple] = Field(..., description="List of (match_value, result) tuples")
    default: Any = Field(None, description="Default value if no match")


class LogicalArrayRequest(BaseModel):
    """Request for AND/OR/XOR with array of booleans."""
    values: List[bool] = Field(..., min_length=1, description="List of boolean values")


class NotRequest(BaseModel):
    """Request for NOT operation."""
    value: bool = Field(..., description="Boolean value to negate")


class CompareRequest(BaseModel):
    """Request for comparison operations."""
    value1: Union[int, float, str] = Field(..., description="First value")
    value2: Union[int, float, str] = Field(..., description="Second value")
    operator: str = Field(..., description="Comparison operator: eq, ne, gt, gte, lt, lte")


class IfErrorRequest(BaseModel):
    """Request for IFERROR/IFNA operations."""
    value: Any = Field(..., description="Value to check")
    is_error: bool = Field(False, description="Whether the value is an error")
    value_if_error: Any = Field(..., description="Value to return if error")


class ChooseRequest(BaseModel):
    """Request for CHOOSE operation."""
    index_num: int = Field(..., ge=1, description="Index to select (1-based)")
    values: List[Any] = Field(..., min_length=1, description="Values to choose from")


class LogicalResponse(BaseModel):
    """Response for logical operations."""
    result: Any
    operation: str


class BooleanResponse(BaseModel):
    """Response for boolean operations."""
    result: bool
    operation: str
    inputs: List[bool]
