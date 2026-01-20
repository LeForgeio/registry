"""
Qdrant Client Service - Vector database operations.
"""
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings


class QdrantServiceError(Exception):
    """Custom exception for Qdrant service errors."""

    def __init__(self, message: str, code: str = "QDRANT_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class QdrantService:
    """
    Service for interacting with Qdrant vector database.
    """

    def __init__(self):
        self.host = settings.qdrant_host
        self.port = settings.qdrant_port
        self.grpc_port = settings.qdrant_grpc_port
        self.api_key = settings.qdrant_api_key
        self.https = settings.qdrant_https
        self.prefer_grpc = settings.qdrant_prefer_grpc
        self.timeout = settings.qdrant_timeout

        self._client: Optional[AsyncQdrantClient] = None
        self._sync_client: Optional[QdrantClient] = None

        logger.info(f"QdrantService initialized: {self.host}:{self.port}")

    async def connect(self) -> None:
        """Establish connection to Qdrant."""
        try:
            self._client = AsyncQdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                api_key=self.api_key,
                https=self.https,
                prefer_grpc=self.prefer_grpc,
                timeout=self.timeout,
            )
            # Test connection
            await self._client.get_collections()
            logger.info("Connected to Qdrant successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise QdrantServiceError(
                message=f"Failed to connect to Qdrant: {str(e)}",
                code="CONNECTION_ERROR",
            )

    async def close(self) -> None:
        """Close connection to Qdrant."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Qdrant connection closed")

    @property
    def client(self) -> AsyncQdrantClient:
        """Get the async client."""
        if not self._client:
            raise QdrantServiceError(
                message="Qdrant client not initialized",
                code="NOT_CONNECTED",
            )
        return self._client

    async def check_health(self) -> Dict[str, Any]:
        """Check Qdrant health status."""
        try:
            collections = await self.client.get_collections()
            return {
                "status": "healthy",
                "connected": True,
                "collections_count": len(collections.collections),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }

    # =========================================================================
    # Collection Operations
    # =========================================================================

    async def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "Cosine",
        on_disk: bool = False,
        hnsw_config: Optional[Dict[str, Any]] = None,
        quantization_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new collection.

        Args:
            name: Collection name
            vector_size: Vector dimensions
            distance: Distance metric (Cosine, Euclid, Dot)
            on_disk: Store vectors on disk
            hnsw_config: HNSW index configuration
            quantization_config: Quantization configuration

        Returns:
            Collection creation result
        """
        # Map distance string to enum
        distance_map = {
            "Cosine": qdrant_models.Distance.COSINE,
            "Euclid": qdrant_models.Distance.EUCLID,
            "Dot": qdrant_models.Distance.DOT,
        }
        distance_enum = distance_map.get(distance, qdrant_models.Distance.COSINE)

        # Build HNSW config
        hnsw = None
        if hnsw_config:
            hnsw = qdrant_models.HnswConfigDiff(**hnsw_config)

        # Build quantization config
        quantization = None
        if quantization_config:
            if quantization_config.get("scalar"):
                quantization = qdrant_models.ScalarQuantization(
                    scalar=qdrant_models.ScalarQuantizationConfig(
                        **quantization_config["scalar"]
                    )
                )

        try:
            await self.client.create_collection(
                collection_name=name,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=distance_enum,
                    on_disk=on_disk,
                ),
                hnsw_config=hnsw,
                quantization_config=quantization,
            )

            return {
                "name": name,
                "vector_size": vector_size,
                "distance": distance,
                "created": True,
            }

        except UnexpectedResponse as e:
            if "already exists" in str(e).lower():
                raise QdrantServiceError(
                    message=f"Collection '{name}' already exists",
                    code="COLLECTION_EXISTS",
                )
            raise QdrantServiceError(
                message=f"Failed to create collection: {str(e)}",
                code="CREATE_ERROR",
            )
        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to create collection: {str(e)}",
                code="CREATE_ERROR",
            )

    async def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections with details."""
        try:
            collections_response = await self.client.get_collections()
            collections = []

            for col in collections_response.collections:
                try:
                    info = await self.client.get_collection(col.name)
                    collections.append({
                        "name": col.name,
                        "status": info.status.value if info.status else "unknown",
                        "vectors_count": info.vectors_count or 0,
                        "points_count": info.points_count or 0,
                        "indexed_vectors_count": info.indexed_vectors_count or 0,
                        "vector_size": info.config.params.vectors.size if info.config else 0,
                        "distance": info.config.params.vectors.distance.value if info.config else "unknown",
                        "on_disk": info.config.params.vectors.on_disk if info.config else False,
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for collection {col.name}: {e}")
                    collections.append({
                        "name": col.name,
                        "status": "error",
                        "vectors_count": 0,
                        "points_count": 0,
                        "indexed_vectors_count": 0,
                        "vector_size": 0,
                        "distance": "unknown",
                        "on_disk": False,
                    })

            return collections

        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to list collections: {str(e)}",
                code="LIST_ERROR",
            )

    async def get_collection(self, name: str) -> Dict[str, Any]:
        """Get collection details."""
        try:
            info = await self.client.get_collection(name)
            return {
                "name": name,
                "status": info.status.value if info.status else "unknown",
                "vectors_count": info.vectors_count or 0,
                "points_count": info.points_count or 0,
                "indexed_vectors_count": info.indexed_vectors_count or 0,
                "segments_count": len(info.segments) if info.segments else 0,
                "vector_size": info.config.params.vectors.size if info.config else 0,
                "distance": info.config.params.vectors.distance.value if info.config else "unknown",
            }
        except UnexpectedResponse as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                raise QdrantServiceError(
                    message=f"Collection '{name}' not found",
                    code="NOT_FOUND",
                )
            raise QdrantServiceError(
                message=f"Failed to get collection: {str(e)}",
                code="GET_ERROR",
            )
        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to get collection: {str(e)}",
                code="GET_ERROR",
            )

    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            result = await self.client.delete_collection(name)
            return result
        except UnexpectedResponse as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                raise QdrantServiceError(
                    message=f"Collection '{name}' not found",
                    code="NOT_FOUND",
                )
            raise QdrantServiceError(
                message=f"Failed to delete collection: {str(e)}",
                code="DELETE_ERROR",
            )
        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to delete collection: {str(e)}",
                code="DELETE_ERROR",
            )

    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            await self.client.get_collection(name)
            return True
        except Exception:
            return False

    # =========================================================================
    # Point Operations
    # =========================================================================

    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        wait: bool = True,
    ) -> Dict[str, Any]:
        """
        Upsert points into a collection.

        Args:
            collection_name: Target collection
            points: List of points with id, vector, payload
            wait: Wait for indexing

        Returns:
            Upsert result
        """
        try:
            qdrant_points = []
            for point in points:
                qdrant_points.append(
                    qdrant_models.PointStruct(
                        id=point["id"],
                        vector=point["vector"],
                        payload=point.get("payload"),
                    )
                )

            # Batch upsert for large datasets
            batch_size = settings.default_batch_size
            total_upserted = 0

            for i in range(0, len(qdrant_points), batch_size):
                batch = qdrant_points[i:i + batch_size]
                await self.client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=wait,
                )
                total_upserted += len(batch)

            return {
                "status": "completed",
                "count": total_upserted,
            }

        except UnexpectedResponse as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                raise QdrantServiceError(
                    message=f"Collection '{collection_name}' not found",
                    code="NOT_FOUND",
                )
            raise QdrantServiceError(
                message=f"Failed to upsert points: {str(e)}",
                code="UPSERT_ERROR",
            )
        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to upsert points: {str(e)}",
                code="UPSERT_ERROR",
            )

    async def delete_points(
        self,
        collection_name: str,
        ids: List[Union[str, int]],
        wait: bool = True,
    ) -> int:
        """Delete points by IDs."""
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.PointIdsList(points=ids),
                wait=wait,
            )
            return len(ids)
        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to delete points: {str(e)}",
                code="DELETE_ERROR",
            )

    async def get_points(
        self,
        collection_name: str,
        ids: List[Union[str, int]],
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get points by IDs."""
        try:
            result = await self.client.retrieve(
                collection_name=collection_name,
                ids=ids,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )
            return [
                {
                    "id": point.id,
                    "payload": point.payload,
                    "vector": point.vector if with_vectors else None,
                }
                for point in result
            ]
        except Exception as e:
            raise QdrantServiceError(
                message=f"Failed to get points: {str(e)}",
                code="GET_ERROR",
            )

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search(
        self,
        collection_name: str,
        vector: List[float],
        limit: int = 10,
        offset: int = 0,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Collection to search
            vector: Query vector
            limit: Maximum results
            offset: Results offset
            filter: Qdrant filter
            score_threshold: Minimum score
            with_payload: Include payload
            with_vectors: Include vectors

        Returns:
            List of search results
        """
        try:
            # Build filter
            qdrant_filter = None
            if filter:
                qdrant_filter = qdrant_models.Filter(**filter)

            result = await self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                offset=offset,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )

            return [
                {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload if with_payload else None,
                    "vector": point.vector if with_vectors else None,
                }
                for point in result
            ]

        except UnexpectedResponse as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                raise QdrantServiceError(
                    message=f"Collection '{collection_name}' not found",
                    code="NOT_FOUND",
                )
            raise QdrantServiceError(
                message=f"Search failed: {str(e)}",
                code="SEARCH_ERROR",
            )
        except Exception as e:
            raise QdrantServiceError(
                message=f"Search failed: {str(e)}",
                code="SEARCH_ERROR",
            )

    async def search_batch(
        self,
        collection_name: str,
        vectors: List[List[float]],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for multiple vectors."""
        try:
            requests = [
                qdrant_models.SearchRequest(
                    vector=vector,
                    limit=limit,
                    filter=qdrant_models.Filter(**filter) if filter else None,
                    with_payload=with_payload,
                )
                for vector in vectors
            ]

            results = await self.client.search_batch(
                collection_name=collection_name,
                requests=requests,
            )

            return [
                [
                    {
                        "id": point.id,
                        "score": point.score,
                        "payload": point.payload,
                    }
                    for point in batch
                ]
                for batch in results
            ]

        except Exception as e:
            raise QdrantServiceError(
                message=f"Batch search failed: {str(e)}",
                code="SEARCH_ERROR",
            )

    async def recommend(
        self,
        collection_name: str,
        positive: List[Union[str, int]],
        negative: Optional[List[Union[str, int]]] = None,
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
        strategy: str = "average_vector",
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations based on positive/negative examples.

        Args:
            collection_name: Collection to search
            positive: IDs of positive examples
            negative: IDs of negative examples
            limit: Maximum results
            filter: Qdrant filter
            with_payload: Include payload
            with_vectors: Include vectors
            strategy: Recommendation strategy

        Returns:
            List of recommended points
        """
        try:
            qdrant_filter = None
            if filter:
                qdrant_filter = qdrant_models.Filter(**filter)

            # Map strategy
            strategy_map = {
                "average_vector": qdrant_models.RecommendStrategy.AVERAGE_VECTOR,
                "best_score": qdrant_models.RecommendStrategy.BEST_SCORE,
            }
            qdrant_strategy = strategy_map.get(
                strategy,
                qdrant_models.RecommendStrategy.AVERAGE_VECTOR
            )

            result = await self.client.recommend(
                collection_name=collection_name,
                positive=positive,
                negative=negative or [],
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=with_payload,
                with_vectors=with_vectors,
                strategy=qdrant_strategy,
            )

            return [
                {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload if with_payload else None,
                    "vector": point.vector if with_vectors else None,
                }
                for point in result
            ]

        except Exception as e:
            raise QdrantServiceError(
                message=f"Recommendation failed: {str(e)}",
                code="RECOMMEND_ERROR",
            )

    async def scroll(
        self,
        collection_name: str,
        limit: int = 100,
        offset: Optional[Union[str, int]] = None,
        filter: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> Dict[str, Any]:
        """Scroll through collection points."""
        try:
            qdrant_filter = None
            if filter:
                qdrant_filter = qdrant_models.Filter(**filter)

            result, next_offset = await self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset,
                scroll_filter=qdrant_filter,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )

            return {
                "points": [
                    {
                        "id": point.id,
                        "payload": point.payload,
                        "vector": point.vector if with_vectors else None,
                    }
                    for point in result
                ],
                "next_offset": next_offset,
            }

        except Exception as e:
            raise QdrantServiceError(
                message=f"Scroll failed: {str(e)}",
                code="SCROLL_ERROR",
            )


# =============================================================================
# Singleton
# =============================================================================

_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Get or create the Qdrant service singleton."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service


async def close_qdrant_service() -> None:
    """Close the Qdrant service."""
    global _qdrant_service
    if _qdrant_service:
        await _qdrant_service.close()
        _qdrant_service = None
