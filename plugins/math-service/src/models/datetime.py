"""
Date/Time function Pydantic models for Excel-like date operations.
"""
from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class DateComponentsRequest(BaseModel):
    """Request for DATE function."""
    year: int = Field(..., ge=1900, le=9999, description="Year (1900-9999)")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Day (1-31)")


class DateStringRequest(BaseModel):
    """Request for date parsing."""
    date_string: str = Field(..., description="Date string to parse")
    format: Optional[str] = Field(None, description="Date format (e.g., '%Y-%m-%d')")


class SingleDateRequest(BaseModel):
    """Request for single date operations."""
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")


class TwoDateRequest(BaseModel):
    """Request for operations with two dates."""
    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")


class DateDifRequest(BaseModel):
    """Request for DATEDIF operation."""
    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")
    unit: str = Field(..., description="Unit: Y (years), M (months), D (days), MD, YM, YD")


class NetworkDaysRequest(BaseModel):
    """Request for NETWORKDAYS operation."""
    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")
    holidays: List[str] = Field(default=[], description="List of holiday dates in ISO format")


class WorkdayRequest(BaseModel):
    """Request for WORKDAY operation."""
    start_date: str = Field(..., description="Start date in ISO format")
    days: int = Field(..., description="Number of workdays to add (can be negative)")
    holidays: List[str] = Field(default=[], description="List of holiday dates in ISO format")


class EDateRequest(BaseModel):
    """Request for EDATE operation."""
    start_date: str = Field(..., description="Start date in ISO format")
    months: int = Field(..., description="Number of months to add (can be negative)")


class DateTimeRequest(BaseModel):
    """Request for datetime operations."""
    datetime_string: str = Field(..., description="Datetime string")
    format: Optional[str] = Field(None, description="Datetime format")


class TimeRequest(BaseModel):
    """Request for TIME function."""
    hour: int = Field(..., ge=0, le=23, description="Hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Minute (0-59)")
    second: int = Field(0, ge=0, le=59, description="Second (0-59)")


class DateResponse(BaseModel):
    """Response for date operations returning a date."""
    result: str
    operation: str


class NumberResponse(BaseModel):
    """Response for date operations returning a number."""
    result: Union[int, float]
    operation: str


class DateTimeResponse(BaseModel):
    """Response for datetime operations."""
    result: str
    date: str
    time: str
    operation: str


class DateComponentsResponse(BaseModel):
    """Response with date components."""
    year: int
    month: int
    day: int
    weekday: int
    weekday_name: str
    day_of_year: int
    week_number: int
    quarter: int
    operation: str
