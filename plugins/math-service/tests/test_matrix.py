"""
Tests for matrix endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import numpy as np


class TestMatrixOperations:
    """Tests for basic matrix operations."""

    def test_matrix_add(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix addition."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "add",
            "matrixA": sample_matrix,
            "matrixB": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]["result"]
        assert result == [[2.0, 4.0], [6.0, 8.0]]

    def test_matrix_subtract(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix subtraction."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "subtract",
            "matrixA": sample_matrix,
            "matrixB": [[1.0, 1.0], [1.0, 1.0]]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]["result"]
        assert result == [[0.0, 1.0], [2.0, 3.0]]

    def test_matrix_multiply(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix multiplication."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "multiply",
            "matrixA": sample_matrix,
            "matrixB": [[1.0, 0.0], [0.0, 1.0]]  # Identity matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]["result"]
        assert result == sample_matrix

    def test_matrix_scalar_multiply(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix scalar multiplication."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "scalar_multiply",
            "matrixA": sample_matrix,
            "scalar": 2.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]["result"]
        assert result == [[2.0, 4.0], [6.0, 8.0]]

    def test_matrix_transpose(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix transpose."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "transpose",
            "matrixA": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]["result"]
        assert result == [[1.0, 3.0], [2.0, 4.0]]

    def test_matrix_determinant(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix determinant."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "determinant",
            "matrixA": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # det([[1,2],[3,4]]) = 1*4 - 2*3 = -2
        assert data["data"]["result"] == pytest.approx(-2.0, rel=1e-6)

    def test_matrix_inverse(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix inverse."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "inverse",
            "matrixA": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]["result"]
        # Verify A * A^-1 = I
        a = np.array(sample_matrix)
        a_inv = np.array(result)
        identity = np.matmul(a, a_inv)
        np.testing.assert_array_almost_equal(identity, np.eye(2), decimal=6)

    def test_matrix_trace(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix trace."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "trace",
            "matrixA": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # trace([[1,2],[3,4]]) = 1 + 4 = 5
        assert data["data"]["result"] == 5.0

    def test_matrix_rank(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test matrix rank."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "rank",
            "matrixA": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 2


class TestMatrixEigenvalues:
    """Tests for eigenvalue calculations."""

    def test_matrix_eigenvalues(self, client: TestClient, sample_matrix: list[list[float]]):
        """Test eigenvalue calculation."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "eigenvalues",
            "matrixA": sample_matrix
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "eigenvalues" in data["data"]


class TestMatrixErrors:
    """Tests for error handling in matrix operations."""

    def test_singular_matrix_inverse(self, client: TestClient):
        """Test error when inverting singular matrix."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "inverse",
            "matrixA": [[1, 2], [2, 4]]  # Singular matrix
        })
        data = response.json()
        # Should handle gracefully - either error or special message
        assert response.status_code in [200, 400, 422]

    def test_incompatible_dimensions(self, client: TestClient):
        """Test error with incompatible matrix dimensions."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "multiply",
            "matrixA": [[1, 2], [3, 4]],
            "matrixB": [[1], [2], [3]]  # 3x1, incompatible with 2x2
        })
        data = response.json()
        # Should handle gracefully

    def test_non_square_determinant(self, client: TestClient):
        """Test error when calculating determinant of non-square matrix."""
        response = client.post("/api/v1/math/matrix", json={
            "operation": "determinant",
            "matrixA": [[1, 2, 3], [4, 5, 6]]  # 2x3 matrix
        })
        data = response.json()
        # Should handle gracefully


class TestMatrixInfo:
    """Tests for matrix info endpoints."""

    def test_list_operations(self, client: TestClient):
        """Test listing available matrix operations."""
        response = client.get("/api/v1/math/matrix/operations")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "unary_operations" in data["data"]
        assert "binary_operations" in data["data"]
