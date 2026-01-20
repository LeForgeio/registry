"""
Logical Functions Routes - Excel-like logical functions.

Implements: IF, IFS, AND, OR, NOT, XOR, SWITCH, IFERROR, IFNA, TRUE, FALSE, CHOOSE
"""
from typing import Any, List
from fastapi import APIRouter, HTTPException

from ..models.logical import (
    IfRequest, IfsRequest, SwitchRequest, LogicalArrayRequest,
    NotRequest, CompareRequest, IfErrorRequest, ChooseRequest,
    LogicalResponse, BooleanResponse
)


router = APIRouter(prefix="/logical", tags=["Logical Functions"])


# ============================================================================
# BASIC LOGICAL FUNCTIONS
# ============================================================================

@router.post("/if", response_model=LogicalResponse)
async def logical_if(request: IfRequest) -> LogicalResponse:
    """
    IF - Returns one value if a condition is true and another if false.
    
    Excel equivalent: =IF(logical_test, value_if_true, value_if_false)
    """
    result = request.value_if_true if request.condition else request.value_if_false
    return LogicalResponse(result=result, operation="IF")


@router.post("/ifs", response_model=LogicalResponse)
async def logical_ifs(request: IfsRequest) -> LogicalResponse:
    """
    IFS - Checks multiple conditions and returns the value for the first TRUE condition.
    
    Excel equivalent: =IFS(condition1, value1, condition2, value2, ...)
    """
    for pair in request.conditions:
        if pair.condition:
            return LogicalResponse(result=pair.value, operation="IFS")
    
    raise HTTPException(status_code=400, detail="No condition evaluated to TRUE")


@router.post("/switch")
async def logical_switch(expression: Any, cases: dict, default: Any = None) -> LogicalResponse:
    """
    SWITCH - Evaluates an expression against a list of values and returns the result for the first match.
    
    Excel equivalent: =SWITCH(expression, value1, result1, value2, result2, ..., default)
    
    Args:
        expression: Value to match
        cases: Dictionary of {match_value: result}
        default: Default result if no match
    """
    # Convert expression to string for comparison with dict keys
    str_expr = str(expression)
    
    for match_val, result in cases.items():
        if str(match_val) == str_expr or match_val == expression:
            return LogicalResponse(result=result, operation="SWITCH")
    
    if default is not None:
        return LogicalResponse(result=default, operation="SWITCH")
    
    raise HTTPException(status_code=400, detail="No match found and no default specified")


# ============================================================================
# BOOLEAN OPERATIONS
# ============================================================================

@router.post("/and", response_model=BooleanResponse)
async def logical_and(request: LogicalArrayRequest) -> BooleanResponse:
    """
    AND - Returns TRUE if all arguments are TRUE.
    
    Excel equivalent: =AND(logical1, logical2, ...)
    """
    result = all(request.values)
    return BooleanResponse(result=result, operation="AND", inputs=request.values)


@router.post("/or", response_model=BooleanResponse)
async def logical_or(request: LogicalArrayRequest) -> BooleanResponse:
    """
    OR - Returns TRUE if any argument is TRUE.
    
    Excel equivalent: =OR(logical1, logical2, ...)
    """
    result = any(request.values)
    return BooleanResponse(result=result, operation="OR", inputs=request.values)


@router.post("/not", response_model=BooleanResponse)
async def logical_not(request: NotRequest) -> BooleanResponse:
    """
    NOT - Reverses the logic of its argument.
    
    Excel equivalent: =NOT(logical)
    """
    return BooleanResponse(result=not request.value, operation="NOT", inputs=[request.value])


@router.post("/xor", response_model=BooleanResponse)
async def logical_xor(request: LogicalArrayRequest) -> BooleanResponse:
    """
    XOR - Returns TRUE if an odd number of arguments are TRUE.
    
    Excel equivalent: =XOR(logical1, logical2, ...)
    """
    true_count = sum(1 for v in request.values if v)
    result = true_count % 2 == 1
    return BooleanResponse(result=result, operation="XOR", inputs=request.values)


# ============================================================================
# ERROR HANDLING
# ============================================================================

@router.post("/iferror", response_model=LogicalResponse)
async def logical_iferror(request: IfErrorRequest) -> LogicalResponse:
    """
    IFERROR - Returns value_if_error if is_error is True, otherwise returns value.
    
    Excel equivalent: =IFERROR(value, value_if_error)
    
    Note: Since we can't detect runtime errors, use the is_error flag to indicate an error state.
    """
    if request.is_error:
        return LogicalResponse(result=request.value_if_error, operation="IFERROR")
    return LogicalResponse(result=request.value, operation="IFERROR")


@router.post("/ifna", response_model=LogicalResponse)
async def logical_ifna(value: Any, is_na: bool, value_if_na: Any) -> LogicalResponse:
    """
    IFNA - Returns value_if_na if is_na is True, otherwise returns value.
    
    Excel equivalent: =IFNA(value, value_if_na)
    
    Note: Use the is_na flag to indicate an N/A state.
    """
    if is_na:
        return LogicalResponse(result=value_if_na, operation="IFNA")
    return LogicalResponse(result=value, operation="IFNA")


# ============================================================================
# COMPARISON OPERATIONS
# ============================================================================

@router.post("/compare", response_model=BooleanResponse)
async def compare(request: CompareRequest) -> BooleanResponse:
    """
    Compare two values using a specified operator.
    
    Operators:
    - eq: Equal (=)
    - ne: Not equal (<>)
    - gt: Greater than (>)
    - gte: Greater than or equal (>=)
    - lt: Less than (<)
    - lte: Less than or equal (<=)
    """
    v1, v2 = request.value1, request.value2
    op = request.operator.lower()
    
    operators = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
    }
    
    if op not in operators:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown operator '{op}'. Use: eq, ne, gt, gte, lt, lte"
        )
    
    try:
        result = operators[op](v1, v2)
        return BooleanResponse(result=result, operation=f"COMPARE_{op.upper()}", inputs=[])
    except TypeError:
        raise HTTPException(status_code=400, detail=f"Cannot compare {type(v1).__name__} with {type(v2).__name__}")


# ============================================================================
# SELECTION FUNCTIONS
# ============================================================================

@router.post("/choose", response_model=LogicalResponse)
async def logical_choose(request: ChooseRequest) -> LogicalResponse:
    """
    CHOOSE - Returns a value from a list based on index.
    
    Excel equivalent: =CHOOSE(index_num, value1, value2, ...)
    Note: index_num is 1-based (Excel convention)
    """
    if request.index_num > len(request.values):
        raise HTTPException(
            status_code=400, 
            detail=f"Index {request.index_num} is out of range (only {len(request.values)} values)"
        )
    
    result = request.values[request.index_num - 1]
    return LogicalResponse(result=result, operation="CHOOSE")


# ============================================================================
# CONSTANT FUNCTIONS
# ============================================================================

@router.get("/true")
async def logical_true() -> BooleanResponse:
    """
    TRUE - Returns the logical value TRUE.
    
    Excel equivalent: =TRUE()
    """
    return BooleanResponse(result=True, operation="TRUE", inputs=[])


@router.get("/false")
async def logical_false() -> BooleanResponse:
    """
    FALSE - Returns the logical value FALSE.
    
    Excel equivalent: =FALSE()
    """
    return BooleanResponse(result=False, operation="FALSE", inputs=[])


# ============================================================================
# CONDITIONAL AGGREGATION HELPERS
# ============================================================================

@router.post("/count-true", response_model=LogicalResponse)
async def count_true(values: List[bool]) -> LogicalResponse:
    """
    Count the number of TRUE values in a list.
    """
    return LogicalResponse(result=sum(1 for v in values if v), operation="COUNT_TRUE")


@router.post("/count-false", response_model=LogicalResponse)
async def count_false(values: List[bool]) -> LogicalResponse:
    """
    Count the number of FALSE values in a list.
    """
    return LogicalResponse(result=sum(1 for v in values if not v), operation="COUNT_FALSE")


@router.post("/all-true", response_model=BooleanResponse)
async def all_true(values: List[bool]) -> BooleanResponse:
    """
    Check if all values are TRUE (alias for AND).
    """
    return BooleanResponse(result=all(values), operation="ALL_TRUE", inputs=values)


@router.post("/any-true", response_model=BooleanResponse)
async def any_true(values: List[bool]) -> BooleanResponse:
    """
    Check if any value is TRUE (alias for OR).
    """
    return BooleanResponse(result=any(values), operation="ANY_TRUE", inputs=values)


@router.post("/none-true", response_model=BooleanResponse)
async def none_true(values: List[bool]) -> BooleanResponse:
    """
    Check if no values are TRUE.
    """
    return BooleanResponse(result=not any(values), operation="NONE_TRUE", inputs=values)
