"""
vLLM Provider - Local/self-hosted vLLM inference server.

vLLM provides high-throughput LLM serving with PagedAttention.
Uses OpenAI-compatible API for easy integration.
"""
import time
from typing import Optional, List, Dict, Any, AsyncIterator
from openai import AsyncOpenAI
import httpx
from loguru import logger

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
    TokenUsage,
    MessageRole,
)


class VLLMProvider(LLMProvider):
    """
    vLLM Provider for local/self-hosted LLM inference.
    
    vLLM is optimized for high-throughput serving with:
    - PagedAttention for efficient memory
    - Continuous batching
    - Tensor parallelism
    - OpenAI-compatible API
    """
    
    name = "vllm"
    display_name = "vLLM (Local)"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.api_base or "http://localhost:8001/v1"
        self.api_key = config.api_key or "EMPTY"  # vLLM uses dummy key
        self.default_model = config.default_model
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> None:
        """Initialize the vLLM client."""
        self._client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.config.timeout,
        )
        self._http_client = httpx.AsyncClient(timeout=10.0)
        logger.info(f"vLLM provider initialized: {self.base_url}")
    
    async def close(self) -> None:
        """Close connections."""
        if self._http_client:
            await self._http_client.aclose()
    
    def get_capabilities(self) -> ProviderCapabilities:
        """vLLM capabilities."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=False,  # vLLM doesn't do embeddings
            streaming=True,
            function_calling=False,  # Depends on model
            json_mode=False,
            vision=False,  # Depends on model
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models from vLLM server."""
        try:
            models = await self._client.models.list()
            return [
                ModelInfo(
                    id=model.id,
                    name=model.id,
                    provider=self.name,
                    context_length=4096,  # vLLM doesn't expose this
                    supports_streaming=True,
                )
                for model in models.data
            ]
        except Exception as e:
            logger.error(f"Failed to list vLLM models: {e}")
            return []
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion via vLLM."""
        start_time = time.time()
        model = model or self.default_model
        
        openai_messages = [msg.to_dict() for msg in messages]
        
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens or 512,
                temperature=temperature if temperature is not None else 0.7,
                top_p=top_p if top_p is not None else 1.0,
                stop=stop,
            )
            
            choice = response.choices[0]
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )
            
            return ChatResponse(
                message=choice.message.content,
                role=MessageRole.ASSISTANT,
                finish_reason=choice.finish_reason,
                usage=usage,
                model=model,
                provider=self.name,
                latency_ms=self._measure_latency(start_time),
            )
            
        except Exception as e:
            logger.error(f"vLLM chat error: {e}")
            raise ProviderError(
                message=f"vLLM chat failed: {str(e)}",
                code="VLLM_ERROR",
                provider=self.name,
                retryable="connect" in str(e).lower(),
            )
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion."""
        model = model or self.default_model
        openai_messages = [msg.to_dict() for msg in messages]
        
        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens or 512,
                temperature=temperature if temperature is not None else 0.7,
                top_p=top_p if top_p is not None else 1.0,
                stop=stop,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"vLLM stream error: {e}")
            raise ProviderError(
                message=f"vLLM streaming failed: {str(e)}",
                code="VLLM_STREAM_ERROR",
                provider=self.name,
            )
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> GenerationResponse:
        """Generate text completion."""
        start_time = time.time()
        model = model or self.default_model
        
        try:
            response = await self._client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens or 512,
                temperature=temperature if temperature is not None else 0.7,
                top_p=top_p if top_p is not None else 1.0,
                stop=stop,
            )
            
            choice = response.choices[0]
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )
            
            return GenerationResponse(
                text=choice.text,
                finish_reason=choice.finish_reason,
                usage=usage,
                model=model,
                provider=self.name,
                latency_ms=self._measure_latency(start_time),
            )
            
        except Exception as e:
            logger.error(f"vLLM generation error: {e}")
            raise ProviderError(
                message=f"vLLM generation failed: {str(e)}",
                code="VLLM_ERROR",
                provider=self.name,
            )
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream text generation."""
        model = model or self.default_model
        
        try:
            stream = await self._client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens or 512,
                temperature=temperature if temperature is not None else 0.7,
                top_p=top_p if top_p is not None else 1.0,
                stop=stop,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].text:
                    yield chunk.choices[0].text
                    
        except Exception as e:
            logger.error(f"vLLM stream error: {e}")
            raise ProviderError(
                message=f"vLLM streaming failed: {str(e)}",
                code="VLLM_STREAM_ERROR",
                provider=self.name,
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vLLM server health."""
        try:
            # Remove /v1 suffix for health check
            base = self.base_url.rstrip("/v1").rstrip("/")
            response = await self._http_client.get(f"{base}/health")
            
            models = await self.list_models()
            
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "provider": self.name,
                "base_url": self.base_url,
                "models_available": len(models),
                "model_ids": [m.id for m in models],
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.name,
                "error": str(e),
            }
