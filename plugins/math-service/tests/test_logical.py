"""
Tests for Logical Functions routes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_logical_if_true(client):
    """Test IF function with true condition."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/if",
            json={"condition": True, "value_if_true": "Yes", "value_if_false": "No"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Yes"


@pytest.mark.asyncio
async def test_logical_if_false(client):
    """Test IF function with false condition."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/if",
            json={"condition": False, "value_if_true": "Yes", "value_if_false": "No"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "No"


@pytest.mark.asyncio
async def test_logical_ifs(client):
    """Test IFS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/ifs",
            json={
                "conditions": [
                    {"condition": False, "value": "A"},
                    {"condition": True, "value": "B"},
                    {"condition": True, "value": "C"}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "B"


@pytest.mark.asyncio
async def test_logical_and_all_true(client):
    """Test AND function with all true values."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/and",
            json={"values": [True, True, True]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_logical_and_one_false(client):
    """Test AND function with one false value."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/and",
            json={"values": [True, False, True]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_logical_or(client):
    """Test OR function."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/or",
            json={"values": [False, True, False]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_logical_or_all_false(client):
    """Test OR function with all false."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/or",
            json={"values": [False, False, False]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_logical_not(client):
    """Test NOT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/not",
            json={"value": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_logical_xor_odd_true(client):
    """Test XOR function with odd number of true values."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/xor",
            json={"values": [True, False, True, True]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True  # 3 true values (odd)


@pytest.mark.asyncio
async def test_logical_xor_even_true(client):
    """Test XOR function with even number of true values."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/xor",
            json={"values": [True, True, False, False]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False  # 2 true values (even)


@pytest.mark.asyncio
async def test_logical_choose(client):
    """Test CHOOSE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/choose",
            json={"index_num": 2, "values": ["First", "Second", "Third"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Second"


@pytest.mark.asyncio
async def test_logical_compare_eq(client):
    """Test comparison equals."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/compare",
            json={"value1": 5, "value2": 5, "operator": "eq"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_logical_compare_gt(client):
    """Test comparison greater than."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/compare",
            json={"value1": 10, "value2": 5, "operator": "gt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_logical_true(client):
    """Test TRUE constant."""
    async with client:
        response = await client.get("/api/v1/math/logical/true")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_logical_false(client):
    """Test FALSE constant."""
    async with client:
        response = await client.get("/api/v1/math/logical/false")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is False


@pytest.mark.asyncio
async def test_logical_switch(client):
    """Test SWITCH function."""
    async with client:
        response = await client.post(
            "/api/v1/math/logical/switch",
            params={"expression": "B", "default": "Unknown"},
            json={"A": "Apple", "B": "Banana", "C": "Cherry"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Banana"
