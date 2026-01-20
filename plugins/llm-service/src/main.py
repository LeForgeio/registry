"""
LLM Service - FastAPI wrapper for vLLM

A production-ready LLM inference service providing:
- Text generation with streaming
- Chat completion
- Text classification
- Entity extraction
- Text summarization
- Embeddings generation
"""
import asyncio
import signal
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .config import settings
from .routes import (
    generate_router,
    chat_router,
    classify_router,
    extract_router,
    summarize_router,
    embeddings_router,
    health_router,
    vision_router,
    transform_router,
)
from .services import get_vllm_client, get_embedding_service, get_queue_service


def configure_logging():
    """Configure loguru logging."""
    import sys

    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{extra[request_id]} | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        serialize=settings.environment == "production",
    )

    # Add file handler in production
    if settings.environment == "production":
        logger.add(
            f"/var/log/{settings.service_name}/app.log",
            rotation="100 MB",
            retention="7 days",
            compression="gz",
            level="INFO",
            serialize=True,
        )

    logger.configure(extra={"request_id": "-"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Manages startup and shutdown of services.
    """
    from .services import get_vision_service, close_vision_service
    from .services import get_transform_service, close_transform_service
    
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"vLLM URL: {settings.vllm_base_url}")
    logger.info(f"Default model: {settings.default_model}")

    # Initialize services
    vllm_client = get_vllm_client()

    # Pre-warm embedding model
    if settings.enable_embeddings:
        logger.info("Pre-warming embedding model...")
        embedding_service = get_embedding_service()
        await embedding_service.load_model()
        logger.info("Embedding model ready")

    # Connect to Redis if queue enabled
    if settings.enable_queue:
        logger.info("Connecting to Redis queue...")
        queue_service = get_queue_service()
        await queue_service.connect()
        logger.info("Queue service ready")

    # Initialize vision service
    if settings.enable_vision:
        logger.info(f"Initializing vision service with model: {settings.vision_model}")
        get_vision_service()
        logger.info("Vision service ready")

    # Initialize transform service
    logger.info("Initializing transform service...")
    get_transform_service()
    logger.info("Transform service ready")

    # Check vLLM health
    health = await vllm_client.check_health()
    if health.get("status") == "healthy":
        logger.info(f"vLLM server healthy, models: {health.get('models', [])}")
    else:
        logger.warning(f"vLLM server not ready: {health}")

    logger.info("LLM Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down LLM Service...")

    # Close vision service
    if settings.enable_vision:
        await close_vision_service()
        logger.info("Vision service closed")

    # Close transform service
    await close_transform_service()
    logger.info("Transform service closed")

    # Close queue connection
    if settings.enable_queue:
        queue_service = get_queue_service()
        await queue_service.close()
        logger.info("Queue service closed")

    # Close vLLM client
    await vllm_client.close()
    logger.info("vLLM client closed")

    logger.info("LLM Service stopped")


# Configure logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.service_name,
    description="""
## LLM Service

A production-ready wrapper around vLLM for on-premise LLM inference.

### Features

- **Text Generation**: Generate text with streaming support
- **Chat Completion**: Multi-turn conversations
- **Classification**: Categorize text into predefined classes
- **Entity Extraction**: Extract structured information from text
- **Summarization**: Generate summaries with length control
- **Embeddings**: Generate text embeddings for semantic search

### Authentication

All endpoints require a valid API key passed via `X-API-Key` header.

### Rate Limiting

Rate limits are applied per API key. See response headers for limit info.
    """,
    version=settings.service_version,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to all requests."""
    import uuid

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id

    # Add to logger context
    with logger.contextualize(request_id=request_id):
        response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests."""
    import time

    start_time = time.time()

    # Skip health checks in logs
    if request.url.path in ["/health/live", "/health/ready"]:
        return await call_next(request)

    logger.info(f"{request.method} {request.url.path}")

    response = await call_next(request)

    duration = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}ms"
    )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
        },
    )


# Include routers
app.include_router(health_router, prefix="", tags=["Health"])
app.include_router(generate_router, prefix="/api/v1", tags=["Generation"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(classify_router, prefix="/api/v1", tags=["Classification"])
app.include_router(extract_router, prefix="/api/v1", tags=["Extraction"])
app.include_router(summarize_router, prefix="/api/v1", tags=["Summarization"])
app.include_router(embeddings_router, prefix="/api/v1", tags=["Embeddings"])
app.include_router(vision_router, prefix="/api/v1", tags=["Vision"])
app.include_router(transform_router, prefix="/api/v1", tags=["Transform"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "docs": "/docs",
        "health": "/health",
    }


def run():
    """Run the service."""
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        workers=1 if settings.environment == "development" else settings.workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
