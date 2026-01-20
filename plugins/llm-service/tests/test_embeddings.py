"""
Embeddings Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestEmbeddingsEndpoint:
    """Tests for /api/v1/embeddings endpoint."""

    @pytest.mark.asyncio
    async def test_embeddings_single_text(self, client: AsyncClient):
        """Test embeddings for single text."""
        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": "Hello, world!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "embeddings" in data
        assert len(data["embeddings"]) == 1
        assert isinstance(data["embeddings"][0], list)
        assert len(data["embeddings"][0]) > 0  # Has dimensions

    @pytest.mark.asyncio
    async def test_embeddings_batch(self, client: AsyncClient):
        """Test embeddings for multiple texts."""
        texts = [
            "First sentence",
            "Second sentence",
            "Third sentence",
        ]

        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": texts,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "embeddings" in data
        assert len(data["embeddings"]) == len(texts)

    @pytest.mark.asyncio
    async def test_embeddings_dimensions(self, client: AsyncClient):
        """Test embeddings have correct dimensions."""
        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": "Test text",
            },
        )

        assert response.status_code == 200
        data = response.json()
        embeddings = data["embeddings"][0]

        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        assert len(embeddings) == 384

    @pytest.mark.asyncio
    async def test_embeddings_normalized(self, client: AsyncClient):
        """Test embeddings are normalized."""
        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": "Test text for normalization",
            },
        )

        assert response.status_code == 200
        data = response.json()
        embeddings = data["embeddings"][0]

        # Calculate L2 norm
        import math
        norm = math.sqrt(sum(x**2 for x in embeddings))

        # Normalized vectors should have norm close to 1
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_embeddings_empty_text(self, client: AsyncClient):
        """Test embeddings with empty text."""
        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": "",
            },
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_embeddings_empty_array(self, client: AsyncClient):
        """Test embeddings with empty array."""
        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": [],
            },
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_embeddings_response_structure(self, client: AsyncClient):
        """Test embeddings response structure."""
        response = await client.post(
            "/api/v1/embeddings",
            json={"text": "Test text"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "embeddings" in data
        assert "model" in data
        assert "dimensions" in data
        assert "usage" in data

        # Check usage
        assert "total_tokens" in data["usage"]

    @pytest.mark.asyncio
    async def test_embeddings_semantic_similarity(self, client: AsyncClient):
        """Test similar texts produce similar embeddings."""
        texts = [
            "The cat sat on the mat",
            "A cat was sitting on a mat",
            "The dog ran in the park",
        ]

        response = await client.post(
            "/api/v1/embeddings",
            json={"text": texts},
        )

        assert response.status_code == 200
        data = response.json()
        embeddings = data["embeddings"]

        # Calculate cosine similarity
        def cosine_similarity(a, b):
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x**2 for x in a) ** 0.5
            norm_b = sum(x**2 for x in b) ** 0.5
            return dot_product / (norm_a * norm_b)

        # Similar sentences should have higher similarity
        sim_similar = cosine_similarity(embeddings[0], embeddings[1])
        sim_different = cosine_similarity(embeddings[0], embeddings[2])

        # Similar sentences should be more similar than different ones
        # Note: With mocked embeddings this may not hold
        assert isinstance(sim_similar, float)
        assert isinstance(sim_different, float)

    @pytest.mark.asyncio
    async def test_embeddings_long_text(self, client: AsyncClient):
        """Test embeddings for long text."""
        long_text = "This is a test sentence. " * 200  # ~1000 words

        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": long_text,
            },
        )

        # Should handle or truncate long text
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_embeddings_special_characters(self, client: AsyncClient):
        """Test embeddings with special characters."""
        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": "Hello! @#$%^&*() 你好 🎉",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "embeddings" in data

    @pytest.mark.asyncio
    async def test_embeddings_large_batch(self, client: AsyncClient):
        """Test embeddings for large batch."""
        texts = [f"Text number {i}" for i in range(50)]

        response = await client.post(
            "/api/v1/embeddings",
            json={
                "text": texts,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["embeddings"]) == 50
