"""
Hugging Face Provider - Open source models via Inference API or local.

Supports:
- Hugging Face Inference API (serverless)
- Inference Endpoints (dedicated)
- Local models via transformers
- Text generation, embeddings, and more
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


# Popular Hugging Face models
HUGGINGFACE_MODELS = {
    # Text Generation
    "meta-llama/Llama-3.2-3B-Instruct": ModelInfo(
        id="meta-llama/Llama-3.2-3B-Instruct",
        name="Llama 3.2 3B Instruct",
        provider="huggingface",
        context_length=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        description="Meta's efficient Llama 3.2",
    ),
    "meta-llama/Llama-3.1-8B-Instruct": ModelInfo(
        id="meta-llama/Llama-3.1-8B-Instruct",
        name="Llama 3.1 8B Instruct",
        provider="huggingface",
        context_length=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        description="Meta's Llama 3.1 8B",
    ),
    "mistralai/Mistral-7B-Instruct-v0.3": ModelInfo(
        id="mistralai/Mistral-7B-Instruct-v0.3",
        name="Mistral 7B Instruct v0.3",
        provider="huggingface",
        context_length=32768,
        max_output_tokens=4096,
        supports_streaming=True,
        description="Mistral's flagship 7B model",
    ),
    "microsoft/Phi-3-mini-4k-instruct": ModelInfo(
        id="microsoft/Phi-3-mini-4k-instruct",
        name="Phi-3 Mini 4K",
        provider="huggingface",
        context_length=4096,
        max_output_tokens=2048,
        supports_streaming=True,
        description="Microsoft's small but capable model",
    ),
    "google/gemma-2-9b-it": ModelInfo(
        id="google/gemma-2-9b-it",
        name="Gemma 2 9B Instruct",
        provider="huggingface",
        context_length=8192,
        max_output_tokens=4096,
        supports_streaming=True,
        description="Google's open Gemma 2",
    ),
    "Qwen/Qwen2.5-7B-Instruct": ModelInfo(
        id="Qwen/Qwen2.5-7B-Instruct",
        name="Qwen 2.5 7B Instruct",
        provider="huggingface",
        context_length=32768,
        max_output_tokens=8192,
        supports_streaming=True,
        description="Alibaba's Qwen 2.5",
    ),
    # Embeddings
    "sentence-transformers/all-MiniLM-L6-v2": ModelInfo(
        id="sentence-transformers/all-MiniLM-L6-v2",
        name="all-MiniLM-L6-v2",
        provider="huggingface",
        context_length=256,
        description="Fast sentence embeddings (384 dims)",
    ),
    "sentence-transformers/all-mpnet-base-v2": ModelInfo(
        id="sentence-transformers/all-mpnet-base-v2",
        name="all-mpnet-base-v2",
        provider="huggingface",
        context_length=384,
        description="High quality embeddings (768 dims)",
    ),
    "BAAI/bge-large-en-v1.5": ModelInfo(
        id="BAAI/bge-large-en-v1.5",
        name="BGE Large English v1.5",
        provider="huggingface",
        context_length=512,
        description="BAAI's top embedding model",
    ),
}


class HuggingFaceProvider(LLMProvider):
    """
    Hugging Face Provider for open source models.
    
    Access modes:
    1. Inference API (serverless) - Free tier available
    2. Inference Endpoints (dedicated) - Custom endpoint URL
    3. Local (via transformers) - Not implemented in this provider
    
    Popular models:
    - Llama 3.x
    - Mistral/Mixtral
    - Phi-3
    - Gemma 2
    - Qwen 2.5
    - Falcon
    - And thousands more on the Hub
    """
    
    name = "huggingface"
    display_name = "Hugging Face"
    
    INFERENCE_API_BASE = "https://api-inference.huggingface.co/models"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key  # HF token
        self.endpoint_url = config.api_base  # Custom endpoint URL
        self.default_model = config.default_model or "meta-llama/Llama-3.2-3B-Instruct"
        self.default_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> None:
        """Initialize the HF client."""
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self._http_client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers,
        )
        
        mode = "Inference Endpoint" if self.endpoint_url else "Inference API"
        logger.info(f"Hugging Face provider initialized ({mode})")
    
    async def close(self) -> None:
        """Close the client."""
        if self._http_client:
            await self._http_client.aclose()
    
    def get_capabilities(self) -> ProviderCapabilities:
        """HF capabilities."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=True,
            streaming=True,
            function_calling=False,  # Model dependent
            json_mode=False,
            vision=False,  # Model dependent
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List popular HF models."""
        return list(HUGGINGFACE_MODELS.values())
    
    def _get_endpoint(self, model: str) -> str:
        """Get the API endpoint for a model."""
        if self.endpoint_url:
            return self.endpoint_url
        return f"{self.INFERENCE_API_BASE}/{model}"
    
    def _build_chat_prompt(self, messages: List[ChatMessage], model: str) -> str:
        """Build chat prompt in model-specific format."""
        # Detect model family and use appropriate format
        model_lower = model.lower()
        
        if "llama" in model_lower:
            # Llama 3 format
            parts = ["<|begin_of_text|>"]
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    parts.append(f"<|start_header_id|>system<|end_header_id|>\n\n{msg.content}<|eot_id|>")
                elif msg.role == MessageRole.USER:
                    parts.append(f"<|start_header_id|>user<|end_header_id|>\n\n{msg.content}<|eot_id|>")
                else:
                    parts.append(f"<|start_header_id|>assistant<|end_header_id|>\n\n{msg.content}<|eot_id|>")
            parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
            return "".join(parts)
        
        elif "mistral" in model_lower or "mixtral" in model_lower:
            # Mistral format
            parts = []
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    parts.append(f"[INST] {msg.content} [/INST]")
                elif msg.role == MessageRole.USER:
                    parts.append(f"[INST] {msg.content} [/INST]")
                else:
                    parts.append(msg.content)
            return " ".join(parts)
        
        elif "phi" in model_lower:
            # Phi format
            parts = []
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    parts.append(f"<|system|>\n{msg.content}<|end|>")
                elif msg.role == MessageRole.USER:
                    parts.append(f"<|user|>\n{msg.content}<|end|>")
                else:
                    parts.append(f"<|assistant|>\n{msg.content}<|end|>")
            parts.append("<|assistant|>\n")
            return "".join(parts)
        
        elif "gemma" in model_lower:
            # Gemma format
            parts = []
            for msg in messages:
                if msg.role == MessageRole.USER:
                    parts.append(f"<start_of_turn>user\n{msg.content}<end_of_turn>")
                else:
                    parts.append(f"<start_of_turn>model\n{msg.content}<end_of_turn>")
            parts.append("<start_of_turn>model\n")
            return "\n".join(parts)
        
        elif "qwen" in model_lower:
            # Qwen format
            parts = []
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    parts.append(f"<|im_start|>system\n{msg.content}<|im_end|>")
                elif msg.role == MessageRole.USER:
                    parts.append(f"<|im_start|>user\n{msg.content}<|im_end|>")
                else:
                    parts.append(f"<|im_start|>assistant\n{msg.content}<|im_end|>")
            parts.append("<|im_start|>assistant\n")
            return "\n".join(parts)
        
        else:
            # Generic ChatML format
            parts = []
            for msg in messages:
                parts.append(f"<|im_start|>{msg.role.value}\n{msg.content}<|im_end|>")
            parts.append("<|im_start|>assistant\n")
            return "\n".join(parts)
    
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
        """Generate chat completion via HF Inference API."""
        start_time = time.time()
        model = model or self.default_model
        
        prompt = self._build_chat_prompt(messages, model)
        endpoint = self._get_endpoint(model)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens or 512,
                "temperature": temperature if temperature is not None else 0.7,
                "top_p": top_p or 0.95,
                "do_sample": True,
                "return_full_text": False,
            },
        }
        
        if stop:
            payload["parameters"]["stop_sequences"] = stop
        
        try:
            response = await self._http_client.post(endpoint, json=payload)
            
            # Handle model loading
            if response.status_code == 503:
                data = response.json()
                estimated_time = data.get("estimated_time", 30)
                raise ProviderError(
                    message=f"Model is loading. Estimated time: {estimated_time}s",
                    code="MODEL_LOADING",
                    provider=self.name,
                    retryable=True,
                    details={"estimated_time": estimated_time},
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            if isinstance(data, list):
                generated_text = data[0].get("generated_text", "")
            else:
                generated_text = data.get("generated_text", "")
            
            return ChatResponse(
                message=generated_text.strip(),
                role=MessageRole.ASSISTANT,
                finish_reason="stop",
                model=model,
                provider=self.name,
                latency_ms=self._measure_latency(start_time),
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except:
                pass
            
            logger.error(f"HF API error: {error_detail}")
            
            raise ProviderError(
                message=f"HF API error: {error_detail.get('error', str(e))}",
                code="HF_API_ERROR",
                provider=self.name,
                status_code=e.response.status_code,
                retryable=e.response.status_code in [429, 500, 503],
            )
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"HF error: {e}")
            raise ProviderError(
                message=f"HF request failed: {str(e)}",
                code="HF_ERROR",
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
        """Stream chat completion (if supported by endpoint)."""
        model = model or self.default_model
        
        # Check if using dedicated endpoint with streaming
        if self.endpoint_url:
            prompt = self._build_chat_prompt(messages, model)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens or 512,
                    "temperature": temperature if temperature is not None else 0.7,
                    "top_p": top_p or 0.95,
                    "do_sample": True,
                    "return_full_text": False,
                },
                "stream": True,
            }
            
            try:
                async with self._http_client.stream("POST", self.endpoint_url, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            import json
                            try:
                                data = json.loads(line[5:])
                                token = data.get("token", {}).get("text", "")
                                if token and not data.get("token", {}).get("special", False):
                                    yield token
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                logger.error(f"HF stream error: {e}")
                raise ProviderError(
                    message=f"HF streaming failed: {str(e)}",
                    code="HF_STREAM_ERROR",
                    provider=self.name,
                )
        else:
            # Fall back to non-streaming for Inference API
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
        endpoint = self._get_endpoint(model)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens or 512,
                "temperature": temperature if temperature is not None else 0.7,
                "top_p": top_p or 0.95,
                "do_sample": True,
                "return_full_text": False,
            },
        }
        
        if stop:
            payload["parameters"]["stop_sequences"] = stop
        
        try:
            response = await self._http_client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                generated_text = data[0].get("generated_text", "")
            else:
                generated_text = data.get("generated_text", "")
            
            return GenerationResponse(
                text=generated_text.strip(),
                finish_reason="stop",
                model=model,
                provider=self.name,
                latency_ms=self._measure_latency(start_time),
            )
            
        except Exception as e:
            logger.error(f"HF generation error: {e}")
            raise ProviderError(
                message=f"HF generation failed: {str(e)}",
                code="HF_ERROR",
                provider=self.name,
            )
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embeddings using sentence-transformers models."""
        model = model or self.default_embedding_model
        endpoint = self._get_endpoint(model)
        
        try:
            response = await self._http_client.post(
                endpoint,
                json={"inputs": texts, "options": {"wait_for_model": True}},
            )
            response.raise_for_status()
            embeddings = response.json()
            
            # Handle single vs batch response
            if not isinstance(embeddings[0], list):
                embeddings = [embeddings]
            
            dimensions = len(embeddings[0]) if embeddings else 0
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                provider=self.name,
                dimensions=dimensions,
            )
            
        except Exception as e:
            logger.error(f"HF embedding error: {e}")
            raise ProviderError(
                message=f"HF embedding failed: {str(e)}",
                code="HF_EMBED_ERROR",
                provider=self.name,
            )
    
    async def download_model(self, model_id: str, cache_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a model from Hugging Face Hub for local use.
        
        This is a utility method - the downloaded model would be used
        with vLLM or transformers directly.
        """
        try:
            from huggingface_hub import snapshot_download
            
            path = snapshot_download(
                repo_id=model_id,
                cache_dir=cache_dir,
                token=self.api_key,
            )
            
            return {
                "success": True,
                "model_id": model_id,
                "local_path": path,
            }
            
        except ImportError:
            raise ProviderError(
                message="huggingface_hub is required. Install with: pip install huggingface_hub",
                code="MISSING_DEPENDENCY",
                provider=self.name,
            )
        except Exception as e:
            raise ProviderError(
                message=f"Failed to download model: {str(e)}",
                code="DOWNLOAD_ERROR",
                provider=self.name,
            )
