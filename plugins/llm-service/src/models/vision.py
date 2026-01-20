"""
Vision OCR models for image-based text extraction and understanding.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from enum import Enum


class ImageInputType(str, Enum):
    """Type of image input."""
    URL = "url"
    BASE64 = "base64"
    FILE = "file"


class ImageInput(BaseModel):
    """
    Image input specification.
    
    Supports multiple input methods:
    - URL: HTTP/HTTPS URL to the image
    - Base64: Base64-encoded image data with optional media type
    - File: File path (for server-side processing)
    """
    url: Optional[str] = Field(default=None, description="URL to the image")
    base64: Optional[str] = Field(default=None, description="Base64-encoded image data")
    media_type: Optional[str] = Field(
        default="image/png",
        description="Media type (e.g., image/png, image/jpeg)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/document.png"
            }
        }


class OCRRegion(BaseModel):
    """A region of detected text with bounding box."""
    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    bbox: Optional[List[int]] = Field(
        default=None,
        description="Bounding box [x1, y1, x2, y2]"
    )
    line_number: Optional[int] = Field(default=None, description="Line number")
    word_count: Optional[int] = Field(default=None, description="Number of words")


class VisionOCRRequest(BaseModel):
    """
    Request for Vision-based OCR.
    
    Uses a vision-language model (like LLaVA, Qwen-VL) for intelligent
    text extraction that can handle handwriting, rotated text, and complex layouts.
    """
    image: ImageInput = Field(..., description="Image to process")
    language_hints: Optional[List[str]] = Field(
        default=None,
        description="Hint languages (e.g., ['en', 'es'])"
    )
    output_format: Literal["text", "structured", "markdown"] = Field(
        default="text",
        description="Output format: plain text, structured with regions, or markdown"
    )
    detail_level: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Detail level: low=fast, high=thorough"
    )
    preserve_layout: bool = Field(
        default=False,
        description="Try to preserve original text layout/formatting"
    )
    model: Optional[str] = Field(
        default=None,
        description="Vision model to use (defaults to configured vision model)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image": {"url": "https://example.com/document.png"},
                "output_format": "structured",
                "detail_level": "high",
                "preserve_layout": True
            }
        }


class VisionOCRResponse(BaseModel):
    """Response for Vision OCR."""
    success: bool = True
    text: str = Field(..., description="Extracted text (full)")
    regions: Optional[List[OCRRegion]] = Field(
        default=None,
        description="Text regions with positions (if structured output)"
    )
    language_detected: Optional[str] = Field(
        default=None,
        description="Detected primary language"
    )
    confidence: float = Field(..., description="Overall confidence score", ge=0.0, le=1.0)
    word_count: int = Field(..., description="Total words extracted")
    model: str = Field(..., description="Model used")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")


class VisionDescribeRequest(BaseModel):
    """
    Request to describe an image.
    
    Uses vision-language model to generate a natural language description
    of the image contents.
    """
    image: ImageInput = Field(..., description="Image to describe")
    prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for description (e.g., 'Describe the chart data')"
    )
    max_length: Optional[int] = Field(
        default=200,
        description="Maximum description length in tokens",
        ge=10,
        le=1024
    )
    focus: Optional[Literal["general", "objects", "text", "people", "scene"]] = Field(
        default="general",
        description="What to focus on in the description"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "image": {"base64": "iVBORw0KGgo..."},
                "prompt": "Describe the main elements in this diagram",
                "focus": "objects"
            }
        }


class VisionDescribeResponse(BaseModel):
    """Response for image description."""
    success: bool = True
    description: str = Field(..., description="Generated description")
    objects_detected: Optional[List[str]] = Field(
        default=None,
        description="Objects detected in image"
    )
    text_detected: Optional[str] = Field(
        default=None,
        description="Any text visible in image"
    )
    model: str = Field(..., description="Model used")


class ExtractedField(BaseModel):
    """A field extracted from structured document."""
    name: str = Field(..., description="Field name")
    value: Union[str, int, float, bool, List, dict] = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0)
    location: Optional[str] = Field(default=None, description="Location hint in document")


class VisionExtractRequest(BaseModel):
    """
    Request to extract structured data from an image.
    
    Uses vision-language model to extract specific fields from
    documents, forms, receipts, invoices, etc.
    """
    image: ImageInput = Field(..., description="Image to extract from")
    fields: List[str] = Field(
        ...,
        description="Field names to extract (e.g., ['invoice_number', 'total', 'date'])",
        min_length=1
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Document type hint (e.g., 'invoice', 'receipt', 'form')"
    )
    schema: Optional[dict] = Field(
        default=None,
        description="JSON schema for expected output structure"
    )
    examples: Optional[List[dict]] = Field(
        default=None,
        description="Few-shot examples for extraction"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "image": {"url": "https://example.com/invoice.png"},
                "fields": ["invoice_number", "date", "total", "vendor_name"],
                "document_type": "invoice"
            }
        }


class VisionExtractResponse(BaseModel):
    """Response for structured extraction from image."""
    success: bool = True
    fields: List[ExtractedField] = Field(..., description="Extracted fields")
    raw_data: Optional[dict] = Field(
        default=None,
        description="Raw extracted data as dictionary"
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Detected or confirmed document type"
    )
    confidence: float = Field(..., description="Overall extraction confidence", ge=0.0, le=1.0)
    model: str = Field(..., description="Model used")


class VisionCompareRequest(BaseModel):
    """
    Request to compare two images.
    
    Uses vision-language model to identify differences or similarities.
    """
    image1: ImageInput = Field(..., description="First image")
    image2: ImageInput = Field(..., description="Second image")
    comparison_type: Literal["diff", "similarity", "changes"] = Field(
        default="diff",
        description="Type of comparison"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Areas to focus on (e.g., ['text', 'layout', 'colors'])"
    )
    model: Optional[str] = Field(default=None)


class VisionCompareResponse(BaseModel):
    """Response for image comparison."""
    success: bool = True
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    differences: List[str] = Field(..., description="List of identified differences")
    summary: str = Field(..., description="Summary of comparison")
    model: str = Field(..., description="Model used")
