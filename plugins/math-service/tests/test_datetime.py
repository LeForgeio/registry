"""
Tests for DateTime Functions routes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_date_create(client):
    """Test DATE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/date",
            json={"year": 2024, "month": 6, "day": 15}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "2024-06-15"


@pytest.mark.asyncio
async def test_today(client):
    """Test TODAY function."""
    async with client:
        response = await client.get("/api/v1/math/datetime/today")
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["operation"] == "TODAY"


@pytest.mark.asyncio
async def test_now(client):
    """Test NOW function."""
    async with client:
        response = await client.get("/api/v1/math/datetime/now")
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "date" in data
        assert "time" in data


@pytest.mark.asyncio
async def test_year(client):
    """Test YEAR function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/year",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 2024


@pytest.mark.asyncio
async def test_month(client):
    """Test MONTH function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/month",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 6


@pytest.mark.asyncio
async def test_day(client):
    """Test DAY function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/day",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 15


@pytest.mark.asyncio
async def test_weekday(client):
    """Test WEEKDAY function."""
    async with client:
        # June 15, 2024 is a Saturday
        response = await client.post(
            "/api/v1/math/datetime/weekday",
            params={"return_type": 2},  # Monday=1
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 6  # Saturday


@pytest.mark.asyncio
async def test_weeknum(client):
    """Test WEEKNUM function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/weeknum",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 24


@pytest.mark.asyncio
async def test_datedif_days(client):
    """Test DATEDIF function for days."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/datedif",
            json={"start_date": "2024-01-01", "end_date": "2024-01-31", "unit": "D"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 30


@pytest.mark.asyncio
async def test_datedif_months(client):
    """Test DATEDIF function for months."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/datedif",
            json={"start_date": "2024-01-15", "end_date": "2024-06-15", "unit": "M"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 5


@pytest.mark.asyncio
async def test_datedif_years(client):
    """Test DATEDIF function for years."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/datedif",
            json={"start_date": "2020-01-01", "end_date": "2024-01-01", "unit": "Y"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 4


@pytest.mark.asyncio
async def test_networkdays(client):
    """Test NETWORKDAYS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/networkdays",
            json={
                "start_date": "2024-01-01",
                "end_date": "2024-01-12",
                "holidays": ["2024-01-08"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 9  # 10 weekdays (Mon-Fri) minus 1 holiday


@pytest.mark.asyncio
async def test_workday(client):
    """Test WORKDAY function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/workday",
            json={
                "start_date": "2024-01-01",
                "days": 5,
                "holidays": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "2024-01-08"


@pytest.mark.asyncio
async def test_edate(client):
    """Test EDATE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/edate",
            json={"start_date": "2024-01-15", "months": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "2024-04-15"


@pytest.mark.asyncio
async def test_eomonth(client):
    """Test EOMONTH function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/eomonth",
            json={"start_date": "2024-01-15", "months": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "2024-02-29"  # 2024 is a leap year


@pytest.mark.asyncio
async def test_quarter(client):
    """Test QUARTER function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/quarter",
            json={"date": "2024-08-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 3  # Q3


@pytest.mark.asyncio
async def test_components(client):
    """Test date components."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/components",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert data["month"] == 6
        assert data["day"] == 15
        assert "weekday_name" in data


@pytest.mark.asyncio
async def test_is_weekend(client):
    """Test IS_WEEKEND function."""
    async with client:
        # Saturday
        response = await client.post(
            "/api/v1/math/datetime/is-weekend",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_is_leap_year(client):
    """Test IS_LEAP_YEAR function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/is-leap-year",
            params={"year": 2024}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True


@pytest.mark.asyncio
async def test_days(client):
    """Test DAYS function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/days",
            json={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 365  # Leap year but counting days between

@pytest.mark.asyncio
async def test_time_create(client):
    """Test TIME function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/time",
            json={"hour": 14, "minute": 30, "second": 45}
        )
        assert response.status_code == 200
        data = response.json()
        assert "14:30:45" in data["result"]


@pytest.mark.asyncio
async def test_hour(client):
    """Test HOUR function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/hour",
            params={"datetime_str": "2024-06-15T14:30:45"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 14


@pytest.mark.asyncio
async def test_minute(client):
    """Test MINUTE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/minute",
            params={"datetime_str": "2024-06-15T14:30:45"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 30


@pytest.mark.asyncio
async def test_second(client):
    """Test SECOND function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/second",
            params={"datetime_str": "2024-06-15T14:30:45"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 45


@pytest.mark.asyncio
async def test_days360(client):
    """Test DAYS360 function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/days360",
            json={"start_date": "2024-01-15", "end_date": "2024-02-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 30  # 30-day month


@pytest.mark.asyncio
async def test_datevalue(client):
    """Test DATEVALUE function."""
    async with client:
        response = await client.post(
            "/api/v1/math/datetime/datevalue",
            json={"date": "2024-06-15"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] > 0  # Serial date number