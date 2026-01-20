"""
Summarization models.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class SummarizeRequest(BaseModel):
    """Request for text summarization."""
    text: str = Field(..., description="Text to summarize", min_length=10)
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum summary length in tokens",
        ge=10,
        le=1024
    )
    min_length: Optional[int] = Field(
        default=None,
        description="Minimum summary length in tokens",
        ge=5
    )
    style: Optional[Literal["bullet", "paragraph", "tldr"]] = Field(
        default="paragraph",
        description="Summary style"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a long article about technology...",
                "max_length": 100,
                "style": "paragraph"
            }
        }


class SummarizeResponse(BaseModel):
    """Response for summarization."""
    success: bool = True
    summary: str = Field(..., description="Generated summary")
    original_length: int = Field(..., description="Original text token count")
    summary_length: int = Field(..., description="Summary token count")
    compression_ratio: float = Field(..., description="Compression ratio")
    model: str = Field(..., description="Model used")
