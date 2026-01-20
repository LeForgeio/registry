"""
Generation models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

from .common import TokenUsage


class GenerateRequest(BaseModel):
    """Request for text generation."""
    prompt: str = Field(..., description="The prompt to generate from", min_length=1)
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate",
        ge=1,
        le=4096
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Sampling temperature",
        ge=0.0,
        le=2.0
    )
    top_p: Optional[float] = Field(
        default=None,
        description="Top-p (nucleus) sampling",
        ge=0.0,
        le=1.0
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Top-k sampling",
        ge=1
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="Stop sequences"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use (defaults to configured model)"
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Write a haiku about coding:",
                "max_tokens": 50,
                "temperature": 0.7
            }
        }


class GenerateResponse(BaseModel):
    """Response for text generation."""
    success: bool = True
    text: str = Field(..., description="Generated text")
    tokens_used: int = Field(..., description="Total tokens used")
    usage: Optional[TokenUsage] = Field(default=None, description="Detailed token usage")
    model: str = Field(..., description="Model used for generation")
    finish_reason: Optional[str] = Field(default=None, description="Reason for finishing")
