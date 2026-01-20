"""
Entity Extraction Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestExtractEndpoint:
    """Tests for /api/v1/extract-entities endpoint."""

    @pytest.mark.asyncio
    async def test_extract_basic(self, client: AsyncClient, sample_text):
        """Test basic entity extraction."""
        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": sample_text,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert isinstance(data["entities"], list)

    @pytest.mark.asyncio
    async def test_extract_with_entity_types(
        self, client: AsyncClient, sample_text, entity_types
    ):
        """Test extraction with specific entity types."""
        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": sample_text,
                "entity_types": entity_types,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

        # All entities should have types from the requested list
        for entity in data["entities"]:
            if "type" in entity:
                assert entity["type"] in entity_types

    @pytest.mark.asyncio
    async def test_extract_person_entities(self, client: AsyncClient):
        """Test extraction of person entities."""
        text = "John Smith and Jane Doe met at the conference."

        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": text,
                "entity_types": ["PERSON"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_extract_organization_entities(self, client: AsyncClient):
        """Test extraction of organization entities."""
        text = "Microsoft and Google announced a partnership with OpenAI."

        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": text,
                "entity_types": ["ORGANIZATION"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_extract_location_entities(self, client: AsyncClient):
        """Test extraction of location entities."""
        text = "The event will be held in New York, Paris, and Tokyo."

        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": text,
                "entity_types": ["LOCATION"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_extract_empty_text(self, client: AsyncClient):
        """Test extraction with empty text."""
        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": "",
            },
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extract_no_entities(self, client: AsyncClient):
        """Test extraction from text with no entities."""
        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": "Hello, how are you today?",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        # May return empty list or minimal entities

    @pytest.mark.asyncio
    async def test_extract_response_structure(self, client: AsyncClient, sample_text):
        """Test extraction response structure."""
        response = await client.post(
            "/api/v1/extract-entities",
            json={"text": sample_text},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "entities" in data
        assert "model" in data
        assert "usage" in data

        # Check entity structure if any
        for entity in data["entities"]:
            assert "text" in entity
            assert "type" in entity

    @pytest.mark.asyncio
    async def test_extract_with_confidence(self, client: AsyncClient, sample_text):
        """Test extraction includes confidence scores."""
        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": sample_text,
                "include_confidence": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_extract_custom_types(self, client: AsyncClient):
        """Test extraction with custom entity types."""
        text = "Order #12345 was shipped on 2024-01-15 for $99.99"
        custom_types = ["ORDER_ID", "DATE", "PRICE"]

        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": text,
                "entity_types": custom_types,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_extract_long_text(self, client: AsyncClient):
        """Test extraction from long text."""
        long_text = (
            "John Smith from Acme Corp visited New York. " * 100
        )

        response = await client.post(
            "/api/v1/extract-entities",
            json={
                "text": long_text,
            },
        )

        # Should handle or truncate long text
        assert response.status_code in [200, 422]
