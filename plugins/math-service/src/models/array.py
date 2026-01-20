"""
Array function Pydantic models for Excel-like array operations.
"""
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class ArrayRequest(BaseModel):
    """Request with a single array."""
    values: List[Any] = Field(..., min_length=1, description="Array of values")


class SortRequest(BaseModel):
    """Request for SORT operation."""
    values: List[Any] = Field(..., min_length=1, description="Array to sort")
    descending: bool = Field(False, description="Sort in descending order")


class SortByRequest(BaseModel):
    """Request for SORTBY operation."""
    values: List[Any] = Field(..., min_length=1, description="Array to sort")
    sort_by: List[Any] = Field(..., description="Array to sort by")
    descending: bool = Field(False, description="Sort in descending order")


class FilterRequest(BaseModel):
    """Request for FILTER operation."""
    values: List[Any] = Field(..., min_length=1, description="Array to filter")
    criteria: List[bool] = Field(..., description="Boolean array indicating which elements to include")
    if_empty: Any = Field(None, description="Value to return if no matches")


class SequenceRequest(BaseModel):
    """Request for SEQUENCE operation."""
    rows: int = Field(..., ge=1, description="Number of rows")
    columns: int = Field(1, ge=1, description="Number of columns")
    start: Union[int, float] = Field(1, description="Starting number")
    step: Union[int, float] = Field(1, description="Step between numbers")


class Matrix2DRequest(BaseModel):
    """Request for 2D matrix operations."""
    matrix: List[List[Any]] = Field(..., min_length=1, description="2D matrix")


class TakeRequest(BaseModel):
    """Request for TAKE operation."""
    values: List[Any] = Field(..., min_length=1, description="Array of values")
    rows: int = Field(..., description="Number of rows to take (negative for from end)")


class DropRequest(BaseModel):
    """Request for DROP operation."""
    values: List[Any] = Field(..., min_length=1, description="Array of values")
    rows: int = Field(..., description="Number of rows to drop (negative for from end)")


class ChunkRequest(BaseModel):
    """Request for chunking array."""
    values: List[Any] = Field(..., min_length=1, description="Array of values")
    size: int = Field(..., ge=1, description="Chunk size")


class SliceRequest(BaseModel):
    """Request for array slicing."""
    values: List[Any] = Field(..., min_length=1, description="Array of values")
    start: int = Field(0, description="Start index (0-based)")
    end: Optional[int] = Field(None, description="End index (exclusive)")
    step: int = Field(1, description="Step size")


class SearchRequest(BaseModel):
    """Request for search operations (contains, index-of)."""
    values: List[Any] = Field(..., min_length=1, description="Array to search in")
    search_value: Any = Field(..., description="Value to search for")


class ExpandRequest(BaseModel):
    """Request for EXPAND operation."""
    values: List[Any] = Field(..., description="Array to expand")
    rows: int = Field(..., ge=1, description="Target number of rows")
    pad_with: Any = Field(None, description="Value to pad with")


class ArrayResponse(BaseModel):
    """Response for array operations."""
    result: List[Any]
    count: int
    operation: str


class Matrix2DResponse(BaseModel):
    """Response for 2D matrix operations."""
    result: List[List[Any]]
    rows: int
    columns: int
    operation: str


class ScalarResponse(BaseModel):
    """Response for operations returning a single value."""
    result: Any
    operation: str
