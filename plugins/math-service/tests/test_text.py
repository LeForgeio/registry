"""
Tests for Text Functions routes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_text_left(client):
    """Test LEFT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/left",
            json={"text": "Hello World", "num_chars": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Hello"
        assert data["operation"] == "LEFT"


@pytest.mark.asyncio
async def test_text_right(client):
    """Test RIGHT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/right",
            json={"text": "Hello World", "num_chars": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "World"


@pytest.mark.asyncio
async def test_text_mid(client):
    """Test MID function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/mid",
            json={"text": "Hello World", "start_num": 7, "num_chars": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "World"


@pytest.mark.asyncio
async def test_text_len(client):
    """Test LEN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/len",
            json={"text": "Hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 5


@pytest.mark.asyncio
async def test_text_trim(client):
    """Test TRIM function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/trim",
            json={"text": "  Hello   World  "}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Hello World"


@pytest.mark.asyncio
async def test_text_upper(client):
    """Test UPPER function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/upper",
            json={"text": "hello world"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "HELLO WORLD"


@pytest.mark.asyncio
async def test_text_lower(client):
    """Test LOWER function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/lower",
            json={"text": "HELLO WORLD"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "hello world"


@pytest.mark.asyncio
async def test_text_proper(client):
    """Test PROPER function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/proper",
            json={"text": "hello world"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Hello World"


@pytest.mark.asyncio
async def test_text_find(client):
    """Test FIND function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/find",
            json={"find_text": "World", "within_text": "Hello World"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 7


@pytest.mark.asyncio
async def test_text_substitute(client):
    """Test SUBSTITUTE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/substitute",
            json={"text": "Hello World World", "old_text": "World", "new_text": "Earth"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Hello Earth Earth"


@pytest.mark.asyncio
async def test_text_concat(client):
    """Test CONCAT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/concat",
            json={"texts": ["Hello", "World"], "delimiter": " "}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Hello World"


@pytest.mark.asyncio
async def test_text_textjoin(client):
    """Test TEXTJOIN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/textjoin",
            json={"delimiter": ", ", "ignore_empty": True, "texts": ["A", "", "B", "C"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "A, B, C"


@pytest.mark.asyncio
async def test_text_rept(client):
    """Test REPT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/rept",
            json={"text": "Ha", "number_times": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "HaHaHa"


@pytest.mark.asyncio
async def test_text_value(client):
    """Test VALUE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/value",
            json={"text": "123.45"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 123.45


@pytest.mark.asyncio
async def test_text_split(client):
    """Test SPLIT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/split",
            json={"text": "A,B,C", "delimiter": ","}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == ["A", "B", "C"]
        assert data["count"] == 3


@pytest.mark.asyncio
async def test_text_clean(client):
    """Test CLEAN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/clean",
            json={"text": "Hello\x00World"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "HelloWorld"


@pytest.mark.asyncio
async def test_text_code(client):
    """Test CODE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/text/code",
            json={"text": "A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 65
