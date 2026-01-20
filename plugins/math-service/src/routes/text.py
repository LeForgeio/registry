"""
Text Functions Routes - Excel-like text manipulation functions.

Implements: LEFT, RIGHT, MID, LEN, TRIM, UPPER, LOWER, PROPER, CONCAT, 
SUBSTITUTE, FIND, SEARCH, REPLACE, REPT, CLEAN, TEXT, TEXTJOIN, EXACT, VALUE
"""
import re
from typing import Optional
from fastapi import APIRouter, HTTPException

from ..models.text import (
    TextOperationRequest, LeftRightRequest, MidRequest, SubstituteRequest,
    FindSearchRequest, ReplaceRequest, ConcatRequest, TextJoinRequest,
    ReptRequest, PadRequest, TextFormatRequest, ExtractNumbersRequest,
    WordOperationRequest, SplitTextRequest,
    TextResponse, NumberResponse, BoolResponse, ListResponse
)


router = APIRouter(prefix="/text", tags=["Text Functions"])


# ============================================================================
# BASIC TEXT OPERATIONS
# ============================================================================

@router.post("/left", response_model=TextResponse)
async def text_left(request: LeftRightRequest) -> TextResponse:
    """
    LEFT - Returns the leftmost characters from a text string.
    
    Excel equivalent: =LEFT(text, num_chars)
    """
    result = request.text[:request.num_chars]
    return TextResponse(result=result, original=request.text, operation="LEFT")


@router.post("/right", response_model=TextResponse)
async def text_right(request: LeftRightRequest) -> TextResponse:
    """
    RIGHT - Returns the rightmost characters from a text string.
    
    Excel equivalent: =RIGHT(text, num_chars)
    """
    if request.num_chars == 0:
        result = ""
    else:
        result = request.text[-request.num_chars:]
    return TextResponse(result=result, original=request.text, operation="RIGHT")


@router.post("/mid", response_model=TextResponse)
async def text_mid(request: MidRequest) -> TextResponse:
    """
    MID - Returns characters from the middle of a text string.
    
    Excel equivalent: =MID(text, start_num, num_chars)
    Note: start_num is 1-based (Excel convention)
    """
    start_idx = request.start_num - 1  # Convert to 0-based
    result = request.text[start_idx:start_idx + request.num_chars]
    return TextResponse(result=result, original=request.text, operation="MID")


@router.post("/len", response_model=NumberResponse)
async def text_len(request: TextOperationRequest) -> NumberResponse:
    """
    LEN - Returns the number of characters in a text string.
    
    Excel equivalent: =LEN(text)
    """
    return NumberResponse(result=len(request.text), original=request.text, operation="LEN")


@router.post("/trim", response_model=TextResponse)
async def text_trim(request: TextOperationRequest) -> TextResponse:
    """
    TRIM - Removes extra spaces from text (leading, trailing, and multiple internal spaces).
    
    Excel equivalent: =TRIM(text)
    """
    # Remove leading/trailing and collapse multiple spaces to single
    result = " ".join(request.text.split())
    return TextResponse(result=result, original=request.text, operation="TRIM")


@router.post("/clean", response_model=TextResponse)
async def text_clean(request: TextOperationRequest) -> TextResponse:
    """
    CLEAN - Removes all non-printable characters from text.
    
    Excel equivalent: =CLEAN(text)
    """
    # Remove non-printable ASCII characters (0-31 and 127)
    result = "".join(char for char in request.text if ord(char) >= 32 and ord(char) != 127)
    return TextResponse(result=result, original=request.text, operation="CLEAN")


# ============================================================================
# CASE CONVERSION
# ============================================================================

@router.post("/upper", response_model=TextResponse)
async def text_upper(request: TextOperationRequest) -> TextResponse:
    """
    UPPER - Converts text to uppercase.
    
    Excel equivalent: =UPPER(text)
    """
    return TextResponse(result=request.text.upper(), original=request.text, operation="UPPER")


@router.post("/lower", response_model=TextResponse)
async def text_lower(request: TextOperationRequest) -> TextResponse:
    """
    LOWER - Converts text to lowercase.
    
    Excel equivalent: =LOWER(text)
    """
    return TextResponse(result=request.text.lower(), original=request.text, operation="LOWER")


@router.post("/proper", response_model=TextResponse)
async def text_proper(request: TextOperationRequest) -> TextResponse:
    """
    PROPER - Capitalizes the first letter of each word.
    
    Excel equivalent: =PROPER(text)
    """
    return TextResponse(result=request.text.title(), original=request.text, operation="PROPER")


# ============================================================================
# FIND AND REPLACE
# ============================================================================

@router.post("/find", response_model=NumberResponse)
async def text_find(request: FindSearchRequest) -> NumberResponse:
    """
    FIND - Finds the position of a substring (case-sensitive).
    
    Excel equivalent: =FIND(find_text, within_text, start_num)
    Returns 1-based position. Raises error if not found.
    """
    search_text = request.within_text[request.start_num - 1:]
    pos = search_text.find(request.find_text)
    
    if pos == -1:
        raise HTTPException(status_code=400, detail=f"'{request.find_text}' not found in text")
    
    # Return 1-based position accounting for start_num
    result = pos + request.start_num
    return NumberResponse(result=result, original=request.within_text, operation="FIND")


@router.post("/search", response_model=NumberResponse)
async def text_search(request: FindSearchRequest) -> NumberResponse:
    """
    SEARCH - Finds the position of a substring (case-insensitive).
    
    Excel equivalent: =SEARCH(find_text, within_text, start_num)
    Returns 1-based position. Raises error if not found.
    """
    search_text = request.within_text[request.start_num - 1:].lower()
    find_text = request.find_text.lower()
    pos = search_text.find(find_text)
    
    if pos == -1:
        raise HTTPException(status_code=400, detail=f"'{request.find_text}' not found in text")
    
    result = pos + request.start_num
    return NumberResponse(result=result, original=request.within_text, operation="SEARCH")


@router.post("/substitute", response_model=TextResponse)
async def text_substitute(request: SubstituteRequest) -> TextResponse:
    """
    SUBSTITUTE - Replaces occurrences of old_text with new_text.
    
    Excel equivalent: =SUBSTITUTE(text, old_text, new_text, instance_num)
    If instance_num is not specified, replaces all occurrences.
    """
    if request.instance_num is None:
        result = request.text.replace(request.old_text, request.new_text)
    else:
        # Replace only the nth occurrence
        parts = request.text.split(request.old_text)
        if len(parts) <= request.instance_num:
            result = request.text  # Instance not found, return original
        else:
            # Reconstruct with replacement at specific position
            before = request.old_text.join(parts[:request.instance_num])
            after = request.old_text.join(parts[request.instance_num:])
            result = before + request.new_text + after
    
    return TextResponse(result=result, original=request.text, operation="SUBSTITUTE")


@router.post("/replace", response_model=TextResponse)
async def text_replace(request: ReplaceRequest) -> TextResponse:
    """
    REPLACE - Replaces characters at a specific position.
    
    Excel equivalent: =REPLACE(old_text, start_num, num_chars, new_text)
    Note: start_num is 1-based (Excel convention)
    """
    start_idx = request.start_num - 1
    result = request.old_text[:start_idx] + request.new_text + request.old_text[start_idx + request.num_chars:]
    return TextResponse(result=result, original=request.old_text, operation="REPLACE")


# ============================================================================
# CONCATENATION
# ============================================================================

@router.post("/concat", response_model=TextResponse)
async def text_concat(request: ConcatRequest) -> TextResponse:
    """
    CONCAT/CONCATENATE - Joins multiple text strings.
    
    Excel equivalent: =CONCAT(text1, text2, ...) or =CONCATENATE(text1, text2, ...)
    """
    result = request.delimiter.join(request.texts)
    return TextResponse(result=result, original=str(request.texts), operation="CONCAT")


@router.post("/textjoin", response_model=TextResponse)
async def text_textjoin(request: TextJoinRequest) -> TextResponse:
    """
    TEXTJOIN - Joins texts with a delimiter, optionally ignoring empty strings.
    
    Excel equivalent: =TEXTJOIN(delimiter, ignore_empty, text1, text2, ...)
    """
    if request.ignore_empty:
        texts = [t for t in request.texts if t]
    else:
        texts = request.texts
    
    result = request.delimiter.join(texts)
    return TextResponse(result=result, original=str(request.texts), operation="TEXTJOIN")


@router.post("/rept", response_model=TextResponse)
async def text_rept(request: ReptRequest) -> TextResponse:
    """
    REPT - Repeats text a given number of times.
    
    Excel equivalent: =REPT(text, number_times)
    """
    result = request.text * request.number_times
    return TextResponse(result=result, original=request.text, operation="REPT")


# ============================================================================
# COMPARISON AND TESTING
# ============================================================================

@router.post("/exact")
async def text_exact(text1: str, text2: str) -> BoolResponse:
    """
    EXACT - Checks if two text strings are exactly identical (case-sensitive).
    
    Excel equivalent: =EXACT(text1, text2)
    """
    return BoolResponse(result=text1 == text2, original=f"{text1} vs {text2}", operation="EXACT")


# ============================================================================
# VALUE EXTRACTION
# ============================================================================

@router.post("/value", response_model=NumberResponse)
async def text_value(request: TextOperationRequest) -> NumberResponse:
    """
    VALUE - Converts a text string that represents a number to a number.
    
    Excel equivalent: =VALUE(text)
    """
    try:
        # Try integer first, then float
        text = request.text.strip().replace(",", "").replace(" ", "")
        if "." in text or "e" in text.lower():
            result = float(text)
        else:
            result = int(text)
        return NumberResponse(result=result, original=request.text, operation="VALUE")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Cannot convert '{request.text}' to a number")


@router.post("/text", response_model=TextResponse)
async def text_format(request: TextFormatRequest) -> TextResponse:
    """
    TEXT - Formats a number and converts it to text.
    
    Excel equivalent: =TEXT(value, format_text)
    Supported formats: "0.00", "#,##0", "0%", "0.00E+00", etc.
    """
    value = request.value
    fmt = request.format_text.upper()
    
    try:
        if "%" in fmt:
            # Percentage format
            decimals = fmt.count("0") - 1 if "." in fmt else 0
            result = f"{value * 100:.{decimals}f}%"
        elif "E" in fmt:
            # Scientific notation
            decimals = fmt.split(".")[1].count("0") if "." in fmt else 2
            result = f"{value:.{decimals}E}"
        elif "#,##" in fmt or ",##" in fmt:
            # Thousands separator
            decimals = fmt.split(".")[1].count("0") if "." in fmt else 0
            result = f"{value:,.{decimals}f}"
        elif "." in fmt:
            # Decimal places
            decimals = fmt.split(".")[1].count("0")
            result = f"{value:.{decimals}f}"
        else:
            # Integer
            result = f"{int(round(value))}"
        
        return TextResponse(result=result, original=str(value), operation="TEXT")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(e)}")


@router.post("/extract-numbers", response_model=ListResponse)
async def extract_numbers(request: ExtractNumbersRequest) -> ListResponse:
    """
    Extract all numbers from a text string (not standard Excel, but useful).
    
    Returns a list of all numbers found in the text.
    """
    # Find all number patterns including decimals and negatives
    pattern = r"-?\d+\.?\d*"
    matches = re.findall(pattern, request.text)
    
    results = []
    for match in matches:
        if "." in match:
            results.append(float(match))
        else:
            results.append(int(match))
    
    return ListResponse(result=results, original=request.text, operation="EXTRACT_NUMBERS", count=len(results))


# ============================================================================
# PADDING OPERATIONS
# ============================================================================

@router.post("/lpad", response_model=TextResponse)
async def text_lpad(request: PadRequest) -> TextResponse:
    """
    Left-pad text to a specified length (similar to Excel's custom formatting).
    """
    result = request.text.rjust(request.total_length, request.pad_char)
    return TextResponse(result=result, original=request.text, operation="LPAD")


@router.post("/rpad", response_model=TextResponse)
async def text_rpad(request: PadRequest) -> TextResponse:
    """
    Right-pad text to a specified length (similar to Excel's custom formatting).
    """
    result = request.text.ljust(request.total_length, request.pad_char)
    return TextResponse(result=result, original=request.text, operation="RPAD")


# ============================================================================
# WORD OPERATIONS
# ============================================================================

@router.post("/word-count", response_model=NumberResponse)
async def word_count(request: WordOperationRequest) -> NumberResponse:
    """
    Count the number of words in text.
    """
    words = [w for w in request.text.split(request.delimiter) if w]
    return NumberResponse(result=len(words), original=request.text, operation="WORD_COUNT")


@router.post("/get-word", response_model=TextResponse)
async def get_word(request: WordOperationRequest) -> TextResponse:
    """
    Get a specific word from text by position (1-based).
    """
    if request.word_num is None:
        raise HTTPException(status_code=400, detail="word_num is required")
    
    words = [w for w in request.text.split(request.delimiter) if w]
    
    if request.word_num > len(words):
        raise HTTPException(status_code=400, detail=f"Word {request.word_num} not found (only {len(words)} words)")
    
    result = words[request.word_num - 1]
    return TextResponse(result=result, original=request.text, operation="GET_WORD")


@router.post("/split", response_model=ListResponse)
async def text_split(request: SplitTextRequest) -> ListResponse:
    """
    Split text by a delimiter.
    """
    if request.limit:
        result = request.text.split(request.delimiter, request.limit)
    else:
        result = request.text.split(request.delimiter)
    
    return ListResponse(result=result, original=request.text, operation="SPLIT", count=len(result))


@router.post("/reverse", response_model=TextResponse)
async def text_reverse(request: TextOperationRequest) -> TextResponse:
    """
    Reverse a text string.
    """
    return TextResponse(result=request.text[::-1], original=request.text, operation="REVERSE")


@router.post("/char")
async def text_char(number: int) -> TextResponse:
    """
    CHAR - Returns the character specified by a number.
    
    Excel equivalent: =CHAR(number)
    """
    if number < 1 or number > 255:
        raise HTTPException(status_code=400, detail="Number must be between 1 and 255")
    return TextResponse(result=chr(number), original=str(number), operation="CHAR")


@router.post("/code", response_model=NumberResponse)
async def text_code(request: TextOperationRequest) -> NumberResponse:
    """
    CODE - Returns the numeric code for the first character.
    
    Excel equivalent: =CODE(text)
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return NumberResponse(result=ord(request.text[0]), original=request.text, operation="CODE")
