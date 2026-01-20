"""
Embeddings models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Union


class EmbeddingsRequest(BaseModel):
    """Request for text embeddings."""
    text: Union[str, List[str]] = Field(
        ...,
        description="Text or list of texts to embed"
    )
    model: Optional[str] = Field(
        default=None,
        description="Embedding model to use"
    )
    normalize: bool = Field(
        default=True,
        description="Whether to normalize embeddings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": ["Hello, world!", "How are you?"],
                "normalize": True
            }
        }


class EmbeddingsResponse(BaseModel):
    """Response for embeddings."""
    success: bool = True
    embeddings: List[List[float]] = Field(..., description="Embedding vectors")
    dimensions: int = Field(..., description="Embedding dimensions")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Total tokens processed")
