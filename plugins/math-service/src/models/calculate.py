"""
Pydantic models for calculation endpoints.
"""
from typing import Any, Optional, Union
from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    """Request model for expression calculation."""
    
    expression: str = Field(
        ...,
        description="Mathematical expression to evaluate",
        min_length=1,
        max_length=1000,
        json_schema_extra={"example": "2 + 2 * 10"}
    )
    variables: Optional[dict[str, Union[int, float]]] = Field(
        default=None,
        description="Variables to substitute in the expression",
        json_schema_extra={"example": {"x": 5, "y": 10}}
    )
    precision: int = Field(
        default=10,
        ge=1,
        le=15,
        description="Decimal precision for result"
    )
    use_symbolic: bool = Field(
        default=False,
        description="Use symbolic computation (SymPy) for complex expressions"
    )


class CalculateData(BaseModel):
    """Data returned from calculation."""
    
    result: Union[int, float, str] = Field(..., description="Calculation result")
    expression: str = Field(..., description="Original expression")
    variables: Optional[dict[str, Union[int, float]]] = Field(
        default=None,
        description="Variables used"
    )
    precision: int = Field(..., description="Precision used")


class CalculateResponse(BaseModel):
    """Response model for calculation."""
    
    success: bool = Field(..., description="Whether the calculation succeeded")
    data: dict[str, Any] = Field(..., description="Calculation result data")
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")
    timestamp: str = Field(..., description="Response timestamp")
