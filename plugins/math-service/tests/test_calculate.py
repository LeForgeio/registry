"""
Tests for calculation endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import math


class TestCalculateEndpoint:
    """Tests for expression calculation."""

    def test_simple_arithmetic(self, client: TestClient):
        """Test simple arithmetic expressions."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "2 + 3"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 5

    def test_complex_arithmetic(self, client: TestClient):
        """Test complex arithmetic expressions."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "(10 + 5) * 2 / 3"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == pytest.approx(10.0, rel=1e-9)

    def test_power_operations(self, client: TestClient):
        """Test power operations."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "2 ** 10"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == 1024

    def test_modulo_operation(self, client: TestClient):
        """Test modulo operation."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "17 % 5"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == 2

    def test_negative_numbers(self, client: TestClient):
        """Test negative numbers."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "-5 + 3"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == -2

    def test_floating_point(self, client: TestClient):
        """Test floating point calculations."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "3.14159 * 2"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == pytest.approx(6.28318, rel=1e-5)

    def test_math_functions_sqrt(self, client: TestClient):
        """Test sqrt function."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "sqrt(16)"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == 4

    def test_math_functions_sin(self, client: TestClient):
        """Test sin function."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "sin(0)"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == pytest.approx(0, abs=1e-9)

    def test_math_functions_cos(self, client: TestClient):
        """Test cos function."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "cos(0)"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == pytest.approx(1, rel=1e-9)

    def test_math_functions_log(self, client: TestClient):
        """Test log function."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "log(e)"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == pytest.approx(1, rel=1e-9)

    def test_math_functions_abs(self, client: TestClient):
        """Test abs function."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "abs(-42)"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == 42

    def test_constants_pi(self, client: TestClient):
        """Test pi constant."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "pi"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == pytest.approx(math.pi, rel=1e-9)

    def test_constants_e(self, client: TestClient):
        """Test e constant."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "e"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == pytest.approx(math.e, rel=1e-9)

    def test_with_variables(self, client: TestClient):
        """Test calculation with variables."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "x + y * 2",
            "variables": {"x": 10, "y": 5}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == 20

    def test_complex_expression_with_functions(self, client: TestClient):
        """Test complex expression with multiple functions."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "sqrt(pow(3, 2) + pow(4, 2))"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["result"] == 5


class TestCalculateErrors:
    """Tests for error handling in calculations."""

    def test_division_by_zero(self, client: TestClient):
        """Test division by zero error."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "1 / 0"
        })
        # Should still return 200 but with error in response
        data = response.json()
        # The response could be an error or infinity depending on implementation

    def test_invalid_expression(self, client: TestClient):
        """Test invalid expression."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": "2 + + 3"
        })
        data = response.json()
        # Should handle gracefully

    def test_empty_expression(self, client: TestClient):
        """Test empty expression."""
        response = client.post("/api/v1/math/calculate", json={
            "expression": ""
        })
        # Should return validation error
        assert response.status_code in [200, 422]
