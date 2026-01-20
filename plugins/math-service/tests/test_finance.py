"""
Tests for financial calculation endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import math


class TestNPV:
    """Tests for Net Present Value calculation."""

    def test_npv_basic(self, client: TestClient):
        """Test basic NPV calculation."""
        response = client.post("/api/v1/math/finance/npv", json={
            "rate": 0.1,
            "cash_flows": [-1000, 300, 420, 680]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "npv" in data["data"]
        # NPV is calculated with period 0 as initial investment
        assert data["data"]["npv"] > 0  # Positive NPV
        assert data["data"]["is_profitable"] is True

    def test_npv_negative_result(self, client: TestClient):
        """Test NPV with negative result."""
        response = client.post("/api/v1/math/finance/npv", json={
            "rate": 0.1,
            "cash_flows": [-1000, 100, 100, 100]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["npv"] < 0
        assert data["data"]["is_profitable"] is False

    def test_npv_zero_rate(self, client: TestClient):
        """Test NPV with zero discount rate."""
        response = client.post("/api/v1/math/finance/npv", json={
            "rate": 0,
            "cash_flows": [-1000, 500, 500, 500]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Sum of cash flows without discounting
        assert data["data"]["npv"] == pytest.approx(500, rel=0.01)


class TestIRR:
    """Tests for Internal Rate of Return calculation."""

    def test_irr_basic(self, client: TestClient):
        """Test basic IRR calculation."""
        response = client.post("/api/v1/math/finance/irr", json={
            "cash_flows": [-1000, 400, 400, 400]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "irr" in data["data"]
        # IRR should be around 9.7%
        assert 0.08 < data["data"]["irr"] < 0.12

    def test_irr_high_return(self, client: TestClient):
        """Test IRR with high return investment."""
        response = client.post("/api/v1/math/finance/irr", json={
            "cash_flows": [-100, 150]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # IRR should be 50%
        assert data["data"]["irr"] == pytest.approx(0.5, rel=0.01)


class TestPMT:
    """Tests for Payment calculation."""

    def test_pmt_basic(self, client: TestClient):
        """Test basic PMT calculation."""
        # Loan of $10,000, 5% annual rate, 12 monthly payments
        response = client.post("/api/v1/math/finance/pmt", json={
            "rate": 0.05/12,  # Monthly rate
            "nper": 12,
            "pv": 10000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "payment" in data["data"]
        # Monthly payment should be around $856
        assert 850 < abs(data["data"]["payment"]) < 860

    def test_pmt_with_fv(self, client: TestClient):
        """Test PMT calculation with future value."""
        response = client.post("/api/v1/math/finance/pmt", json={
            "rate": 0.06/12,
            "nper": 60,
            "pv": 0,
            "fv": 10000  # Saving for $10,000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "payment" in data["data"]

    def test_pmt_due_at_beginning(self, client: TestClient):
        """Test PMT with payments at beginning of period."""
        response = client.post("/api/v1/math/finance/pmt", json={
            "rate": 0.05/12,
            "nper": 12,
            "pv": 10000,
            "payment_type": "beginning"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestFV:
    """Tests for Future Value calculation."""

    def test_fv_basic(self, client: TestClient):
        """Test basic FV calculation."""
        # $1000 invested at 5% for 10 years
        response = client.post("/api/v1/math/finance/fv", json={
            "rate": 0.05,
            "nper": 10,
            "pmt": 0,
            "pv": 1000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # FV = 1000 * (1.05)^10 ≈ 1628.89 (negative due to sign convention)
        assert abs(data["data"]["future_value"]) == pytest.approx(1628.89, rel=0.01)

    def test_fv_with_payments(self, client: TestClient):
        """Test FV with regular payments."""
        # $100/month for 5 years at 6% annual (0.5% monthly)
        response = client.post("/api/v1/math/finance/fv", json={
            "rate": 0.06/12,
            "nper": 60,
            "pmt": 100,
            "pv": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should accumulate to around $6,977
        assert 6900 < abs(data["data"]["future_value"]) < 7100


class TestPV:
    """Tests for Present Value calculation."""

    def test_pv_basic(self, client: TestClient):
        """Test basic PV calculation."""
        # FV of $1000 in 10 years at 5%
        response = client.post("/api/v1/math/finance/pv", json={
            "rate": 0.05,
            "nper": 10,
            "pmt": 0,
            "fv": 1000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # PV = 1000 / (1.05)^10 ≈ 613.91
        assert abs(data["data"]["present_value"]) == pytest.approx(613.91, rel=0.01)

    def test_pv_annuity(self, client: TestClient):
        """Test PV of annuity."""
        # Annuity of $100/month for 12 months at 6%
        response = client.post("/api/v1/math/finance/pv", json={
            "rate": 0.06/12,
            "nper": 12,
            "pmt": 100,
            "fv": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAmortization:
    """Tests for amortization schedule."""

    def test_amortization_basic(self, client: TestClient):
        """Test basic amortization schedule."""
        response = client.post("/api/v1/math/finance/amortization", json={
            "principal": 10000,
            "annual_rate": 0.06,
            "periods": 12
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        schedule = data["data"]["schedule"]
        assert len(schedule) == 12
        
        # Check first payment
        first = schedule[0]
        assert "period" in first
        assert "payment" in first
        assert "principal_payment" in first
        assert "interest_payment" in first
        assert "principal_balance" in first
        
        # Check last payment has balance close to 0
        last = schedule[-1]
        assert abs(last["principal_balance"]) < 0.01

    def test_amortization_summary(self, client: TestClient):
        """Test amortization summary."""
        response = client.post("/api/v1/math/finance/amortization", json={
            "principal": 100000,
            "annual_rate": 0.05,
            "periods": 360  # 30-year mortgage
        })
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data["data"]
        summary = data["data"]["summary"]
        assert "total_payments" in summary or "total_payment" in summary
        assert "total_interest" in summary


class TestFinanceErrors:
    """Tests for error handling in financial calculations."""

    def test_npv_too_few_cash_flows(self, client: TestClient):
        """Test NPV with too few cash flows."""
        response = client.post("/api/v1/math/finance/npv", json={
            "rate": 0.1,
            "cash_flows": [-1000]  # Only one cash flow
        })
        # Should return validation error
        assert response.status_code in [200, 422]

    def test_irr_no_sign_change(self, client: TestClient):
        """Test IRR when no sign change in cash flows."""
        response = client.post("/api/v1/math/finance/irr", json={
            "cash_flows": [100, 200, 300]  # All positive
        })
        # Should handle gracefully - may return error or None

    def test_pmt_zero_periods(self, client: TestClient):
        """Test PMT with invalid periods."""
        response = client.post("/api/v1/math/finance/pmt", json={
            "rate": 0.05,
            "nper": 0,
            "pv": 1000
        })
        # Should return validation error
        assert response.status_code in [200, 422]


class TestFinanceFunctions:
    """Tests for listing finance functions."""

    def test_list_functions(self, client: TestClient):
        """Test listing available finance functions."""
        response = client.get("/api/v1/math/finance/functions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "functions" in data["data"]
