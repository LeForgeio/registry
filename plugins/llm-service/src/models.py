"""
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from enum import Enum


# ============ Enums ============

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


# ============ Common Models ============

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


# ============ Text Generation ============

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


# ============ Chat Completion ============

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


# ============ Classification ============

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


# ============ Entity Extraction ============

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


# ============ Summarization ============

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


# ============ Embeddings ============

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


# ============ Health & Status ============

class ModelInfo(BaseModel):
    """Information about a loaded model."""
    name: str
    loaded: bool
    size_mb: Optional[float] = None
    max_context: Optional[int] = None
    capabilities: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "unhealthy", "degraded"]
    timestamp: str
    version: str
    uptime: float
    checks: dict


class ModelsResponse(BaseModel):
    """List of available models."""
    models: List[ModelInfo]
    default_model: str
    default_embedding_model: str


# ============ Queue Status ============

class QueueStatus(BaseModel):
    """Queue status information."""
    enabled: bool
    pending_requests: int
    processing_requests: int
    queue_name: str
