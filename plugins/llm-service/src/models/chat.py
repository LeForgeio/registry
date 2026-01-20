"""
Chat models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

from .common import MessageRole, TokenUsage


class ChatMessage(BaseModel):
    """A single chat message."""
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1
    )
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    model: Optional[str] = Field(default=None)
    stream: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "max_tokens": 100
            }
        }


class ChatResponseMessage(BaseModel):
    """Response message from chat completion."""
    role: str = Field(default="assistant", description="Role of the responder")
    content: str = Field(..., description="Message content")


class ChatResponse(BaseModel):
    """Response for chat completion."""
    success: bool = True
    message: ChatResponseMessage = Field(..., description="Assistant's response message")
    tokens_used: int = Field(..., description="Total tokens used")
    usage: Optional[TokenUsage] = Field(default=None)
    model: str = Field(..., description="Model used")
    finish_reason: Optional[str] = Field(default=None)
