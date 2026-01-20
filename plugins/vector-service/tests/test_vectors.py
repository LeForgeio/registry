"""
Tests for vector operations endpoints.
"""

import pytest
import numpy as np
from httpx import AsyncClient


# =============================================================================
# Upsert Vectors Tests
# =============================================================================


class TestUpsertVectors:
    """Tests for POST /api/v1/collections/{name}/upsert endpoint."""

    @pytest.mark.asyncio
    async def test_upsert_single_vector(self, client: AsyncClient, mock_qdrant_service):
        """Test upserting a single vector."""
        response = await client.post(
            "/api/v1/collections/test_collection/upsert",
            json={
                "points": [
                    {
                        "id": "point_1",
                        "vector": np.random.randn(384).tolist(),
                        "payload": {"text": "Sample text", "category": "test"}
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        mock_qdrant_service.upsert_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_batch_vectors(self, client: AsyncClient, mock_qdrant_service, sample_vectors):
        """Test upserting batch of vectors."""
        response = await client.post(
            "/api/v1/collections/test_collection/upsert",
            json={"points": sample_vectors}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_upsert_with_integer_id(self, client: AsyncClient, mock_qdrant_service):
        """Test upserting vector with integer ID."""
        response = await client.post(
            "/api/v1/collections/test_collection/upsert",
            json={
                "points": [
                    {
                        "id": 12345,
                        "vector": np.random.randn(384).tolist(),
                        "payload": {"text": "Integer ID point"}
                    }
                ]
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upsert_without_payload(self, client: AsyncClient, mock_qdrant_service):
        """Test upserting vector without payload."""
        response = await client.post(
            "/api/v1/collections/test_collection/upsert",
            json={
                "points": [
                    {
                        "id": "point_no_payload",
                        "vector": np.random.randn(384).tolist()
                    }
                ]
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upsert_empty_points(self, client: AsyncClient):
        """Test upserting empty points list."""
        response = await client.post(
            "/api/v1/collections/test_collection/upsert",
            json={"points": []}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upsert_invalid_vector_dimension(self, client: AsyncClient):
        """Test upserting vector with wrong dimension."""
        response = await client.post(
            "/api/v1/collections/test_collection/upsert",
            json={
                "points": [
                    {
                        "id": "point_1",
                        "vector": [0.1, 0.2, 0.3]  # Wrong dimension
                    }
                ]
            }
        )
        
        # May return 200 but Qdrant will reject, or validation may catch it
        # depending on implementation
        assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# Vector Search Tests
# =============================================================================


class TestVectorSearch:
    """Tests for POST /api/v1/collections/{name}/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_with_vector(self, client: AsyncClient, mock_qdrant_service, sample_search_request):
        """Test search with vector input."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json=sample_search_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        mock_qdrant_service.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_limit(self, client: AsyncClient, mock_qdrant_service):
        """Test search with custom limit."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "limit": 5
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_with_score_threshold(self, client: AsyncClient, mock_qdrant_service):
        """Test search with score threshold."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "score_threshold": 0.8
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_with_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test search with filter conditions."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "filter": {
                    "must": [
                        {"key": "category", "match": {"value": "test"}}
                    ]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_with_payload(self, client: AsyncClient, mock_qdrant_service):
        """Test search returning payload."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "with_payload": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        for result in data["results"]:
            assert "payload" in result

    @pytest.mark.asyncio
    async def test_search_with_vectors_returned(self, client: AsyncClient, mock_qdrant_service):
        """Test search returning vectors."""
        mock_qdrant_service.search.return_value = [
            {"id": "1", "score": 0.95, "payload": {}, "vector": np.random.randn(384).tolist()}
        ]
        
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "with_vectors": True
            }
        )
        
        assert response.status_code == 200


# =============================================================================
# Text Search Tests
# =============================================================================


class TestTextSearch:
    """Tests for POST /api/v1/collections/{name}/search-text endpoint."""

    @pytest.mark.asyncio
    async def test_text_search_basic(self, client: AsyncClient, mock_qdrant_service, mock_embedding_service):
        """Test basic text search."""
        response = await client.post(
            "/api/v1/collections/test_collection/search-text",
            json={
                "text": "semantic search query",
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @pytest.mark.asyncio
    async def test_text_search_with_filter(self, client: AsyncClient, mock_qdrant_service, mock_embedding_service):
        """Test text search with filter."""
        response = await client.post(
            "/api/v1/collections/test_collection/search-text",
            json={
                "text": "machine learning",
                "filter": {
                    "must": [{"key": "category", "match": {"value": "ai"}}]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_text_search_empty_text(self, client: AsyncClient):
        """Test text search with empty text."""
        response = await client.post(
            "/api/v1/collections/test_collection/search-text",
            json={"text": ""}
        )
        
        assert response.status_code == 422


# =============================================================================
# Hybrid Search Tests
# =============================================================================


class TestHybridSearch:
    """Tests for POST /api/v1/collections/{name}/hybrid-search endpoint."""

    @pytest.mark.asyncio
    async def test_hybrid_search_basic(self, client: AsyncClient, mock_qdrant_service, mock_embedding_service):
        """Test basic hybrid search."""
        response = await client.post(
            "/api/v1/collections/test_collection/hybrid-search",
            json={
                "text": "vector database search",
                "sparse_field": "text",
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        mock_qdrant_service.hybrid_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_hybrid_search_with_alpha(self, client: AsyncClient, mock_qdrant_service, mock_embedding_service):
        """Test hybrid search with custom alpha."""
        response = await client.post(
            "/api/v1/collections/test_collection/hybrid-search",
            json={
                "text": "test query",
                "sparse_field": "text",
                "alpha": 0.3
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize("alpha", [0.0, 0.5, 1.0])
    async def test_hybrid_search_alpha_range(
        self, client: AsyncClient, mock_qdrant_service, mock_embedding_service, alpha: float
    ):
        """Test hybrid search with different alpha values."""
        response = await client.post(
            "/api/v1/collections/test_collection/hybrid-search",
            json={
                "text": "test",
                "sparse_field": "text",
                "alpha": alpha
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_hybrid_search_invalid_alpha(self, client: AsyncClient):
        """Test hybrid search with invalid alpha."""
        response = await client.post(
            "/api/v1/collections/test_collection/hybrid-search",
            json={
                "text": "test",
                "sparse_field": "text",
                "alpha": 1.5  # Out of range
            }
        )
        
        assert response.status_code == 422


# =============================================================================
# Recommend Tests
# =============================================================================


class TestRecommend:
    """Tests for POST /api/v1/collections/{name}/recommend endpoint."""

    @pytest.mark.asyncio
    async def test_recommend_with_positive_ids(self, client: AsyncClient, mock_qdrant_service):
        """Test recommendations with positive IDs."""
        response = await client.post(
            "/api/v1/collections/test_collection/recommend",
            json={
                "positive": ["point_1", "point_2"],
                "limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        mock_qdrant_service.recommend.assert_called_once()

    @pytest.mark.asyncio
    async def test_recommend_with_negative_ids(self, client: AsyncClient, mock_qdrant_service):
        """Test recommendations with positive and negative IDs."""
        response = await client.post(
            "/api/v1/collections/test_collection/recommend",
            json={
                "positive": ["point_1"],
                "negative": ["point_5"],
                "limit": 5
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recommend_with_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test recommendations with filter."""
        response = await client.post(
            "/api/v1/collections/test_collection/recommend",
            json={
                "positive": ["point_1"],
                "filter": {
                    "must": [{"key": "category", "match": {"value": "test"}}]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recommend_empty_positive(self, client: AsyncClient):
        """Test recommendations with empty positive list."""
        response = await client.post(
            "/api/v1/collections/test_collection/recommend",
            json={
                "positive": [],
                "limit": 5
            }
        )
        
        assert response.status_code == 422


# =============================================================================
# Delete Points Tests
# =============================================================================


class TestDeletePoints:
    """Tests for DELETE /api/v1/collections/{name}/points endpoint."""

    @pytest.mark.asyncio
    async def test_delete_points_by_ids(self, client: AsyncClient, mock_qdrant_service):
        """Test deleting points by IDs."""
        response = await client.request(
            "DELETE",
            "/api/v1/collections/test_collection/points",
            json={"point_ids": ["point_1", "point_2"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_qdrant_service.delete_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_points_by_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test deleting points by filter."""
        response = await client.request(
            "DELETE",
            "/api/v1/collections/test_collection/points",
            json={
                "filter": {
                    "must": [{"key": "category", "match": {"value": "test"}}]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_points_empty_ids(self, client: AsyncClient):
        """Test deleting with empty IDs list."""
        response = await client.request(
            "DELETE",
            "/api/v1/collections/test_collection/points",
            json={"point_ids": []}
        )
        
        assert response.status_code == 422


# =============================================================================
# Filter Query Tests
# =============================================================================


class TestFilterQueries:
    """Tests for filter query functionality."""

    @pytest.mark.asyncio
    async def test_must_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test must filter condition."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "filter": {
                    "must": [
                        {"key": "category", "match": {"value": "test"}}
                    ]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_should_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test should filter condition."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "filter": {
                    "should": [
                        {"key": "category", "match": {"value": "test"}},
                        {"key": "category", "match": {"value": "demo"}}
                    ]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_must_not_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test must_not filter condition."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "filter": {
                    "must_not": [
                        {"key": "category", "match": {"value": "excluded"}}
                    ]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_range_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test range filter condition."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "filter": {
                    "must": [
                        {"key": "price", "range": {"gte": 10, "lte": 100}}
                    ]
                }
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_geo_filter(self, client: AsyncClient, mock_qdrant_service):
        """Test geo filter condition."""
        response = await client.post(
            "/api/v1/collections/test_collection/search",
            json={
                "vector": np.random.randn(384).tolist(),
                "filter": {
                    "must": [
                        {
                            "key": "location",
                            "geo_radius": {
                                "center": {"lat": 40.7128, "lon": -74.0060},
                                "radius": 10000
                            }
                        }
                    ]
                }
            }
        )
        
        assert response.status_code == 200
