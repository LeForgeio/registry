"""
Classification models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ClassifyRequest(BaseModel):
    """Request for text classification."""
    text: str = Field(..., description="Text to classify", min_length=1)
    categories: List[str] = Field(
        ...,
        description="List of possible categories",
        min_length=2
    )
    model: Optional[str] = Field(default=None)
    multi_label: bool = Field(
        default=False,
        description="Allow multiple category assignments"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "I love this product! It's amazing!",
                "categories": ["positive", "negative", "neutral"]
            }
        }


class CategoryScore(BaseModel):
    """Score for a single category."""
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ClassifyResponse(BaseModel):
    """Response for classification."""
    success: bool = True
    category: str = Field(..., description="Most likely category")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    scores: Optional[List[CategoryScore]] = Field(
        default=None,
        description="Scores for all categories"
    )
    model: str = Field(..., description="Model used")
