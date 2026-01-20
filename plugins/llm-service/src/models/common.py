"""
Common Pydantic models shared across the service.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class MessageRole(str, Enum):
    """Role in a chat message."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class EntityType(str, Enum):
    """Standard entity types for extraction."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    PERCENTAGE = "percentage"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    PRODUCT = "product"
    EVENT = "event"
    CUSTOM = "custom"


class TokenUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(default=None, description="Additional error details")
