"""
Configuration settings for the Math Service.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    port: int = 3002
    environment: str = "development"
    log_level: str = "info"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # Math specific
    max_precision: int = 15
    max_array_size: int = 10000
    max_matrix_size: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
