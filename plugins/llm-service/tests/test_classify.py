"""
Classification Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestClassifyEndpoint:
    """Tests for /api/v1/classify endpoint."""

    @pytest.mark.asyncio
    async def test_classify_basic(
        self, client: AsyncClient, sample_text, classification_labels
    ):
        """Test basic classification."""
        response = await client.post(
            "/api/v1/classify",
            json={
                "text": sample_text,
                "categories": classification_labels,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert "confidence" in data
        assert data["category"] in classification_labels

    @pytest.mark.asyncio
    async def test_classify_sentiment(self, client: AsyncClient):
        """Test sentiment classification."""
        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "I absolutely love this product! It's amazing!",
                "categories": ["positive", "negative", "neutral"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert data["confidence"] >= 0.0
        assert data["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_classify_multiple_categories(self, client: AsyncClient):
        """Test classification with multiple categories."""
        categories = ["technology", "sports", "politics", "entertainment", "science"]

        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "The new smartphone features an advanced AI processor.",
                "categories": categories,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] in categories

    @pytest.mark.asyncio
    async def test_classify_with_all_scores(self, client: AsyncClient):
        """Test classification returning all category scores."""
        categories = ["positive", "negative", "neutral"]

        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "This is an okay product.",
                "categories": categories,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "category" in data

        if data.get("scores"):
            assert len(data["scores"]) == len(categories)

    @pytest.mark.asyncio
    async def test_classify_empty_text(self, client: AsyncClient):
        """Test classification with empty text."""
        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "",
                "categories": ["positive", "negative"],
            },
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_classify_no_categories(self, client: AsyncClient):
        """Test classification without categories."""
        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "Some text to classify",
                "categories": [],
            },
        )

        # Should fail - need at least 2 categories
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_classify_single_category(self, client: AsyncClient):
        """Test classification with single category."""
        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "Some text",
                "categories": ["only_one"],
            },
        )

        # Should fail - need at least 2 categories
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_classify_response_structure(
        self, client: AsyncClient, classification_labels
    ):
        """Test classification response structure."""
        response = await client.post(
            "/api/v1/classify",
            json={
                "text": "Test text for classification",
                "categories": classification_labels,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "category" in data
        assert "confidence" in data
        assert "model" in data

        # Validate confidence range
        assert 0.0 <= data["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_classify_long_text(self, client: AsyncClient):
        """Test classification with long text."""
        long_text = "This is a test sentence. " * 500  # ~3000 words

        response = await client.post(
            "/api/v1/classify",
            json={
                "text": long_text,
                "categories": ["positive", "negative"],
            },
        )

        # Should handle or truncate long text
        assert response.status_code in [200, 422]
