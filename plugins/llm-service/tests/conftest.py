"""
Test Configuration and Fixtures

Pytest fixtures for testing LLM service with mocked vLLM responses.
"""
import asyncio
import json
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["VLLM_BASE_URL"] = "http://mock-vllm:8001/v1"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ENABLE_QUEUE"] = "false"
os.environ["ENABLE_EMBEDDINGS"] = "true"
os.environ["DEFAULT_MODEL"] = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Mock vLLM Client
# =============================================================================

@pytest.fixture
def mock_vllm_response():
    """Standard mock vLLM completion response."""
    return {
        "id": "cmpl-test123",
        "object": "text_completion",
        "created": 1700000000,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "choices": [
            {
                "index": 0,
                "text": "This is a mock response from the LLM.",
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18,
        },
    }


@pytest.fixture
def mock_chat_response():
    """Standard mock vLLM chat completion response."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a mock chat response from the LLM.",
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 9,
            "total_tokens": 24,
        },
    }


@pytest.fixture
def mock_classification_response():
    """Mock response for classification."""
    return {
        "id": "chatcmpl-classify",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"label": "positive", "confidence": 0.92}',
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 15,
            "total_tokens": 65,
        },
    }


@pytest.fixture
def mock_extraction_response():
    """Mock response for entity extraction."""
    return {
        "id": "chatcmpl-extract",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "entities": [
                            {"text": "John Smith", "type": "PERSON", "confidence": 0.95},
                            {"text": "Acme Inc", "type": "ORGANIZATION", "confidence": 0.88},
                            {"text": "New York", "type": "LOCATION", "confidence": 0.91},
                        ]
                    }),
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 80,
            "completion_tokens": 45,
            "total_tokens": 125,
        },
    }


@pytest.fixture
def mock_summarization_response():
    """Mock response for summarization."""
    return {
        "id": "chatcmpl-summarize",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a concise summary capturing the main points of the original text.",
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 200,
            "completion_tokens": 15,
            "total_tokens": 215,
        },
    }


@pytest.fixture
def mock_models_response():
    """Mock response for list models."""
    return {
        "object": "list",
        "data": [
            {
                "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "object": "model",
                "created": 1700000000,
                "owned_by": "vllm",
            }
        ],
    }


# =============================================================================
# Mocked Services
# =============================================================================

@pytest.fixture
def mock_openai_client(
    mock_vllm_response,
    mock_chat_response,
    mock_models_response,
):
    """Create mocked OpenAI client."""
    client = MagicMock()

    # Mock completions
    client.completions = MagicMock()
    client.completions.create = AsyncMock(
        return_value=MagicMock(**mock_vllm_response)
    )

    # Mock chat completions
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(**mock_chat_response)
    )

    # Mock models
    client.models = MagicMock()
    client.models.list = AsyncMock(
        return_value=MagicMock(data=[
            MagicMock(id="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        ])
    )

    return client


@pytest.fixture
def mock_embedding_service():
    """Create mocked embedding service."""
    service = MagicMock()
    service.is_loaded = MagicMock(return_value=True)
    service.model_name = "all-MiniLM-L6-v2"
    service.generate_embeddings = MagicMock(
        return_value=[[0.1] * 384]  # 384-dim embeddings
    )
    service.generate_embeddings_batch = MagicMock(
        return_value=[[0.1] * 384, [0.2] * 384]
    )
    service.get_info = MagicMock(return_value={
        "name": "all-MiniLM-L6-v2",
        "loaded": True,
        "dimensions": 384,
        "capabilities": ["embeddings"],
    })
    return service


@pytest.fixture
def mock_queue_service():
    """Create mocked queue service."""
    service = MagicMock()
    service.connect = AsyncMock()
    service.close = AsyncMock()
    service.enqueue = AsyncMock(return_value="job-123")
    service.get_job = AsyncMock(return_value={
        "id": "job-123",
        "status": "completed",
        "result": {"text": "Generated text"},
    })
    service.get_status = AsyncMock(return_value={
        "enabled": False,
        "connected": True,
        "pending_requests": 0,
        "processing_requests": 0,
        "queue_name": "llm_requests",
    })
    return service


# =============================================================================
# App Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def app_with_mocks(
    mock_openai_client,
    mock_embedding_service,
    mock_queue_service,
):
    """Create app with mocked services."""
    with patch("src.services.llm_client.AsyncOpenAI", return_value=mock_openai_client):
        with patch("src.services.embedding_service.SentenceTransformer"):
            with patch("src.services.queue_service.redis.asyncio.from_url"):
                # Reset singletons
                from src.services import llm_client, embedding_service, queue_service
                llm_client._vllm_client = None
                embedding_service._embedding_service = None
                queue_service._queue_service = None

                # Import app after patching
                from src.main import app

                yield app


@pytest_asyncio.fixture
async def client(app_with_mocks) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with mocked services."""
    # Create transport for ASGI app
    transport = ASGITransport(app=app_with_mocks)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as ac:
        yield ac


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return (
        "Artificial intelligence (AI) is transforming industries worldwide. "
        "Companies like Google, Microsoft, and OpenAI are leading the charge "
        "in developing advanced AI systems. John Smith, CEO of TechCorp, "
        "announced a new partnership with Acme Inc in New York yesterday."
    )


@pytest.fixture
def sample_messages():
    """Sample chat messages."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]


@pytest.fixture
def classification_labels():
    """Sample classification labels."""
    return ["positive", "negative", "neutral"]


@pytest.fixture
def entity_types():
    """Sample entity types."""
    return ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "MONEY"]
