"""
Text function Pydantic models for Excel-like text operations.
"""
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class TextOperationRequest(BaseModel):
    """Request for single text operations."""
    text: str = Field(..., description="Input text to operate on")
    

class LeftRightRequest(BaseModel):
    """Request for LEFT/RIGHT operations."""
    text: str = Field(..., description="Input text")
    num_chars: int = Field(..., ge=0, description="Number of characters to extract")


class MidRequest(BaseModel):
    """Request for MID operation."""
    text: str = Field(..., description="Input text")
    start_num: int = Field(..., ge=1, description="Starting position (1-based)")
    num_chars: int = Field(..., ge=0, description="Number of characters to extract")


class SubstituteRequest(BaseModel):
    """Request for SUBSTITUTE operation."""
    text: str = Field(..., description="Input text")
    old_text: str = Field(..., description="Text to replace")
    new_text: str = Field(..., description="Replacement text")
    instance_num: Optional[int] = Field(None, ge=1, description="Which occurrence to replace (all if not specified)")


class FindSearchRequest(BaseModel):
    """Request for FIND/SEARCH operations."""
    find_text: str = Field(..., description="Text to find")
    within_text: str = Field(..., description="Text to search within")
    start_num: int = Field(1, ge=1, description="Starting position (1-based)")


class ReplaceRequest(BaseModel):
    """Request for REPLACE operation."""
    old_text: str = Field(..., description="Original text")
    start_num: int = Field(..., ge=1, description="Starting position (1-based)")
    num_chars: int = Field(..., ge=0, description="Number of characters to replace")
    new_text: str = Field(..., description="Replacement text")


class ConcatRequest(BaseModel):
    """Request for CONCAT/CONCATENATE operation."""
    texts: List[str] = Field(..., min_length=1, description="List of texts to concatenate")
    delimiter: str = Field("", description="Delimiter between texts")


class TextJoinRequest(BaseModel):
    """Request for TEXTJOIN operation."""
    delimiter: str = Field(..., description="Delimiter between texts")
    ignore_empty: bool = Field(True, description="Whether to ignore empty strings")
    texts: List[str] = Field(..., min_length=1, description="List of texts to join")


class ReptRequest(BaseModel):
    """Request for REPT operation."""
    text: str = Field(..., description="Text to repeat")
    number_times: int = Field(..., ge=0, le=32767, description="Number of times to repeat")


class PadRequest(BaseModel):
    """Request for padding operations (custom, not standard Excel)."""
    text: str = Field(..., description="Text to pad")
    total_length: int = Field(..., ge=1, description="Total length after padding")
    pad_char: str = Field(" ", max_length=1, description="Character to pad with")


class TextFormatRequest(BaseModel):
    """Request for TEXT formatting operation."""
    value: Union[float, int] = Field(..., description="Number to format")
    format_text: str = Field(..., description="Format string (e.g., '0.00', '#,##0', '0%')")


class ExtractNumbersRequest(BaseModel):
    """Request for extracting numbers from text."""
    text: str = Field(..., description="Text containing numbers")


class WordOperationRequest(BaseModel):
    """Request for word-level operations."""
    text: str = Field(..., description="Input text")
    word_num: Optional[int] = Field(None, ge=1, description="Word number to extract (1-based)")
    delimiter: str = Field(" ", description="Word delimiter")


class SplitTextRequest(BaseModel):
    """Request for splitting text."""
    text: str = Field(..., description="Text to split")
    delimiter: str = Field(..., description="Delimiter to split on")
    limit: Optional[int] = Field(None, ge=1, description="Maximum number of splits")


class TextResponse(BaseModel):
    """Response for text operations returning a string."""
    result: str
    original: str
    operation: str


class NumberResponse(BaseModel):
    """Response for text operations returning a number."""
    result: Union[int, float]
    original: str
    operation: str


class BoolResponse(BaseModel):
    """Response for text operations returning a boolean."""
    result: bool
    original: str
    operation: str


class ListResponse(BaseModel):
    """Response for text operations returning a list."""
    result: List[Any]
    original: str
    operation: str
    count: int
