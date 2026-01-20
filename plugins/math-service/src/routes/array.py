"""
Array Functions Routes - Excel-like dynamic array functions.

Implements: UNIQUE, SORT, SORTBY, FILTER, SEQUENCE, TRANSPOSE, FLATTEN,
TAKE, DROP, EXPAND, RANDARRAY, and more.
"""
import random
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException

from ..models.array import (
    ArrayRequest, SortRequest, SortByRequest, FilterRequest,
    SequenceRequest, Matrix2DRequest, TakeRequest, DropRequest,
    ChunkRequest, SliceRequest, ExpandRequest, SearchRequest,
    ArrayResponse, Matrix2DResponse, ScalarResponse
)


router = APIRouter(prefix="/array", tags=["Array Functions"])


# ============================================================================
# UNIQUE AND DEDUPLICATION
# ============================================================================

@router.post("/unique", response_model=ArrayResponse)
async def array_unique(request: ArrayRequest) -> ArrayResponse:
    """
    UNIQUE - Returns unique values from an array.
    
    Excel equivalent: =UNIQUE(array)
    Preserves order of first occurrence.
    """
    seen = set()
    result = []
    for item in request.values:
        # Handle unhashable types
        try:
            if item not in seen:
                seen.add(item)
                result.append(item)
        except TypeError:
            # For unhashable items (lists, dicts), use string comparison
            str_item = str(item)
            if str_item not in seen:
                seen.add(str_item)
                result.append(item)
    
    return ArrayResponse(result=result, count=len(result), operation="UNIQUE")


@router.post("/distinct-count", response_model=ScalarResponse)
async def distinct_count(request: ArrayRequest) -> ScalarResponse:
    """
    Count the number of distinct/unique values in an array.
    """
    try:
        result = len(set(request.values))
    except TypeError:
        # For unhashable items
        result = len(set(str(v) for v in request.values))
    
    return ScalarResponse(result=result, operation="DISTINCT_COUNT")


# ============================================================================
# SORTING
# ============================================================================

@router.post("/sort", response_model=ArrayResponse)
async def array_sort(request: SortRequest) -> ArrayResponse:
    """
    SORT - Sorts an array.
    
    Excel equivalent: =SORT(array, [sort_index], [sort_order])
    """
    try:
        result = sorted(request.values, reverse=request.descending)
        return ArrayResponse(result=result, count=len(result), operation="SORT")
    except TypeError:
        raise HTTPException(status_code=400, detail="Cannot compare items of different types")


@router.post("/sortby", response_model=ArrayResponse)
async def array_sortby(request: SortByRequest) -> ArrayResponse:
    """
    SORTBY - Sorts an array based on another array's values.
    
    Excel equivalent: =SORTBY(array, by_array, [sort_order])
    """
    if len(request.values) != len(request.sort_by):
        raise HTTPException(
            status_code=400, 
            detail="values and sort_by arrays must have the same length"
        )
    
    try:
        # Pair values with sort_by, sort, then extract values
        paired = list(zip(request.values, request.sort_by))
        sorted_pairs = sorted(paired, key=lambda x: x[1], reverse=request.descending)
        result = [p[0] for p in sorted_pairs]
        
        return ArrayResponse(result=result, count=len(result), operation="SORTBY")
    except TypeError:
        raise HTTPException(status_code=400, detail="Cannot compare sort_by items")


@router.post("/reverse", response_model=ArrayResponse)
async def array_reverse(request: ArrayRequest) -> ArrayResponse:
    """
    Reverse an array.
    """
    return ArrayResponse(result=list(reversed(request.values)), count=len(request.values), operation="REVERSE")


# ============================================================================
# FILTERING
# ============================================================================

@router.post("/filter", response_model=ArrayResponse)
async def array_filter(request: FilterRequest) -> ArrayResponse:
    """
    FILTER - Filters an array based on criteria.
    
    Excel equivalent: =FILTER(array, include, [if_empty])
    """
    if len(request.values) != len(request.criteria):
        raise HTTPException(
            status_code=400, 
            detail="values and criteria arrays must have the same length"
        )
    
    result = [v for v, c in zip(request.values, request.criteria) if c]
    
    if not result and request.if_empty is not None:
        return ArrayResponse(result=[request.if_empty], count=1, operation="FILTER")
    
    return ArrayResponse(result=result, count=len(result), operation="FILTER")


@router.post("/filter-by-value")
async def filter_by_value(
    values: List[Any], 
    match_value: Any, 
    operator: str = "eq"
) -> ArrayResponse:
    """
    Filter array by comparing to a value.
    
    Operators: eq, ne, gt, gte, lt, lte, contains, starts_with, ends_with
    """
    operators = {
        "eq": lambda v, m: v == m,
        "ne": lambda v, m: v != m,
        "gt": lambda v, m: v > m,
        "gte": lambda v, m: v >= m,
        "lt": lambda v, m: v < m,
        "lte": lambda v, m: v <= m,
        "contains": lambda v, m: str(m) in str(v),
        "starts_with": lambda v, m: str(v).startswith(str(m)),
        "ends_with": lambda v, m: str(v).endswith(str(m)),
    }
    
    if operator not in operators:
        raise HTTPException(status_code=400, detail=f"Unknown operator: {operator}")
    
    try:
        result = [v for v in values if operators[operator](v, match_value)]
        return ArrayResponse(result=result, count=len(result), operation=f"FILTER_{operator.upper()}")
    except TypeError:
        raise HTTPException(status_code=400, detail="Cannot compare items")


# ============================================================================
# SEQUENCE GENERATION
# ============================================================================

@router.post("/sequence", response_model=Matrix2DResponse)
async def array_sequence(request: SequenceRequest) -> Matrix2DResponse:
    """
    SEQUENCE - Generates a sequence of numbers.
    
    Excel equivalent: =SEQUENCE(rows, [columns], [start], [step])
    """
    if request.rows * request.columns > 1000000:
        raise HTTPException(status_code=400, detail="Sequence too large (max 1,000,000 elements)")
    
    result = []
    current = request.start
    
    for _ in range(request.rows):
        row = []
        for _ in range(request.columns):
            row.append(current)
            current += request.step
        result.append(row)
    
    return Matrix2DResponse(result=result, rows=request.rows, columns=request.columns, operation="SEQUENCE")


@router.post("/sequence-flat", response_model=ArrayResponse)
async def sequence_flat(
    count: int, 
    start: float = 1, 
    step: float = 1
) -> ArrayResponse:
    """
    Generate a flat sequence of numbers.
    """
    if count > 1000000:
        raise HTTPException(status_code=400, detail="Sequence too large (max 1,000,000 elements)")
    
    result = [start + i * step for i in range(count)]
    return ArrayResponse(result=result, count=len(result), operation="SEQUENCE_FLAT")


@router.post("/randarray", response_model=Matrix2DResponse)
async def randarray(
    rows: int = 1,
    columns: int = 1,
    min_val: float = 0,
    max_val: float = 1,
    whole_numbers: bool = False
) -> Matrix2DResponse:
    """
    RANDARRAY - Generates an array of random numbers.
    
    Excel equivalent: =RANDARRAY([rows], [columns], [min], [max], [whole_number])
    """
    if rows * columns > 1000000:
        raise HTTPException(status_code=400, detail="Array too large (max 1,000,000 elements)")
    
    result = []
    for _ in range(rows):
        row = []
        for _ in range(columns):
            if whole_numbers:
                row.append(random.randint(int(min_val), int(max_val)))
            else:
                row.append(random.uniform(min_val, max_val))
        result.append(row)
    
    return Matrix2DResponse(result=result, rows=rows, columns=columns, operation="RANDARRAY")


# ============================================================================
# MATRIX OPERATIONS
# ============================================================================

@router.post("/transpose", response_model=Matrix2DResponse)
async def array_transpose(request: Matrix2DRequest) -> Matrix2DResponse:
    """
    TRANSPOSE - Transposes a matrix (swaps rows and columns).
    
    Excel equivalent: =TRANSPOSE(array)
    """
    if not request.matrix:
        return Matrix2DResponse(result=[], rows=0, columns=0, operation="TRANSPOSE")
    
    rows = len(request.matrix)
    cols = len(request.matrix[0]) if request.matrix else 0
    
    result = []
    for j in range(cols):
        new_row = []
        for i in range(rows):
            if j < len(request.matrix[i]):
                new_row.append(request.matrix[i][j])
            else:
                new_row.append(None)
        result.append(new_row)
    
    return Matrix2DResponse(result=result, rows=cols, columns=rows, operation="TRANSPOSE")


@router.post("/flatten", response_model=ArrayResponse)
async def array_flatten(request: Matrix2DRequest) -> ArrayResponse:
    """
    Flatten a 2D matrix into a 1D array.
    """
    result = []
    for row in request.matrix:
        result.extend(row)
    
    return ArrayResponse(result=result, count=len(result), operation="FLATTEN")


@router.post("/reshape")
async def array_reshape(values: List[Any], rows: int, columns: int) -> Matrix2DResponse:
    """
    Reshape a 1D array into a 2D matrix.
    """
    if len(values) != rows * columns:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot reshape {len(values)} elements into {rows}x{columns} matrix"
        )
    
    result = []
    idx = 0
    for _ in range(rows):
        row = []
        for _ in range(columns):
            row.append(values[idx])
            idx += 1
        result.append(row)
    
    return Matrix2DResponse(result=result, rows=rows, columns=columns, operation="RESHAPE")


# ============================================================================
# TAKE AND DROP
# ============================================================================

@router.post("/take", response_model=ArrayResponse)
async def array_take(request: TakeRequest) -> ArrayResponse:
    """
    TAKE - Returns a specified number of rows from the start or end of an array.
    
    Excel equivalent: =TAKE(array, rows)
    Positive rows: from start. Negative rows: from end.
    """
    if request.rows > 0:
        result = request.values[:request.rows]
    else:
        result = request.values[request.rows:]
    
    return ArrayResponse(result=result, count=len(result), operation="TAKE")


@router.post("/drop", response_model=ArrayResponse)
async def array_drop(request: DropRequest) -> ArrayResponse:
    """
    DROP - Removes a specified number of rows from the start or end of an array.
    
    Excel equivalent: =DROP(array, rows)
    Positive rows: drop from start. Negative rows: drop from end.
    """
    if request.rows > 0:
        result = request.values[request.rows:]
    else:
        result = request.values[:request.rows]
    
    return ArrayResponse(result=result, count=len(result), operation="DROP")


# ============================================================================
# SLICING AND CHUNKING
# ============================================================================

@router.post("/slice", response_model=ArrayResponse)
async def array_slice(request: SliceRequest) -> ArrayResponse:
    """
    Slice an array (Python-style slicing).
    """
    result = request.values[request.start:request.end:request.step]
    return ArrayResponse(result=result, count=len(result), operation="SLICE")


@router.post("/chunk", response_model=Matrix2DResponse)
async def array_chunk(request: ChunkRequest) -> ArrayResponse:
    """
    Split an array into chunks of specified size.
    """
    result = []
    for i in range(0, len(request.values), request.size):
        result.append(request.values[i:i + request.size])
    
    return Matrix2DResponse(result=result, rows=len(result), columns=request.size, operation="CHUNK")


@router.post("/expand", response_model=ArrayResponse)
async def array_expand(request: ExpandRequest) -> ArrayResponse:
    """
    EXPAND - Expands an array to a specified size, padding if needed.
    
    Excel equivalent: =EXPAND(array, rows, [columns], [pad_with])
    """
    result = list(request.values)
    while len(result) < request.rows:
        result.append(request.pad_with)
    
    return ArrayResponse(result=result, count=len(result), operation="EXPAND")


# ============================================================================
# SET OPERATIONS
# ============================================================================

@router.post("/union", response_model=ArrayResponse)
async def array_union(array1: List[Any], array2: List[Any]) -> ArrayResponse:
    """
    Return the union of two arrays (all unique elements from both).
    """
    seen = set()
    result = []
    for item in array1 + array2:
        try:
            if item not in seen:
                seen.add(item)
                result.append(item)
        except TypeError:
            str_item = str(item)
            if str_item not in seen:
                seen.add(str_item)
                result.append(item)
    
    return ArrayResponse(result=result, count=len(result), operation="UNION")


@router.post("/intersect", response_model=ArrayResponse)
async def array_intersect(array1: List[Any], array2: List[Any]) -> ArrayResponse:
    """
    Return the intersection of two arrays (elements in both).
    """
    set2 = set(array2)
    result = [x for x in array1 if x in set2]
    result = list(dict.fromkeys(result))  # Remove duplicates, preserve order
    
    return ArrayResponse(result=result, count=len(result), operation="INTERSECT")


@router.post("/difference", response_model=ArrayResponse)
async def array_difference(array1: List[Any], array2: List[Any]) -> ArrayResponse:
    """
    Return elements in array1 but not in array2.
    """
    set2 = set(array2)
    result = [x for x in array1 if x not in set2]
    result = list(dict.fromkeys(result))  # Remove duplicates, preserve order
    
    return ArrayResponse(result=result, count=len(result), operation="DIFFERENCE")


# ============================================================================
# AGGREGATION
# ============================================================================

@router.post("/first", response_model=ScalarResponse)
async def array_first(request: ArrayRequest, default: Any = None) -> ScalarResponse:
    """
    Get the first element of an array.
    """
    result = request.values[0] if request.values else default
    return ScalarResponse(result=result, operation="FIRST")


@router.post("/last", response_model=ScalarResponse)
async def array_last(request: ArrayRequest, default: Any = None) -> ScalarResponse:
    """
    Get the last element of an array.
    """
    result = request.values[-1] if request.values else default
    return ScalarResponse(result=result, operation="LAST")


@router.post("/nth", response_model=ScalarResponse)
async def array_nth(request: SearchRequest) -> ScalarResponse:
    """
    Get the nth element of an array (0-based index).
    Values array contains the array, search_value is the index.
    """
    index = int(request.search_value)
    try:
        result = request.values[index]
    except IndexError:
        result = None
    
    return ScalarResponse(result=result, operation="NTH")


@router.post("/index-of", response_model=ScalarResponse)
async def array_index_of(request: SearchRequest) -> ScalarResponse:
    """
    Find the index of a value in an array (0-based, -1 if not found).
    """
    try:
        result = request.values.index(request.search_value)
    except ValueError:
        result = -1
    
    return ScalarResponse(result=result, operation="INDEX_OF")


@router.post("/contains")
async def array_contains(request: SearchRequest) -> dict:
    """
    Check if an array contains a value.
    """
    return {
        "result": request.search_value in request.values,
        "value": request.search_value,
        "operation": "CONTAINS"
    }


@router.post("/count-if", response_model=ScalarResponse)
async def array_count_if(request: SearchRequest) -> ScalarResponse:
    """
    Count occurrences of a value in an array.
    """
    result = request.values.count(request.search_value)
    return ScalarResponse(result=result, operation="COUNT_IF")
