"""
AWS Bedrock Provider - Multiple foundation models on AWS.

Supports:
- Anthropic Claude (3.5 Sonnet, 3 Opus/Sonnet/Haiku)
- Amazon Titan (Text, Embeddings)
- Meta Llama 3
- Mistral
- Cohere
"""
import time
import json
from typing import Optional, List, Dict, Any, AsyncIterator
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


# Bedrock model catalog
BEDROCK_MODELS = {
    # Anthropic Claude on Bedrock
    "anthropic.claude-3-5-sonnet-20241022-v2:0": ModelInfo(
        id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        name="Claude 3.5 Sonnet v2 (Bedrock)",
        provider="bedrock",
        context_length=200000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        description="Most intelligent Claude model on Bedrock",
    ),
    "anthropic.claude-3-sonnet-20240229-v1:0": ModelInfo(
        id="anthropic.claude-3-sonnet-20240229-v1:0",
        name="Claude 3 Sonnet (Bedrock)",
        provider="bedrock",
        context_length=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
    ),
    "anthropic.claude-3-haiku-20240307-v1:0": ModelInfo(
        id="anthropic.claude-3-haiku-20240307-v1:0",
        name="Claude 3 Haiku (Bedrock)",
        provider="bedrock",
        context_length=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        supports_vision=True,
        description="Fast and affordable",
    ),
    # Amazon Titan
    "amazon.titan-text-premier-v1:0": ModelInfo(
        id="amazon.titan-text-premier-v1:0",
        name="Titan Text Premier",
        provider="bedrock",
        context_length=32000,
        max_output_tokens=8192,
        supports_streaming=True,
        description="Amazon's premier text model",
    ),
    "amazon.titan-text-express-v1": ModelInfo(
        id="amazon.titan-text-express-v1",
        name="Titan Text Express",
        provider="bedrock",
        context_length=8000,
        max_output_tokens=8000,
        supports_streaming=True,
        description="Fast Amazon model",
    ),
    "amazon.titan-embed-text-v2:0": ModelInfo(
        id="amazon.titan-embed-text-v2:0",
        name="Titan Embeddings V2",
        provider="bedrock",
        context_length=8192,
        description="Amazon embeddings model",
    ),
    # Meta Llama
    "meta.llama3-1-70b-instruct-v1:0": ModelInfo(
        id="meta.llama3-1-70b-instruct-v1:0",
        name="Llama 3.1 70B Instruct",
        provider="bedrock",
        context_length=128000,
        max_output_tokens=2048,
        supports_streaming=True,
        description="Meta's largest Llama 3.1",
    ),
    "meta.llama3-1-8b-instruct-v1:0": ModelInfo(
        id="meta.llama3-1-8b-instruct-v1:0",
        name="Llama 3.1 8B Instruct",
        provider="bedrock",
        context_length=128000,
        max_output_tokens=2048,
        supports_streaming=True,
        description="Fast Llama 3.1",
    ),
    # Mistral
    "mistral.mistral-large-2407-v1:0": ModelInfo(
        id="mistral.mistral-large-2407-v1:0",
        name="Mistral Large",
        provider="bedrock",
        context_length=128000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_functions=True,
        description="Mistral's flagship model",
    ),
    "mistral.mixtral-8x7b-instruct-v0:1": ModelInfo(
        id="mistral.mixtral-8x7b-instruct-v0:1",
        name="Mixtral 8x7B",
        provider="bedrock",
        context_length=32000,
        max_output_tokens=4096,
        supports_streaming=True,
        description="Mistral MoE model",
    ),
    # Cohere
    "cohere.command-r-plus-v1:0": ModelInfo(
        id="cohere.command-r-plus-v1:0",
        name="Command R+",
        provider="bedrock",
        context_length=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_functions=True,
        description="Cohere's RAG-optimized model",
    ),
    "cohere.embed-english-v3": ModelInfo(
        id="cohere.embed-english-v3",
        name="Cohere Embed English v3",
        provider="bedrock",
        context_length=512,
        description="Cohere embeddings",
    ),
}

# Model aliases for convenience
BEDROCK_ALIASES = {
    "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "titan-premier": "amazon.titan-text-premier-v1:0",
    "titan-express": "amazon.titan-text-express-v1",
    "llama3-70b": "meta.llama3-1-70b-instruct-v1:0",
    "llama3-8b": "meta.llama3-1-8b-instruct-v1:0",
    "mistral-large": "mistral.mistral-large-2407-v1:0",
    "mixtral": "mistral.mixtral-8x7b-instruct-v0:1",
    "command-r-plus": "cohere.command-r-plus-v1:0",
}


class BedrockProvider(LLMProvider):
    """
    AWS Bedrock Provider for multiple foundation models.
    
    Provides access to:
    - Anthropic Claude (3.5 Sonnet, 3 Opus/Sonnet/Haiku)
    - Amazon Titan (Text, Embeddings)
    - Meta Llama 3
    - Mistral/Mixtral
    - Cohere Command
    
    Requires:
    - AWS credentials (access key + secret, or IAM role)
    - Bedrock model access enabled in AWS console
    """
    
    name = "bedrock"
    display_name = "AWS Bedrock"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.region = config.region or "us-east-1"
        self.access_key = config.api_key
        self.secret_key = config.extra.get("aws_secret_key")
        self.default_model = config.default_model or "anthropic.claude-3-5-sonnet-20241022-v2:0"
        self._bedrock_client = None
        self._bedrock_runtime = None
    
    async def initialize(self) -> None:
        """Initialize the Bedrock client."""
        try:
            import boto3
            from botocore.config import Config
            
            boto_config = Config(
                region_name=self.region,
                retries={"max_attempts": self.config.max_retries, "mode": "adaptive"},
            )
            
            # Use explicit credentials if provided, otherwise use default credential chain
            if self.access_key and self.secret_key:
                session = boto3.Session(
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region,
                )
            else:
                session = boto3.Session(region_name=self.region)
            
            self._bedrock_runtime = session.client(
                "bedrock-runtime",
                config=boto_config,
            )
            
            logger.info(f"Bedrock provider initialized: {self.region}")
            
        except ImportError:
            raise ProviderError(
                message="boto3 is required for AWS Bedrock. Install with: pip install boto3",
                code="MISSING_DEPENDENCY",
                provider=self.name,
            )
        except Exception as e:
            raise ProviderError(
                message=f"Failed to initialize Bedrock: {str(e)}",
                code="INIT_ERROR",
                provider=self.name,
            )
    
    async def close(self) -> None:
        """Close the client."""
        # Boto3 clients don't need explicit cleanup
        pass
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Bedrock capabilities (varies by model)."""
        return ProviderCapabilities(
            chat=True,
            completion=True,
            embeddings=True,
            streaming=True,
            function_calling=True,  # Claude, Mistral, Cohere
            json_mode=False,
            vision=True,  # Claude
        )
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Bedrock models."""
        return list(BEDROCK_MODELS.values())
    
    def _resolve_model(self, model: Optional[str]) -> str:
        """Resolve model alias to full model ID."""
        if not model:
            return self.default_model
        return BEDROCK_ALIASES.get(model, model)
    
    def _build_claude_body(
        self,
        messages: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        top_p: Optional[float],
        stop: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Build request body for Claude models."""
        system_prompt = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                anthropic_messages.append({"role": role, "content": msg.content})
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
            "temperature": temperature,
        }
        
        if system_prompt:
            body["system"] = system_prompt
        if top_p is not None:
            body["top_p"] = top_p
        if stop:
            body["stop_sequences"] = stop
        
        return body
    
    def _build_titan_body(
        self,
        messages: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        top_p: Optional[float],
        stop: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Build request body for Titan models."""
        # Combine messages into a single prompt
        prompt_parts = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                prompt_parts.append(f"Instructions: {msg.content}\n")
            elif msg.role == MessageRole.USER:
                prompt_parts.append(f"User: {msg.content}\n")
            else:
                prompt_parts.append(f"Assistant: {msg.content}\n")
        prompt_parts.append("Assistant:")
        
        return {
            "inputText": "".join(prompt_parts),
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": top_p or 1.0,
                "stopSequences": stop or [],
            }
        }
    
    def _build_llama_body(
        self,
        messages: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        top_p: Optional[float],
    ) -> Dict[str, Any]:
        """Build request body for Llama models."""
        # Llama uses a specific prompt format
        prompt_parts = ["<|begin_of_text|>"]
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                prompt_parts.append(f"<|start_header_id|>system<|end_header_id|>\n{msg.content}<|eot_id|>")
            elif msg.role == MessageRole.USER:
                prompt_parts.append(f"<|start_header_id|>user<|end_header_id|>\n{msg.content}<|eot_id|>")
            else:
                prompt_parts.append(f"<|start_header_id|>assistant<|end_header_id|>\n{msg.content}<|eot_id|>")
        
        prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>")
        
        return {
            "prompt": "".join(prompt_parts),
            "max_gen_len": max_tokens,
            "temperature": temperature,
            "top_p": top_p or 0.9,
        }
    
    def _build_mistral_body(
        self,
        messages: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        top_p: Optional[float],
    ) -> Dict[str, Any]:
        """Build request body for Mistral models."""
        # Mistral uses OpenAI-like format
        return {
            "messages": [msg.to_dict() for msg in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p or 1.0,
        }
    
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
        """Generate chat completion via Bedrock."""
        import asyncio
        
        start_time = time.time()
        model_id = self._resolve_model(model)
        max_tokens = max_tokens or 1024
        temperature = temperature if temperature is not None else 0.7
        
        # Build model-specific request body
        if model_id.startswith("anthropic."):
            body = self._build_claude_body(messages, max_tokens, temperature, top_p, stop)
        elif model_id.startswith("amazon.titan"):
            body = self._build_titan_body(messages, max_tokens, temperature, top_p, stop)
        elif model_id.startswith("meta.llama"):
            body = self._build_llama_body(messages, max_tokens, temperature, top_p)
        elif model_id.startswith("mistral."):
            body = self._build_mistral_body(messages, max_tokens, temperature, top_p)
        else:
            # Default to Anthropic format
            body = self._build_claude_body(messages, max_tokens, temperature, top_p, stop)
        
        try:
            # Run sync boto3 call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._bedrock_runtime.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )
            )
            
            response_body = json.loads(response["body"].read())
            
            # Parse model-specific response
            if model_id.startswith("anthropic."):
                content = response_body.get("content", [{}])[0].get("text", "")
                usage = TokenUsage(
                    prompt_tokens=response_body.get("usage", {}).get("input_tokens", 0),
                    completion_tokens=response_body.get("usage", {}).get("output_tokens", 0),
                )
                usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
                finish_reason = response_body.get("stop_reason")
            elif model_id.startswith("amazon.titan"):
                content = response_body.get("results", [{}])[0].get("outputText", "")
                usage = TokenUsage(
                    prompt_tokens=response_body.get("inputTextTokenCount", 0),
                    completion_tokens=response_body.get("results", [{}])[0].get("tokenCount", 0),
                )
                usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
                finish_reason = response_body.get("results", [{}])[0].get("completionReason")
            elif model_id.startswith("meta.llama"):
                content = response_body.get("generation", "")
                usage = TokenUsage(
                    prompt_tokens=response_body.get("prompt_token_count", 0),
                    completion_tokens=response_body.get("generation_token_count", 0),
                )
                usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
                finish_reason = response_body.get("stop_reason")
            elif model_id.startswith("mistral."):
                content = response_body.get("outputs", [{}])[0].get("text", "")
                usage = TokenUsage()
                finish_reason = response_body.get("outputs", [{}])[0].get("stop_reason")
            else:
                content = str(response_body)
                usage = TokenUsage()
                finish_reason = None
            
            return ChatResponse(
                message=content,
                role=MessageRole.ASSISTANT,
                finish_reason=finish_reason,
                usage=usage,
                model=model_id,
                provider=self.name,
                latency_ms=self._measure_latency(start_time),
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Bedrock error: {error_msg}")
            
            raise ProviderError(
                message=f"Bedrock request failed: {error_msg}",
                code="BEDROCK_ERROR",
                provider=self.name,
                retryable="throttl" in error_msg.lower() or "timeout" in error_msg.lower(),
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
        """Stream chat completion via Bedrock."""
        import asyncio
        
        model_id = self._resolve_model(model)
        max_tokens = max_tokens or 1024
        temperature = temperature if temperature is not None else 0.7
        
        # Build body based on model
        if model_id.startswith("anthropic."):
            body = self._build_claude_body(messages, max_tokens, temperature, top_p, stop)
        elif model_id.startswith("meta.llama"):
            body = self._build_llama_body(messages, max_tokens, temperature, top_p)
        elif model_id.startswith("mistral."):
            body = self._build_mistral_body(messages, max_tokens, temperature, top_p)
        else:
            body = self._build_claude_body(messages, max_tokens, temperature, top_p, stop)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._bedrock_runtime.invoke_model_with_response_stream(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )
            )
            
            stream = response.get("body")
            if stream:
                for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        chunk_data = json.loads(chunk.get("bytes", b"{}").decode())
                        
                        # Extract text based on model
                        if model_id.startswith("anthropic."):
                            if chunk_data.get("type") == "content_block_delta":
                                text = chunk_data.get("delta", {}).get("text", "")
                                if text:
                                    yield text
                        elif model_id.startswith("meta.llama"):
                            text = chunk_data.get("generation", "")
                            if text:
                                yield text
                        elif model_id.startswith("mistral."):
                            outputs = chunk_data.get("outputs", [])
                            if outputs:
                                text = outputs[0].get("text", "")
                                if text:
                                    yield text
                                    
        except Exception as e:
            logger.error(f"Bedrock stream error: {e}")
            raise ProviderError(
                message=f"Bedrock streaming failed: {str(e)}",
                code="BEDROCK_STREAM_ERROR",
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
        """Generate embeddings using Titan or Cohere."""
        import asyncio
        
        model_id = model or "amazon.titan-embed-text-v2:0"
        embeddings = []
        
        for text in texts:
            if model_id.startswith("amazon.titan"):
                body = {"inputText": text}
            elif model_id.startswith("cohere."):
                body = {"texts": [text], "input_type": "search_document"}
            else:
                raise ProviderError(
                    message=f"Model {model_id} does not support embeddings",
                    code="NOT_SUPPORTED",
                    provider=self.name,
                )
            
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self._bedrock_runtime.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body),
                        contentType="application/json",
                        accept="application/json",
                    )
                )
                
                response_body = json.loads(response["body"].read())
                
                if model_id.startswith("amazon.titan"):
                    embedding = response_body.get("embedding", [])
                elif model_id.startswith("cohere."):
                    embedding = response_body.get("embeddings", [[]])[0]
                else:
                    embedding = []
                
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Bedrock embedding error: {e}")
                raise ProviderError(
                    message=f"Bedrock embedding failed: {str(e)}",
                    code="BEDROCK_EMBED_ERROR",
                    provider=self.name,
                )
        
        dimensions = len(embeddings[0]) if embeddings else 0
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model=model_id,
            provider=self.name,
            dimensions=dimensions,
        )
