"""
OpenAI Provider - GPT-4, GPT-3.5, and other OpenAI models.

Supports the full OpenAI API including:
- Chat completions with streaming
- Function calling / Tools
- JSON mode
- Vision (GPT-4V)
- Embeddings
"""
import time
from typing import Optional, List, Dict, Any, AsyncIterator
from openai import AsyncOpenAI
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


# OpenAI model catalog
OPENAI_MODELS = {
    # GPT-4 Turbo
    "gpt-4-turbo": ModelInfo(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        context_length=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        supports_json_mode=True,
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
        description="Most capable GPT-4 model with vision",
    ),
    "gpt-4-turbo-preview": ModelInfo(
        id="gpt-4-turbo-preview",
        name="GPT-4 Turbo Preview",
        provider="openai",
        context_length=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_json_mode=True,
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
    ),
    # GPT-4
    "gpt-4": ModelInfo(
        id="gpt-4",
        name="GPT-4",
        provider="openai",
        context_length=8192,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        input_cost_per_1k=0.03,
        output_cost_per_1k=0.06,
    ),
    "gpt-4-32k": ModelInfo(
        id="gpt-4-32k",
        name="GPT-4 32K",
        provider="openai",
        context_length=32768,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        input_cost_per_1k=0.06,
        output_cost_per_1k=0.12,
    ),
    # GPT-4o
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        context_length=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        supports_json_mode=True,
        input_cost_per_1k=0.005,
        output_cost_per_1k=0.015,
        description="Most advanced multimodal model",
    ),
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        context_length=128000,
        max_output_tokens=16384,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        supports_json_mode=True,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        description="Fast and affordable small model",
    ),
    # GPT-3.5
    "gpt-3.5-turbo": ModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        context_length=16385,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_json_mode=True,
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.0015,
        description="Fast and cost-effective",
    ),
    # Embeddings
    "text-embedding-3-small": ModelInfo(
        id="text-embedding-3-small",
        name="Embedding 3 Small",
        provider="openai",
        context_length=8191,
        input_cost_per_1k=0.00002,
        description="Efficient embedding model",
    ),
    "text-embedding-3-large": ModelInfo(
        id="text-embedding-3-large",
        name="Embedding 3 Large",
        provider="openai",
        context_length=8191,
        input_cost_per_1k=0.00013,
        description="Highest quality embeddings",
    ),
    "text-embedding-ada-002": ModelInfo(
        id="text-embedding-ada-002",
        name="Ada 002",
        provider="openai",
        context_length=8191,
        input_cost_per_1k=0.0001,
        description="Legacy embedding model",
    ),
}


class OpenAIProvider(LLMProvider):
    """
    OpenAI Provider for GPT models.
    
    Supports:
    - GPT-4 Turbo, GPT-4, GPT-4o, GPT-3.5
    - Streaming responses
    - Function calling / Tools
    - JSON mode
    - Vision (GPT-4V, GPT-4o)
    - Embeddings
    """
    
    name = "openai"
    display_name = "OpenAI"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.organization = config.organization
        self.default_model = config.default_model or "gpt-4o-mini"
        self.default_embedding_model = "text-embedding-3-small"
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self.api_key:
            raise ProviderError(
                message="OpenAI API key is required",
                code="MISSING_API_KEY",
                provider=self.name,
            )
        
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        logger.info("OpenAI provider initialized")
    
    async def close(self) -> None:
        """Close the client."""
        # AsyncOpenAI handles cleanup automatically
        pass
    
    def get_capabilities(self) -> ProviderCapabilities:
        """OpenAI capabilities."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=True,
            streaming=True,
            function_calling=True,
            json_mode=True,
            vision=True,
            audio=False,  # Whisper is separate
            fine_tuning=True,
            batch=True,
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List available OpenAI models."""
        return list(OPENAI_MODELS.values())
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str | Dict[str, str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str | Dict[str, Any]] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion."""
        start_time = time.time()
        model = model or self.default_model
        
        openai_messages = [msg.to_dict() for msg in messages]
        
        # Build request parameters
        params = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature if temperature is not None else 0.7,
        }
        
        if top_p is not None:
            params["top_p"] = top_p
        if stop:
            params["stop"] = stop
        
        # Function calling (tools preferred over deprecated functions)
        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
        elif functions:
            params["functions"] = functions
            if function_call:
                params["function_call"] = function_call
        
        # JSON mode
        if response_format:
            params["response_format"] = response_format
        
        try:
            response = await self._client.chat.completions.create(**params)
            
            choice = response.choices[0]
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            
            # Handle tool calls
            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
            
            return ChatResponse(
                message=choice.message.content or "",
                role=MessageRole.ASSISTANT,
                finish_reason=choice.finish_reason,
                usage=usage,
                model=model,
                provider=self.name,
                function_call=dict(choice.message.function_call) if choice.message.function_call else None,
                tool_calls=tool_calls,
                latency_ms=self._measure_latency(start_time),
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI chat error: {error_msg}")
            
            # Determine if retryable
            retryable = any(x in error_msg.lower() for x in ["rate limit", "timeout", "overloaded"])
            
            raise ProviderError(
                message=f"OpenAI chat failed: {error_msg}",
                code="OPENAI_ERROR",
                provider=self.name,
                retryable=retryable,
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
                max_tokens=max_tokens or 1024,
                temperature=temperature if temperature is not None else 0.7,
                top_p=top_p,
                stop=stop,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            raise ProviderError(
                message=f"OpenAI streaming failed: {str(e)}",
                code="OPENAI_STREAM_ERROR",
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
        """Generate text (uses chat under the hood since completions is deprecated)."""
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        response = await self.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            **kwargs
        )
        
        return GenerationResponse(
            text=response.message,
            finish_reason=response.finish_reason,
            usage=response.usage,
            model=response.model,
            provider=self.name,
            latency_ms=response.latency_ms,
        )
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embeddings."""
        model = model or self.default_embedding_model
        
        try:
            response = await self._client.embeddings.create(
                model=model,
                input=texts,
            )
            
            embeddings = [item.embedding for item in response.data]
            dimensions = len(embeddings[0]) if embeddings else 0
            
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
            )
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                provider=self.name,
                usage=usage,
                dimensions=dimensions,
            )
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise ProviderError(
                message=f"OpenAI embedding failed: {str(e)}",
                code="OPENAI_EMBED_ERROR",
                provider=self.name,
            )
