"""
Tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient


# =============================================================================
# Basic Health Tests
# =============================================================================


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test main health endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "service" in data
        assert data["service"] == "vector-service"

    @pytest.mark.asyncio
    async def test_health_ready_endpoint(self, client: AsyncClient, mock_qdrant_service):
        """Test readiness probe endpoint."""
        response = await client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True

    @pytest.mark.asyncio
    async def test_health_live_endpoint(self, client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    @pytest.mark.asyncio
    async def test_health_qdrant_endpoint(self, client: AsyncClient, mock_qdrant_service):
        """Test Qdrant health check endpoint."""
        response = await client.get("/health/qdrant")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        mock_qdrant_service.check_health.assert_called_once()


# =============================================================================
# Health Response Structure Tests
# =============================================================================


class TestHealthResponseStructure:
    """Tests for health response structure."""

    @pytest.mark.asyncio
    async def test_health_response_has_timestamp(self, client: AsyncClient):
        """Test health response includes timestamp."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_response_has_version(self, client: AsyncClient):
        """Test health response includes version."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_response_has_environment(self, client: AsyncClient):
        """Test health response includes environment."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data


# =============================================================================
# Dependency Health Tests
# =============================================================================


class TestDependencyHealth:
    """Tests for dependency health checks."""

    @pytest.mark.asyncio
    async def test_health_with_qdrant_healthy(self, client: AsyncClient, mock_qdrant_service):
        """Test health when Qdrant is healthy."""
        mock_qdrant_service.check_health.return_value = {"status": "healthy"}
        
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_with_qdrant_unhealthy(self, client: AsyncClient, mock_qdrant_service):
        """Test health when Qdrant is unhealthy."""
        mock_qdrant_service.check_health.side_effect = Exception("Connection failed")
        
        response = await client.get("/health")
        
        # Should still return 200 but with degraded status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["degraded", "unhealthy"]


# =============================================================================
# Root Endpoint Tests
# =============================================================================


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns service info."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "docs" in data or "documentation" in data


# =============================================================================
# OpenAPI Endpoints Tests
# =============================================================================


class TestOpenAPIEndpoints:
    """Tests for OpenAPI documentation endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_json_endpoint(self, client: AsyncClient):
        """Test OpenAPI JSON endpoint."""
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_docs_endpoint(self, client: AsyncClient):
        """Test Swagger UI docs endpoint."""
        response = await client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_redoc_endpoint(self, client: AsyncClient):
        """Test ReDoc docs endpoint."""
        response = await client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
