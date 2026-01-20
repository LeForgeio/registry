"""
Tests for Array Functions routes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_array_unique(client):
    """Test UNIQUE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/unique",
            json={"values": [1, 2, 2, 3, 3, 3, 4]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [1, 2, 3, 4]
        assert data["count"] == 4


@pytest.mark.asyncio
async def test_array_sort_ascending(client):
    """Test SORT function ascending."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/sort",
            json={"values": [3, 1, 4, 1, 5], "descending": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [1, 1, 3, 4, 5]


@pytest.mark.asyncio
async def test_array_sort_descending(client):
    """Test SORT function descending."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/sort",
            json={"values": [3, 1, 4, 1, 5], "descending": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [5, 4, 3, 1, 1]


@pytest.mark.asyncio
async def test_array_sortby(client):
    """Test SORTBY function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/sortby",
            json={
                "values": ["Alice", "Bob", "Charlie"],
                "sort_by": [30, 20, 25],
                "descending": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == ["Bob", "Charlie", "Alice"]


@pytest.mark.asyncio
async def test_array_filter(client):
    """Test FILTER function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/filter",
            json={
                "values": [10, 20, 30, 40, 50],
                "criteria": [True, False, True, False, True]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [10, 30, 50]


@pytest.mark.asyncio
async def test_array_sequence(client):
    """Test SEQUENCE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/sequence",
            json={"rows": 3, "columns": 2, "start": 1, "step": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [[1, 2], [3, 4], [5, 6]]


@pytest.mark.asyncio
async def test_array_transpose(client):
    """Test TRANSPOSE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/transpose",
            json={"matrix": [[1, 2, 3], [4, 5, 6]]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [[1, 4], [2, 5], [3, 6]]


@pytest.mark.asyncio
async def test_array_flatten(client):
    """Test FLATTEN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/flatten",
            json={"matrix": [[1, 2], [3, 4], [5, 6]]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [1, 2, 3, 4, 5, 6]


@pytest.mark.asyncio
async def test_array_take_positive(client):
    """Test TAKE function with positive count."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/take",
            json={"values": [1, 2, 3, 4, 5], "rows": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_array_take_negative(client):
    """Test TAKE function with negative count (from end)."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/take",
            json={"values": [1, 2, 3, 4, 5], "rows": -2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [4, 5]


@pytest.mark.asyncio
async def test_array_drop(client):
    """Test DROP function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/drop",
            json={"values": [1, 2, 3, 4, 5], "rows": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [3, 4, 5]


@pytest.mark.asyncio
async def test_array_reverse(client):
    """Test REVERSE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/reverse",
            json={"values": [1, 2, 3, 4, 5]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [5, 4, 3, 2, 1]


@pytest.mark.asyncio
async def test_array_union(client):
    """Test UNION function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/union",
            json={"array1": [1, 2, 3], "array2": [3, 4, 5]}
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data["result"]) == {1, 2, 3, 4, 5}


@pytest.mark.asyncio
async def test_array_intersect(client):
    """Test INTERSECT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/intersect",
            json={"array1": [1, 2, 3, 4], "array2": [3, 4, 5, 6]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [3, 4]


@pytest.mark.asyncio
async def test_array_difference(client):
    """Test DIFFERENCE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/difference",
            json={"array1": [1, 2, 3, 4], "array2": [3, 4, 5]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [1, 2]


@pytest.mark.asyncio
async def test_array_first(client):
    """Test FIRST function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/first",
            json={"values": [10, 20, 30]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 10


@pytest.mark.asyncio
async def test_array_last(client):
    """Test LAST function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/last",
            json={"values": [10, 20, 30]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 30


@pytest.mark.asyncio
async def test_array_contains(client):
    """Test CONTAINS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/contains",
            json={"values": [1, 2, 3, 4, 5], "search_value": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_array_index_of(client):
    """Test INDEX_OF function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/index-of",
            json={"values": ["A", "B", "C", "D"], "search_value": "C"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 2


@pytest.mark.asyncio
async def test_array_randarray(client):
    """Test RANDARRAY function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/randarray",
            params={"rows": 2, "columns": 3, "min_val": 0, "max_val": 10, "whole_numbers": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        assert len(data["result"][0]) == 3


@pytest.mark.asyncio
async def test_array_chunk(client):
    """Test CHUNK function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/chunk",
            json={"values": [1, 2, 3, 4, 5, 6, 7], "size": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [[1, 2, 3], [4, 5, 6], [7]]

@pytest.mark.asyncio
async def test_array_expand(client):
    """Test EXPAND function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/expand",
            json={"values": [1, 2, 3], "rows": 5, "pad_with": 0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [1, 2, 3, 0, 0]


@pytest.mark.asyncio
async def test_array_slice(client):
    """Test SLICE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/slice",
            json={"values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "start": 2, "end": 7, "step": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == [3, 5, 7]


@pytest.mark.asyncio
async def test_array_count_if(client):
    """Test COUNT_IF function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/count-if",
            json={"values": [1, 2, 2, 3, 2, 4, 2], "search_value": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 4


@pytest.mark.asyncio
async def test_array_nth(client):
    """Test NTH function."""
    async with client:
        response = await client.post(
            "/api/v1/math/array/nth",
            json={"values": ["A", "B", "C", "D"], "search_value": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "C"


