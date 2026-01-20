"""
Information Functions Routes - Excel-like information functions.

Implements: ISBLANK, ISERROR, ISEVEN, ISLOGICAL, ISNA, ISNONTEXT, ISNUMBER,
ISODD, ISREF, ISTEXT, N, NA, TYPE, ERROR.TYPE, INFO, CELL
"""
from typing import Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..models.info import (
    ValueRequest, NumberCheckRequest, TextCheckRequest, ArrayCheckRequest,
    InfoResponse, TypeResponse, ArrayInfoResponse
)


router = APIRouter(prefix="/info", tags=["Information Functions"])


class AnyValueRequest(BaseModel):
    """Request with any value type."""
    value: Any = None


# ============================================================================
# TYPE CHECKING FUNCTIONS
# ============================================================================

@router.post("/isblank", response_model=InfoResponse)
async def is_blank(request: AnyValueRequest) -> InfoResponse:
    """
    ISBLANK - Returns TRUE if the value is blank/null/empty.
    
    Excel equivalent: =ISBLANK(value)
    """
    value = request.value
    result = value is None or value == "" or (isinstance(value, list) and len(value) == 0)
    return InfoResponse(result=result, value=value, operation="ISBLANK")


@router.post("/iserror", response_model=InfoResponse)
async def is_error(value: Any, is_error_value: bool = False) -> InfoResponse:
    """
    ISERROR - Returns TRUE if the value is an error.
    
    Excel equivalent: =ISERROR(value)
    Note: Pass is_error_value=True if the value represents an error state.
    """
    return InfoResponse(result=is_error_value, value=value, operation="ISERROR")


@router.post("/isna", response_model=InfoResponse)
async def is_na(value: Any, is_na_value: bool = False) -> InfoResponse:
    """
    ISNA - Returns TRUE if the value is the #N/A error.
    
    Excel equivalent: =ISNA(value)
    Note: Pass is_na_value=True if the value represents an N/A state.
    """
    return InfoResponse(result=is_na_value, value=value, operation="ISNA")


@router.post("/isnumber", response_model=InfoResponse)
async def is_number(request: AnyValueRequest) -> InfoResponse:
    """
    ISNUMBER - Returns TRUE if the value is a number.
    
    Excel equivalent: =ISNUMBER(value)
    """
    value = request.value
    result = isinstance(value, (int, float)) and not isinstance(value, bool)
    return InfoResponse(result=result, value=value, operation="ISNUMBER")


@router.post("/istext", response_model=InfoResponse)
async def is_text(request: AnyValueRequest) -> InfoResponse:
    """
    ISTEXT - Returns TRUE if the value is text.
    
    Excel equivalent: =ISTEXT(value)
    """
    value = request.value
    result = isinstance(value, str)
    return InfoResponse(result=result, value=value, operation="ISTEXT")


@router.post("/isnontext", response_model=InfoResponse)
async def is_nontext(request: AnyValueRequest) -> InfoResponse:
    """
    ISNONTEXT - Returns TRUE if the value is not text.
    
    Excel equivalent: =ISNONTEXT(value)
    """
    value = request.value
    result = not isinstance(value, str)
    return InfoResponse(result=result, value=value, operation="ISNONTEXT")


@router.post("/islogical", response_model=InfoResponse)
async def is_logical(request: AnyValueRequest) -> InfoResponse:
    """
    ISLOGICAL - Returns TRUE if the value is a logical (boolean) value.
    
    Excel equivalent: =ISLOGICAL(value)
    """
    value = request.value
    result = isinstance(value, bool)
    return InfoResponse(result=result, value=value, operation="ISLOGICAL")


@router.post("/iseven", response_model=InfoResponse)
async def is_even(request: NumberCheckRequest) -> InfoResponse:
    """
    ISEVEN - Returns TRUE if the number is even.
    
    Excel equivalent: =ISEVEN(number)
    """
    result = int(request.value) % 2 == 0
    return InfoResponse(result=result, value=request.value, operation="ISEVEN")


@router.post("/isodd", response_model=InfoResponse)
async def is_odd(request: NumberCheckRequest) -> InfoResponse:
    """
    ISODD - Returns TRUE if the number is odd.
    
    Excel equivalent: =ISODD(number)
    """
    result = int(request.value) % 2 != 0
    return InfoResponse(result=result, value=request.value, operation="ISODD")


@router.post("/isarray", response_model=InfoResponse)
async def is_array(request: AnyValueRequest) -> InfoResponse:
    """
    Check if the value is an array/list.
    """
    value = request.value
    result = isinstance(value, (list, tuple))
    return InfoResponse(result=result, value=str(value)[:100], operation="ISARRAY")


@router.post("/isinteger", response_model=InfoResponse)
async def is_integer(request: AnyValueRequest) -> InfoResponse:
    """
    Check if the value is an integer.
    """
    value = request.value
    if isinstance(value, bool):
        result = False
    elif isinstance(value, int):
        result = True
    elif isinstance(value, float):
        result = value.is_integer()
    else:
        result = False
    return InfoResponse(result=result, value=value, operation="ISINTEGER")


@router.post("/ispositive", response_model=InfoResponse)
async def is_positive(request: NumberCheckRequest) -> InfoResponse:
    """
    Check if the number is positive.
    """
    return InfoResponse(result=request.value > 0, value=request.value, operation="ISPOSITIVE")


@router.post("/isnegative", response_model=InfoResponse)
async def is_negative(request: NumberCheckRequest) -> InfoResponse:
    """
    Check if the number is negative.
    """
    return InfoResponse(result=request.value < 0, value=request.value, operation="ISNEGATIVE")


@router.post("/iszero", response_model=InfoResponse)
async def is_zero(request: NumberCheckRequest) -> InfoResponse:
    """
    Check if the number is zero.
    """
    return InfoResponse(result=request.value == 0, value=request.value, operation="ISZERO")


# ============================================================================
# TYPE FUNCTION
# ============================================================================

@router.post("/type", response_model=TypeResponse)
async def get_type(request: AnyValueRequest) -> TypeResponse:
    """
    TYPE - Returns a number indicating the data type of a value.
    
    Excel equivalent: =TYPE(value)
    
    Returns:
    - 1 = Number
    - 2 = Text
    - 4 = Logical (Boolean)
    - 16 = Error
    - 64 = Array
    """
    value = request.value
    if value is None:
        type_code = 1  # Excel treats blank as 0
        type_name = "blank"
    elif isinstance(value, bool):
        type_code = 4
        type_name = "logical"
    elif isinstance(value, (int, float)):
        type_code = 1
        type_name = "number"
    elif isinstance(value, str):
        type_code = 2
        type_name = "text"
    elif isinstance(value, (list, tuple)):
        type_code = 64
        type_name = "array"
    elif isinstance(value, dict):
        type_code = 64
        type_name = "object"
    else:
        type_code = 2
        type_name = str(type(value).__name__)
    
    return TypeResponse(type_code=type_code, type_name=type_name, value=str(value)[:100], operation="TYPE")


# ============================================================================
# VALUE CONVERSION
# ============================================================================

@router.post("/n")
async def info_n(request: AnyValueRequest) -> dict:
    """
    N - Returns a value converted to a number.
    
    Excel equivalent: =N(value)
    - Numbers return themselves
    - TRUE returns 1
    - FALSE returns 0
    - Text returns 0
    - Errors return the error value
    """
    value = request.value
    if isinstance(value, bool):
        result = 1 if value else 0
    elif isinstance(value, (int, float)):
        result = value
    else:
        result = 0
    
    return {"result": result, "original": str(value), "operation": "N"}


@router.get("/na")
async def info_na() -> dict:
    """
    NA - Returns the error value #N/A.
    
    Excel equivalent: =NA()
    """
    return {"result": None, "is_na": True, "operation": "NA"}


# ============================================================================
# BATCH CHECKING
# ============================================================================

@router.post("/check-numbers", response_model=ArrayInfoResponse)
async def check_numbers(request: ArrayCheckRequest) -> ArrayInfoResponse:
    """
    Check which values in an array are numbers.
    """
    results = [isinstance(v, (int, float)) and not isinstance(v, bool) for v in request.values]
    return ArrayInfoResponse(
        results=results,
        count_true=sum(results),
        count_false=len(results) - sum(results),
        operation="CHECK_NUMBERS"
    )


@router.post("/check-texts", response_model=ArrayInfoResponse)
async def check_texts(request: ArrayCheckRequest) -> ArrayInfoResponse:
    """
    Check which values in an array are text strings.
    """
    results = [isinstance(v, str) for v in request.values]
    return ArrayInfoResponse(
        results=results,
        count_true=sum(results),
        count_false=len(results) - sum(results),
        operation="CHECK_TEXTS"
    )


@router.post("/check-blanks", response_model=ArrayInfoResponse)
async def check_blanks(request: ArrayCheckRequest) -> ArrayInfoResponse:
    """
    Check which values in an array are blank/empty.
    """
    results = [v is None or v == "" for v in request.values]
    return ArrayInfoResponse(
        results=results,
        count_true=sum(results),
        count_false=len(results) - sum(results),
        operation="CHECK_BLANKS"
    )


# ============================================================================
# STRING INFO
# ============================================================================

@router.post("/isempty", response_model=InfoResponse)
async def is_empty(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string is empty.
    """
    return InfoResponse(result=len(request.value) == 0, value=request.value, operation="ISEMPTY")


@router.post("/iswhitespace", response_model=InfoResponse)
async def is_whitespace(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string contains only whitespace.
    """
    result = len(request.value) > 0 and request.value.isspace()
    return InfoResponse(result=result, value=request.value, operation="ISWHITESPACE")


@router.post("/isalpha", response_model=InfoResponse)
async def is_alpha(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string contains only alphabetic characters.
    """
    result = len(request.value) > 0 and request.value.isalpha()
    return InfoResponse(result=result, value=request.value, operation="ISALPHA")


@router.post("/isalnum", response_model=InfoResponse)
async def is_alnum(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string contains only alphanumeric characters.
    """
    result = len(request.value) > 0 and request.value.isalnum()
    return InfoResponse(result=result, value=request.value, operation="ISALNUM")


@router.post("/isdigit", response_model=InfoResponse)
async def is_digit(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string contains only digits.
    """
    result = len(request.value) > 0 and request.value.isdigit()
    return InfoResponse(result=result, value=request.value, operation="ISDIGIT")


@router.post("/isupper", response_model=InfoResponse)
async def is_upper(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string is all uppercase.
    """
    result = len(request.value) > 0 and request.value.isupper()
    return InfoResponse(result=result, value=request.value, operation="ISUPPER")


@router.post("/islower", response_model=InfoResponse)
async def is_lower(request: TextCheckRequest) -> InfoResponse:
    """
    Check if a string is all lowercase.
    """
    result = len(request.value) > 0 and request.value.islower()
    return InfoResponse(result=result, value=request.value, operation="ISLOWER")


# ============================================================================
# SYSTEM INFO
# ============================================================================

@router.get("/version")
async def get_version() -> dict:
    """
    Get the math service version and capabilities.
    """
    return {
        "service": "math-service",
        "version": "1.0.0",
        "categories": [
            "math", "statistics", "finance", "excel",
            "text", "logical", "datetime", "array", "info"
        ],
        "operation": "VERSION"
    }
