"""
Health Check Routes
"""
import time
from datetime import datetime
from fastapi import APIRouter
from loguru import logger

from ..config import settings
from ..models import HealthResponse, ModelsResponse, ModelInfo, QueueStatus
from ..services import get_vllm_client, get_embedding_service, get_queue_service

router = APIRouter(tags=["Health"])

# Track start time for uptime calculation
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the LLM service and its dependencies.",
)
async def health_check():
    """
    Comprehensive health check.

    Returns status of:
    - vLLM server connection
    - Embedding model
    - Redis queue (if enabled)
    """
    checks = {}

    # Check vLLM server
    vllm_client = get_vllm_client()
    vllm_health = await vllm_client.check_health()
    checks["vllm"] = vllm_health

    # Check embedding service
    embedding_service = get_embedding_service()
    checks["embeddings"] = {
        "status": "healthy" if embedding_service.is_loaded() else "not_loaded",
        "model": embedding_service.model_name,
    }

    # Check queue if enabled
    if settings.enable_queue:
        queue_service = get_queue_service()
        queue_status = await queue_service.get_status()
        checks["queue"] = {
            "status": "healthy" if queue_status["connected"] else "unhealthy",
            **queue_status,
        }

    # Determine overall status
    vllm_ok = vllm_health.get("status") == "healthy"

    if vllm_ok:
        status = "healthy"
    elif not vllm_ok and embedding_service.is_loaded():
        status = "degraded"  # Can still do embeddings
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
    vllm_client = get_vllm_client()
    vllm_health = await vllm_client.check_health()

    if vllm_health.get("status") == "healthy":
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}

    return {
        "status": "not_ready",
        "reason": "vLLM server not available",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List models",
    description="List available models.",
)
async def list_models():
    """
    List available models.

    Returns both LLM models from vLLM and local embedding models.
    """
    vllm_client = get_vllm_client()
    embedding_service = get_embedding_service()

    # Get vLLM models
    vllm_models = await vllm_client.list_models()

    models = []

    # Add vLLM models
    for model_name in vllm_models:
        models.append(ModelInfo(
            name=model_name,
            loaded=True,
            capabilities=["generate", "chat", "classify", "extract", "summarize"],
        ))

    # If no vLLM models, add default
    if not vllm_models:
        models.append(ModelInfo(
            name=settings.default_model,
            loaded=False,
            capabilities=["generate", "chat", "classify", "extract", "summarize"],
        ))

    # Add embedding model
    embedding_info = embedding_service.get_info()
    models.append(ModelInfo(
        name=embedding_info["name"],
        loaded=embedding_info["loaded"],
        capabilities=embedding_info["capabilities"],
    ))

    return ModelsResponse(
        models=models,
        default_model=settings.default_model,
        default_embedding_model=settings.default_embedding_model,
    )


@router.get(
    "/queue/status",
    response_model=QueueStatus,
    summary="Queue status",
    description="Get the status of the request queue.",
)
async def queue_status():
    """Get queue status."""
    queue_service = get_queue_service()
    status = await queue_service.get_status()

    return QueueStatus(
        enabled=status["enabled"],
        pending_requests=status["pending_requests"],
        processing_requests=status["processing_requests"],
        queue_name=status["queue_name"],
    )


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
        "default_model": settings.default_model,
        "default_embedding_model": settings.default_embedding_model,
        "default_max_tokens": settings.default_max_tokens,
        "default_temperature": settings.default_temperature,
        "max_input_tokens": settings.max_input_tokens,
        "max_output_tokens": settings.max_output_tokens,
        "request_timeout": settings.request_timeout,
        "enable_queue": settings.enable_queue,
        "enable_metrics": settings.enable_metrics,
    }
