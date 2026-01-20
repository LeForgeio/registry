"""
Tests for collection management endpoints.
"""

import pytest
from httpx import AsyncClient


# =============================================================================
# Create Collection Tests
# =============================================================================


class TestCreateCollection:
    """Tests for POST /api/v1/collections/create endpoint."""

    @pytest.mark.asyncio
    async def test_create_collection_success(self, client: AsyncClient, mock_qdrant_service):
        """Test successful collection creation."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "test_collection",
                "vector_size": 384,
                "distance": "Cosine"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["collection_name"] == "test_collection"
        mock_qdrant_service.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_collection_with_custom_config(self, client: AsyncClient, mock_qdrant_service):
        """Test collection creation with custom HNSW config."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "custom_collection",
                "vector_size": 768,
                "distance": "Euclidean",
                "on_disk": True,
                "hnsw_config": {
                    "m": 32,
                    "ef_construct": 200
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_create_collection_default_values(self, client: AsyncClient, mock_qdrant_service):
        """Test collection creation with default values."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "minimal_collection"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_create_collection_invalid_distance(self, client: AsyncClient):
        """Test collection creation with invalid distance metric."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "test_collection",
                "distance": "InvalidMetric"
            }
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_collection_missing_name(self, client: AsyncClient):
        """Test collection creation without name."""
        response = await client.post(
            "/api/v1/collections/create",
            json={}
        )
        
        assert response.status_code == 422


# =============================================================================
# List Collections Tests
# =============================================================================


class TestListCollections:
    """Tests for GET /api/v1/collections/list endpoint."""

    @pytest.mark.asyncio
    async def test_list_collections_success(self, client: AsyncClient, mock_qdrant_service):
        """Test successful collection listing."""
        response = await client.get("/api/v1/collections/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert isinstance(data["collections"], list)
        mock_qdrant_service.list_collections.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_collections_empty(self, client: AsyncClient, mock_qdrant_service):
        """Test listing when no collections exist."""
        mock_qdrant_service.list_collections.return_value = []
        
        response = await client.get("/api/v1/collections/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == []


# =============================================================================
# Get Collection Info Tests
# =============================================================================


class TestGetCollectionInfo:
    """Tests for GET /api/v1/collections/{name} endpoint."""

    @pytest.mark.asyncio
    async def test_get_collection_info_success(self, client: AsyncClient, mock_qdrant_service):
        """Test successful collection info retrieval."""
        response = await client.get("/api/v1/collections/test_collection")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_collection"
        assert "vectors_count" in data
        mock_qdrant_service.get_collection_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_info_not_found(self, client: AsyncClient, mock_qdrant_service):
        """Test getting info for non-existent collection."""
        mock_qdrant_service.collection_exists.return_value = False
        mock_qdrant_service.get_collection_info.side_effect = Exception("Collection not found")
        
        response = await client.get("/api/v1/collections/nonexistent")
        
        assert response.status_code in [404, 500]


# =============================================================================
# Delete Collection Tests
# =============================================================================


class TestDeleteCollection:
    """Tests for DELETE /api/v1/collections/{name} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(self, client: AsyncClient, mock_qdrant_service):
        """Test successful collection deletion."""
        response = await client.delete("/api/v1/collections/test_collection")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_qdrant_service.delete_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_collection_not_found(self, client: AsyncClient, mock_qdrant_service):
        """Test deleting non-existent collection."""
        mock_qdrant_service.delete_collection.return_value = False
        
        response = await client.delete("/api/v1/collections/nonexistent")
        
        # Should still return success (idempotent)
        assert response.status_code == 200


# =============================================================================
# Collection Name Validation Tests
# =============================================================================


class TestCollectionNameValidation:
    """Tests for collection name validation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", [
        "valid_collection",
        "collection123",
        "my-collection",
        "UPPERCASE",
        "mixed_Case-123"
    ])
    async def test_valid_collection_names(self, client: AsyncClient, mock_qdrant_service, name: str):
        """Test valid collection names are accepted."""
        response = await client.post(
            "/api/v1/collections/create",
            json={"name": name}
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", [
        "",
        " ",
        "a" * 256,  # Too long
    ])
    async def test_invalid_collection_names(self, client: AsyncClient, name: str):
        """Test invalid collection names are rejected."""
        response = await client.post(
            "/api/v1/collections/create",
            json={"name": name}
        )
        
        assert response.status_code == 422


# =============================================================================
# Distance Metric Tests
# =============================================================================


class TestDistanceMetrics:
    """Tests for distance metric options."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("distance", ["Cosine", "Euclidean", "Dot"])
    async def test_supported_distance_metrics(
        self, client: AsyncClient, mock_qdrant_service, distance: str
    ):
        """Test all supported distance metrics."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": f"collection_{distance.lower()}",
                "distance": distance
            }
        )
        
        assert response.status_code == 200


# =============================================================================
# HNSW Config Tests
# =============================================================================


class TestHNSWConfig:
    """Tests for HNSW configuration options."""

    @pytest.mark.asyncio
    async def test_custom_hnsw_m(self, client: AsyncClient, mock_qdrant_service):
        """Test custom HNSW M parameter."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "hnsw_test",
                "hnsw_config": {"m": 48}
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_custom_hnsw_ef_construct(self, client: AsyncClient, mock_qdrant_service):
        """Test custom HNSW ef_construct parameter."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "hnsw_test",
                "hnsw_config": {"ef_construct": 256}
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_full_hnsw_config(self, client: AsyncClient, mock_qdrant_service):
        """Test full HNSW configuration."""
        response = await client.post(
            "/api/v1/collections/create",
            json={
                "name": "full_hnsw_test",
                "hnsw_config": {
                    "m": 32,
                    "ef_construct": 200,
                    "full_scan_threshold": 10000,
                    "max_indexing_threads": 4,
                    "on_disk": True
                }
            }
        )
        
        assert response.status_code == 200
