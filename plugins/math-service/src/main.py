"""
FlowForge Math Service - Main Application
"""
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.config import settings
from src.routes import calculate, statistics, matrix, health, excel, finance
from src.routes import text, logical, datetime, array, math_funcs, info
from src.middleware.request_id import RequestIDMiddleware
from src.middleware.error_handler import http_exception_handler, general_exception_handler

# Configure logging
logger.add(
    "logs/math-service.log",
    rotation="10 MB",
    retention="7 days",
    level=settings.log_level.upper(),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info(f"Math service starting on port {settings.port}")
    yield
    logger.info("Math service shutting down")


app = FastAPI(
    title="FlowForge Math Service",
    description="Mathematical operations service providing calculations, statistics, and matrix operations.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(calculate.router, prefix="/api/v1/math", tags=["Calculate"])
app.include_router(statistics.router, prefix="/api/v1/math", tags=["Statistics"])
app.include_router(matrix.router, prefix="/api/v1/math", tags=["Matrix"])
app.include_router(excel.router, prefix="/api/v1/math", tags=["Excel"])
app.include_router(finance.router, prefix="/api/v1/math", tags=["Finance"])
app.include_router(text.router, prefix="/api/v1/math", tags=["Text"])
app.include_router(logical.router, prefix="/api/v1/math", tags=["Logical"])
app.include_router(datetime.router, prefix="/api/v1/math", tags=["DateTime"])
app.include_router(array.router, prefix="/api/v1/math", tags=["Array"])
app.include_router(math_funcs.router, prefix="/api/v1/math", tags=["Math"])
app.include_router(info.router, prefix="/api/v1/math", tags=["Information"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "math-service",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
