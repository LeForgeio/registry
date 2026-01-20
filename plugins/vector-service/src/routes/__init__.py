"""Vector Service Routes"""
from .collections import router as collections_router
from .vectors import router as vectors_router
from .health import router as health_router

__all__ = [
    "collections_router",
    "vectors_router",
    "health_router",
]
