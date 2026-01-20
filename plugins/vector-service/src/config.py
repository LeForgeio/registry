"""
Vector Service Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service settings
    service_name: str = "vector-service"
    service_version: str = "1.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=1, alias="WORKERS")

    # Qdrant settings
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_https: bool = Field(default=False, alias="QDRANT_HTTPS")
    qdrant_prefer_grpc: bool = Field(default=True, alias="QDRANT_PREFER_GRPC")
    qdrant_timeout: int = Field(default=30, alias="QDRANT_TIMEOUT")

    # Embedding settings
    embedding_provider: str = Field(
        default="local",
        alias="EMBEDDING_PROVIDER",
        description="'local' for sentence-transformers, 'llm-service' for remote"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL"
    )
    embedding_dimensions: int = Field(
        default=384,
        alias="EMBEDDING_DIMENSIONS"
    )

    # LLM Service settings (for remote embeddings)
    llm_service_url: str = Field(
        default="http://localhost:8000",
        alias="LLM_SERVICE_URL"
    )
    llm_service_timeout: int = Field(default=30, alias="LLM_SERVICE_TIMEOUT")

    # Batch settings
    default_batch_size: int = Field(default=100, alias="DEFAULT_BATCH_SIZE")
    max_batch_size: int = Field(default=1000, alias="MAX_BATCH_SIZE")

    # Search settings
    default_search_limit: int = Field(default=10, alias="DEFAULT_SEARCH_LIMIT")
    max_search_limit: int = Field(default=100, alias="MAX_SEARCH_LIMIT")
    default_score_threshold: float = Field(default=0.0, alias="DEFAULT_SCORE_THRESHOLD")

    # Collection defaults
    default_distance: str = Field(
        default="Cosine",
        alias="DEFAULT_DISTANCE",
        description="Cosine, Euclid, or Dot"
    )
    default_on_disk: bool = Field(default=False, alias="DEFAULT_ON_DISK")

    # CORS settings
    cors_origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
