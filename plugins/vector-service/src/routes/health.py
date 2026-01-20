"""
Health Check Routes
"""
import time
from datetime import datetime
from fastapi import APIRouter
from loguru import logger

from ..config import settings
from ..models import HealthResponse
from ..services import get_qdrant_service, get_embedding_service

router = APIRouter(tags=["Health"])

# Track start time for uptime calculation
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the Vector service and its dependencies.",
)
async def health_check():
    """
    Comprehensive health check.

    Returns status of:
    - Qdrant connection
    - Embedding service
    """
    checks = {}

    # Check Qdrant
    qdrant = get_qdrant_service()
    qdrant_health = await qdrant.check_health()
    checks["qdrant"] = qdrant_health

    # Check embedding service
    embedding_service = get_embedding_service()
    embedding_health = await embedding_service.check_health()
    checks["embeddings"] = embedding_health

    # Determine overall status
    qdrant_ok = qdrant_health.get("status") == "healthy"
    embedding_ok = embedding_health.get("status") in ["healthy", "not_loaded"]

    if qdrant_ok and embedding_ok:
        status = "healthy"
    elif qdrant_ok:
        status = "degraded"  # Qdrant works but embeddings may not
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=settings.service_version,
        uptime=time.time() - _start_time,
        checks=checks,
    )


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes.",
)
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Readiness check for Kubernetes.",
)
async def readiness():
    """Kubernetes readiness probe."""
    qdrant = get_qdrant_service()
    qdrant_health = await qdrant.check_health()

    if qdrant_health.get("status") == "healthy":
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}

    return {
        "status": "not_ready",
        "reason": "Qdrant not available",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get(
    "/config",
    summary="Service configuration",
    description="Get non-sensitive service configuration.",
)
async def get_config():
    """Get service configuration (non-sensitive)."""
    return {
        "service_name": settings.service_name,
        "service_version": settings.service_version,
        "environment": settings.environment,
        "qdrant_host": settings.qdrant_host,
        "qdrant_port": settings.qdrant_port,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "default_batch_size": settings.default_batch_size,
        "default_search_limit": settings.default_search_limit,
        "max_search_limit": settings.max_search_limit,
    }


@router.get(
    "/embedding-info",
    summary="Embedding info",
    description="Get information about the embedding service.",
)
async def embedding_info():
    """Get embedding service information."""
    embedding_service = get_embedding_service()
    return await embedding_service.check_health()
