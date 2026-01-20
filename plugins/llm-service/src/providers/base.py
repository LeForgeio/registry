"""
Base LLM Provider Interface.

All providers must implement this interface for consistent behavior.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, AsyncIterator
import time


class MessageRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"role": self.role.value, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class TokenUsage:
    """Token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost (placeholder, varies by provider/model)."""
        # Default to GPT-3.5 pricing as baseline
        return (self.prompt_tokens * 0.0005 + self.completion_tokens * 0.0015) / 1000


@dataclass
class ChatResponse:
    """Chat completion response."""
    message: str
    role: MessageRole = MessageRole.ASSISTANT
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    latency_ms: Optional[int] = None


@dataclass
class GenerationResponse:
    """Text generation response."""
    text: str
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: Optional[int] = None


@dataclass
class EmbeddingResponse:
    """Embedding generation response."""
    embeddings: List[List[float]]
    model: Optional[str] = None
    provider: Optional[str] = None
    usage: Optional[TokenUsage] = None
    dimensions: int = 0


@dataclass
class ModelInfo:
    """Information about an available model."""
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
    deprecated: bool = False


@dataclass
class ProviderCapabilities:
    """Capabilities of an LLM provider."""
    chat: bool = True
    completion: bool = True
    embeddings: bool = False
    streaming: bool = True
    function_calling: bool = False
    json_mode: bool = False
    vision: bool = False
    audio: bool = False
    fine_tuning: bool = False
    batch: bool = False


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    region: Optional[str] = None
    deployment_name: Optional[str] = None
    default_model: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    extra: Dict[str, Any] = field(default_factory=dict)


class ProviderError(Exception):
    """Exception raised by providers."""
    
    def __init__(
        self,
        message: str,
        code: str = "PROVIDER_ERROR",
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All providers must implement the core methods for chat, generation,
    and optionally embeddings and streaming.
    """
    
    name: str = "base"
    display_name: str = "Base Provider"
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the provider client and cleanup resources."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models for this provider."""
        pass
    
    @abstractmethod
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
        """
        Generate a chat completion.
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to provider's default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            functions: Function definitions (deprecated, use tools)
            function_call: Function call preference
            tools: Tool definitions
            tool_choice: Tool choice preference
            response_format: Response format (e.g., {"type": "json_object"})
            **kwargs: Provider-specific options
            
        Returns:
            ChatResponse with generated message
        """
        pass
    
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
        """
        Stream a chat completion.
        
        Yields:
            Text chunks as they are generated
        """
        # Default implementation: fall back to non-streaming
        response = await self.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            **kwargs
        )
        yield response.message
    
    @abstractmethod
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
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            **kwargs: Provider-specific options
            
        Returns:
            GenerationResponse with generated text
        """
        pass
    
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
        """
        Stream text generation.
        
        Yields:
            Text chunks as they are generated
        """
        # Default: fall back to non-streaming
        response = await self.generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            **kwargs
        )
        yield response.text
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            **kwargs: Provider-specific options
            
        Returns:
            EmbeddingResponse with embeddings
        """
        raise ProviderError(
            message=f"Provider {self.name} does not support embeddings",
            code="NOT_SUPPORTED",
            provider=self.name
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health/connectivity.
        
        Returns:
            Dict with status and details
        """
        try:
            models = await self.list_models()
            return {
                "status": "healthy",
                "provider": self.name,
                "models_available": len(models),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.name,
                "error": str(e),
            }
    
    def _measure_latency(self, start_time: float) -> int:
        """Calculate latency in milliseconds."""
        return int((time.time() - start_time) * 1000)
