"""
Pydantic models for financial calculations.
"""
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class NPVRequest(BaseModel):
    """Request model for Net Present Value calculation."""
    
    rate: float = Field(
        ...,
        description="Discount rate (as decimal, e.g., 0.10 for 10%)",
        ge=-1.0,
        le=10.0,
        json_schema_extra={"example": 0.10}
    )
    cash_flows: list[float] = Field(
        ...,
        description="Array of cash flows (first element is initial investment, typically negative)",
        min_length=2,
        max_length=1000,
        json_schema_extra={"example": [-1000, 300, 400, 400, 300]}
    )


class NPVData(BaseModel):
    """NPV result data."""
    
    npv: float = Field(..., description="Net Present Value")
    rate: float = Field(..., description="Discount rate used")
    periods: int = Field(..., description="Number of periods")
    present_values: list[float] = Field(
        ...,
        description="Present value of each cash flow"
    )
    is_profitable: bool = Field(
        ...,
        description="Whether NPV is positive (investment is profitable)"
    )


class NPVResponse(BaseModel):
    """Response model for NPV calculation."""
    
    success: bool
    data: NPVData
    request_id: Optional[str] = None
    timestamp: str


class IRRRequest(BaseModel):
    """Request model for Internal Rate of Return calculation."""
    
    cash_flows: list[float] = Field(
        ...,
        description="Array of cash flows (first element is initial investment, typically negative)",
        min_length=2,
        max_length=1000,
        json_schema_extra={"example": [-1000, 300, 400, 400, 300]}
    )
    guess: float = Field(
        default=0.1,
        description="Initial guess for IRR (as decimal)",
        ge=-1.0,
        le=10.0
    )


class IRRData(BaseModel):
    """IRR result data."""
    
    irr: float = Field(..., description="Internal Rate of Return (as decimal)")
    irr_percentage: float = Field(..., description="IRR as percentage")
    periods: int = Field(..., description="Number of periods")
    npv_at_irr: float = Field(
        ...,
        description="NPV at the calculated IRR (should be ~0)"
    )


class IRRResponse(BaseModel):
    """Response model for IRR calculation."""
    
    success: bool
    data: IRRData
    request_id: Optional[str] = None
    timestamp: str


class PMTRequest(BaseModel):
    """Request model for loan Payment calculation."""
    
    rate: float = Field(
        ...,
        description="Interest rate per period (as decimal, e.g., 0.05/12 for 5% annual rate paid monthly)",
        ge=0.0,
        le=1.0,
        json_schema_extra={"example": 0.004167}
    )
    nper: int = Field(
        ...,
        description="Total number of payment periods",
        ge=1,
        le=1200,
        json_schema_extra={"example": 360}
    )
    pv: float = Field(
        ...,
        description="Present value (loan principal)",
        json_schema_extra={"example": 200000}
    )
    fv: float = Field(
        default=0.0,
        description="Future value (balloon payment, 0 for fully amortizing loan)"
    )
    payment_type: Literal["end", "beginning"] = Field(
        default="end",
        description="When payments are due ('end' for end of period, 'beginning' for start)"
    )


class PMTData(BaseModel):
    """PMT result data."""
    
    payment: float = Field(..., description="Payment amount per period (negative = outflow)")
    total_payments: float = Field(..., description="Total of all payments")
    total_interest: float = Field(..., description="Total interest paid")
    principal: float = Field(..., description="Original principal")
    periods: int = Field(..., description="Number of periods")
    rate_per_period: float = Field(..., description="Interest rate per period")


class PMTResponse(BaseModel):
    """Response model for PMT calculation."""
    
    success: bool
    data: PMTData
    request_id: Optional[str] = None
    timestamp: str


class FinancialResult(BaseModel):
    """Generic financial calculation result."""
    
    result: float = Field(..., description="Calculation result")
    formula: str = Field(..., description="Formula used")
    inputs: dict[str, Any] = Field(..., description="Input values")


class FVRequest(BaseModel):
    """Request model for Future Value calculation."""
    
    rate: float = Field(
        ...,
        description="Interest rate per period",
        ge=0.0,
        le=1.0
    )
    nper: int = Field(
        ...,
        description="Number of periods",
        ge=1,
        le=1200
    )
    pmt: float = Field(
        default=0.0,
        description="Payment per period"
    )
    pv: float = Field(
        default=0.0,
        description="Present value"
    )
    payment_type: Literal["end", "beginning"] = Field(
        default="end",
        description="When payments are due"
    )


class PVRequest(BaseModel):
    """Request model for Present Value calculation."""
    
    rate: float = Field(
        ...,
        description="Interest rate per period",
        ge=0.0,
        le=1.0
    )
    nper: int = Field(
        ...,
        description="Number of periods",
        ge=1,
        le=1200
    )
    pmt: float = Field(
        default=0.0,
        description="Payment per period"
    )
    fv: float = Field(
        default=0.0,
        description="Future value"
    )
    payment_type: Literal["end", "beginning"] = Field(
        default="end",
        description="When payments are due"
    )


class AmortizationRequest(BaseModel):
    """Request model for amortization schedule."""
    
    principal: float = Field(
        ...,
        description="Loan principal",
        gt=0
    )
    annual_rate: float = Field(
        ...,
        description="Annual interest rate (as decimal)",
        ge=0.0,
        le=1.0
    )
    periods: int = Field(
        ...,
        description="Number of payment periods",
        ge=1,
        le=1200
    )
    periods_per_year: int = Field(
        default=12,
        description="Payment frequency per year",
        ge=1,
        le=365
    )


class AmortizationRow(BaseModel):
    """Single row in amortization schedule."""
    
    period: int = Field(..., description="Period number")
    payment: float = Field(..., description="Total payment")
    principal_payment: float = Field(..., description="Principal portion")
    interest_payment: float = Field(..., description="Interest portion")
    principal_balance: float = Field(..., description="Remaining balance")
    cumulative_interest: float = Field(..., description="Total interest paid to date")


class AmortizationData(BaseModel):
    """Amortization schedule data."""
    
    schedule: list[AmortizationRow] = Field(..., description="Payment schedule")
    summary: dict[str, float] = Field(
        ...,
        description="Summary statistics",
        json_schema_extra={
            "example": {
                "total_payments": 360000,
                "total_interest": 160000,
                "monthly_payment": 1000
            }
        }
    )
