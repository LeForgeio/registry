"""
LLM Service Routes
"""
from .generate import router as generate_router
from .chat import router as chat_router
from .classify import router as classify_router
from .extract import router as extract_router
from .summarize import router as summarize_router
from .embeddings import router as embeddings_router
from .health import router as health_router
from .vision import router as vision_router
from .transform import router as transform_router

__all__ = [
    "generate_router",
    "chat_router",
    "classify_router",
    "extract_router",
    "summarize_router",
    "embeddings_router",
    "health_router",
    "vision_router",
    "transform_router",
]
