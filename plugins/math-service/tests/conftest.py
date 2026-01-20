"""
Pytest configuration and fixtures for math-service tests.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Generator

# Import the app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_data() -> list[float]:
    """Sample data for statistical tests."""
    return [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]


@pytest.fixture
def sample_matrix() -> list[list[float]]:
    """Sample matrix for matrix tests."""
    return [[1.0, 2.0], [3.0, 4.0]]


@pytest.fixture
def sample_identity_matrix() -> list[list[float]]:
    """Sample identity matrix."""
    return [[1.0, 0.0], [0.0, 1.0]]


@pytest.fixture
def sample_financial_data() -> dict:
    """Sample financial data for finance tests."""
    return {
        "rate": 0.05,  # 5% annual rate
        "cash_flows": [-1000, 300, 400, 500, 600],  # Initial investment + returns
        "pv": 10000,
        "nper": 12,
        "pmt": 1000,
    }


@pytest.fixture
def sample_excel_data() -> dict:
    """Sample data for Excel-like function tests."""
    return {
        "lookup_data": [
            {"id": 1, "name": "Alice", "age": 30, "salary": 50000},
            {"id": 2, "name": "Bob", "age": 25, "salary": 45000},
            {"id": 3, "name": "Charlie", "age": 35, "salary": 60000},
            {"id": 4, "name": "Diana", "age": 28, "salary": 52000},
        ],
        "pivot_data": [
            {"region": "North", "product": "A", "sales": 100},
            {"region": "North", "product": "B", "sales": 150},
            {"region": "South", "product": "A", "sales": 200},
            {"region": "South", "product": "B", "sales": 250},
        ],
    }
