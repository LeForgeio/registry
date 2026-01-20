"""
Generate Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestGenerateEndpoint:
    """Tests for /api/v1/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_basic(self, client: AsyncClient):
        """Test basic text generation."""
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Once upon a time",
                "max_tokens": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "usage" in data
        assert data["usage"]["prompt_tokens"] > 0

    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, client: AsyncClient):
        """Test generation with custom parameters."""
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Write a haiku about coding",
                "max_tokens": 100,
                "temperature": 0.8,
                "top_p": 0.9,
                "stop": ["\n\n"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["model"] is not None

    @pytest.mark.asyncio
    async def test_generate_empty_prompt(self, client: AsyncClient):
        """Test generation with empty prompt."""
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "",
            },
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_with_model(self, client: AsyncClient):
        """Test generation with specific model."""
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Hello, world!",
                "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    @pytest.mark.asyncio
    async def test_generate_response_structure(self, client: AsyncClient):
        """Test response has correct structure."""
        response = await client.post(
            "/api/v1/generate",
            json={"prompt": "Test prompt"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "text" in data
        assert "model" in data
        assert "usage" in data

        # Check usage structure
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage

    @pytest.mark.asyncio
    async def test_generate_max_tokens_limit(self, client: AsyncClient):
        """Test max_tokens validation."""
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Test",
                "max_tokens": 100000,  # Exceeds limit
            },
        )

        # Should either succeed with capped tokens or fail validation
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_generate_temperature_bounds(self, client: AsyncClient):
        """Test temperature parameter bounds."""
        # Valid temperature
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Test",
                "temperature": 0.5,
            },
        )
        assert response.status_code == 200

        # Temperature at bounds
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Test",
                "temperature": 0.0,
            },
        )
        assert response.status_code == 200

        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Test",
                "temperature": 2.0,
            },
        )
        assert response.status_code == 200


class TestGenerateStreaming:
    """Tests for streaming generation."""

    @pytest.mark.asyncio
    async def test_generate_stream_request(self, client: AsyncClient):
        """Test streaming generation request."""
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Tell me a story",
                "stream": True,
            },
        )

        # Streaming returns SSE
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
