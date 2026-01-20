"""
Entity extraction models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ExtractEntitiesRequest(BaseModel):
    """Request for entity extraction."""
    text: str = Field(..., description="Text to extract entities from", min_length=1)
    entity_types: Optional[List[str]] = Field(
        default=None,
        description="Entity types to extract (defaults to all)"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "John Smith works at Google in Mountain View. Contact him at john@google.com.",
                "entity_types": ["person", "organization", "location", "email"]
            }
        }


class Entity(BaseModel):
    """An extracted entity."""
    text: str = Field(..., description="The entity text")
    type: str = Field(..., description="Entity type")
    start: int = Field(..., description="Start character position", ge=0)
    end: int = Field(..., description="End character position", ge=0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ExtractEntitiesResponse(BaseModel):
    """Response for entity extraction."""
    success: bool = True
    entities: List[Entity] = Field(..., description="Extracted entities")
    text: str = Field(..., description="Original text")
    model: str = Field(..., description="Model used")
