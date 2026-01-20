"""
Pydantic models for Excel-like operations.
"""
from typing import Any, Optional, Literal, Union
from pydantic import BaseModel, Field


class VLookupRequest(BaseModel):
    """Request model for VLOOKUP operation."""
    
    lookup_value: Union[str, int, float] = Field(
        ...,
        description="Value to search for in the first column"
    )
    table_array: list[list[Any]] = Field(
        ...,
        description="2D array (table) to search",
        min_length=1,
        json_schema_extra={
            "example": [
                ["A001", "Widget", 10.99],
                ["A002", "Gadget", 25.50],
                ["A003", "Gizmo", 15.00]
            ]
        }
    )
    col_index: int = Field(
        ...,
        description="Column index to return (1-based)",
        ge=1
    )
    exact_match: bool = Field(
        default=True,
        description="Whether to require exact match (True) or approximate match (False)"
    )


class VLookupData(BaseModel):
    """VLOOKUP result data."""
    
    result: Any = Field(..., description="Found value or None if not found")
    found: bool = Field(..., description="Whether a match was found")
    lookup_value: Union[str, int, float] = Field(..., description="Original lookup value")
    row_index: Optional[int] = Field(default=None, description="Row index where match was found (0-based)")


class VLookupResponse(BaseModel):
    """Response model for VLOOKUP."""
    
    success: bool
    data: VLookupData
    request_id: Optional[str] = None
    timestamp: str


class SumIfRequest(BaseModel):
    """Request model for SUMIF operation."""
    
    range_values: list[Any] = Field(
        ...,
        description="Range of values to evaluate against criteria",
        min_length=1,
        json_schema_extra={"example": ["Apple", "Banana", "Apple", "Orange", "Apple"]}
    )
    criteria: str = Field(
        ...,
        description="Criteria to match (supports >, <, >=, <=, <>, =, and wildcards */?)",
        json_schema_extra={"example": "Apple"}
    )
    sum_range: Optional[list[Union[int, float]]] = Field(
        default=None,
        description="Range of values to sum (if different from range_values)",
        json_schema_extra={"example": [100, 50, 75, 200, 150]}
    )


class SumIfData(BaseModel):
    """SUMIF result data."""
    
    result: float = Field(..., description="Sum of values matching criteria")
    matches_count: int = Field(..., description="Number of matches found")
    criteria: str = Field(..., description="Criteria used")


class SumIfResponse(BaseModel):
    """Response model for SUMIF."""
    
    success: bool
    data: SumIfData
    request_id: Optional[str] = None
    timestamp: str


class PivotAggregation(BaseModel):
    """Aggregation configuration for pivot table."""
    
    column: str = Field(..., description="Column name to aggregate")
    function: Literal["sum", "count", "mean", "min", "max", "std", "var", "first", "last"] = Field(
        default="sum",
        description="Aggregation function"
    )
    alias: Optional[str] = Field(
        default=None,
        description="Optional alias for the aggregated column"
    )


class PivotRequest(BaseModel):
    """Request model for pivot table operation."""
    
    data: list[dict[str, Any]] = Field(
        ...,
        description="Array of objects (records) to pivot",
        min_length=1,
        json_schema_extra={
            "example": [
                {"region": "North", "product": "A", "sales": 100},
                {"region": "North", "product": "B", "sales": 150},
                {"region": "South", "product": "A", "sales": 200},
                {"region": "South", "product": "B", "sales": 250}
            ]
        }
    )
    rows: list[str] = Field(
        ...,
        description="Column names to use as row indices",
        min_length=1,
        json_schema_extra={"example": ["region"]}
    )
    columns: Optional[list[str]] = Field(
        default=None,
        description="Column names to use as column headers",
        json_schema_extra={"example": ["product"]}
    )
    values: list[PivotAggregation] = Field(
        ...,
        description="Aggregations to perform",
        min_length=1
    )
    fill_value: Optional[Union[int, float, str]] = Field(
        default=0,
        description="Value to fill missing cells"
    )


class PivotData(BaseModel):
    """Pivot table result data."""
    
    table: list[dict[str, Any]] = Field(
        ...,
        description="Pivoted data as array of records"
    )
    rows: list[str] = Field(..., description="Row indices used")
    columns: Optional[list[str]] = Field(default=None, description="Column indices used")
    aggregations: list[str] = Field(..., description="Aggregations performed")
    shape: dict[str, int] = Field(
        ...,
        description="Shape of result table",
        json_schema_extra={"example": {"rows": 2, "columns": 3}}
    )


class PivotResponse(BaseModel):
    """Response model for pivot table."""
    
    success: bool
    data: PivotData
    request_id: Optional[str] = None
    timestamp: str


class HLookupRequest(BaseModel):
    """Request model for HLOOKUP operation."""
    
    lookup_value: Union[str, int, float] = Field(
        ...,
        description="Value to search for in the first row"
    )
    table_array: list[list[Any]] = Field(
        ...,
        description="2D array (table) to search",
        min_length=1
    )
    row_index: int = Field(
        ...,
        description="Row index to return (1-based)",
        ge=1
    )
    exact_match: bool = Field(
        default=True,
        description="Whether to require exact match"
    )


class CountIfRequest(BaseModel):
    """Request model for COUNTIF operation."""
    
    range_values: list[Any] = Field(
        ...,
        description="Range of values to count",
        min_length=1
    )
    criteria: str = Field(
        ...,
        description="Criteria to match"
    )


class AverageIfRequest(BaseModel):
    """Request model for AVERAGEIF operation."""
    
    range_values: list[Any] = Field(
        ...,
        description="Range of values to evaluate"
    )
    criteria: str = Field(
        ...,
        description="Criteria to match"
    )
    average_range: Optional[list[Union[int, float]]] = Field(
        default=None,
        description="Range of values to average"
    )
