"""
Tests for Math Functions routes.
"""
import math
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_math_abs(client):
    """Test ABS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/abs",
            json={"value": -42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 42


@pytest.mark.asyncio
async def test_math_sign_positive(client):
    """Test SIGN function with positive number."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/sign",
            json={"value": 42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 1


@pytest.mark.asyncio
async def test_math_sign_negative(client):
    """Test SIGN function with negative number."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/sign",
            json={"value": -42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == -1


@pytest.mark.asyncio
async def test_math_mod(client):
    """Test MOD function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/mod",
            json={"value1": 17, "value2": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 2


@pytest.mark.asyncio
async def test_math_round(client):
    """Test ROUND function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/round",
            json={"value": 3.14159, "num_digits": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 3.14


@pytest.mark.asyncio
async def test_math_roundup(client):
    """Test ROUNDUP function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/roundup",
            json={"value": 3.14159, "num_digits": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 3.15


@pytest.mark.asyncio
async def test_math_rounddown(client):
    """Test ROUNDDOWN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/rounddown",
            json={"value": 3.14999, "num_digits": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 3.14


@pytest.mark.asyncio
async def test_math_ceiling(client):
    """Test CEILING function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/ceiling",
            json={"value": 4.3, "significance": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 5


@pytest.mark.asyncio
async def test_math_floor(client):
    """Test FLOOR function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/floor",
            json={"value": 4.7, "significance": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 4


@pytest.mark.asyncio
async def test_math_power(client):
    """Test POWER function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/power",
            json={"base": 2, "exponent": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 1024


@pytest.mark.asyncio
async def test_math_sqrt(client):
    """Test SQRT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/sqrt",
            json={"value": 144}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 12


@pytest.mark.asyncio
async def test_math_exp(client):
    """Test EXP function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/exp",
            json={"value": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - math.e) < 0.0001


@pytest.mark.asyncio
async def test_math_log(client):
    """Test LOG function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/log",
            json={"value": 100, "base": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 2


@pytest.mark.asyncio
async def test_math_ln(client):
    """Test LN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/ln",
            json={"value": math.e}
        )
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - 1) < 0.0001


@pytest.mark.asyncio
async def test_math_gcd(client):
    """Test GCD function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/gcd",
            json={"values": [48, 18, 24]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 6


@pytest.mark.asyncio
async def test_math_lcm(client):
    """Test LCM function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/lcm",
            json={"values": [4, 6]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 12


@pytest.mark.asyncio
async def test_math_rand(client):
    """Test RAND function."""
    async with client:
        response = await client.get("/api/v1/math/math/rand")
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["result"] <= 1


@pytest.mark.asyncio
async def test_math_pi(client):
    """Test PI function."""
    async with client:
        response = await client.get("/api/v1/math/math/pi")
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - math.pi) < 0.0001


@pytest.mark.asyncio
async def test_math_sin(client):
    """Test SIN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/sin",
            json={"angle": math.pi / 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - 1) < 0.0001


@pytest.mark.asyncio
async def test_math_cos(client):
    """Test COS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/cos",
            json={"angle": 0}
        )
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - 1) < 0.0001


@pytest.mark.asyncio
async def test_math_radians(client):
    """Test RADIANS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/radians",
            json={"value": 180}
        )
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - math.pi) < 0.0001


@pytest.mark.asyncio
async def test_math_degrees(client):
    """Test DEGREES function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/degrees",
            json={"value": math.pi}
        )
        assert response.status_code == 200
        data = response.json()
        assert abs(data["result"] - 180) < 0.0001


@pytest.mark.asyncio
async def test_math_combin(client):
    """Test COMBIN function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/combin",
            json={"n": 5, "k": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 10


@pytest.mark.asyncio
async def test_math_permut(client):
    """Test PERMUT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/permut",
            json={"n": 5, "k": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 20


@pytest.mark.asyncio
async def test_math_fact(client):
    """Test FACT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/fact",
            json={"value": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 120


@pytest.mark.asyncio
async def test_math_product(client):
    """Test PRODUCT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/product",
            json={"values": [2, 3, 4]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 24


@pytest.mark.asyncio
async def test_math_sumproduct(client):
    """Test SUMPRODUCT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/sumproduct",
            json={"arrays": [[1, 2, 3], [4, 5, 6]]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 32  # 1*4 + 2*5 + 3*6


@pytest.mark.asyncio
async def test_math_sumsq(client):
    """Test SUMSQ function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/sumsq",
            json={"values": [3, 4]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 25


@pytest.mark.asyncio
async def test_math_quotient(client):
    """Test QUOTIENT function."""
    async with client:
        response = await client.post(
            "/api/v1/math/math/quotient",
            json={"numerator": 17, "denominator": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 3
