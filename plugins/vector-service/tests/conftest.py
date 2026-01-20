"""
Pytest configuration and fixtures for Vector Service tests.
"""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import numpy as np
from httpx import AsyncClient, ASGITransport

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["USE_LOCAL_EMBEDDINGS"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"


# =============================================================================
# Event Loop Fixture
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Test Collection Name
# =============================================================================


@pytest.fixture
def test_collection_name() -> str:
    """Generate unique test collection name."""
    return f"test_collection_{uuid.uuid4().hex[:8]}"


# =============================================================================
# Mock Embedding Service
# =============================================================================


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service."""
    mock = AsyncMock()
    
    def generate_embedding(dim: int = 384) -> list[float]:
        """Generate random embedding vector."""
        return np.random.randn(dim).tolist()
    
    mock.embed_text = AsyncMock(side_effect=lambda text, **kwargs: generate_embedding())
    mock.embed_texts = AsyncMock(
        side_effect=lambda texts, **kwargs: [generate_embedding() for _ in texts]
    )
    mock.get_model_info = MagicMock(return_value={
        "model_name": "all-MiniLM-L6-v2",
        "embedding_dim": 384,
        "max_sequence_length": 256,
        "source": "mock"
    })
    
    return mock


# =============================================================================
# Mock Qdrant Service
# =============================================================================


@pytest.fixture
def mock_qdrant_service():
    """Create mock Qdrant service."""
    mock = AsyncMock()
    
    # Collection operations
    mock.create_collection = AsyncMock(return_value=True)
    mock.list_collections = AsyncMock(return_value=["collection1", "collection2"])
    mock.get_collection_info = AsyncMock(return_value={
        "name": "test_collection",
        "vectors_count": 100,
        "points_count": 100,
        "status": "green",
        "config": {
            "params": {
                "vectors": {
                    "size": 384,
                    "distance": "Cosine"
                }
            }
        }
    })
    mock.delete_collection = AsyncMock(return_value=True)
    mock.collection_exists = AsyncMock(return_value=True)
    
    # Vector operations
    mock.upsert_points = AsyncMock(return_value={"status": "completed", "upserted_count": 10})
    mock.search = AsyncMock(return_value=[
        {"id": "1", "score": 0.95, "payload": {"text": "result 1"}},
        {"id": "2", "score": 0.90, "payload": {"text": "result 2"}},
    ])
    mock.hybrid_search = AsyncMock(return_value=[
        {"id": "1", "score": 0.95, "payload": {"text": "result 1"}},
        {"id": "2", "score": 0.88, "payload": {"text": "result 2"}},
    ])
    mock.recommend = AsyncMock(return_value=[
        {"id": "3", "score": 0.92, "payload": {"text": "recommended 1"}},
        {"id": "4", "score": 0.87, "payload": {"text": "recommended 2"}},
    ])
    mock.delete_points = AsyncMock(return_value=True)
    
    # Health check
    mock.check_health = AsyncMock(return_value={"status": "healthy", "version": "1.7.4"})
    
    return mock


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_vectors() -> list[dict]:
    """Generate sample vector points."""
    return [
        {
            "id": f"point_{i}",
            "vector": np.random.randn(384).tolist(),
            "payload": {
                "text": f"Sample text {i}",
                "category": "test",
                "index": i
            }
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_texts() -> list[str]:
    """Sample texts for embedding tests."""
    return [
        "Machine learning is a subset of artificial intelligence.",
        "Natural language processing enables computers to understand text.",
        "Vector databases store high-dimensional embeddings for similarity search.",
        "Semantic search finds results based on meaning, not just keywords.",
        "RAG combines retrieval with generation for better AI responses."
    ]


@pytest.fixture
def sample_search_request() -> dict:
    """Sample search request."""
    return {
        "vector": np.random.randn(384).tolist(),
        "limit": 10,
        "score_threshold": 0.5,
        "with_payload": True,
        "with_vectors": False
    }


@pytest.fixture
def sample_text_search_request() -> dict:
    """Sample text search request."""
    return {
        "text": "semantic search with vectors",
        "limit": 10,
        "score_threshold": 0.5,
        "with_payload": True
    }


@pytest.fixture
def sample_hybrid_search_request() -> dict:
    """Sample hybrid search request."""
    return {
        "text": "machine learning",
        "sparse_field": "text",
        "limit": 10,
        "alpha": 0.7,
        "score_threshold": 0.5
    }


@pytest.fixture
def sample_recommend_request() -> dict:
    """Sample recommend request."""
    return {
        "positive": ["point_1", "point_2"],
        "negative": ["point_5"],
        "limit": 5,
        "score_threshold": 0.5
    }


@pytest.fixture
def sample_collection_config() -> dict:
    """Sample collection configuration."""
    return {
        "name": "test_collection",
        "vector_size": 384,
        "distance": "Cosine",
        "on_disk": False,
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100
        }
    }


# =============================================================================
# Application Client Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def app_with_mocks(mock_qdrant_service, mock_embedding_service):
    """Create app with mocked services."""
    # Import after setting environment
    from src.main import app
    from src.services import qdrant_service, embedding_service
    
    # Patch services
    with patch.object(qdrant_service, 'get_qdrant_service', return_value=mock_qdrant_service):
        with patch.object(embedding_service, 'get_embedding_service', return_value=mock_embedding_service):
            yield app


@pytest_asyncio.fixture
async def client(app_with_mocks) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with mocked services."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def client_no_mocks() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client without mocks (for integration tests)."""
    from src.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# Integration Test Fixtures
# =============================================================================


@pytest.fixture
def qdrant_available() -> bool:
    """Check if Qdrant is available for integration tests."""
    import httpx
    try:
        response = httpx.get("http://localhost:6333/healthz", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def skip_if_no_qdrant(qdrant_available):
    """Skip test if Qdrant is not available."""
    if not qdrant_available:
        pytest.skip("Qdrant is not available")


# =============================================================================
# Utility Functions
# =============================================================================


def generate_random_vector(dim: int = 384) -> list[float]:
    """Generate random normalized vector."""
    vec = np.random.randn(dim)
    return (vec / np.linalg.norm(vec)).tolist()


def generate_random_points(count: int, dim: int = 384) -> list[dict]:
    """Generate random vector points."""
    return [
        {
            "id": f"point_{i}",
            "vector": generate_random_vector(dim),
            "payload": {"text": f"Text content {i}", "index": i}
        }
        for i in range(count)
    ]
