"""
Vector Service - FastAPI application for semantic search and RAG

A production-ready vector database service providing:
- Collection management
- Vector upsert and search
- Text-to-vector conversion
- Hybrid search (vector + keyword)
- Recommendations
"""
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .config import settings
from .routes import collections_router, vectors_router, health_router
from .services import (
    get_qdrant_service,
    get_embedding_service,
    close_qdrant_service,
    close_embedding_service,
)


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

    logger.configure(extra={"request_id": "-"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Manages startup and shutdown of services.
    """
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    logger.info(f"Embedding provider: {settings.embedding_provider}")

    # Connect to Qdrant
    qdrant = get_qdrant_service()
    try:
        await qdrant.connect()
        logger.info("Connected to Qdrant")
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        # Continue anyway - might recover later

    # Pre-warm embedding model if local
    if settings.embedding_provider == "local":
        logger.info("Pre-warming embedding model...")
        embedding_service = get_embedding_service()
        try:
            await embedding_service.generate_single("warmup")
            logger.info(f"Embedding model ready: {embedding_service.model_name}")
        except Exception as e:
            logger.warning(f"Failed to pre-warm embedding model: {e}")

    logger.info("Vector Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Vector Service...")

    await close_qdrant_service()
    await close_embedding_service()

    logger.info("Vector Service stopped")


# Configure logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.service_name,
    description="""
## Vector Service

A production-ready semantic search and RAG service using Qdrant.

### Features

- **Collection Management**: Create, list, and delete vector collections
- **Vector Operations**: Upsert, search, and delete vectors
- **Text Search**: Automatic text-to-vector conversion
- **Hybrid Search**: Combine vector similarity with keyword matching
- **Recommendations**: Find similar items based on examples

### Integration

Works with LLM Service for embeddings, or uses local sentence-transformers.
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
            "success": False,
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
        },
    )


# Include routers
app.include_router(health_router, prefix="", tags=["Health"])
app.include_router(collections_router, prefix="/api/v1", tags=["Collections"])
app.include_router(vectors_router, prefix="/api/v1", tags=["Vectors"])


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
