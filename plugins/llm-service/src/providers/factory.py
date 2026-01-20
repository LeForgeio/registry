"""
Provider Factory - Create and manage LLM provider instances.
"""
from typing import Dict, Optional, List, Type
from loguru import logger

from .base import LLMProvider, ProviderConfig, ProviderCapabilities, ProviderError, ModelInfo


# Provider registry
_provider_registry: Dict[str, Type[LLMProvider]] = {}
_provider_instances: Dict[str, LLMProvider] = {}


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """Register a provider class."""
    _provider_registry[name.lower()] = provider_class
    logger.debug(f"Registered provider: {name}")


def get_registered_providers() -> List[str]:
    """Get list of registered provider names."""
    return list(_provider_registry.keys())


class ProviderFactory:
    """
    Factory for creating and managing LLM provider instances.
    
    Supports:
    - vllm: Local vLLM server (default)
    - openai: OpenAI API (GPT-4, GPT-3.5, etc.)
    - anthropic: Anthropic API (Claude 3)
    - azure: Azure OpenAI Service
    - google: Google Vertex AI (Gemini)
    - bedrock: AWS Bedrock
    - huggingface: Hugging Face Inference API
    """
    
    # Lazy import providers to avoid circular imports
    _providers_loaded = False
    
    @classmethod
    def _load_providers(cls):
        """Load and register all providers."""
        if cls._providers_loaded:
            return
        
        from .vllm_provider import VLLMProvider
        from .openai_provider import OpenAIProvider
        from .anthropic_provider import AnthropicProvider
        from .azure_provider import AzureOpenAIProvider
        from .google_provider import GoogleVertexProvider
        from .bedrock_provider import BedrockProvider
        from .huggingface_provider import HuggingFaceProvider
        
        register_provider("vllm", VLLMProvider)
        register_provider("openai", OpenAIProvider)
        register_provider("anthropic", AnthropicProvider)
        register_provider("azure", AzureOpenAIProvider)
        register_provider("google", GoogleVertexProvider)
        register_provider("vertex", GoogleVertexProvider)
        register_provider("bedrock", BedrockProvider)
        register_provider("aws", BedrockProvider)
        register_provider("huggingface", HuggingFaceProvider)
        register_provider("hf", HuggingFaceProvider)
        
        cls._providers_loaded = True
    
    @classmethod
    async def create(
        cls,
        provider_name: str,
        config: Optional[ProviderConfig] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create a provider instance.
        
        Args:
            provider_name: Name of the provider (openai, anthropic, etc.)
            config: Provider configuration
            **kwargs: Additional config options
            
        Returns:
            Initialized provider instance
        """
        cls._load_providers()
        
        name = provider_name.lower()
        if name not in _provider_registry:
            available = ", ".join(_provider_registry.keys())
            raise ProviderError(
                message=f"Unknown provider: {provider_name}. Available: {available}",
                code="UNKNOWN_PROVIDER"
            )
        
        # Create config if not provided
        if config is None:
            config = ProviderConfig(name=name, **kwargs)
        
        # Create and initialize provider
        provider_class = _provider_registry[name]
        provider = provider_class(config)
        await provider.initialize()
        
        # Cache the instance
        instance_key = f"{name}:{config.api_base or 'default'}"
        _provider_instances[instance_key] = provider
        
        logger.info(f"Created provider: {name}")
        return provider
    
    @classmethod
    def get_cached(cls, provider_name: str, api_base: Optional[str] = None) -> Optional[LLMProvider]:
        """Get a cached provider instance if available."""
        instance_key = f"{provider_name.lower()}:{api_base or 'default'}"
        return _provider_instances.get(instance_key)
    
    @classmethod
    async def close_all(cls):
        """Close all provider instances."""
        for name, provider in _provider_instances.items():
            try:
                await provider.close()
                logger.debug(f"Closed provider: {name}")
            except Exception as e:
                logger.error(f"Error closing provider {name}: {e}")
        _provider_instances.clear()
    
    @classmethod
    def list_available(cls) -> List[Dict[str, any]]:
        """List all available providers with their capabilities."""
        cls._load_providers()
        
        providers = []
        for name, provider_class in _provider_registry.items():
            # Skip aliases
            if name in ["vertex", "aws", "hf"]:
                continue
            
            providers.append({
                "name": name,
                "display_name": provider_class.display_name,
                "description": provider_class.__doc__.strip().split('\n')[0] if provider_class.__doc__ else "",
            })
        
        return providers


# Convenience functions

async def get_provider(
    provider_name: str = "vllm",
    config: Optional[ProviderConfig] = None,
    use_cache: bool = True,
    **kwargs
) -> LLMProvider:
    """
    Get or create a provider instance.
    
    Args:
        provider_name: Provider name
        config: Optional configuration
        use_cache: Whether to use cached instances
        **kwargs: Config options
        
    Returns:
        Provider instance
    """
    if use_cache:
        cached = ProviderFactory.get_cached(provider_name, kwargs.get("api_base"))
        if cached:
            return cached
    
    return await ProviderFactory.create(provider_name, config, **kwargs)


def list_providers() -> List[Dict[str, any]]:
    """List available providers."""
    return ProviderFactory.list_available()
