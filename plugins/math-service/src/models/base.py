"""
Base models for the Math Service.
"""
from datetime import datetime
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail model."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional error details")


class BaseResponse(BaseModel, Generic[T]):
    """Base response model with generic data type."""
    
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(default=None, description="Response data")
    error: Optional[ErrorDetail] = Field(default=None, description="Error details if request failed")
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Response timestamp in ISO format"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "request_id": "abc-123",
                "timestamp": "2026-01-18T12:00:00Z"
            }
        }
