"""
LLM Providers - Multi-provider support for LLM Service.

Supports:
- vLLM (local/self-hosted)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Azure OpenAI
- Google Vertex AI (Gemini)
- AWS Bedrock (Claude, Titan, Llama)
- Hugging Face Inference API
"""
from .base import (
    LLMProvider,
    ProviderConfig,
    ProviderCapabilities,
    ProviderError,
    ModelInfo,
    ChatMessage,
    ChatResponse,
    GenerationResponse,
    EmbeddingResponse,
)
from .factory import ProviderFactory, get_provider, list_providers
from .vllm_provider import VLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .azure_provider import AzureOpenAIProvider
from .google_provider import GoogleVertexProvider
from .bedrock_provider import BedrockProvider
from .huggingface_provider import HuggingFaceProvider

__all__ = [
    # Base classes
    "LLMProvider",
    "ProviderConfig",
    "ProviderCapabilities",
    "ProviderError",
    "ModelInfo",
    "ChatMessage",
    "ChatResponse",
    "GenerationResponse",
    "EmbeddingResponse",
    # Factory
    "ProviderFactory",
    "get_provider",
    "list_providers",
    # Providers
    "VLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "AzureOpenAIProvider",
    "GoogleVertexProvider",
    "BedrockProvider",
    "HuggingFaceProvider",
]
