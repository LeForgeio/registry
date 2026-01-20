"""
Tests for Excel-like function endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestVLookup:
    """Tests for VLOOKUP function."""

    def test_vlookup_exact_match(self, client: TestClient):
        """Test VLOOKUP with exact match."""
        response = client.post("/api/v1/math/excel/vlookup", json={
            "lookup_value": "A002",
            "table_array": [
                ["A001", "Widget", 10.99],
                ["A002", "Gadget", 25.50],
                ["A003", "Gizmo", 15.00]
            ],
            "col_index": 2,
            "exact_match": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == "Gadget"
        assert data["data"]["found"] is True

    def test_vlookup_not_found(self, client: TestClient):
        """Test VLOOKUP when value not found."""
        response = client.post("/api/v1/math/excel/vlookup", json={
            "lookup_value": "A999",
            "table_array": [
                ["A001", "Widget", 10.99],
                ["A002", "Gadget", 25.50]
            ],
            "col_index": 2,
            "exact_match": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["found"] is False

    def test_vlookup_numeric_lookup(self, client: TestClient):
        """Test VLOOKUP with numeric lookup."""
        response = client.post("/api/v1/math/excel/vlookup", json={
            "lookup_value": 2,
            "table_array": [
                [1, "One", 100],
                [2, "Two", 200],
                [3, "Three", 300]
            ],
            "col_index": 3,
            "exact_match": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 200


class TestHLookup:
    """Tests for HLOOKUP function."""

    def test_hlookup_exact_match(self, client: TestClient):
        """Test HLOOKUP with exact match."""
        response = client.post("/api/v1/math/excel/hlookup", json={
            "lookup_value": "Feb",
            "table_array": [
                ["Jan", "Feb", "Mar"],
                [100, 200, 300],
                [150, 250, 350]
            ],
            "row_index": 2,
            "exact_match": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 200


class TestSumIf:
    """Tests for SUMIF function."""

    def test_sumif_equals(self, client: TestClient):
        """Test SUMIF with equals condition."""
        response = client.post("/api/v1/math/excel/sumif", json={
            "range_values": ["Apple", "Banana", "Apple", "Orange", "Apple"],
            "criteria": "Apple",
            "sum_range": [100, 50, 75, 200, 150]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Apple rows: 100 + 75 + 150 = 325
        assert data["data"]["result"] == 325

    def test_sumif_greater_than(self, client: TestClient):
        """Test SUMIF with greater than condition."""
        response = client.post("/api/v1/math/excel/sumif", json={
            "range_values": [10, 25, 15, 30, 5],
            "criteria": ">20"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Values > 20: 25 + 30 = 55
        assert data["data"]["result"] == 55

    def test_sumif_less_than(self, client: TestClient):
        """Test SUMIF with less than condition."""
        response = client.post("/api/v1/math/excel/sumif", json={
            "range_values": [10, 25, 15, 30, 5],
            "criteria": "<20"
        })
        assert response.status_code == 200
        data = response.json()
        # Values < 20: 10 + 15 + 5 = 30
        assert data["data"]["result"] == 30


class TestCountIf:
    """Tests for COUNTIF function."""

    def test_countif_equals(self, client: TestClient):
        """Test COUNTIF with equals condition."""
        response = client.post("/api/v1/math/excel/countif", json={
            "range_values": ["Apple", "Banana", "Apple", "Orange", "Apple"],
            "criteria": "Apple"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 3

    def test_countif_greater_than(self, client: TestClient):
        """Test COUNTIF with greater than condition."""
        response = client.post("/api/v1/math/excel/countif", json={
            "range_values": [10, 25, 15, 30, 5],
            "criteria": ">20"
        })
        assert response.status_code == 200
        data = response.json()
        # Values > 20: 25, 30 = 2 records
        assert data["data"]["result"] == 2


class TestPivot:
    """Tests for Pivot table function."""

    def test_pivot_sum(self, client: TestClient):
        """Test pivot table with SUM aggregation."""
        response = client.post("/api/v1/math/excel/pivot", json={
            "data": [
                {"region": "North", "product": "A", "sales": 100},
                {"region": "North", "product": "B", "sales": 150},
                {"region": "South", "product": "A", "sales": 200},
                {"region": "South", "product": "B", "sales": 250}
            ],
            "rows": ["region"],
            "values": [{"column": "sales", "function": "sum"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "table" in data["data"]

    def test_pivot_mean(self, client: TestClient):
        """Test pivot table with MEAN aggregation."""
        response = client.post("/api/v1/math/excel/pivot", json={
            "data": [
                {"region": "North", "product": "A", "sales": 100},
                {"region": "North", "product": "B", "sales": 150},
                {"region": "South", "product": "A", "sales": 200},
                {"region": "South", "product": "B", "sales": 250}
            ],
            "rows": ["region"],
            "values": [{"column": "sales", "function": "mean"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_pivot_with_columns(self, client: TestClient):
        """Test pivot table with columns."""
        response = client.post("/api/v1/math/excel/pivot", json={
            "data": [
                {"region": "North", "product": "A", "sales": 100},
                {"region": "North", "product": "B", "sales": 150},
                {"region": "South", "product": "A", "sales": 200},
                {"region": "South", "product": "B", "sales": 250}
            ],
            "rows": ["region"],
            "columns": ["product"],
            "values": [{"column": "sales", "function": "sum"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_pivot_count(self, client: TestClient):
        """Test pivot table with COUNT aggregation."""
        response = client.post("/api/v1/math/excel/pivot", json={
            "data": [
                {"region": "North", "product": "A", "sales": 100},
                {"region": "North", "product": "B", "sales": 150},
                {"region": "South", "product": "A", "sales": 200},
                {"region": "South", "product": "B", "sales": 250}
            ],
            "rows": ["region"],
            "values": [{"column": "sales", "function": "count"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestExcelErrors:
    """Tests for error handling in Excel functions."""

    def test_vlookup_invalid_col_index(self, client: TestClient):
        """Test VLOOKUP with invalid column index."""
        response = client.post("/api/v1/math/excel/vlookup", json={
            "lookup_value": "A001",
            "table_array": [["A001", "Widget"]],
            "col_index": 10,  # Invalid - exceeds table width
            "exact_match": True
        })
        data = response.json()
        # Should handle gracefully
        assert response.status_code == 200


class TestExcelFunctions:
    """Tests for listing Excel functions."""

    def test_list_functions(self, client: TestClient):
        """Test listing available Excel functions."""
        response = client.get("/api/v1/math/excel/functions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestSumIfAvgIf:
    """Tests for SUMIF and AVERAGEIF functions."""

    def test_averageif_equals(self, client: TestClient):
        """Test AVERAGEIF with equals criteria."""
        response = client.post("/api/v1/math/excel/averageif", json={
            "range_values": ["A", "B", "A", "B", "A"],
            "criteria": "A",
            "average_range": [10, 20, 30, 40, 50]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 30  # (10 + 30 + 50) / 3

    def test_averageif_greater(self, client: TestClient):
        """Test AVERAGEIF with greater than criteria."""
        response = client.post("/api/v1/math/excel/averageif", json={
            "range_values": [10, 20, 30, 40, 50],
            "criteria": ">25"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == 40  # (30 + 40 + 50) / 3

