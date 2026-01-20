"""
Tests for Information Functions routes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_isblank_true(client):
    """Test ISBLANK with blank value."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isblank",
            json={"value": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_isblank_false(client):
    """Test ISBLANK with non-blank value."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isblank",
            json={"value": "hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_isnumber_true(client):
    """Test ISNUMBER with number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isnumber",
            json={"value": 42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_isnumber_false(client):
    """Test ISNUMBER with non-number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isnumber",
            json={"value": "text"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_istext_true(client):
    """Test ISTEXT with text."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/istext",
            json={"value": "hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_islogical_true(client):
    """Test ISLOGICAL with boolean."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/islogical",
            json={"value": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_iseven_true(client):
    """Test ISEVEN with even number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/iseven",
            json={"value": 4}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_iseven_false(client):
    """Test ISEVEN with odd number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/iseven",
            json={"value": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_isodd_true(client):
    """Test ISODD with odd number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isodd",
            json={"value": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_type_number(client):
    """Test TYPE with number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/type",
            json={"value": 42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type_code"] == 1
        assert data["type_name"] == "number"


@pytest.mark.asyncio
async def test_type_text(client):
    """Test TYPE with text."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/type",
            json={"value": "hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type_code"] == 2
        assert data["type_name"] == "text"


@pytest.mark.asyncio
async def test_type_logical(client):
    """Test TYPE with boolean."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/type",
            json={"value": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type_code"] == 4
        assert data["type_name"] == "logical"


@pytest.mark.asyncio
async def test_n_number(client):
    """Test N with number."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/n",
            json={"value": 42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 42


@pytest.mark.asyncio
async def test_n_true(client):
    """Test N with TRUE."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/n",
            json={"value": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 1


@pytest.mark.asyncio
async def test_n_text(client):
    """Test N with text returns 0."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/n",
            json={"value": "text"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 0


@pytest.mark.asyncio
async def test_na(client):
    """Test NA function."""
    async with client:
        response = await client.get("/api/v1/math/info/na")
        assert response.status_code == 200
        data = response.json()
        assert data["is_na"] is True


@pytest.mark.asyncio
async def test_check_numbers(client):
    """Test check_numbers batch function."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/check-numbers",
            json={"values": [1, "text", 3.14, True, None]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == [True, False, True, False, False]
        assert data["count_true"] == 2


@pytest.mark.asyncio
async def test_ispositive(client):
    """Test ISPOSITIVE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/ispositive",
            json={"value": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_isnegative(client):
    """Test ISNEGATIVE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isnegative",
            json={"value": -5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_isdigit(client):
    """Test ISDIGIT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/info/isdigit",
            json={"value": "12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_version(client):
    """Test version endpoint."""
    async with client:
        response = await client.get("/api/v1/math/info/version")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "math-service"
        assert "categories" in data
