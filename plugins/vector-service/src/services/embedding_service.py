"""
Embedding Service - Generate text embeddings locally or via LLM service.
"""
from typing import Optional, List, Union
import asyncio

import httpx
import numpy as np
from loguru import logger

from ..config import settings


class EmbeddingServiceError(Exception):
    """Custom exception for embedding service errors."""

    def __init__(self, message: str, code: str = "EMBEDDING_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class EmbeddingService:
    """
    Service for generating text embeddings.

    Supports two modes:
    - local: Uses sentence-transformers model
    - llm-service: Calls remote LLM service for embeddings
    """

    def __init__(self):
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.llm_service_url = settings.llm_service_url
        self.llm_service_timeout = settings.llm_service_timeout

        self._model = None
        self._http_client: Optional[httpx.AsyncClient] = None

        logger.info(f"EmbeddingService initialized: provider={self.provider}, model={self.model_name}")

    def _load_local_model(self) -> None:
        """Load the local sentence-transformers model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)

            # Update dimensions from model
            self.dimensions = self._model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded: dimensions={self.dimensions}")

        except ImportError:
            raise EmbeddingServiceError(
                message="sentence-transformers not installed. Run: pip install sentence-transformers",
                code="IMPORT_ERROR",
            )
        except Exception as e:
            raise EmbeddingServiceError(
                message=f"Failed to load embedding model: {str(e)}",
                code="LOAD_ERROR",
            )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for LLM service."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.llm_service_timeout,
                base_url=self.llm_service_url,
            )
        return self._http_client

    async def close(self) -> None:
        """Close resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def is_loaded(self) -> bool:
        """Check if local model is loaded."""
        return self._model is not None

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        if self.provider == "local" and self._model:
            return self._model.get_sentence_embedding_dimension()
        return self.dimensions

    async def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
    ) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings

        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return []

        if self.provider == "local":
            return await self._generate_local(texts, normalize)
        else:
            return await self._generate_remote(texts, normalize)

    async def _generate_local(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings using local model."""
        # Load model if not loaded
        if self._model is None:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_local_model)

        try:
            # Generate embeddings in executor
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._model.encode(
                    texts,
                    normalize_embeddings=normalize,
                    show_progress_bar=False,
                )
            )

            # Convert to list of lists
            return embeddings.tolist()

        except Exception as e:
            raise EmbeddingServiceError(
                message=f"Failed to generate embeddings: {str(e)}",
                code="GENERATE_ERROR",
            )

    async def _generate_remote(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings using remote LLM service."""
        try:
            client = await self._get_http_client()

            response = await client.post(
                "/api/v1/embeddings",
                json={
                    "text": texts,
                    "model": self.model_name,
                    "normalize": normalize,
                },
            )

            if response.status_code != 200:
                raise EmbeddingServiceError(
                    message=f"LLM service returned status {response.status_code}",
                    code="REMOTE_ERROR",
                    details={"response": response.text},
                )

            data = response.json()

            if not data.get("success", True):
                raise EmbeddingServiceError(
                    message=data.get("error", "Unknown error from LLM service"),
                    code="REMOTE_ERROR",
                )

            return data["embeddings"]

        except httpx.TimeoutException:
            raise EmbeddingServiceError(
                message="LLM service request timed out",
                code="TIMEOUT_ERROR",
            )
        except httpx.ConnectError:
            raise EmbeddingServiceError(
                message=f"Failed to connect to LLM service at {self.llm_service_url}",
                code="CONNECTION_ERROR",
            )
        except EmbeddingServiceError:
            raise
        except Exception as e:
            raise EmbeddingServiceError(
                message=f"Failed to generate embeddings: {str(e)}",
                code="REMOTE_ERROR",
            )

    async def generate_single(
        self,
        text: str,
        normalize: bool = True,
    ) -> List[float]:
        """Generate embedding for single text."""
        embeddings = await self.generate_embeddings([text], normalize)
        return embeddings[0] if embeddings else []

    async def check_health(self) -> dict:
        """Check embedding service health."""
        if self.provider == "local":
            return {
                "status": "healthy" if self._model else "not_loaded",
                "provider": "local",
                "model": self.model_name,
                "dimensions": self.dimensions,
                "loaded": self._model is not None,
            }
        else:
            try:
                client = await self._get_http_client()
                response = await client.get("/health", timeout=5.0)
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "provider": "llm-service",
                        "url": self.llm_service_url,
                        "model": self.model_name,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "provider": "llm-service",
                        "error": f"Status {response.status_code}",
                    }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "provider": "llm-service",
                    "error": str(e),
                }


# =============================================================================
# Singleton
# =============================================================================

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def close_embedding_service() -> None:
    """Close the embedding service."""
    global _embedding_service
    if _embedding_service:
        await _embedding_service.close()
        _embedding_service = None
