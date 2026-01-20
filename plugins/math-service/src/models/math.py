"""
Math function Pydantic models for Excel-like math operations.
"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class SingleNumberRequest(BaseModel):
    """Request with a single number."""
    value: Union[int, float] = Field(..., description="Number to operate on")


class TwoNumberRequest(BaseModel):
    """Request with two numbers."""
    value1: Union[int, float] = Field(..., description="First number")
    value2: Union[int, float] = Field(..., description="Second number")


class RoundRequest(BaseModel):
    """Request for rounding operations."""
    value: Union[int, float] = Field(..., description="Number to round")
    num_digits: int = Field(0, description="Number of decimal places")


class CeilingFloorRequest(BaseModel):
    """Request for CEILING/FLOOR operations."""
    value: Union[int, float] = Field(..., description="Number to round")
    significance: Union[int, float] = Field(1, description="Multiple to round to")


class PowerRequest(BaseModel):
    """Request for POWER operation."""
    base: Union[int, float] = Field(..., description="Base number")
    exponent: Union[int, float] = Field(..., description="Exponent")


class LogRequest(BaseModel):
    """Request for LOG operation."""
    value: Union[int, float] = Field(..., gt=0, description="Number (must be positive)")
    base: Union[int, float] = Field(10, gt=0, description="Logarithm base")


class NumberArrayRequest(BaseModel):
    """Request with an array of numbers."""
    values: List[Union[int, float]] = Field(..., min_length=1, description="Array of numbers")


class GcdLcmRequest(BaseModel):
    """Request for GCD/LCM operations."""
    values: List[int] = Field(..., min_length=2, description="List of integers")


class RandomRequest(BaseModel):
    """Request for random number generation."""
    count: int = Field(1, ge=1, le=10000, description="Number of random values to generate")


class RandBetweenRequest(BaseModel):
    """Request for RANDBETWEEN operation."""
    bottom: int = Field(..., description="Minimum value")
    top: int = Field(..., description="Maximum value")
    count: int = Field(1, ge=1, le=10000, description="Number of values to generate")


class TrigRequest(BaseModel):
    """Request for trigonometric operations."""
    angle: Union[int, float] = Field(..., description="Angle in radians")


class AngleConvertRequest(BaseModel):
    """Request for angle conversion."""
    value: Union[int, float] = Field(..., description="Angle value to convert")


class CombPermRequest(BaseModel):
    """Request for COMBIN/PERMUT operations."""
    n: int = Field(..., ge=0, description="Total number of items")
    k: int = Field(..., ge=0, description="Number of items to choose")


class FactorialRequest(BaseModel):
    """Request for factorial operation."""
    value: int = Field(..., ge=0, le=170, description="Non-negative integer (max 170)")


class ProductRequest(BaseModel):
    """Request for PRODUCT operation."""
    values: List[Union[int, float]] = Field(..., min_length=1, description="Numbers to multiply")


class SumProductRequest(BaseModel):
    """Request for SUMPRODUCT operation."""
    arrays: List[List[Union[int, float]]] = Field(..., min_length=2, description="Arrays to multiply and sum")


class QuotientRequest(BaseModel):
    """Request for QUOTIENT operation."""
    numerator: Union[int, float] = Field(..., description="Numerator")
    denominator: Union[int, float] = Field(..., description="Denominator (non-zero)")


class MathResponse(BaseModel):
    """Response for math operations."""
    result: Union[int, float]
    operation: str


class ArrayMathResponse(BaseModel):
    """Response for array math operations."""
    result: List[Union[int, float]]
    count: int
    operation: str


class TrigResponse(BaseModel):
    """Response for trigonometric operations."""
    result: float
    input_radians: float
    input_degrees: float
    operation: str
