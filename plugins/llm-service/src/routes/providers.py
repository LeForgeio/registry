"""
Provider Management Routes - List, configure, and switch between LLM providers.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from loguru import logger

from ..providers import (
    ProviderFactory,
    get_provider,
    list_providers,
    ProviderConfig,
    ProviderError,
    ChatMessage,
    MessageRole,
)


router = APIRouter(prefix="/providers", tags=["Providers"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ProviderInfo(BaseModel):
    """Provider information."""
    name: str
    display_name: str
    description: str = ""
    available: bool = True


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    name: str
    provider: str
    context_length: int = 4096
    max_output_tokens: int = 4096
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    description: Optional[str] = None


class ProviderConfigRequest(BaseModel):
    """Request to configure a provider."""
    provider: str = Field(..., description="Provider name (openai, anthropic, etc.)")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    api_base: Optional[str] = Field(None, description="Custom API base URL")
    api_version: Optional[str] = Field(None, description="API version (for Azure)")
    organization: Optional[str] = Field(None, description="Organization ID (for OpenAI)")
    project: Optional[str] = Field(None, description="Project ID (for Google)")
    region: Optional[str] = Field(None, description="Region (for AWS/Google)")
    deployment_name: Optional[str] = Field(None, description="Deployment name (for Azure)")
    default_model: Optional[str] = Field(None, description="Default model to use")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional config")


class MultiProviderChatRequest(BaseModel):
    """Chat request with provider selection."""
    provider: str = Field("vllm", description="Provider to use")
    model: Optional[str] = Field(None, description="Model to use")
    messages: List[Dict[str, str]] = Field(..., description="Chat messages")
    max_tokens: Optional[int] = Field(None, description="Max tokens to generate")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    top_p: Optional[float] = Field(None, description="Nucleus sampling parameter")
    stream: bool = Field(False, description="Stream response")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Tool definitions")
    response_format: Optional[Dict[str, str]] = Field(None, description="Response format")


class ProviderHealthResponse(BaseModel):
    """Provider health check response."""
    provider: str
    status: str
    models_available: int = 0
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Provider cache for configured providers
# ============================================================================

_configured_providers: Dict[str, Any] = {}


async def get_configured_provider(provider_name: str):
    """Get a configured provider or raise error."""
    if provider_name not in _configured_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' is not configured. Use POST /providers/configure first."
        )
    return _configured_providers[provider_name]


# ============================================================================
# Routes
# ============================================================================

@router.get(
    "",
    response_model=List[ProviderInfo],
    summary="List available providers",
    description="Get list of all available LLM providers.",
)
async def get_providers():
    """List all available LLM providers."""
    providers = list_providers()
    return [
        ProviderInfo(
            name=p["name"],
            display_name=p["display_name"],
            description=p.get("description", ""),
            available=True,
        )
        for p in providers
    ]


@router.get(
    "/configured",
    summary="List configured providers",
    description="Get list of providers that have been configured with credentials.",
)
async def get_configured_providers():
    """List configured providers."""
    return {
        "providers": list(_configured_providers.keys()),
        "count": len(_configured_providers),
    }


@router.post(
    "/configure",
    summary="Configure a provider",
    description="""
Configure an LLM provider with credentials.

After configuring, the provider can be used for chat/generation requests.
Configuration is stored in memory and lost on restart.

**Examples:**

OpenAI:
```json
{
    "provider": "openai",
    "api_key": "sk-...",
    "default_model": "gpt-4o-mini"
}
```

Anthropic:
```json
{
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "default_model": "claude-3-5-sonnet-20241022"
}
```

Azure OpenAI:
```json
{
    "provider": "azure",
    "api_key": "...",
    "api_base": "https://your-resource.openai.azure.com",
    "deployment_name": "gpt-4",
    "api_version": "2024-02-01"
}
```

AWS Bedrock:
```json
{
    "provider": "bedrock",
    "region": "us-east-1",
    "extra": {"aws_secret_key": "..."}
}
```
    """,
)
async def configure_provider(request: ProviderConfigRequest):
    """Configure a provider with credentials."""
    try:
        config = ProviderConfig(
            name=request.provider,
            api_key=request.api_key,
            api_base=request.api_base,
            api_version=request.api_version,
            organization=request.organization,
            project=request.project,
            region=request.region,
            deployment_name=request.deployment_name,
            default_model=request.default_model,
            extra=request.extra,
        )
        
        provider = await ProviderFactory.create(request.provider, config)
        _configured_providers[request.provider] = provider
        
        # Get capabilities
        capabilities = provider.get_capabilities()
        
        logger.info(f"Configured provider: {request.provider}")
        
        return {
            "success": True,
            "provider": request.provider,
            "default_model": request.default_model,
            "capabilities": {
                "chat": capabilities.chat,
                "completion": capabilities.completion,
                "embeddings": capabilities.embeddings,
                "streaming": capabilities.streaming,
                "function_calling": capabilities.function_calling,
                "json_mode": capabilities.json_mode,
                "vision": capabilities.vision,
            }
        }
        
    except ProviderError as e:
        raise HTTPException(status_code=400, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception(f"Failed to configure provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/configure/{provider_name}",
    summary="Remove provider configuration",
    description="Remove a configured provider.",
)
async def remove_provider(provider_name: str):
    """Remove a provider configuration."""
    if provider_name in _configured_providers:
        provider = _configured_providers.pop(provider_name)
        await provider.close()
        return {"success": True, "provider": provider_name, "message": "Provider removed"}
    
    raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not configured")


@router.get(
    "/{provider_name}/models",
    response_model=List[ModelInfo],
    summary="List provider models",
    description="Get list of available models for a provider.",
)
async def get_provider_models(provider_name: str):
    """List available models for a provider."""
    if provider_name not in _configured_providers:
        # Try to get static model list for unconfigured providers
        try:
            # Create temporary provider just to get model list
            ProviderFactory._load_providers()
            from ..providers import (
                OPENAI_MODELS,
                ANTHROPIC_MODELS,
                GOOGLE_MODELS,
                BEDROCK_MODELS,
                HUGGINGFACE_MODELS,
            )
            
            model_catalogs = {
                "openai": OPENAI_MODELS,
                "anthropic": ANTHROPIC_MODELS,
                "google": GOOGLE_MODELS,
                "vertex": GOOGLE_MODELS,
                "bedrock": BEDROCK_MODELS,
                "aws": BEDROCK_MODELS,
                "huggingface": HUGGINGFACE_MODELS,
                "hf": HUGGINGFACE_MODELS,
            }
            
            if provider_name.lower() in model_catalogs:
                catalog = model_catalogs[provider_name.lower()]
                return [
                    ModelInfo(
                        id=m.id,
                        name=m.name,
                        provider=m.provider,
                        context_length=m.context_length,
                        max_output_tokens=m.max_output_tokens,
                        supports_streaming=m.supports_streaming,
                        supports_functions=m.supports_functions,
                        supports_vision=m.supports_vision,
                        supports_json_mode=m.supports_json_mode,
                        input_cost_per_1k=m.input_cost_per_1k,
                        output_cost_per_1k=m.output_cost_per_1k,
                        description=m.description,
                    )
                    for m in catalog.values()
                ]
        except ImportError:
            pass
        
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_name}' not found or not configured"
        )
    
    provider = _configured_providers[provider_name]
    models = await provider.list_models()
    
    return [
        ModelInfo(
            id=m.id,
            name=m.name,
            provider=m.provider,
            context_length=m.context_length,
            max_output_tokens=m.max_output_tokens,
            supports_streaming=m.supports_streaming,
            supports_functions=m.supports_functions,
            supports_vision=m.supports_vision,
            supports_json_mode=m.supports_json_mode,
            input_cost_per_1k=m.input_cost_per_1k,
            output_cost_per_1k=m.output_cost_per_1k,
            description=m.description,
        )
        for m in models
    ]


@router.get(
    "/{provider_name}/health",
    response_model=ProviderHealthResponse,
    summary="Check provider health",
    description="Check if a configured provider is healthy and accessible.",
)
async def check_provider_health(provider_name: str):
    """Check provider health."""
    if provider_name not in _configured_providers:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_name}' not configured"
        )
    
    provider = _configured_providers[provider_name]
    health = await provider.health_check()
    
    return ProviderHealthResponse(
        provider=provider_name,
        status=health.get("status", "unknown"),
        models_available=health.get("models_available", 0),
        error=health.get("error"),
        details=health,
    )


@router.post(
    "/{provider_name}/chat",
    summary="Chat with specific provider",
    description="Send a chat request to a specific configured provider.",
)
async def provider_chat(provider_name: str, request: MultiProviderChatRequest):
    """Chat using a specific provider."""
    if provider_name not in _configured_providers:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_name}' not configured. Use POST /providers/configure first."
        )
    
    provider = _configured_providers[provider_name]
    
    # Convert messages
    messages = [
        ChatMessage(
            role=MessageRole(msg.get("role", "user")),
            content=msg.get("content", ""),
        )
        for msg in request.messages
    ]
    
    try:
        if request.stream:
            # Return streaming response
            from fastapi.responses import StreamingResponse
            import json
            
            async def generate():
                async for chunk in provider.chat_stream(
                    messages=messages,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
            )
        
        # Non-streaming
        response = await provider.chat(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            tools=request.tools,
            response_format=request.response_format,
        )
        
        return {
            "success": True,
            "message": response.message,
            "model": response.model,
            "provider": response.provider,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            "finish_reason": response.finish_reason,
            "tool_calls": response.tool_calls,
            "latency_ms": response.latency_ms,
        }
        
    except ProviderError as e:
        raise HTTPException(
            status_code=503 if e.retryable else 400,
            detail={"error": e.message, "code": e.code, "provider": e.provider}
        )
    except Exception as e:
        logger.exception(f"Provider chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{provider_name}/embed",
    summary="Generate embeddings with specific provider",
    description="Generate embeddings using a specific configured provider.",
)
async def provider_embed(
    provider_name: str,
    texts: List[str],
    model: Optional[str] = None,
):
    """Generate embeddings using a specific provider."""
    if provider_name not in _configured_providers:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_name}' not configured"
        )
    
    provider = _configured_providers[provider_name]
    
    try:
        response = await provider.embed(texts=texts, model=model)
        
        return {
            "success": True,
            "embeddings": response.embeddings,
            "model": response.model,
            "provider": response.provider,
            "dimensions": response.dimensions,
        }
        
    except ProviderError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception(f"Provider embed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chat",
    summary="Universal chat endpoint",
    description="""
Chat with any configured provider using a unified API.

Specify the provider in the request body. If not specified,
falls back to the default provider (vLLM).
    """,
)
async def universal_chat(request: MultiProviderChatRequest):
    """Universal chat endpoint that routes to the specified provider."""
    return await provider_chat(request.provider, request)
