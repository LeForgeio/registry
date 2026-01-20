"""
Anthropic Provider - Claude 3 models.

Supports:
- Claude 3 Opus, Sonnet, Haiku
- Streaming responses
- System prompts
- Vision (Claude 3)
- Tool use
"""
import time
from typing import Optional, List, Dict, Any, AsyncIterator
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


# Anthropic model catalog
ANTHROPIC_MODELS = {
    # Claude 3.5
    "claude-3-5-sonnet-20241022": ModelInfo(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        context_length=200000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        description="Most intelligent Claude model",
    ),
    "claude-3-5-haiku-20241022": ModelInfo(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        context_length=200000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.005,
        description="Fast and affordable",
    ),
    # Claude 3
    "claude-3-opus-20240229": ModelInfo(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider="anthropic",
        context_length=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.075,
        description="Most powerful for complex tasks",
    ),
    "claude-3-sonnet-20240229": ModelInfo(
        id="claude-3-sonnet-20240229",
        name="Claude 3 Sonnet",
        provider="anthropic",
        context_length=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        description="Balanced performance and cost",
    ),
    "claude-3-haiku-20240307": ModelInfo(
        id="claude-3-haiku-20240307",
        name="Claude 3 Haiku",
        provider="anthropic",
        context_length=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        input_cost_per_1k=0.00025,
        output_cost_per_1k=0.00125,
        description="Fastest and most compact",
    ),
}

# Aliases
ANTHROPIC_MODELS["claude-3-5-sonnet"] = ANTHROPIC_MODELS["claude-3-5-sonnet-20241022"]
ANTHROPIC_MODELS["claude-3-5-haiku"] = ANTHROPIC_MODELS["claude-3-5-haiku-20241022"]
ANTHROPIC_MODELS["claude-3-opus"] = ANTHROPIC_MODELS["claude-3-opus-20240229"]
ANTHROPIC_MODELS["claude-3-sonnet"] = ANTHROPIC_MODELS["claude-3-sonnet-20240229"]
ANTHROPIC_MODELS["claude-3-haiku"] = ANTHROPIC_MODELS["claude-3-haiku-20240307"]


class AnthropicProvider(LLMProvider):
    """
    Anthropic Provider for Claude models.
    
    Supports:
    - Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku
    - Streaming responses
    - System prompts (handled separately)
    - Vision (image analysis)
    - Tool use
    """
    
    name = "anthropic"
    display_name = "Anthropic"
    
    API_BASE = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.default_model = config.default_model or "claude-3-5-sonnet-20241022"
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self.api_key:
            raise ProviderError(
                message="Anthropic API key is required",
                code="MISSING_API_KEY",
                provider=self.name,
            )
        
        self._http_client = httpx.AsyncClient(
            base_url=self.API_BASE,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
            timeout=self.config.timeout,
        )
        logger.info("Anthropic provider initialized")
    
    async def close(self) -> None:
        """Close the client."""
        if self._http_client:
            await self._http_client.aclose()
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Anthropic capabilities."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=False,  # Anthropic doesn't offer embeddings
            streaming=True,
            function_calling=True,  # Tool use
            json_mode=False,  # Use tool for structured output
            vision=True,
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Anthropic models."""
        # Return non-alias models only
        return [m for k, m in ANTHROPIC_MODELS.items() if "-202" in k]
    
    def _convert_messages(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict]]:
        """
        Convert messages to Anthropic format.
        
        Anthropic requires system prompt to be separate from messages.
        """
        system_prompt = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                anthropic_messages.append({
                    "role": role,
                    "content": msg.content,
                })
        
        return system_prompt, anthropic_messages
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str | Dict[str, Any]] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion via Anthropic API."""
        start_time = time.time()
        model = model or self.default_model
        
        # Resolve alias to full model name
        if model in ANTHROPIC_MODELS and "-202" not in model:
            model = ANTHROPIC_MODELS[model].id
        
        system_prompt, anthropic_messages = self._convert_messages(messages)
        
        # Build request
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 1024,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if stop:
            payload["stop_sequences"] = stop
        
        # Tool use
        if tools:
            payload["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {}),
                }
                for t in tools
            ]
            if tool_choice:
                if tool_choice == "auto":
                    payload["tool_choice"] = {"type": "auto"}
                elif tool_choice == "any":
                    payload["tool_choice"] = {"type": "any"}
                elif isinstance(tool_choice, dict):
                    payload["tool_choice"] = {"type": "tool", "name": tool_choice.get("function", {}).get("name")}
        
        try:
            response = await self._http_client.post("/messages", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract text content
            content = ""
            tool_calls = []
            
            for block in data.get("content", []):
                if block["type"] == "text":
                    content += block["text"]
                elif block["type"] == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "type": "function",
                        "function": {
                            "name": block["name"],
                            "arguments": str(block["input"]),
                        }
                    })
            
            usage = TokenUsage(
                prompt_tokens=data.get("usage", {}).get("input_tokens", 0),
                completion_tokens=data.get("usage", {}).get("output_tokens", 0),
                total_tokens=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
            )
            
            return ChatResponse(
                message=content,
                role=MessageRole.ASSISTANT,
                finish_reason=data.get("stop_reason"),
                usage=usage,
                model=model,
                provider=self.name,
                tool_calls=tool_calls if tool_calls else None,
                latency_ms=self._measure_latency(start_time),
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            logger.error(f"Anthropic API error: {error_detail}")
            
            raise ProviderError(
                message=f"Anthropic API error: {error_detail.get('error', {}).get('message', str(e))}",
                code=error_detail.get('error', {}).get('type', 'API_ERROR'),
                provider=self.name,
                status_code=e.response.status_code,
                retryable=e.response.status_code in [429, 500, 502, 503],
            )
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise ProviderError(
                message=f"Anthropic request failed: {str(e)}",
                code="ANTHROPIC_ERROR",
                provider=self.name,
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
        
        if model in ANTHROPIC_MODELS and "-202" not in model:
            model = ANTHROPIC_MODELS[model].id
        
        system_prompt, anthropic_messages = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 1024,
            "stream": True,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if stop:
            payload["stop_sequences"] = stop
        
        try:
            async with self._http_client.stream("POST", "/messages", json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        data = json.loads(line[6:])
                        
                        if data["type"] == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                                
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise ProviderError(
                message=f"Anthropic streaming failed: {str(e)}",
                code="ANTHROPIC_STREAM_ERROR",
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
        """Generate text (uses chat format)."""
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
