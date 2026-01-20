"""
Date/Time Functions Routes - Excel-like date and time functions.

Implements: DATE, DATEDIF, TODAY, NOW, YEAR, MONTH, DAY, WEEKDAY, WEEKNUM,
NETWORKDAYS, WORKDAY, EDATE, EOMONTH, TIME, HOUR, MINUTE, SECOND, DATEVALUE, TIMEVALUE
"""
from datetime import date, datetime, timedelta
from typing import List
from calendar import monthrange
from fastapi import APIRouter, HTTPException

from ..models.datetime import (
    DateComponentsRequest, SingleDateRequest, TwoDateRequest, DateDifRequest,
    NetworkDaysRequest, WorkdayRequest, EDateRequest, TimeRequest,
    DateResponse, NumberResponse, DateTimeResponse, DateComponentsResponse
)


router = APIRouter(prefix="/datetime", tags=["Date/Time Functions"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_date(date_str: str) -> date:
    """Parse a date string in ISO format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def is_workday(d: date, holidays: List[date]) -> bool:
    """Check if a date is a workday (not weekend, not holiday)."""
    return d.weekday() < 5 and d not in holidays


# ============================================================================
# DATE CREATION FUNCTIONS
# ============================================================================

@router.post("/date", response_model=DateResponse)
async def create_date(request: DateComponentsRequest) -> DateResponse:
    """
    DATE - Creates a date from year, month, and day.
    
    Excel equivalent: =DATE(year, month, day)
    """
    try:
        result = date(request.year, request.month, request.day)
        return DateResponse(result=result.isoformat(), operation="DATE")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/today", response_model=DateResponse)
async def today() -> DateResponse:
    """
    TODAY - Returns the current date.
    
    Excel equivalent: =TODAY()
    """
    return DateResponse(result=date.today().isoformat(), operation="TODAY")


@router.get("/now", response_model=DateTimeResponse)
async def now() -> DateTimeResponse:
    """
    NOW - Returns the current date and time.
    
    Excel equivalent: =NOW()
    """
    current = datetime.now()
    return DateTimeResponse(
        result=current.isoformat(),
        date=current.date().isoformat(),
        time=current.time().isoformat(),
        operation="NOW"
    )


@router.post("/time", response_model=DateResponse)
async def create_time(request: TimeRequest) -> DateResponse:
    """
    TIME - Creates a time value from hour, minute, and second.
    
    Excel equivalent: =TIME(hour, minute, second)
    """
    from datetime import time as dt_time
    result = dt_time(request.hour, request.minute, request.second)
    return DateResponse(result=result.isoformat(), operation="TIME")


# ============================================================================
# DATE EXTRACTION FUNCTIONS
# ============================================================================

@router.post("/year", response_model=NumberResponse)
async def extract_year(request: SingleDateRequest) -> NumberResponse:
    """
    YEAR - Extracts the year from a date.
    
    Excel equivalent: =YEAR(date)
    """
    d = parse_date(request.date)
    return NumberResponse(result=d.year, operation="YEAR")


@router.post("/month", response_model=NumberResponse)
async def extract_month(request: SingleDateRequest) -> NumberResponse:
    """
    MONTH - Extracts the month from a date (1-12).
    
    Excel equivalent: =MONTH(date)
    """
    d = parse_date(request.date)
    return NumberResponse(result=d.month, operation="MONTH")


@router.post("/day", response_model=NumberResponse)
async def extract_day(request: SingleDateRequest) -> NumberResponse:
    """
    DAY - Extracts the day from a date (1-31).
    
    Excel equivalent: =DAY(date)
    """
    d = parse_date(request.date)
    return NumberResponse(result=d.day, operation="DAY")


@router.post("/weekday", response_model=NumberResponse)
async def extract_weekday(request: SingleDateRequest, return_type: int = 1) -> NumberResponse:
    """
    WEEKDAY - Returns the day of the week for a date.
    
    Excel equivalent: =WEEKDAY(date, return_type)
    
    return_type:
    - 1: Sunday=1, Saturday=7 (default)
    - 2: Monday=1, Sunday=7
    - 3: Monday=0, Sunday=6
    """
    d = parse_date(request.date)
    weekday = d.weekday()  # Python: Monday=0, Sunday=6
    
    if return_type == 1:
        # Sunday=1, Saturday=7
        result = (weekday + 2) % 7
        if result == 0:
            result = 7
    elif return_type == 2:
        # Monday=1, Sunday=7
        result = weekday + 1
    elif return_type == 3:
        # Monday=0, Sunday=6
        result = weekday
    else:
        raise HTTPException(status_code=400, detail="return_type must be 1, 2, or 3")
    
    return NumberResponse(result=result, operation="WEEKDAY")


@router.post("/weeknum", response_model=NumberResponse)
async def week_number(request: SingleDateRequest) -> NumberResponse:
    """
    WEEKNUM - Returns the week number of a date in the year.
    
    Excel equivalent: =WEEKNUM(date)
    """
    d = parse_date(request.date)
    return NumberResponse(result=d.isocalendar()[1], operation="WEEKNUM")


@router.post("/quarter", response_model=NumberResponse)
async def quarter(request: SingleDateRequest) -> NumberResponse:
    """
    Returns the quarter (1-4) of a date.
    """
    d = parse_date(request.date)
    result = (d.month - 1) // 3 + 1
    return NumberResponse(result=result, operation="QUARTER")


@router.post("/hour", response_model=NumberResponse)
async def extract_hour(datetime_str: str) -> NumberResponse:
    """
    HOUR - Extracts the hour from a time/datetime.
    
    Excel equivalent: =HOUR(time)
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        return NumberResponse(result=dt.hour, operation="HOUR")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")


@router.post("/minute", response_model=NumberResponse)
async def extract_minute(datetime_str: str) -> NumberResponse:
    """
    MINUTE - Extracts the minute from a time/datetime.
    
    Excel equivalent: =MINUTE(time)
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        return NumberResponse(result=dt.minute, operation="MINUTE")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")


@router.post("/second", response_model=NumberResponse)
async def extract_second(datetime_str: str) -> NumberResponse:
    """
    SECOND - Extracts the second from a time/datetime.
    
    Excel equivalent: =SECOND(time)
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        return NumberResponse(result=dt.second, operation="SECOND")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")


@router.post("/components", response_model=DateComponentsResponse)
async def date_components(request: SingleDateRequest) -> DateComponentsResponse:
    """
    Get all components of a date in one call.
    """
    d = parse_date(request.date)
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return DateComponentsResponse(
        year=d.year,
        month=d.month,
        day=d.day,
        weekday=d.weekday() + 1,  # 1-based
        weekday_name=weekday_names[d.weekday()],
        day_of_year=d.timetuple().tm_yday,
        week_number=d.isocalendar()[1],
        quarter=(d.month - 1) // 3 + 1,
        operation="COMPONENTS"
    )


# ============================================================================
# DATE ARITHMETIC
# ============================================================================

@router.post("/datedif", response_model=NumberResponse)
async def datedif(request: DateDifRequest) -> NumberResponse:
    """
    DATEDIF - Calculates the difference between two dates.
    
    Excel equivalent: =DATEDIF(start_date, end_date, unit)
    
    Units:
    - Y: Complete years
    - M: Complete months
    - D: Days
    - MD: Days ignoring years and months
    - YM: Months ignoring years
    - YD: Days ignoring years
    """
    start = parse_date(request.start_date)
    end = parse_date(request.end_date)
    unit = request.unit.upper()
    
    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    
    if unit == "D":
        result = (end - start).days
    elif unit == "Y":
        result = end.year - start.year
        if (end.month, end.day) < (start.month, start.day):
            result -= 1
    elif unit == "M":
        result = (end.year - start.year) * 12 + end.month - start.month
        if end.day < start.day:
            result -= 1
    elif unit == "MD":
        # Days ignoring months and years
        if end.day >= start.day:
            result = end.day - start.day
        else:
            # Get days in previous month
            prev_month = end.month - 1 if end.month > 1 else 12
            prev_year = end.year if end.month > 1 else end.year - 1
            days_in_prev = monthrange(prev_year, prev_month)[1]
            result = days_in_prev - start.day + end.day
    elif unit == "YM":
        # Months ignoring years
        result = end.month - start.month
        if end.day < start.day:
            result -= 1
        if result < 0:
            result += 12
    elif unit == "YD":
        # Days ignoring years
        temp_date = start.replace(year=end.year)
        if temp_date > end:
            temp_date = start.replace(year=end.year - 1)
        result = (end - temp_date).days
    else:
        raise HTTPException(status_code=400, detail=f"Unknown unit: {unit}. Use Y, M, D, MD, YM, or YD")
    
    return NumberResponse(result=result, operation="DATEDIF")


@router.post("/days", response_model=NumberResponse)
async def days_between(request: TwoDateRequest) -> NumberResponse:
    """
    DAYS - Returns the number of days between two dates.
    
    Excel equivalent: =DAYS(end_date, start_date)
    """
    start = parse_date(request.start_date)
    end = parse_date(request.end_date)
    return NumberResponse(result=(end - start).days, operation="DAYS")


@router.post("/days360", response_model=NumberResponse)
async def days360(request: TwoDateRequest, method: bool = False) -> NumberResponse:
    """
    DAYS360 - Returns the number of days between two dates based on a 360-day year.
    
    Excel equivalent: =DAYS360(start_date, end_date, method)
    
    method:
    - False (US method): If day is 31, becomes 30
    - True (European method): If day is 31, becomes 30
    """
    start = parse_date(request.start_date)
    end = parse_date(request.end_date)
    
    start_day = min(start.day, 30)
    end_day = min(end.day, 30)
    
    if not method:  # US method
        if start.day == 31:
            start_day = 30
        if end.day == 31 and start_day == 30:
            end_day = 30
    
    result = (
        (end.year - start.year) * 360 +
        (end.month - start.month) * 30 +
        (end_day - start_day)
    )
    
    return NumberResponse(result=result, operation="DAYS360")


@router.post("/networkdays", response_model=NumberResponse)
async def networkdays(request: NetworkDaysRequest) -> NumberResponse:
    """
    NETWORKDAYS - Returns the number of working days between two dates.
    
    Excel equivalent: =NETWORKDAYS(start_date, end_date, [holidays])
    Excludes weekends (Saturday, Sunday) and specified holidays.
    """
    start = parse_date(request.start_date)
    end = parse_date(request.end_date)
    holidays = [parse_date(h) for h in request.holidays]
    
    if start > end:
        start, end = end, start
        sign = -1
    else:
        sign = 1
    
    count = 0
    current = start
    while current <= end:
        if is_workday(current, holidays):
            count += 1
        current += timedelta(days=1)
    
    return NumberResponse(result=count * sign, operation="NETWORKDAYS")


@router.post("/workday", response_model=DateResponse)
async def workday(request: WorkdayRequest) -> DateResponse:
    """
    WORKDAY - Returns a date that is a specified number of workdays from a start date.
    
    Excel equivalent: =WORKDAY(start_date, days, [holidays])
    """
    current = parse_date(request.start_date)
    holidays = [parse_date(h) for h in request.holidays]
    days_remaining = abs(request.days)
    direction = 1 if request.days > 0 else -1
    
    while days_remaining > 0:
        current += timedelta(days=direction)
        if is_workday(current, holidays):
            days_remaining -= 1
    
    return DateResponse(result=current.isoformat(), operation="WORKDAY")


@router.post("/edate", response_model=DateResponse)
async def edate(request: EDateRequest) -> DateResponse:
    """
    EDATE - Returns the date that is a specified number of months from a start date.
    
    Excel equivalent: =EDATE(start_date, months)
    """
    start = parse_date(request.start_date)
    
    # Calculate new month and year
    new_month = start.month + request.months
    new_year = start.year
    
    while new_month > 12:
        new_month -= 12
        new_year += 1
    while new_month < 1:
        new_month += 12
        new_year -= 1
    
    # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
    max_day = monthrange(new_year, new_month)[1]
    new_day = min(start.day, max_day)
    
    result = date(new_year, new_month, new_day)
    return DateResponse(result=result.isoformat(), operation="EDATE")


@router.post("/eomonth", response_model=DateResponse)
async def eomonth(request: EDateRequest) -> DateResponse:
    """
    EOMONTH - Returns the last day of the month that is a specified number of months from a date.
    
    Excel equivalent: =EOMONTH(start_date, months)
    """
    start = parse_date(request.start_date)
    
    # Calculate target month and year
    new_month = start.month + request.months
    new_year = start.year
    
    while new_month > 12:
        new_month -= 12
        new_year += 1
    while new_month < 1:
        new_month += 12
        new_year -= 1
    
    # Get last day of that month
    last_day = monthrange(new_year, new_month)[1]
    result = date(new_year, new_month, last_day)
    
    return DateResponse(result=result.isoformat(), operation="EOMONTH")


# ============================================================================
# DATE CONVERSION
# ============================================================================

@router.post("/datevalue", response_model=NumberResponse)
async def datevalue(request: SingleDateRequest) -> NumberResponse:
    """
    DATEVALUE - Converts a date string to a serial date number.
    
    Excel equivalent: =DATEVALUE(date_text)
    Returns days since December 30, 1899 (Excel's epoch).
    """
    d = parse_date(request.date)
    excel_epoch = date(1899, 12, 30)
    return NumberResponse(result=(d - excel_epoch).days, operation="DATEVALUE")


@router.post("/serial-to-date", response_model=DateResponse)
async def serial_to_date(serial_number: int) -> DateResponse:
    """
    Convert an Excel serial date number back to a date.
    """
    excel_epoch = date(1899, 12, 30)
    result = excel_epoch + timedelta(days=serial_number)
    return DateResponse(result=result.isoformat(), operation="SERIAL_TO_DATE")


# ============================================================================
# DATE VALIDATION
# ============================================================================

@router.post("/is-valid-date")
async def is_valid_date(date_string: str) -> dict:
    """
    Check if a string represents a valid date.
    """
    try:
        parse_date(date_string)
        return {"valid": True, "date": date_string, "operation": "IS_VALID_DATE"}
    except HTTPException:
        return {"valid": False, "date": date_string, "operation": "IS_VALID_DATE"}


@router.post("/is-weekend")
async def is_weekend(request: SingleDateRequest) -> dict:
    """
    Check if a date falls on a weekend.
    """
    d = parse_date(request.date)
    return {
        "result": d.weekday() >= 5,
        "date": request.date,
        "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][d.weekday()],
        "operation": "IS_WEEKEND"
    }


@router.post("/is-leap-year")
async def is_leap_year(year: int) -> dict:
    """
    Check if a year is a leap year.
    """
    leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    return {"result": leap, "year": year, "operation": "IS_LEAP_YEAR"}
