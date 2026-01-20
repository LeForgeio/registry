"""
vLLM Client Service - Wrapper for OpenAI-compatible vLLM API.
"""
import asyncio
from typing import Optional, List, Dict, Any, AsyncIterator
from openai import AsyncOpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import tiktoken

from ..config import settings
from ..models import ChatMessage, TokenUsage


class VLLMClientError(Exception):
    """Custom exception for vLLM client errors."""
    def __init__(self, message: str, code: str = "VLLM_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class VLLMClient:
    """
    Client for interacting with vLLM server via OpenAI-compatible API.
    """

    def __init__(self):
        self.base_url = settings.vllm_base_url.rstrip("/v1").rstrip("/")
        self.api_key = settings.vllm_api_key or "EMPTY"  # vLLM uses dummy key
        self.default_model = settings.default_model
        self.timeout = settings.request_timeout

        # Initialize OpenAI client pointing to vLLM
        self.client = AsyncOpenAI(
            base_url=settings.vllm_base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

        # HTTP client for health checks
        self.http_client = httpx.AsyncClient(timeout=10.0)

        # Token encoder for counting
        try:
            self._encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoder = None

        logger.info(f"VLLMClient initialized with base_url={self.base_url}")

    async def close(self):
        """Close the client connections."""
        await self.http_client.aclose()

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self._encoder:
            return len(self._encoder.encode(text))
        # Fallback: rough estimate
        return len(text.split()) * 4 // 3

    async def check_health(self) -> Dict[str, Any]:
        """Check vLLM server health."""
        try:
            response = await self.http_client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return {"status": "healthy", "message": "vLLM server is running"}
            return {"status": "unhealthy", "message": f"Status code: {response.status_code}"}
        except httpx.ConnectError:
            return {"status": "unhealthy", "message": "Cannot connect to vLLM server"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def list_models(self) -> List[str]:
        """List available models from vLLM server."""
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate text completion.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop: Stop sequences
            model: Model to use

        Returns:
            Dictionary with generated text and metadata
        """
        model = model or self.default_model
        max_tokens = max_tokens or settings.default_max_tokens
        temperature = temperature if temperature is not None else settings.default_temperature
        top_p = top_p if top_p is not None else settings.default_top_p

        try:
            response = await self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                extra_body={"top_k": top_k} if top_k else None,
            )

            choice = response.choices[0]
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else self.count_tokens(prompt),
                completion_tokens=response.usage.completion_tokens if response.usage else self.count_tokens(choice.text),
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )

            return {
                "text": choice.text,
                "finish_reason": choice.finish_reason,
                "usage": usage,
                "model": model,
            }

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise VLLMClientError(
                message=f"Text generation failed: {str(e)}",
                code="GENERATION_ERROR",
                details={"model": model, "prompt_length": len(prompt)}
            )

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream text generation.

        Yields:
            Generated text chunks
        """
        model = model or self.default_model
        max_tokens = max_tokens or settings.default_max_tokens
        temperature = temperature if temperature is not None else settings.default_temperature
        top_p = top_p if top_p is not None else settings.default_top_p

        try:
            stream = await self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].text:
                    yield chunk.choices[0].text

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise VLLMClientError(
                message=f"Streaming generation failed: {str(e)}",
                code="STREAM_ERROR",
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def chat(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chat completion.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            model: Model to use

        Returns:
            Dictionary with response message and metadata
        """
        model = model or self.default_model
        max_tokens = max_tokens or settings.default_max_tokens
        temperature = temperature if temperature is not None else settings.default_temperature
        top_p = top_p if top_p is not None else settings.default_top_p

        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            choice = response.choices[0]
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )

            return {
                "message": choice.message.content,
                "finish_reason": choice.finish_reason,
                "usage": usage,
                "model": model,
            }

        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise VLLMClientError(
                message=f"Chat completion failed: {str(e)}",
                code="CHAT_ERROR",
                details={"model": model, "message_count": len(messages)}
            )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion.

        Yields:
            Response message chunks
        """
        model = model or self.default_model
        max_tokens = max_tokens or settings.default_max_tokens
        temperature = temperature if temperature is not None else settings.default_temperature
        top_p = top_p if top_p is not None else settings.default_top_p

        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            raise VLLMClientError(
                message=f"Streaming chat failed: {str(e)}",
                code="STREAM_ERROR",
            )

    async def classify(
        self,
        text: str,
        categories: List[str],
        model: Optional[str] = None,
        multi_label: bool = False,
    ) -> Dict[str, Any]:
        """
        Classify text into categories using few-shot prompting.

        Args:
            text: Text to classify
            categories: List of possible categories
            model: Model to use
            multi_label: Allow multiple categories

        Returns:
            Dictionary with classification results
        """
        model = model or self.default_model
        categories_str = ", ".join(categories)

        if multi_label:
            prompt = f"""Classify the following text into one or more of these categories: {categories_str}

Text: {text}

Return only the category names that apply, separated by commas. If none apply, return "none".

Categories:"""
        else:
            prompt = f"""Classify the following text into exactly one of these categories: {categories_str}

Text: {text}

Return only the single most appropriate category name.

Category:"""

        try:
            result = await self.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1,  # Low temperature for classification
                model=model,
            )

            response_text = result["text"].strip().lower()

            # Parse the response
            scores = []
            for cat in categories:
                cat_lower = cat.lower()
                if cat_lower in response_text:
                    scores.append({"category": cat, "confidence": 0.9})
                else:
                    scores.append({"category": cat, "confidence": 0.1})

            # Normalize scores
            total = sum(s["confidence"] for s in scores)
            if total > 0:
                for s in scores:
                    s["confidence"] = s["confidence"] / total

            # Sort by confidence
            scores.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "category": scores[0]["category"],
                "confidence": scores[0]["confidence"],
                "scores": scores,
                "model": model,
            }

        except VLLMClientError:
            raise
        except Exception as e:
            raise VLLMClientError(
                message=f"Classification failed: {str(e)}",
                code="CLASSIFY_ERROR",
            )

    async def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract named entities from text.

        Args:
            text: Text to extract entities from
            entity_types: Types of entities to extract
            model: Model to use

        Returns:
            Dictionary with extracted entities
        """
        model = model or self.default_model
        default_types = ["person", "organization", "location", "date", "email", "phone", "url"]
        entity_types = entity_types or default_types
        types_str = ", ".join(entity_types)

        prompt = f"""Extract entities from the following text. Find entities of these types: {types_str}

Text: {text}

For each entity found, output in this exact format:
ENTITY: [text] | TYPE: [type] | START: [start_position] | END: [end_position]

If no entities are found, output: NO_ENTITIES_FOUND

Entities:"""

        try:
            result = await self.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,
                model=model,
            )

            response_text = result["text"].strip()
            entities = []

            if "NO_ENTITIES_FOUND" not in response_text:
                lines = response_text.split("\n")
                for line in lines:
                    if "ENTITY:" in line and "TYPE:" in line:
                        try:
                            # Parse the entity line
                            parts = line.split("|")
                            entity_text = parts[0].replace("ENTITY:", "").strip()
                            entity_type = parts[1].replace("TYPE:", "").strip().lower()

                            # Find position in original text
                            start = text.lower().find(entity_text.lower())
                            if start == -1:
                                start = 0
                            end = start + len(entity_text)

                            entities.append({
                                "text": entity_text,
                                "type": entity_type,
                                "start": start,
                                "end": end,
                                "confidence": 0.8,
                            })
                        except (IndexError, ValueError):
                            continue

            return {
                "entities": entities,
                "text": text,
                "model": model,
            }

        except VLLMClientError:
            raise
        except Exception as e:
            raise VLLMClientError(
                message=f"Entity extraction failed: {str(e)}",
                code="EXTRACT_ERROR",
            )

    async def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        style: str = "paragraph",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Summarize text.

        Args:
            text: Text to summarize
            max_length: Maximum summary length in tokens
            min_length: Minimum summary length in tokens
            style: Summary style (bullet, paragraph, tldr)
            model: Model to use

        Returns:
            Dictionary with summary and metadata
        """
        model = model or self.default_model
        max_length = max_length or 150
        original_tokens = self.count_tokens(text)

        style_instructions = {
            "bullet": "Provide the summary as bullet points.",
            "paragraph": "Provide the summary as a coherent paragraph.",
            "tldr": "Provide a very brief TL;DR summary in one or two sentences.",
        }

        style_instruction = style_instructions.get(style, style_instructions["paragraph"])

        prompt = f"""Summarize the following text concisely. {style_instruction}

Text:
{text}

Summary:"""

        try:
            result = await self.generate(
                prompt=prompt,
                max_tokens=max_length,
                temperature=0.3,
                model=model,
            )

            summary = result["text"].strip()
            summary_tokens = self.count_tokens(summary)

            return {
                "summary": summary,
                "original_length": original_tokens,
                "summary_length": summary_tokens,
                "compression_ratio": original_tokens / max(summary_tokens, 1),
                "model": model,
            }

        except VLLMClientError:
            raise
        except Exception as e:
            raise VLLMClientError(
                message=f"Summarization failed: {str(e)}",
                code="SUMMARIZE_ERROR",
            )


# Singleton instance
_client: Optional[VLLMClient] = None


def get_vllm_client() -> VLLMClient:
    """Get or create the vLLM client singleton."""
    global _client
    if _client is None:
        _client = VLLMClient()
    return _client


async def close_vllm_client():
    """Close the vLLM client."""
    global _client
    if _client:
        await _client.close()
        _client = None
