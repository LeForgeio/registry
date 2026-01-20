"""
Health and status models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


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


class QueueStatus(BaseModel):
    """Queue status information."""
    enabled: bool
    pending_requests: int
    processing_requests: int
    queue_name: str
