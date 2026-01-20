"""
Information function Pydantic models for Excel-like information functions.
"""
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class ValueRequest(BaseModel):
    """Request with a single value of any type."""
    value: Any = Field(..., description="Value to check")


class NumberCheckRequest(BaseModel):
    """Request for number type checking."""
    value: Union[int, float] = Field(..., description="Number to check")


class TextCheckRequest(BaseModel):
    """Request for text checking."""
    value: str = Field(..., description="Text to check")


class ArrayCheckRequest(BaseModel):
    """Request for checking array values."""
    values: List[Any] = Field(..., description="Array of values to check")


class InfoResponse(BaseModel):
    """Response for information functions."""
    result: bool
    value: Any
    operation: str


class TypeResponse(BaseModel):
    """Response for TYPE function."""
    type_code: int
    type_name: str
    value: Any
    operation: str


class ArrayInfoResponse(BaseModel):
    """Response for array information functions."""
    results: List[bool]
    count_true: int
    count_false: int
    operation: str
