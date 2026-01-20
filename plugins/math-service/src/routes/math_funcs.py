"""
Math Functions Routes - Excel-like math and trigonometry functions.

Implements: ABS, ROUND, ROUNDUP, ROUNDDOWN, CEILING, FLOOR, INT, TRUNC,
MOD, POWER, SQRT, EXP, LOG, LN, LOG10, GCD, LCM, RAND, RANDBETWEEN,
SIN, COS, TAN, ASIN, ACOS, ATAN, RADIANS, DEGREES, PI, COMBIN, PERMUT,
FACT, PRODUCT, SUMPRODUCT, QUOTIENT, SIGN, and more.
"""
import math
import random
from functools import reduce
from typing import List, Union
from fastapi import APIRouter, HTTPException

from ..models.math import (
    SingleNumberRequest, TwoNumberRequest, RoundRequest, CeilingFloorRequest,
    PowerRequest, LogRequest, NumberArrayRequest, GcdLcmRequest,
    RandomRequest, RandBetweenRequest, TrigRequest, AngleConvertRequest,
    CombPermRequest, FactorialRequest, ProductRequest, SumProductRequest, QuotientRequest,
    MathResponse, ArrayMathResponse, TrigResponse
)


router = APIRouter(prefix="/math", tags=["Math Functions"])


# ============================================================================
# BASIC OPERATIONS
# ============================================================================

@router.post("/abs", response_model=MathResponse)
async def math_abs(request: SingleNumberRequest) -> MathResponse:
    """
    ABS - Returns the absolute value of a number.
    
    Excel equivalent: =ABS(number)
    """
    return MathResponse(result=abs(request.value), operation="ABS")


@router.post("/sign", response_model=MathResponse)
async def math_sign(request: SingleNumberRequest) -> MathResponse:
    """
    SIGN - Returns the sign of a number (-1, 0, or 1).
    
    Excel equivalent: =SIGN(number)
    """
    if request.value > 0:
        result = 1
    elif request.value < 0:
        result = -1
    else:
        result = 0
    return MathResponse(result=result, operation="SIGN")


@router.post("/mod", response_model=MathResponse)
async def math_mod(request: TwoNumberRequest) -> MathResponse:
    """
    MOD - Returns the remainder after division.
    
    Excel equivalent: =MOD(number, divisor)
    """
    if request.value2 == 0:
        raise HTTPException(status_code=400, detail="Divisor cannot be zero")
    
    result = request.value1 % request.value2
    return MathResponse(result=result, operation="MOD")


@router.post("/quotient", response_model=MathResponse)
async def math_quotient(request: QuotientRequest) -> MathResponse:
    """
    QUOTIENT - Returns the integer portion of a division.
    
    Excel equivalent: =QUOTIENT(numerator, denominator)
    """
    if request.denominator == 0:
        raise HTTPException(status_code=400, detail="Denominator cannot be zero")
    
    result = int(request.numerator // request.denominator)
    return MathResponse(result=result, operation="QUOTIENT")


# ============================================================================
# ROUNDING FUNCTIONS
# ============================================================================

@router.post("/round", response_model=MathResponse)
async def math_round(request: RoundRequest) -> MathResponse:
    """
    ROUND - Rounds a number to a specified number of digits.
    
    Excel equivalent: =ROUND(number, num_digits)
    """
    result = round(request.value, request.num_digits)
    return MathResponse(result=result, operation="ROUND")


@router.post("/roundup", response_model=MathResponse)
async def math_roundup(request: RoundRequest) -> MathResponse:
    """
    ROUNDUP - Rounds a number up, away from zero.
    
    Excel equivalent: =ROUNDUP(number, num_digits)
    """
    multiplier = 10 ** request.num_digits
    if request.value >= 0:
        result = math.ceil(request.value * multiplier) / multiplier
    else:
        result = math.floor(request.value * multiplier) / multiplier
    return MathResponse(result=result, operation="ROUNDUP")


@router.post("/rounddown", response_model=MathResponse)
async def math_rounddown(request: RoundRequest) -> MathResponse:
    """
    ROUNDDOWN - Rounds a number down, toward zero.
    
    Excel equivalent: =ROUNDDOWN(number, num_digits)
    """
    multiplier = 10 ** request.num_digits
    if request.value >= 0:
        result = math.floor(request.value * multiplier) / multiplier
    else:
        result = math.ceil(request.value * multiplier) / multiplier
    return MathResponse(result=result, operation="ROUNDDOWN")


@router.post("/ceiling", response_model=MathResponse)
async def math_ceiling(request: CeilingFloorRequest) -> MathResponse:
    """
    CEILING - Rounds a number up to the nearest multiple of significance.
    
    Excel equivalent: =CEILING(number, significance)
    """
    if request.significance == 0:
        return MathResponse(result=0, operation="CEILING")
    
    result = math.ceil(request.value / request.significance) * request.significance
    return MathResponse(result=result, operation="CEILING")


@router.post("/floor", response_model=MathResponse)
async def math_floor(request: CeilingFloorRequest) -> MathResponse:
    """
    FLOOR - Rounds a number down to the nearest multiple of significance.
    
    Excel equivalent: =FLOOR(number, significance)
    """
    if request.significance == 0:
        return MathResponse(result=0, operation="FLOOR")
    
    result = math.floor(request.value / request.significance) * request.significance
    return MathResponse(result=result, operation="FLOOR")


@router.post("/int", response_model=MathResponse)
async def math_int(request: SingleNumberRequest) -> MathResponse:
    """
    INT - Rounds a number down to the nearest integer.
    
    Excel equivalent: =INT(number)
    """
    return MathResponse(result=math.floor(request.value), operation="INT")


@router.post("/trunc", response_model=MathResponse)
async def math_trunc(request: RoundRequest) -> MathResponse:
    """
    TRUNC - Truncates a number to an integer or specified decimal places.
    
    Excel equivalent: =TRUNC(number, num_digits)
    """
    multiplier = 10 ** request.num_digits
    result = int(request.value * multiplier) / multiplier
    return MathResponse(result=result, operation="TRUNC")


@router.post("/mround")
async def math_mround(value: float, multiple: float) -> MathResponse:
    """
    MROUND - Returns a number rounded to the desired multiple.
    
    Excel equivalent: =MROUND(number, multiple)
    """
    if multiple == 0:
        return MathResponse(result=0, operation="MROUND")
    
    result = round(value / multiple) * multiple
    return MathResponse(result=result, operation="MROUND")


@router.post("/even", response_model=MathResponse)
async def math_even(request: SingleNumberRequest) -> MathResponse:
    """
    EVEN - Rounds a number up to the nearest even integer.
    
    Excel equivalent: =EVEN(number)
    """
    if request.value >= 0:
        result = math.ceil(request.value / 2) * 2
    else:
        result = math.floor(request.value / 2) * 2
    return MathResponse(result=int(result), operation="EVEN")


@router.post("/odd", response_model=MathResponse)
async def math_odd(request: SingleNumberRequest) -> MathResponse:
    """
    ODD - Rounds a number up to the nearest odd integer.
    
    Excel equivalent: =ODD(number)
    """
    if request.value >= 0:
        result = math.ceil(request.value)
        if result % 2 == 0:
            result += 1
    else:
        result = math.floor(request.value)
        if result % 2 == 0:
            result -= 1
    return MathResponse(result=int(result), operation="ODD")


# ============================================================================
# POWER AND ROOTS
# ============================================================================

@router.post("/power", response_model=MathResponse)
async def math_power(request: PowerRequest) -> MathResponse:
    """
    POWER - Returns the result of a number raised to a power.
    
    Excel equivalent: =POWER(number, power)
    """
    try:
        result = math.pow(request.base, request.exponent)
        return MathResponse(result=result, operation="POWER")
    except (ValueError, OverflowError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sqrt", response_model=MathResponse)
async def math_sqrt(request: SingleNumberRequest) -> MathResponse:
    """
    SQRT - Returns the square root of a number.
    
    Excel equivalent: =SQRT(number)
    """
    if request.value < 0:
        raise HTTPException(status_code=400, detail="Cannot calculate square root of negative number")
    return MathResponse(result=math.sqrt(request.value), operation="SQRT")


@router.post("/sqrtpi", response_model=MathResponse)
async def math_sqrtpi(request: SingleNumberRequest) -> MathResponse:
    """
    SQRTPI - Returns the square root of (number * pi).
    
    Excel equivalent: =SQRTPI(number)
    """
    if request.value < 0:
        raise HTTPException(status_code=400, detail="Cannot calculate square root of negative number")
    return MathResponse(result=math.sqrt(request.value * math.pi), operation="SQRTPI")


@router.post("/exp", response_model=MathResponse)
async def math_exp(request: SingleNumberRequest) -> MathResponse:
    """
    EXP - Returns e raised to the power of a number.
    
    Excel equivalent: =EXP(number)
    """
    try:
        return MathResponse(result=math.exp(request.value), operation="EXP")
    except OverflowError:
        raise HTTPException(status_code=400, detail="Result too large")


# ============================================================================
# LOGARITHMS
# ============================================================================

@router.post("/log", response_model=MathResponse)
async def math_log(request: LogRequest) -> MathResponse:
    """
    LOG - Returns the logarithm of a number to a specified base.
    
    Excel equivalent: =LOG(number, base)
    """
    return MathResponse(result=math.log(request.value, request.base), operation="LOG")


@router.post("/ln", response_model=MathResponse)
async def math_ln(request: SingleNumberRequest) -> MathResponse:
    """
    LN - Returns the natural logarithm of a number.
    
    Excel equivalent: =LN(number)
    """
    if request.value <= 0:
        raise HTTPException(status_code=400, detail="Value must be positive")
    return MathResponse(result=math.log(request.value), operation="LN")


@router.post("/log10", response_model=MathResponse)
async def math_log10(request: SingleNumberRequest) -> MathResponse:
    """
    LOG10 - Returns the base-10 logarithm of a number.
    
    Excel equivalent: =LOG10(number)
    """
    if request.value <= 0:
        raise HTTPException(status_code=400, detail="Value must be positive")
    return MathResponse(result=math.log10(request.value), operation="LOG10")


# ============================================================================
# GCD AND LCM
# ============================================================================

@router.post("/gcd", response_model=MathResponse)
async def math_gcd(request: GcdLcmRequest) -> MathResponse:
    """
    GCD - Returns the greatest common divisor.
    
    Excel equivalent: =GCD(number1, number2, ...)
    """
    result = request.values[0]
    for val in request.values[1:]:
        result = math.gcd(result, val)
    return MathResponse(result=result, operation="GCD")


@router.post("/lcm", response_model=MathResponse)
async def math_lcm(request: GcdLcmRequest) -> MathResponse:
    """
    LCM - Returns the least common multiple.
    
    Excel equivalent: =LCM(number1, number2, ...)
    """
    def lcm(a: int, b: int) -> int:
        return abs(a * b) // math.gcd(a, b)
    
    result = request.values[0]
    for val in request.values[1:]:
        result = lcm(result, val)
    return MathResponse(result=result, operation="LCM")


# ============================================================================
# RANDOM NUMBERS
# ============================================================================

@router.get("/rand", response_model=MathResponse)
async def math_rand() -> MathResponse:
    """
    RAND - Returns a random number between 0 and 1.
    
    Excel equivalent: =RAND()
    """
    return MathResponse(result=random.random(), operation="RAND")


@router.post("/rand-array", response_model=ArrayMathResponse)
async def math_rand_array(request: RandomRequest) -> ArrayMathResponse:
    """
    Generate multiple random numbers between 0 and 1.
    """
    result = [random.random() for _ in range(request.count)]
    return ArrayMathResponse(result=result, count=len(result), operation="RAND_ARRAY")


@router.post("/randbetween", response_model=MathResponse)
async def math_randbetween(request: RandBetweenRequest) -> MathResponse:
    """
    RANDBETWEEN - Returns a random integer between two values.
    
    Excel equivalent: =RANDBETWEEN(bottom, top)
    """
    if request.bottom > request.top:
        raise HTTPException(status_code=400, detail="bottom must be <= top")
    
    if request.count == 1:
        return MathResponse(result=random.randint(request.bottom, request.top), operation="RANDBETWEEN")
    else:
        result = [random.randint(request.bottom, request.top) for _ in range(request.count)]
        return ArrayMathResponse(result=result, count=len(result), operation="RANDBETWEEN")


# ============================================================================
# TRIGONOMETRIC FUNCTIONS
# ============================================================================

@router.post("/sin", response_model=TrigResponse)
async def math_sin(request: TrigRequest) -> TrigResponse:
    """
    SIN - Returns the sine of an angle (in radians).
    
    Excel equivalent: =SIN(number)
    """
    return TrigResponse(
        result=math.sin(request.angle),
        input_radians=request.angle,
        input_degrees=math.degrees(request.angle),
        operation="SIN"
    )


@router.post("/cos", response_model=TrigResponse)
async def math_cos(request: TrigRequest) -> TrigResponse:
    """
    COS - Returns the cosine of an angle (in radians).
    
    Excel equivalent: =COS(number)
    """
    return TrigResponse(
        result=math.cos(request.angle),
        input_radians=request.angle,
        input_degrees=math.degrees(request.angle),
        operation="COS"
    )


@router.post("/tan", response_model=TrigResponse)
async def math_tan(request: TrigRequest) -> TrigResponse:
    """
    TAN - Returns the tangent of an angle (in radians).
    
    Excel equivalent: =TAN(number)
    """
    return TrigResponse(
        result=math.tan(request.angle),
        input_radians=request.angle,
        input_degrees=math.degrees(request.angle),
        operation="TAN"
    )


@router.post("/asin", response_model=MathResponse)
async def math_asin(request: SingleNumberRequest) -> MathResponse:
    """
    ASIN - Returns the arcsine of a number (in radians).
    
    Excel equivalent: =ASIN(number)
    """
    if not -1 <= request.value <= 1:
        raise HTTPException(status_code=400, detail="Value must be between -1 and 1")
    return MathResponse(result=math.asin(request.value), operation="ASIN")


@router.post("/acos", response_model=MathResponse)
async def math_acos(request: SingleNumberRequest) -> MathResponse:
    """
    ACOS - Returns the arccosine of a number (in radians).
    
    Excel equivalent: =ACOS(number)
    """
    if not -1 <= request.value <= 1:
        raise HTTPException(status_code=400, detail="Value must be between -1 and 1")
    return MathResponse(result=math.acos(request.value), operation="ACOS")


@router.post("/atan", response_model=MathResponse)
async def math_atan(request: SingleNumberRequest) -> MathResponse:
    """
    ATAN - Returns the arctangent of a number (in radians).
    
    Excel equivalent: =ATAN(number)
    """
    return MathResponse(result=math.atan(request.value), operation="ATAN")


@router.post("/atan2", response_model=MathResponse)
async def math_atan2(x: float, y: float) -> MathResponse:
    """
    ATAN2 - Returns the arctangent from x and y coordinates.
    
    Excel equivalent: =ATAN2(x_num, y_num)
    """
    return MathResponse(result=math.atan2(y, x), operation="ATAN2")


@router.post("/sinh", response_model=MathResponse)
async def math_sinh(request: SingleNumberRequest) -> MathResponse:
    """
    SINH - Returns the hyperbolic sine of a number.
    
    Excel equivalent: =SINH(number)
    """
    return MathResponse(result=math.sinh(request.value), operation="SINH")


@router.post("/cosh", response_model=MathResponse)
async def math_cosh(request: SingleNumberRequest) -> MathResponse:
    """
    COSH - Returns the hyperbolic cosine of a number.
    
    Excel equivalent: =COSH(number)
    """
    return MathResponse(result=math.cosh(request.value), operation="COSH")


@router.post("/tanh", response_model=MathResponse)
async def math_tanh(request: SingleNumberRequest) -> MathResponse:
    """
    TANH - Returns the hyperbolic tangent of a number.
    
    Excel equivalent: =TANH(number)
    """
    return MathResponse(result=math.tanh(request.value), operation="TANH")


# ============================================================================
# ANGLE CONVERSION
# ============================================================================

@router.post("/radians", response_model=MathResponse)
async def math_radians(request: AngleConvertRequest) -> MathResponse:
    """
    RADIANS - Converts degrees to radians.
    
    Excel equivalent: =RADIANS(angle)
    """
    return MathResponse(result=math.radians(request.value), operation="RADIANS")


@router.post("/degrees", response_model=MathResponse)
async def math_degrees(request: AngleConvertRequest) -> MathResponse:
    """
    DEGREES - Converts radians to degrees.
    
    Excel equivalent: =DEGREES(angle)
    """
    return MathResponse(result=math.degrees(request.value), operation="DEGREES")


@router.get("/pi", response_model=MathResponse)
async def math_pi() -> MathResponse:
    """
    PI - Returns the value of pi.
    
    Excel equivalent: =PI()
    """
    return MathResponse(result=math.pi, operation="PI")


# ============================================================================
# COMBINATORICS
# ============================================================================

@router.post("/combin", response_model=MathResponse)
async def math_combin(request: CombPermRequest) -> MathResponse:
    """
    COMBIN - Returns the number of combinations.
    
    Excel equivalent: =COMBIN(number, number_chosen)
    """
    if request.k > request.n:
        raise HTTPException(status_code=400, detail="k cannot be greater than n")
    return MathResponse(result=math.comb(request.n, request.k), operation="COMBIN")


@router.post("/combina", response_model=MathResponse)
async def math_combina(request: CombPermRequest) -> MathResponse:
    """
    COMBINA - Returns the number of combinations with repetitions.
    
    Excel equivalent: =COMBINA(number, number_chosen)
    """
    # C(n+k-1, k) = combinations with repetition
    return MathResponse(result=math.comb(request.n + request.k - 1, request.k), operation="COMBINA")


@router.post("/permut", response_model=MathResponse)
async def math_permut(request: CombPermRequest) -> MathResponse:
    """
    PERMUT - Returns the number of permutations.
    
    Excel equivalent: =PERMUT(number, number_chosen)
    """
    if request.k > request.n:
        raise HTTPException(status_code=400, detail="k cannot be greater than n")
    return MathResponse(result=math.perm(request.n, request.k), operation="PERMUT")


@router.post("/fact", response_model=MathResponse)
async def math_fact(request: FactorialRequest) -> MathResponse:
    """
    FACT - Returns the factorial of a number.
    
    Excel equivalent: =FACT(number)
    """
    return MathResponse(result=math.factorial(request.value), operation="FACT")


@router.post("/factdouble", response_model=MathResponse)
async def math_factdouble(request: FactorialRequest) -> MathResponse:
    """
    FACTDOUBLE - Returns the double factorial of a number.
    
    Excel equivalent: =FACTDOUBLE(number)
    n!! = n * (n-2) * (n-4) * ... * 1 (or 2)
    """
    n = request.value
    result = 1
    while n > 1:
        result *= n
        n -= 2
    return MathResponse(result=result, operation="FACTDOUBLE")


# ============================================================================
# AGGREGATION FUNCTIONS
# ============================================================================

@router.post("/product", response_model=MathResponse)
async def math_product(request: ProductRequest) -> MathResponse:
    """
    PRODUCT - Multiplies all numbers in the array.
    
    Excel equivalent: =PRODUCT(number1, number2, ...)
    """
    result = reduce(lambda x, y: x * y, request.values, 1)
    return MathResponse(result=result, operation="PRODUCT")


@router.post("/sumproduct", response_model=MathResponse)
async def math_sumproduct(request: SumProductRequest) -> MathResponse:
    """
    SUMPRODUCT - Returns the sum of products of corresponding array elements.
    
    Excel equivalent: =SUMPRODUCT(array1, array2, ...)
    """
    # Check all arrays have same length
    lengths = [len(arr) for arr in request.arrays]
    if len(set(lengths)) > 1:
        raise HTTPException(status_code=400, detail="All arrays must have the same length")
    
    result = 0
    for i in range(lengths[0]):
        product = 1
        for arr in request.arrays:
            product *= arr[i]
        result += product
    
    return MathResponse(result=result, operation="SUMPRODUCT")


@router.post("/sumsq", response_model=MathResponse)
async def math_sumsq(request: NumberArrayRequest) -> MathResponse:
    """
    SUMSQ - Returns the sum of squares of the arguments.
    
    Excel equivalent: =SUMSQ(number1, number2, ...)
    """
    result = sum(x ** 2 for x in request.values)
    return MathResponse(result=result, operation="SUMSQ")
