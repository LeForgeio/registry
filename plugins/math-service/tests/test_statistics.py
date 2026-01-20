"""
Tests for statistics endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import math


class TestStatisticsOperations:
    """Tests for basic statistical operations."""

    def test_mean_calculation(self, client: TestClient, sample_data: list[float]):
        """Test mean calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["mean"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["mean"] == 5.5

    def test_median_calculation(self, client: TestClient, sample_data: list[float]):
        """Test median calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["median"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["median"] == 5.5

    def test_stddev_calculation(self, client: TestClient, sample_data: list[float]):
        """Test standard deviation calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["stddev"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["stddev"] == pytest.approx(2.8722813232690143, rel=1e-6)

    def test_variance_calculation(self, client: TestClient, sample_data: list[float]):
        """Test variance calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["variance"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "variance" in data["data"]

    def test_min_max_calculation(self, client: TestClient, sample_data: list[float]):
        """Test min and max calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["min", "max"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["min"] == 1.0
        assert data["data"]["max"] == 10.0

    def test_sum_calculation(self, client: TestClient, sample_data: list[float]):
        """Test sum calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["sum"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["sum"] == 55.0

    def test_count_calculation(self, client: TestClient, sample_data: list[float]):
        """Test count calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["count"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["count"] == 10

    def test_percentile_calculation(self, client: TestClient, sample_data: list[float]):
        """Test percentile calculation using q1, q2, q3 operations."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["q1", "q2", "q3"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["q1"] == pytest.approx(3.25, rel=1e-2)
        assert data["data"]["q2"] == 5.5
        assert data["data"]["q3"] == pytest.approx(7.75, rel=1e-2)

    def test_mode_calculation(self, client: TestClient):
        """Test mode calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": [1, 2, 2, 3, 3, 3, 4],
            "operations": ["mode"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["mode"] == 3

    def test_range_calculation(self, client: TestClient, sample_data: list[float]):
        """Test range calculation."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["range"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["range"] == 9.0

    def test_multiple_operations(self, client: TestClient, sample_data: list[float]):
        """Test multiple operations at once."""
        response = client.post("/api/v1/math/statistics", json={
            "data": sample_data,
            "operations": ["mean", "median", "stddev", "min", "max"]
        })
        assert response.status_code == 200
        data = response.json()
        # Check that all requested operations are in the response
        assert "mean" in data["data"]
        assert "median" in data["data"]
        assert "stddev" in data["data"]
        assert "min" in data["data"]
        assert "max" in data["data"]


class TestDescribeEndpoint:
    """Tests for statistical description endpoint."""

    def test_describe_basic(self, client: TestClient, sample_data: list[float]):
        """Test describe endpoint with basic data."""
        response = client.post("/api/v1/math/stats/describe", json={
            "data": sample_data
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert result["count"] == 10
        assert result["mean"] == 5.5
        assert result["median"] == 5.5
        assert result["min"] == 1.0
        assert result["max"] == 10.0
        assert "std" in result
        assert "variance" in result
        assert "quartiles" in result

    def test_describe_quartiles(self, client: TestClient, sample_data: list[float]):
        """Test describe endpoint quartiles."""
        response = client.post("/api/v1/math/stats/describe", json={
            "data": sample_data
        })
        assert response.status_code == 200
        data = response.json()
        quartiles = data["data"]["quartiles"]
        assert "q1" in quartiles
        assert "q2" in quartiles
        assert "q3" in quartiles
        assert "iqr" in quartiles

    def test_describe_outliers(self, client: TestClient):
        """Test describe endpoint outlier detection."""
        data_with_outliers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is an outlier
        response = client.post("/api/v1/math/stats/describe", json={
            "data": data_with_outliers
        })
        assert response.status_code == 200
        data = response.json()
        assert "outliers" in data["data"]
        outliers = data["data"]["outliers"]
        assert outliers["count"] >= 1
        assert 100 in outliers["values"]

    def test_describe_small_dataset(self, client: TestClient):
        """Test describe endpoint with small dataset."""
        response = client.post("/api/v1/math/stats/describe", json={
            "data": [1.0, 2.0]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestCorrelation:
    """Tests for correlation endpoint."""

    def test_correlation_pearson(self, client: TestClient):
        """Test Pearson correlation."""
        response = client.post("/api/v1/math/correlation", json={
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],
            "method": "pearson"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["correlation"] == pytest.approx(1.0, rel=1e-6)

    def test_correlation_spearman(self, client: TestClient):
        """Test Spearman correlation."""
        response = client.post("/api/v1/math/correlation", json={
            "x": [1, 2, 3, 4, 5],
            "y": [5, 6, 7, 8, 7],
            "method": "spearman"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "correlation" in data["data"]

    def test_correlation_kendall(self, client: TestClient):
        """Test Kendall correlation."""
        response = client.post("/api/v1/math/correlation", json={
            "x": [1, 2, 3, 4, 5],
            "y": [1, 2, 3, 4, 5],
            "method": "kendall"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["correlation"] == pytest.approx(1.0, rel=1e-6)

    def test_correlation_negative(self, client: TestClient):
        """Test negative correlation."""
        response = client.post("/api/v1/math/correlation", json={
            "x": [1, 2, 3, 4, 5],
            "y": [10, 8, 6, 4, 2],
            "method": "pearson"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["correlation"] == pytest.approx(-1.0, rel=1e-6)

    def test_stats_correlation_endpoint(self, client: TestClient):
        """Test /stats/correlation endpoint."""
        response = client.post("/api/v1/math/stats/correlation", json={
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5],
            "method": "pearson"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "correlation" in data["data"]
        assert "p_value" in data["data"]
        assert "r_squared" in data["data"]


class TestRegression:
    """Tests for regression endpoint."""

    def test_linear_regression(self, client: TestClient):
        """Test linear regression."""
        response = client.post("/api/v1/math/stats/regression", json={
            "x": [1, 2, 3, 4, 5],
            "y": [2.1, 3.9, 6.1, 7.9, 10.1],
            "model": "linear"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert result["model"] == "linear"
        assert "coefficients" in result
        assert "r_squared" in result
        assert "equation" in result
        assert result["r_squared"] > 0.99  # Very strong linear relationship

    def test_polynomial_regression(self, client: TestClient):
        """Test polynomial regression."""
        # Quadratic data: y = x^2
        x = [1, 2, 3, 4, 5]
        y = [1, 4, 9, 16, 25]
        response = client.post("/api/v1/math/stats/regression", json={
            "x": x,
            "y": y,
            "model": "polynomial",
            "degree": 2
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert result["model"] == "polynomial"
        assert result["r_squared"] > 0.99

    def test_exponential_regression(self, client: TestClient):
        """Test exponential regression."""
        import math
        # Exponential data: y = 2 * e^(0.5*x)
        x = [1, 2, 3, 4, 5]
        y = [2 * math.exp(0.5 * xi) for xi in x]
        response = client.post("/api/v1/math/stats/regression", json={
            "x": x,
            "y": y,
            "model": "exponential"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert result["model"] == "exponential"

    def test_logarithmic_regression(self, client: TestClient):
        """Test logarithmic regression."""
        import math
        # Logarithmic data: y = 2 * ln(x) + 1
        x = [1, 2, 3, 4, 5]
        y = [2 * math.log(xi) + 1 for xi in x]
        response = client.post("/api/v1/math/stats/regression", json={
            "x": x,
            "y": y,
            "model": "logarithmic"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert result["model"] == "logarithmic"

    def test_regression_with_predictions(self, client: TestClient):
        """Test regression includes predictions when requested."""
        response = client.post("/api/v1/math/stats/regression", json={
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],
            "model": "linear",
            "include_predictions": True
        })
        assert response.status_code == 200
        data = response.json()
        result = data["data"]
        assert "predictions" in result
        assert "residuals" in result
        assert len(result["predictions"]) == 5


class TestStatisticsErrors:
    """Tests for error handling in statistics."""

    def test_empty_data(self, client: TestClient):
        """Test error with empty data."""
        response = client.post("/api/v1/math/statistics", json={
            "data": [],
            "operations": ["mean"]
        })
        # Should return validation error
        assert response.status_code in [200, 422]

    def test_mismatched_arrays(self, client: TestClient):
        """Test error with mismatched array lengths."""
        response = client.post("/api/v1/math/correlation", json={
            "x": [1, 2, 3],
            "y": [1, 2],
            "method": "pearson"
        })
        data = response.json()
        # Should handle gracefully
        assert "error" in str(data).lower() or data.get("success") is False


class TestListOperations:
    """Tests for listing available operations."""

    def test_list_operations(self, client: TestClient):
        """Test listing available statistical operations."""
        response = client.get("/api/v1/math/statistics/operations")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "operations" in data["data"]
        assert "correlation_methods" in data["data"]
