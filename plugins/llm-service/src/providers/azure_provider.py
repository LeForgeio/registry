"""
Azure OpenAI Provider - Azure-hosted OpenAI models.

Supports:
- Azure OpenAI deployments
- All GPT models available on Azure
- Streaming responses
- Function calling
"""
import time
from typing import Optional, List, Dict, Any, AsyncIterator
from openai import AsyncAzureOpenAI
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


class AzureOpenAIProvider(LLMProvider):
    """
    Azure OpenAI Provider for enterprise deployments.
    
    Azure OpenAI offers:
    - Enterprise security and compliance
    - Regional data residency
    - Private endpoints
    - Higher rate limits with PTU
    
    Requires:
    - Azure OpenAI endpoint URL
    - API key or Azure AD authentication
    - Deployment name(s)
    """
    
    name = "azure"
    display_name = "Azure OpenAI"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.endpoint = config.api_base  # Azure endpoint URL
        self.api_version = config.api_version or "2024-02-01"
        self.default_deployment = config.deployment_name or config.default_model
        self._deployments: Dict[str, ModelInfo] = {}
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client."""
        if not self.api_key:
            raise ProviderError(
                message="Azure OpenAI API key is required",
                code="MISSING_API_KEY",
                provider=self.name,
            )
        
        if not self.endpoint:
            raise ProviderError(
                message="Azure OpenAI endpoint URL is required",
                code="MISSING_ENDPOINT",
                provider=self.name,
            )
        
        self._client = AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        logger.info(f"Azure OpenAI provider initialized: {self.endpoint}")
    
    async def close(self) -> None:
        """Close the client."""
        pass
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Azure OpenAI capabilities (same as OpenAI)."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=True,
            streaming=True,
            function_calling=True,
            json_mode=True,
            vision=True,  # If using GPT-4V deployment
        )
    
    def register_deployment(
        self,
        deployment_name: str,
        model_name: str,
        context_length: int = 4096,
        **kwargs
    ) -> None:
        """
        Register a deployment for this Azure instance.
        
        Azure uses deployment names instead of model names.
        """
        self._deployments[deployment_name] = ModelInfo(
            id=deployment_name,
            name=f"{model_name} ({deployment_name})",
            provider=self.name,
            context_length=context_length,
            **kwargs
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List registered deployments."""
        if not self._deployments:
            # Return default deployment if registered
            if self.default_deployment:
                return [ModelInfo(
                    id=self.default_deployment,
                    name=f"Azure Deployment: {self.default_deployment}",
                    provider=self.name,
                    supports_streaming=True,
                    supports_functions=True,
                )]
            return []
        return list(self._deployments.values())
    
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
        """Generate chat completion via Azure OpenAI."""
        start_time = time.time()
        deployment = model or self.default_deployment
        
        if not deployment:
            raise ProviderError(
                message="Deployment name is required for Azure OpenAI",
                code="MISSING_DEPLOYMENT",
                provider=self.name,
            )
        
        openai_messages = [msg.to_dict() for msg in messages]
        
        params = {
            "model": deployment,  # This is the deployment name in Azure
            "messages": openai_messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature if temperature is not None else 0.7,
        }
        
        if top_p is not None:
            params["top_p"] = top_p
        if stop:
            params["stop"] = stop
        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
        elif functions:
            params["functions"] = functions
            if function_call:
                params["function_call"] = function_call
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
                model=deployment,
                provider=self.name,
                function_call=dict(choice.message.function_call) if choice.message.function_call else None,
                tool_calls=tool_calls,
                latency_ms=self._measure_latency(start_time),
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Azure OpenAI chat error: {error_msg}")
            
            raise ProviderError(
                message=f"Azure OpenAI chat failed: {error_msg}",
                code="AZURE_ERROR",
                provider=self.name,
                retryable="rate limit" in error_msg.lower() or "timeout" in error_msg.lower(),
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
        deployment = model or self.default_deployment
        
        if not deployment:
            raise ProviderError(
                message="Deployment name is required",
                code="MISSING_DEPLOYMENT",
                provider=self.name,
            )
        
        openai_messages = [msg.to_dict() for msg in messages]
        
        try:
            stream = await self._client.chat.completions.create(
                model=deployment,
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
            logger.error(f"Azure OpenAI stream error: {e}")
            raise ProviderError(
                message=f"Azure OpenAI streaming failed: {str(e)}",
                code="AZURE_STREAM_ERROR",
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
        """Generate embeddings using Azure OpenAI embedding deployment."""
        deployment = model or kwargs.get("embedding_deployment")
        
        if not deployment:
            raise ProviderError(
                message="Embedding deployment name is required",
                code="MISSING_DEPLOYMENT",
                provider=self.name,
            )
        
        try:
            response = await self._client.embeddings.create(
                model=deployment,
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
                model=deployment,
                provider=self.name,
                usage=usage,
                dimensions=dimensions,
            )
            
        except Exception as e:
            logger.error(f"Azure OpenAI embedding error: {e}")
            raise ProviderError(
                message=f"Azure OpenAI embedding failed: {str(e)}",
                code="AZURE_EMBED_ERROR",
                provider=self.name,
            )
