"""
Chat Endpoint Tests
"""
import pytest
from httpx import AsyncClient


class TestChatEndpoint:
    """Tests for /api/v1/chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_basic(self, client: AsyncClient, sample_messages):
        """Test basic chat completion."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": sample_messages,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert "content" in data["message"]

    @pytest.mark.asyncio
    async def test_chat_single_message(self, client: AsyncClient):
        """Test chat with single user message."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, client: AsyncClient):
        """Test chat with system prompt."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a pirate. Respond in pirate speak."},
                    {"role": "user", "content": "Hello, how are you?"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_chat_multi_turn(self, client: AsyncClient):
        """Test multi-turn conversation."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [
                    {"role": "user", "content": "My name is Alice."},
                    {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                    {"role": "user", "content": "What's my name?"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_chat_empty_messages(self, client: AsyncClient):
        """Test chat with empty messages array."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [],
            },
        )

        # Should fail validation - need at least one message
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_with_parameters(self, client: AsyncClient, sample_messages):
        """Test chat with custom parameters."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": sample_messages,
                "max_tokens": 100,
                "temperature": 0.5,
                "top_p": 0.9,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "usage" in data

    @pytest.mark.asyncio
    async def test_chat_response_structure(self, client: AsyncClient, sample_messages):
        """Test chat response has correct structure."""
        response = await client.post(
            "/api/v1/chat",
            json={"messages": sample_messages},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "message" in data
        assert "model" in data
        assert "usage" in data

        # Check message structure
        message = data["message"]
        assert "role" in message
        assert "content" in message
        assert message["role"] == "assistant"

        # Check usage structure
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage

    @pytest.mark.asyncio
    async def test_chat_invalid_role(self, client: AsyncClient):
        """Test chat with invalid message role."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [
                    {"role": "invalid_role", "content": "Hello"}
                ],
            },
        )

        # Should fail validation
        assert response.status_code == 422


class TestChatStreaming:
    """Tests for streaming chat."""

    @pytest.mark.asyncio
    async def test_chat_stream_request(self, client: AsyncClient, sample_messages):
        """Test streaming chat request."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": sample_messages,
                "stream": True,
            },
        )

        # Streaming returns SSE
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
