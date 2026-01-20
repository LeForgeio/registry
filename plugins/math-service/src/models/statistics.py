"""
Pydantic models for statistics endpoints.
"""
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class DescribeRequest(BaseModel):
    """Request model for statistical description."""
    
    data: list[float] = Field(
        ...,
        description="Array of numbers to analyze",
        min_length=1,
        max_length=100000,
        json_schema_extra={"example": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
    )


class StatisticsData(BaseModel):
    """Statistical description data."""
    
    count: int = Field(..., description="Number of data points")
    mean: float = Field(..., description="Arithmetic mean")
    median: float = Field(..., description="Median value")
    std: float = Field(..., description="Standard deviation")
    variance: float = Field(..., description="Variance")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    range: float = Field(..., description="Range (max - min)")
    sum: float = Field(..., description="Sum of all values")
    quartiles: dict[str, float] = Field(
        ...,
        description="Quartile values (q1, q2, q3, iqr)",
        json_schema_extra={"example": {"q1": 2.5, "q2": 5.5, "q3": 7.5, "iqr": 5.0}}
    )
    skewness: float = Field(..., description="Skewness (measure of asymmetry)")
    kurtosis: float = Field(..., description="Kurtosis (measure of tailedness)")


class DescribeResponse(BaseModel):
    """Response model for describe endpoint."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    data: StatisticsData = Field(..., description="Statistical summary")
    request_id: Optional[str] = Field(default=None)
    timestamp: str = Field(...)


class CorrelationRequest(BaseModel):
    """Request model for correlation calculation."""
    
    x: list[float] = Field(
        ...,
        description="First data array",
        min_length=2,
        max_length=100000
    )
    y: list[float] = Field(
        ...,
        description="Second data array",
        min_length=2,
        max_length=100000
    )
    method: Literal["pearson", "spearman", "kendall"] = Field(
        default="pearson",
        description="Correlation method"
    )


class CorrelationData(BaseModel):
    """Correlation result data."""
    
    correlation: float = Field(..., description="Correlation coefficient (-1 to 1)")
    p_value: float = Field(..., description="Statistical significance (p-value)")
    method: str = Field(..., description="Method used")
    n: int = Field(..., description="Number of data points")


class CorrelationResponse(BaseModel):
    """Response model for correlation calculation."""
    
    success: bool
    data: CorrelationData
    request_id: Optional[str] = None
    timestamp: str


class RegressionRequest(BaseModel):
    """Request model for regression analysis."""
    
    x: list[float] = Field(
        ...,
        description="Independent variable (predictor)",
        min_length=2,
        max_length=100000
    )
    y: list[float] = Field(
        ...,
        description="Dependent variable (response)",
        min_length=2,
        max_length=100000
    )
    model: Literal["linear", "polynomial", "exponential", "logarithmic"] = Field(
        default="linear",
        description="Regression model type"
    )
    degree: int = Field(
        default=2,
        ge=2,
        le=10,
        description="Polynomial degree (only for polynomial regression)"
    )


class RegressionResult(BaseModel):
    """Regression analysis result."""
    
    model: str = Field(..., description="Regression model type")
    coefficients: list[float] = Field(
        ...,
        description="Model coefficients (for linear: [slope, intercept])"
    )
    r_squared: float = Field(..., description="Coefficient of determination (R²)")
    adjusted_r_squared: Optional[float] = Field(
        default=None,
        description="Adjusted R² (accounts for number of predictors)"
    )
    std_error: float = Field(..., description="Standard error of the estimate")
    p_value: Optional[float] = Field(
        default=None,
        description="P-value for the model"
    )
    equation: str = Field(
        ...,
        description="Human-readable equation",
        json_schema_extra={"example": "y = 2.5x + 1.0"}
    )
    predictions: Optional[list[float]] = Field(
        default=None,
        description="Predicted y values"
    )
    residuals: Optional[list[float]] = Field(
        default=None,
        description="Residuals (y - predicted)"
    )


class RegressionResponse(BaseModel):
    """Response model for regression analysis."""
    
    success: bool
    data: dict[str, Any]
    request_id: Optional[str] = None
    timestamp: str
