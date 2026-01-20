"""
Statistics calculation routes.
"""
from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from datetime import datetime
from loguru import logger

router = APIRouter()


class StatisticsRequest(BaseModel):
    """Request model for statistics calculation."""
    data: List[float] = Field(..., description="Array of numbers to analyze", min_length=1, max_length=10000)
    operations: List[str] = Field(
        default=["mean", "median", "stddev"],
        description="Statistical operations to perform"
    )


class StatisticsResponse(BaseModel):
    """Response model for statistics."""
    success: bool
    data: Dict[str, Any]
    request_id: Optional[str] = None
    timestamp: str


class PercentileRequest(BaseModel):
    """Request model for percentile calculation."""
    data: List[float] = Field(..., min_length=1, max_length=10000)
    percentiles: List[float] = Field(..., description="Percentiles to calculate (0-100)")


class CorrelationRequest(BaseModel):
    """Request model for correlation calculation."""
    x: List[float] = Field(..., min_length=2, max_length=10000)
    y: List[float] = Field(..., min_length=2, max_length=10000)
    method: str = Field(default="pearson", description="Correlation method: pearson, spearman, kendall")


SUPPORTED_OPERATIONS = {
    "mean": lambda arr: float(np.mean(arr)),
    "median": lambda arr: float(np.median(arr)),
    "mode": lambda arr: float(stats.mode(arr, keepdims=True).mode[0]),
    "stddev": lambda arr: float(np.std(arr)),
    "variance": lambda arr: float(np.var(arr)),
    "min": lambda arr: float(np.min(arr)),
    "max": lambda arr: float(np.max(arr)),
    "sum": lambda arr: float(np.sum(arr)),
    "count": lambda arr: len(arr),
    "range": lambda arr: float(np.max(arr) - np.min(arr)),
    "q1": lambda arr: float(np.percentile(arr, 25)),
    "q2": lambda arr: float(np.percentile(arr, 50)),
    "q3": lambda arr: float(np.percentile(arr, 75)),
    "iqr": lambda arr: float(np.percentile(arr, 75) - np.percentile(arr, 25)),
    "skewness": lambda arr: float(stats.skew(arr)),
    "kurtosis": lambda arr: float(stats.kurtosis(arr)),
    "sem": lambda arr: float(stats.sem(arr)),  # Standard error of mean
}


@router.post("/statistics")
async def calculate_statistics(request: Request, body: StatisticsRequest):
    """
    Calculate statistical measures for a dataset.
    
    Available operations: mean, median, mode, stddev, variance, min, max, sum, count,
    range, q1, q2, q3, iqr, skewness, kurtosis, sem
    """
    try:
        arr = np.array(body.data)
        results = {"count": len(body.data)}
        
        for op in body.operations:
            op_lower = op.lower()
            if op_lower in SUPPORTED_OPERATIONS:
                try:
                    results[op_lower] = round(SUPPORTED_OPERATIONS[op_lower](arr), 10)
                except Exception as e:
                    results[op_lower] = {"error": str(e)}
            else:
                results[op_lower] = {"error": f"Unknown operation: {op}"}
        
        return StatisticsResponse(
            success=True,
            data=results,
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        return StatisticsResponse(
            success=False,
            data={"error": str(e)},
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@router.post("/percentile")
async def calculate_percentiles(request: Request, body: PercentileRequest):
    """Calculate specific percentiles for a dataset."""
    try:
        arr = np.array(body.data)
        results = {}
        
        for p in body.percentiles:
            if 0 <= p <= 100:
                results[f"p{int(p)}"] = round(float(np.percentile(arr, p)), 10)
            else:
                results[f"p{int(p)}"] = {"error": "Percentile must be between 0 and 100"}
        
        return StatisticsResponse(
            success=True,
            data=results,
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        return StatisticsResponse(
            success=False,
            data={"error": str(e)},
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@router.post("/correlation")
async def calculate_correlation(request: Request, body: CorrelationRequest):
    """Calculate correlation between two arrays."""
    try:
        if len(body.x) != len(body.y):
            raise ValueError("Arrays must have the same length")
        
        x = np.array(body.x)
        y = np.array(body.y)
        
        if body.method == "pearson":
            correlation, p_value = stats.pearsonr(x, y)
        elif body.method == "spearman":
            correlation, p_value = stats.spearmanr(x, y)
        elif body.method == "kendall":
            correlation, p_value = stats.kendalltau(x, y)
        else:
            raise ValueError(f"Unknown method: {body.method}")
        
        return StatisticsResponse(
            success=True,
            data={
                "correlation": round(float(correlation), 10),
                "p_value": round(float(p_value), 10),
                "method": body.method,
            },
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        return StatisticsResponse(
            success=False,
            data={"error": str(e)},
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@router.get("/statistics/operations")
async def list_operations():
    """List all supported statistical operations."""
    return {
        "success": True,
        "data": {
            "operations": list(SUPPORTED_OPERATIONS.keys()),
            "correlation_methods": ["pearson", "spearman", "kendall"],
            "regression_models": ["linear", "polynomial", "exponential", "logarithmic"],
        },
    }


class DescribeRequest(BaseModel):
    """Request model for statistical description."""
    data: List[float] = Field(..., min_length=1, max_length=100000, description="Array of numbers to analyze")


@router.post("/stats/describe")
async def describe_statistics(request: Request, body: DescribeRequest):
    """
    Generate comprehensive statistical description of a dataset.
    
    Returns: mean, median, std, min, max, quartiles, skewness, kurtosis, and more.
    """
    try:
        arr = np.array(body.data)
        n = len(arr)
        
        # Basic statistics
        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))
        std_val = float(np.std(arr, ddof=1))  # Sample std
        variance_val = float(np.var(arr, ddof=1))  # Sample variance
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        range_val = max_val - min_val
        sum_val = float(np.sum(arr))
        
        # Quartiles
        q1 = float(np.percentile(arr, 25))
        q2 = float(np.percentile(arr, 50))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        
        # Advanced statistics
        skewness = float(stats.skew(arr)) if n >= 3 else None
        kurtosis_val = float(stats.kurtosis(arr)) if n >= 4 else None
        sem = float(stats.sem(arr)) if n >= 2 else None
        
        # Outlier detection (using IQR method)
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        outliers = [float(x) for x in arr if x < lower_fence or x > upper_fence]
        
        result = {
            "count": n,
            "mean": round(mean_val, 10),
            "median": round(median_val, 10),
            "std": round(std_val, 10),
            "variance": round(variance_val, 10),
            "min": round(min_val, 10),
            "max": round(max_val, 10),
            "range": round(range_val, 10),
            "sum": round(sum_val, 10),
            "quartiles": {
                "q1": round(q1, 10),
                "q2": round(q2, 10),
                "q3": round(q3, 10),
                "iqr": round(iqr, 10),
            },
            "skewness": round(skewness, 10) if skewness is not None else None,
            "kurtosis": round(kurtosis_val, 10) if kurtosis_val is not None else None,
            "sem": round(sem, 10) if sem is not None else None,
            "outliers": {
                "count": len(outliers),
                "lower_fence": round(lower_fence, 10),
                "upper_fence": round(upper_fence, 10),
                "values": outliers[:20] if len(outliers) > 20 else outliers,  # Limit outliers shown
            },
        }
        
        return {
            "success": True,
            "data": result,
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"Describe error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


class RegressionRequest(BaseModel):
    """Request model for regression analysis."""
    x: List[float] = Field(..., min_length=2, max_length=100000, description="Independent variable")
    y: List[float] = Field(..., min_length=2, max_length=100000, description="Dependent variable")
    model: Literal["linear", "polynomial", "exponential", "logarithmic"] = Field(
        default="linear",
        description="Regression model type"
    )
    degree: int = Field(default=2, ge=2, le=10, description="Polynomial degree (only for polynomial)")
    include_predictions: bool = Field(default=True, description="Include predicted values in response")


@router.post("/stats/correlation")
async def stats_correlation(request: Request, body: CorrelationRequest):
    """
    Calculate correlation between two arrays with additional statistics.
    """
    try:
        if len(body.x) != len(body.y):
            raise ValueError("Arrays must have the same length")
        
        x = np.array(body.x)
        y = np.array(body.y)
        n = len(x)
        
        if body.method == "pearson":
            correlation, p_value = stats.pearsonr(x, y)
        elif body.method == "spearman":
            correlation, p_value = stats.spearmanr(x, y)
        elif body.method == "kendall":
            correlation, p_value = stats.kendalltau(x, y)
        else:
            raise ValueError(f"Unknown method: {body.method}")
        
        # Coefficient of determination
        r_squared = correlation ** 2
        
        # Determine strength and direction
        abs_corr = abs(correlation)
        if abs_corr >= 0.9:
            strength = "very strong"
        elif abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.5:
            strength = "moderate"
        elif abs_corr >= 0.3:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if correlation > 0 else "negative" if correlation < 0 else "none"
        
        return {
            "success": True,
            "data": {
                "correlation": round(float(correlation), 10),
                "p_value": round(float(p_value), 10),
                "r_squared": round(float(r_squared), 10),
                "method": body.method,
                "n": n,
                "strength": strength,
                "direction": direction,
                "significant": bool(p_value < 0.05),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"Correlation error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/regression")
async def regression_analysis(request: Request, body: RegressionRequest):
    """
    Perform regression analysis.
    
    Supports linear, polynomial, exponential, and logarithmic regression.
    """
    try:
        if len(body.x) != len(body.y):
            raise ValueError("Arrays must have the same length")
        
        x = np.array(body.x)
        y = np.array(body.y)
        n = len(x)
        
        predictions = None
        residuals = None
        equation = ""
        coefficients = []
        
        if body.model == "linear":
            # Linear regression: y = mx + b
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            coefficients = [round(slope, 10), round(intercept, 10)]
            r_squared = r_value ** 2
            
            if body.include_predictions:
                predictions = [round(slope * xi + intercept, 10) for xi in x]
                residuals = [round(yi - pi, 10) for yi, pi in zip(y, predictions)]
            
            # Format equation
            sign = "+" if intercept >= 0 else "-"
            equation = f"y = {slope:.6f}x {sign} {abs(intercept):.6f}"
            
        elif body.model == "polynomial":
            # Polynomial regression: y = a_n*x^n + ... + a_1*x + a_0
            coeffs = np.polyfit(x, y, body.degree)
            coefficients = [round(c, 10) for c in coeffs]
            
            # Calculate R-squared
            poly_func = np.poly1d(coeffs)
            y_pred = poly_func(x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            if body.include_predictions:
                predictions = [round(float(p), 10) for p in y_pred]
                residuals = [round(float(yi - pi), 10) for yi, pi in zip(y, y_pred)]
            
            # Format equation
            terms = []
            for i, c in enumerate(coeffs):
                power = body.degree - i
                if power == 0:
                    terms.append(f"{c:.6f}")
                elif power == 1:
                    terms.append(f"{c:.6f}x")
                else:
                    terms.append(f"{c:.6f}x^{power}")
            equation = "y = " + " + ".join(terms)
            
            p_value = None
            std_err = None
            
        elif body.model == "exponential":
            # Exponential regression: y = a * e^(bx)
            # Transform to linear: ln(y) = ln(a) + bx
            y_positive = y[y > 0]
            x_positive = x[y > 0]
            
            if len(y_positive) < 2:
                raise ValueError("Exponential regression requires positive y values")
            
            log_y = np.log(y_positive)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_positive, log_y)
            
            a = np.exp(intercept)
            b = slope
            coefficients = [round(a, 10), round(b, 10)]
            r_squared = r_value ** 2
            
            if body.include_predictions:
                predictions = [round(float(a * np.exp(b * xi)), 10) for xi in x]
                residuals = [round(float(yi - pi), 10) for yi, pi in zip(y, predictions)]
            
            equation = f"y = {a:.6f} * e^({b:.6f}x)"
            
        elif body.model == "logarithmic":
            # Logarithmic regression: y = a * ln(x) + b
            x_positive = x[x > 0]
            y_positive = y[x > 0]
            
            if len(x_positive) < 2:
                raise ValueError("Logarithmic regression requires positive x values")
            
            log_x = np.log(x_positive)
            slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, y_positive)
            
            coefficients = [round(slope, 10), round(intercept, 10)]
            r_squared = r_value ** 2
            
            if body.include_predictions:
                predictions = []
                for xi in x:
                    if xi > 0:
                        predictions.append(round(float(slope * np.log(xi) + intercept), 10))
                    else:
                        predictions.append(None)
                residuals = [round(float(yi - pi), 10) if pi is not None else None for yi, pi in zip(y, predictions)]
            
            sign = "+" if intercept >= 0 else "-"
            equation = f"y = {slope:.6f} * ln(x) {sign} {abs(intercept):.6f}"
        
        else:
            raise ValueError(f"Unknown model: {body.model}")
        
        # Calculate adjusted R-squared
        if body.model == "polynomial":
            k = body.degree
        else:
            k = 1  # Number of predictors
        
        adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1) if n > k + 1 else None
        
        result = {
            "model": body.model,
            "coefficients": coefficients,
            "r_squared": round(float(r_squared), 10),
            "adjusted_r_squared": round(float(adjusted_r_squared), 10) if adjusted_r_squared else None,
            "equation": equation,
            "n": n,
        }
        
        if std_err is not None:
            result["std_error"] = round(float(std_err), 10)
        if p_value is not None:
            result["p_value"] = round(float(p_value), 10)
        if predictions is not None:
            result["predictions"] = predictions
        if residuals is not None:
            result["residuals"] = residuals
        
        return {
            "success": True,
            "data": result,
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"Regression error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# ============================================================================
# RANKING FUNCTIONS
# ============================================================================

@router.post("/stats/rank")
async def stat_rank(
    request: Request, 
    data: List[float], 
    value: float,
    order: int = 0
):
    """
    RANK - Returns the rank of a number in a list.
    
    Excel equivalent: =RANK(number, ref, [order])
    
    order:
    - 0: Descending order (largest = 1)
    - 1: Ascending order (smallest = 1)
    """
    try:
        if value not in data:
            raise ValueError(f"Value {value} not found in data")
        
        if order == 0:
            # Descending: count how many are greater + 1
            rank = sum(1 for x in data if x > value) + 1
        else:
            # Ascending: count how many are smaller + 1
            rank = sum(1 for x in data if x < value) + 1
        
        return {
            "success": True,
            "data": {
                "rank": rank,
                "value": value,
                "total": len(data),
                "order": "descending" if order == 0 else "ascending",
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"RANK error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/large")
async def stat_large(request: Request, data: List[float], k: int):
    """
    LARGE - Returns the k-th largest value.
    
    Excel equivalent: =LARGE(array, k)
    """
    try:
        if k < 1 or k > len(data):
            raise ValueError(f"k must be between 1 and {len(data)}")
        
        sorted_data = sorted(data, reverse=True)
        result = sorted_data[k - 1]
        
        return {
            "success": True,
            "data": {
                "result": result,
                "k": k,
                "position": f"{k}th largest",
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"LARGE error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/small")
async def stat_small(request: Request, data: List[float], k: int):
    """
    SMALL - Returns the k-th smallest value.
    
    Excel equivalent: =SMALL(array, k)
    """
    try:
        if k < 1 or k > len(data):
            raise ValueError(f"k must be between 1 and {len(data)}")
        
        sorted_data = sorted(data)
        result = sorted_data[k - 1]
        
        return {
            "success": True,
            "data": {
                "result": result,
                "k": k,
                "position": f"{k}th smallest",
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"SMALL error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/frequency")
async def stat_frequency(request: Request, data: List[float], bins: List[float]):
    """
    FREQUENCY - Returns the frequency distribution of values.
    
    Excel equivalent: =FREQUENCY(data_array, bins_array)
    """
    try:
        bins_sorted = sorted(bins)
        counts = [0] * (len(bins_sorted) + 1)
        
        for val in data:
            placed = False
            for i, bin_val in enumerate(bins_sorted):
                if val <= bin_val:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1
        
        result = []
        for i, count in enumerate(counts[:-1]):
            if i == 0:
                result.append({"bin": f"<= {bins_sorted[i]}", "count": count})
            else:
                result.append({"bin": f"{bins_sorted[i-1]} < x <= {bins_sorted[i]}", "count": count})
        result.append({"bin": f"> {bins_sorted[-1]}", "count": counts[-1]})
        
        return {
            "success": True,
            "data": {
                "frequencies": result,
                "counts": counts,
                "bins": bins_sorted,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"FREQUENCY error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/quartile")
async def stat_quartile(request: Request, data: List[float], quart: int):
    """
    QUARTILE - Returns the specified quartile of a data set.
    
    Excel equivalent: =QUARTILE(array, quart)
    
    quart:
    - 0: Minimum
    - 1: 25th percentile (Q1)
    - 2: 50th percentile (median)
    - 3: 75th percentile (Q3)
    - 4: Maximum
    """
    try:
        if quart < 0 or quart > 4:
            raise ValueError("quart must be 0, 1, 2, 3, or 4")
        
        arr = np.array(data)
        
        if quart == 0:
            result = float(np.min(arr))
            label = "minimum"
        elif quart == 1:
            result = float(np.percentile(arr, 25))
            label = "Q1 (25th percentile)"
        elif quart == 2:
            result = float(np.percentile(arr, 50))
            label = "Q2 (median)"
        elif quart == 3:
            result = float(np.percentile(arr, 75))
            label = "Q3 (75th percentile)"
        else:
            result = float(np.max(arr))
            label = "maximum"
        
        return {
            "success": True,
            "data": {
                "result": round(result, 10),
                "quartile": quart,
                "label": label,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"QUARTILE error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/forecast")
async def stat_forecast(request: Request, x: float, known_y: List[float], known_x: List[float]):
    """
    FORECAST - Predicts a value based on linear regression.
    
    Excel equivalent: =FORECAST(x, known_y's, known_x's)
    """
    try:
        if len(known_x) != len(known_y):
            raise ValueError("known_x and known_y must have the same length")
        
        arr_x = np.array(known_x)
        arr_y = np.array(known_y)
        
        slope, intercept, r_value, _, _ = stats.linregress(arr_x, arr_y)
        result = slope * x + intercept
        
        return {
            "success": True,
            "data": {
                "forecast": round(float(result), 10),
                "x": x,
                "slope": round(float(slope), 10),
                "intercept": round(float(intercept), 10),
                "r_squared": round(float(r_value ** 2), 10),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"FORECAST error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/trend")
async def stat_trend(request: Request, known_y: List[float], known_x: List[float], new_x: List[float]):
    """
    TREND - Returns values along a linear trend.
    
    Excel equivalent: =TREND(known_y's, known_x's, new_x's)
    """
    try:
        if len(known_x) != len(known_y):
            raise ValueError("known_x and known_y must have the same length")
        
        arr_x = np.array(known_x)
        arr_y = np.array(known_y)
        
        slope, intercept, r_value, _, _ = stats.linregress(arr_x, arr_y)
        
        predictions = [round(float(slope * xi + intercept), 10) for xi in new_x]
        
        return {
            "success": True,
            "data": {
                "trend": predictions,
                "slope": round(float(slope), 10),
                "intercept": round(float(intercept), 10),
                "r_squared": round(float(r_value ** 2), 10),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"TREND error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/stats/confidence")
async def stat_confidence(request: Request, alpha: float, stddev: float, size: int):
    """
    CONFIDENCE - Returns the confidence interval for a population mean.
    
    Excel equivalent: =CONFIDENCE(alpha, standard_dev, size)
    """
    try:
        if alpha <= 0 or alpha >= 1:
            raise ValueError("alpha must be between 0 and 1")
        if stddev <= 0:
            raise ValueError("standard deviation must be positive")
        if size < 1:
            raise ValueError("size must be at least 1")
        
        z_score = stats.norm.ppf(1 - alpha / 2)
        margin = z_score * stddev / np.sqrt(size)
        
        return {
            "success": True,
            "data": {
                "confidence_margin": round(float(margin), 10),
                "alpha": alpha,
                "z_score": round(float(z_score), 10),
                "confidence_level": f"{(1 - alpha) * 100}%",
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"CONFIDENCE error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }