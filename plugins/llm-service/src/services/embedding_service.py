"""
Embedding Service - Generate text embeddings using sentence-transformers or vLLM.
"""
import asyncio
from typing import List, Optional, Union
import numpy as np
from loguru import logger

from ..config import settings


class EmbeddingServiceError(Exception):
    """Custom exception for embedding errors."""
    def __init__(self, message: str, code: str = "EMBEDDING_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class EmbeddingService:
    """
    Service for generating text embeddings.
    Uses sentence-transformers for CPU-friendly embeddings.
    """

    def __init__(self):
        self.model_name = settings.default_embedding_model
        self.model = None
        self.dimensions = None
        self._lock = asyncio.Lock()
        self._loaded = False

    async def load_model(self):
        """Load the embedding model."""
        if self._loaded:
            return

        async with self._lock:
            if self._loaded:
                return

            try:
                # Import here to avoid slow startup
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {self.model_name}")

                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None,
                    lambda: SentenceTransformer(
                        self.model_name,
                        cache_folder=settings.model_cache_dir
                    )
                )

                # Get dimensions from a test embedding
                test_embedding = self.model.encode(["test"])
                self.dimensions = len(test_embedding[0])

                self._loaded = True
                logger.info(f"Embedding model loaded. Dimensions: {self.dimensions}")

            except ImportError:
                logger.warning("sentence-transformers not available, embeddings will fail")
                raise EmbeddingServiceError(
                    "sentence-transformers not installed",
                    "DEPENDENCY_MISSING"
                )
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise EmbeddingServiceError(
                    f"Failed to load embedding model: {str(e)}",
                    "MODEL_LOAD_ERROR"
                )

    async def embed(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        model: Optional[str] = None,
    ) -> dict:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings
            model: Model to use (ignored for now, uses default)

        Returns:
            Dictionary with embeddings and metadata
        """
        if not self._loaded:
            await self.load_model()

        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            raise EmbeddingServiceError("No texts provided", "EMPTY_INPUT")

        try:
            # Run encoding in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(
                    texts,
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )
            )

            # Convert to list format
            embeddings_list = embeddings.tolist()

            # Estimate tokens (rough approximation)
            tokens_used = sum(len(text.split()) for text in texts)

            return {
                "embeddings": embeddings_list,
                "dimensions": self.dimensions,
                "model": self.model_name,
                "tokens_used": tokens_used,
            }

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingServiceError(
                f"Embedding generation failed: {str(e)}",
                "EMBED_ERROR"
            )

    async def similarity(
        self,
        text1: str,
        text2: str,
        normalize: bool = True,
    ) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text
            normalize: Whether to normalize embeddings

        Returns:
            Similarity score between 0 and 1
        """
        result = await self.embed([text1, text2], normalize=normalize)
        embeddings = np.array(result["embeddings"])

        # Cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1])
        if not normalize:
            norm1 = np.linalg.norm(embeddings[0])
            norm2 = np.linalg.norm(embeddings[1])
            if norm1 > 0 and norm2 > 0:
                similarity = similarity / (norm1 * norm2)

        return float(similarity)

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded

    def get_info(self) -> dict:
        """Get model info."""
        return {
            "name": self.model_name,
            "loaded": self._loaded,
            "dimensions": self.dimensions,
            "capabilities": ["embeddings", "similarity"],
        }


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
