"""
Pydantic models for the Math Service.
"""
from src.models.base import BaseResponse, ErrorDetail
from src.models.calculate import (
    CalculateRequest,
    CalculateResponse,
)
from src.models.statistics import (
    DescribeRequest,
    DescribeResponse,
    StatisticsData,
    CorrelationRequest,
    CorrelationResponse,
    RegressionRequest,
    RegressionResponse,
    RegressionResult,
)
from src.models.excel import (
    VLookupRequest,
    VLookupResponse,
    SumIfRequest,
    SumIfResponse,
    PivotRequest,
    PivotResponse,
)
from src.models.finance import (
    NPVRequest,
    NPVResponse,
    IRRRequest,
    IRRResponse,
    PMTRequest,
    PMTResponse,
    FinancialResult,
)

__all__ = [
    # Base
    "BaseResponse",
    "ErrorDetail",
    # Calculate
    "CalculateRequest",
    "CalculateResponse",
    # Statistics
    "DescribeRequest",
    "DescribeResponse",
    "StatisticsData",
    "CorrelationRequest",
    "CorrelationResponse",
    "RegressionRequest",
    "RegressionResponse",
    "RegressionResult",
    # Excel
    "VLookupRequest",
    "VLookupResponse",
    "SumIfRequest",
    "SumIfResponse",
    "PivotRequest",
    "PivotResponse",
    # Finance
    "NPVRequest",
    "NPVResponse",
    "IRRRequest",
    "IRRResponse",
    "PMTRequest",
    "PMTResponse",
    "FinancialResult",
]
