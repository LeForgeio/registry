"""
Health Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test main health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_response_structure(self, client: AsyncClient):
        """Test health response has correct structure."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "checks" in data

        # Uptime should be a number
        assert isinstance(data["uptime"], (int, float))
        assert data["uptime"] >= 0

    @pytest.mark.asyncio
    async def test_liveness_probe(self, client: AsyncClient):
        """Test Kubernetes liveness probe."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readiness_probe(self, client: AsyncClient):
        """Test Kubernetes readiness probe."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


class TestModelsEndpoint:
    """Tests for /models endpoint."""

    @pytest.mark.asyncio
    async def test_list_models(self, client: AsyncClient):
        """Test listing available models."""
        response = await client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)

    @pytest.mark.asyncio
    async def test_models_response_structure(self, client: AsyncClient):
        """Test models response structure."""
        response = await client.get("/models")

        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert "default_model" in data
        assert "default_embedding_model" in data

        # Check model info structure
        for model in data["models"]:
            assert "name" in model
            assert "capabilities" in model


class TestQueueStatusEndpoint:
    """Tests for /queue/status endpoint."""

    @pytest.mark.asyncio
    async def test_queue_status(self, client: AsyncClient):
        """Test queue status endpoint."""
        response = await client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "pending_requests" in data
        assert "processing_requests" in data


class TestConfigEndpoint:
    """Tests for /config endpoint."""

    @pytest.mark.asyncio
    async def test_get_config(self, client: AsyncClient):
        """Test getting service configuration."""
        response = await client.get("/config")

        assert response.status_code == 200
        data = response.json()

        # Should include non-sensitive config
        assert "service_name" in data
        assert "service_version" in data
        assert "default_model" in data
        assert "default_embedding_model" in data

    @pytest.mark.asyncio
    async def test_config_no_secrets(self, client: AsyncClient):
        """Test config doesn't expose secrets."""
        response = await client.get("/config")

        assert response.status_code == 200
        data = response.json()

        # Should not contain sensitive information
        config_str = str(data).lower()
        assert "password" not in config_str
        assert "secret" not in config_str
        assert "token" not in config_str
        assert "key" not in config_str or "api_key" not in config_str


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
