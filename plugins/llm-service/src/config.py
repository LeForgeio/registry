"""
LLM Service Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service settings
    service_name: str = "llm-service"
    service_version: str = "1.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=1, alias="WORKERS")

    # vLLM Server settings
    vllm_base_url: str = Field(
        default="http://localhost:8001/v1",
        alias="VLLM_BASE_URL",
        description="Base URL for vLLM server (OpenAI-compatible)"
    )
    vllm_api_key: Optional[str] = Field(
        default=None,
        alias="VLLM_API_KEY",
        description="API key for vLLM server (if required)"
    )

    # Default model settings
    default_model: str = Field(
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        alias="DEFAULT_MODEL"
    )
    default_embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        alias="DEFAULT_EMBEDDING_MODEL"
    )
    
    # Vision model settings
    vision_model: str = Field(
        default="llava-hf/llava-1.5-7b-hf",
        alias="VISION_MODEL",
        description="Default vision-language model for OCR and image understanding"
    )
    max_image_size_mb: int = Field(
        default=10,
        alias="MAX_IMAGE_SIZE_MB",
        description="Maximum image size in MB"
    )
    enable_vision: bool = Field(
        default=True,
        alias="ENABLE_VISION",
        description="Enable vision/OCR endpoints"
    )

    # Generation defaults
    default_max_tokens: int = Field(default=512, alias="DEFAULT_MAX_TOKENS")
    default_temperature: float = Field(default=0.7, alias="DEFAULT_TEMPERATURE")
    default_top_p: float = Field(default=1.0, alias="DEFAULT_TOP_P")

    # Request settings
    request_timeout: int = Field(
        default=120,
        alias="REQUEST_TIMEOUT",
        description="Timeout for LLM requests in seconds"
    )
    max_concurrent_requests: int = Field(
        default=10,
        alias="MAX_CONCURRENT_REQUESTS"
    )

    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )
    redis_queue_name: str = Field(
        default="llm_requests",
        alias="REDIS_QUEUE_NAME"
    )
    enable_queue: bool = Field(
        default=False,
        alias="ENABLE_QUEUE",
        description="Enable Redis request queuing"
    )

    # Embeddings settings
    enable_embeddings: bool = Field(
        default=True,
        alias="ENABLE_EMBEDDINGS",
        description="Enable embeddings endpoint"
    )
    embedding_batch_size: int = Field(
        default=32,
        alias="EMBEDDING_BATCH_SIZE"
    )

    # Token limits
    max_input_tokens: int = Field(default=4096, alias="MAX_INPUT_TOKENS")
    max_output_tokens: int = Field(default=2048, alias="MAX_OUTPUT_TOKENS")

    # Batch processing
    batch_size: int = Field(default=8, alias="BATCH_SIZE")
    batch_timeout: float = Field(
        default=0.1,
        alias="BATCH_TIMEOUT",
        description="Time to wait for batch to fill (seconds)"
    )

    # Model cache
    model_cache_dir: str = Field(
        default="/tmp/llm-service/models",
        alias="MODEL_CACHE_DIR"
    )

    # CORS settings
    cors_origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            return [o.strip() for o in self.cors_origins.split(",")]
        return self.cors_origins

    # Metrics
    enable_metrics: bool = Field(default=False, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")

    # Rate limiting
    rate_limit_requests: int = Field(
        default=100,
        alias="RATE_LIMIT_REQUESTS",
        description="Max requests per minute"
    )

    # ==========================================================================
    # Multi-Provider Settings
    # ==========================================================================
    
    # Default provider (vllm, openai, anthropic, azure, google, bedrock, huggingface)
    default_provider: str = Field(
        default="vllm",
        alias="DEFAULT_PROVIDER",
        description="Default LLM provider to use"
    )
    
    # OpenAI
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key"
    )
    openai_organization: Optional[str] = Field(
        default=None,
        alias="OPENAI_ORGANIZATION",
        description="OpenAI organization ID"
    )
    openai_default_model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_DEFAULT_MODEL",
        description="Default OpenAI model"
    )
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
        description="Anthropic API key"
    )
    anthropic_default_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        alias="ANTHROPIC_DEFAULT_MODEL",
        description="Default Anthropic model"
    )
    
    # Azure OpenAI
    azure_openai_api_key: Optional[str] = Field(
        default=None,
        alias="AZURE_OPENAI_API_KEY",
        description="Azure OpenAI API key"
    )
    azure_openai_endpoint: Optional[str] = Field(
        default=None,
        alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_deployment: Optional[str] = Field(
        default=None,
        alias="AZURE_OPENAI_DEPLOYMENT",
        description="Azure OpenAI deployment name"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-01",
        alias="AZURE_OPENAI_API_VERSION",
        description="Azure OpenAI API version"
    )
    
    # Google Vertex AI / Google AI Studio
    google_api_key: Optional[str] = Field(
        default=None,
        alias="GOOGLE_API_KEY",
        description="Google AI Studio API key"
    )
    google_project: Optional[str] = Field(
        default=None,
        alias="GOOGLE_PROJECT",
        description="Google Cloud project ID (for Vertex AI)"
    )
    google_region: str = Field(
        default="us-central1",
        alias="GOOGLE_REGION",
        description="Google Cloud region"
    )
    google_default_model: str = Field(
        default="gemini-1.5-flash",
        alias="GOOGLE_DEFAULT_MODEL",
        description="Default Google model"
    )
    
    # AWS Bedrock
    aws_access_key_id: Optional[str] = Field(
        default=None,
        alias="AWS_ACCESS_KEY_ID",
        description="AWS access key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        alias="AWS_SECRET_ACCESS_KEY",
        description="AWS secret access key"
    )
    aws_region: str = Field(
        default="us-east-1",
        alias="AWS_REGION",
        description="AWS region for Bedrock"
    )
    bedrock_default_model: str = Field(
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        alias="BEDROCK_DEFAULT_MODEL",
        description="Default Bedrock model"
    )
    
    # Hugging Face
    huggingface_api_key: Optional[str] = Field(
        default=None,
        alias="HUGGINGFACE_API_KEY",
        description="Hugging Face API token"
    )
    huggingface_endpoint: Optional[str] = Field(
        default=None,
        alias="HUGGINGFACE_ENDPOINT",
        description="Custom Hugging Face Inference Endpoint URL"
    )
    huggingface_default_model: str = Field(
        default="meta-llama/Llama-3.2-3B-Instruct",
        alias="HUGGINGFACE_DEFAULT_MODEL",
        description="Default Hugging Face model"
    )

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
