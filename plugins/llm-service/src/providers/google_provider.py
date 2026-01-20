"""
Google Vertex AI Provider - Gemini models.

Supports:
- Gemini 1.5 Pro, Gemini 1.5 Flash
- Streaming responses
- Vision (multimodal)
- Function calling
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


# Google model catalog
GOOGLE_MODELS = {
    # Gemini 1.5
    "gemini-1.5-pro": ModelInfo(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        context_length=1000000,  # 1M tokens!
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        supports_json_mode=True,
        input_cost_per_1k=0.00125,
        output_cost_per_1k=0.005,
        description="Best for complex reasoning, long context",
    ),
    "gemini-1.5-flash": ModelInfo(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        context_length=1000000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        supports_json_mode=True,
        input_cost_per_1k=0.000075,
        output_cost_per_1k=0.0003,
        description="Fast and efficient",
    ),
    "gemini-1.5-flash-8b": ModelInfo(
        id="gemini-1.5-flash-8b",
        name="Gemini 1.5 Flash 8B",
        provider="google",
        context_length=1000000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        input_cost_per_1k=0.0000375,
        output_cost_per_1k=0.00015,
        description="Smallest and fastest",
    ),
    # Gemini 2.0
    "gemini-2.0-flash-exp": ModelInfo(
        id="gemini-2.0-flash-exp",
        name="Gemini 2.0 Flash (Experimental)",
        provider="google",
        context_length=1000000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        supports_json_mode=True,
        description="Next generation model (experimental)",
    ),
    # Embeddings
    "text-embedding-004": ModelInfo(
        id="text-embedding-004",
        name="Text Embedding 004",
        provider="google",
        context_length=2048,
        input_cost_per_1k=0.00001,
        description="Text embeddings model",
    ),
}


class GoogleVertexProvider(LLMProvider):
    """
    Google Vertex AI Provider for Gemini models.
    
    Supports:
    - Gemini 1.5 Pro/Flash (1M token context)
    - Gemini 2.0 Flash (experimental)
    - Streaming responses
    - Vision/multimodal
    - Function calling
    - Embeddings
    
    Can use either:
    - Google AI API (api key based) - simpler
    - Vertex AI (service account) - enterprise
    """
    
    name = "google"
    display_name = "Google Vertex AI"
    
    # Google AI Studio endpoint (simpler than Vertex AI)
    GOOGLE_AI_BASE = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.project = config.project
        self.region = config.region or "us-central1"
        self.default_model = config.default_model or "gemini-1.5-flash"
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Determine if using Vertex AI or Google AI Studio
        self.use_vertex = bool(config.project)
    
    async def initialize(self) -> None:
        """Initialize the Google client."""
        if not self.api_key and not self.use_vertex:
            raise ProviderError(
                message="Google API key or Vertex AI project is required",
                code="MISSING_CREDENTIALS",
                provider=self.name,
            )
        
        headers = {"content-type": "application/json"}
        
        self._http_client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers,
        )
        
        mode = "Vertex AI" if self.use_vertex else "Google AI Studio"
        logger.info(f"Google provider initialized ({mode})")
    
    async def close(self) -> None:
        """Close the client."""
        if self._http_client:
            await self._http_client.aclose()
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Google capabilities."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=True,
            streaming=True,
            function_calling=True,
            json_mode=True,
            vision=True,
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Google models."""
        return list(GOOGLE_MODELS.values())
    
    def _get_endpoint(self, model: str, stream: bool = False) -> str:
        """Get the API endpoint for a model."""
        action = "streamGenerateContent" if stream else "generateContent"
        
        if self.use_vertex:
            # Vertex AI endpoint
            return (
                f"https://{self.region}-aiplatform.googleapis.com/v1/"
                f"projects/{self.project}/locations/{self.region}/"
                f"publishers/google/models/{model}:{action}"
            )
        else:
            # Google AI Studio endpoint
            return f"{self.GOOGLE_AI_BASE}/models/{model}:{action}?key={self.api_key}"
    
    def _convert_messages(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict]]:
        """Convert to Google format."""
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        return system_instruction, contents
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion via Google AI."""
        start_time = time.time()
        model = model or self.default_model
        
        system_instruction, contents = self._convert_messages(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or 1024,
                "temperature": temperature if temperature is not None else 0.7,
            }
        }
        
        if top_p is not None:
            payload["generationConfig"]["topP"] = top_p
        if stop:
            payload["generationConfig"]["stopSequences"] = stop
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        # JSON mode
        if response_format and response_format.get("type") == "json_object":
            payload["generationConfig"]["responseMimeType"] = "application/json"
        
        # Function calling
        if tools:
            payload["tools"] = [{
                "functionDeclarations": [
                    {
                        "name": t["function"]["name"],
                        "description": t["function"].get("description", ""),
                        "parameters": t["function"].get("parameters", {}),
                    }
                    for t in tools
                ]
            }]
        
        endpoint = self._get_endpoint(model)
        
        try:
            response = await self._http_client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract response
            candidate = data["candidates"][0]
            content = candidate["content"]
            
            # Get text and/or function calls
            text_parts = []
            tool_calls = []
            
            for part in content.get("parts", []):
                if "text" in part:
                    text_parts.append(part["text"])
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append({
                        "id": f"call_{len(tool_calls)}",
                        "type": "function",
                        "function": {
                            "name": fc["name"],
                            "arguments": str(fc.get("args", {})),
                        }
                    })
            
            # Get usage
            usage_data = data.get("usageMetadata", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("promptTokenCount", 0),
                completion_tokens=usage_data.get("candidatesTokenCount", 0),
                total_tokens=usage_data.get("totalTokenCount", 0),
            )
            
            return ChatResponse(
                message="\n".join(text_parts),
                role=MessageRole.ASSISTANT,
                finish_reason=candidate.get("finishReason"),
                usage=usage,
                model=model,
                provider=self.name,
                tool_calls=tool_calls if tool_calls else None,
                latency_ms=self._measure_latency(start_time),
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            logger.error(f"Google API error: {error_detail}")
            
            raise ProviderError(
                message=f"Google API error: {error_detail.get('error', {}).get('message', str(e))}",
                code=error_detail.get('error', {}).get('status', 'API_ERROR'),
                provider=self.name,
                status_code=e.response.status_code,
                retryable=e.response.status_code in [429, 500, 503],
            )
        except Exception as e:
            logger.error(f"Google error: {e}")
            raise ProviderError(
                message=f"Google request failed: {str(e)}",
                code="GOOGLE_ERROR",
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
        
        system_instruction, contents = self._convert_messages(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or 1024,
                "temperature": temperature if temperature is not None else 0.7,
            }
        }
        
        if top_p is not None:
            payload["generationConfig"]["topP"] = top_p
        if stop:
            payload["generationConfig"]["stopSequences"] = stop
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        endpoint = self._get_endpoint(model, stream=True) + "&alt=sse"
        
        try:
            async with self._http_client.stream("POST", endpoint, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            data = json.loads(line[6:])
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    if "text" in part:
                                        yield part["text"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Google stream error: {e}")
            raise ProviderError(
                message=f"Google streaming failed: {str(e)}",
                code="GOOGLE_STREAM_ERROR",
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
        """Generate text."""
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
        model = model or "text-embedding-004"
        
        endpoint = f"{self.GOOGLE_AI_BASE}/models/{model}:embedContent?key={self.api_key}"
        
        embeddings = []
        for text in texts:
            payload = {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]}
            }
            
            try:
                response = await self._http_client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                
                embedding = data.get("embedding", {}).get("values", [])
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Google embedding error: {e}")
                raise ProviderError(
                    message=f"Google embedding failed: {str(e)}",
                    code="GOOGLE_EMBED_ERROR",
                    provider=self.name,
                )
        
        dimensions = len(embeddings[0]) if embeddings else 0
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            provider=self.name,
            dimensions=dimensions,
        )
