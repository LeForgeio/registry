"""
Summarization Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestSummarizeEndpoint:
    """Tests for /api/v1/summarize endpoint."""

    @pytest.mark.asyncio
    async def test_summarize_basic(self, client: AsyncClient, sample_text):
        """Test basic summarization."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert len(data["summary"]) > 0

    @pytest.mark.asyncio
    async def test_summarize_short_length(self, client: AsyncClient, sample_text):
        """Test short summary."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "length": "short",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_medium_length(self, client: AsyncClient, sample_text):
        """Test medium-length summary."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "length": "medium",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_long_length(self, client: AsyncClient, sample_text):
        """Test detailed summary."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "length": "long",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_with_max_length(self, client: AsyncClient, sample_text):
        """Test summarization with max_length."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "max_length": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_with_focus(self, client: AsyncClient, sample_text):
        """Test summarization with focus topic."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "focus": "technology companies",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_bullet_points(self, client: AsyncClient, sample_text):
        """Test summarization as bullet points."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "format": "bullets",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_empty_text(self, client: AsyncClient):
        """Test summarization with empty text."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": "",
            },
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_summarize_short_text(self, client: AsyncClient):
        """Test summarization of very short text."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": "Hello world.",
            },
        )

        # Should handle short text gracefully
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_summarize_response_structure(self, client: AsyncClient, sample_text):
        """Test summarization response structure."""
        response = await client.post(
            "/api/v1/summarize",
            json={"text": sample_text},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "summary" in data
        assert "model" in data
        assert "usage" in data

        # Summary should be non-empty string
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0

    @pytest.mark.asyncio
    async def test_summarize_long_document(self, client: AsyncClient):
        """Test summarization of long document."""
        long_text = """
        Artificial intelligence (AI) has emerged as one of the most transformative 
        technologies of the 21st century. From healthcare to finance, transportation 
        to entertainment, AI systems are reshaping how we live and work.
        
        In healthcare, AI-powered diagnostic tools can analyze medical images with 
        accuracy rivaling that of experienced physicians. Machine learning algorithms 
        can predict patient outcomes and recommend personalized treatment plans.
        
        The financial sector has embraced AI for fraud detection, algorithmic trading, 
        and customer service automation. Banks use AI chatbots to handle routine 
        inquiries, freeing human agents for complex issues.
        
        Transportation is being revolutionized by autonomous vehicles, which use 
        AI to navigate roads safely. Companies like Tesla, Waymo, and traditional 
        automakers are racing to bring self-driving cars to market.
        
        Despite its benefits, AI raises important ethical concerns. Issues of bias, 
        privacy, and job displacement require careful consideration and regulation.
        """ * 5  # Repeat to make longer

        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": long_text,
                "length": "short",
            },
        )

        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_summarize_invalid_length(self, client: AsyncClient, sample_text):
        """Test summarization with invalid length parameter."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": sample_text,
                "length": "invalid_length",
            },
        )

        # Should fail validation
        assert response.status_code == 422
