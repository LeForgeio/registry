"""
Data transformation models for LLM-powered data conversion.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from enum import Enum


class DataFormat(str, Enum):
    """Supported data formats."""
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    CSV = "csv"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    SQL = "sql"


class TransformExample(BaseModel):
    """Example for few-shot transformation learning."""
    input: Union[str, dict, list] = Field(..., description="Example input")
    output: Union[str, dict, list] = Field(..., description="Expected output")


class TransformRequest(BaseModel):
    """
    Request for LLM-powered data transformation.
    
    Use this when you need intelligent transformation that understands
    context and semantics, not just structure mapping.
    """
    data: Union[str, dict, list] = Field(..., description="Input data to transform")
    instruction: str = Field(
        ...,
        description="Natural language instruction for transformation",
        min_length=5
    )
    input_format: Optional[DataFormat] = Field(
        default=None,
        description="Input format (auto-detected if not specified)"
    )
    output_format: Optional[DataFormat] = Field(
        default=DataFormat.JSON,
        description="Desired output format"
    )
    examples: Optional[List[TransformExample]] = Field(
        default=None,
        description="Few-shot examples to guide transformation"
    )
    preserve_nulls: bool = Field(
        default=True,
        description="Preserve null/empty values in output"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "data": {"firstName": "John", "lastName": "Doe", "age": 30},
                "instruction": "Combine firstName and lastName into a 'fullName' field and categorize age as 'young' (<30), 'middle' (30-50), or 'senior' (>50)",
                "output_format": "json"
            }
        }


class TransformResponse(BaseModel):
    """Response for data transformation."""
    success: bool = True
    result: Union[str, dict, list] = Field(..., description="Transformed data")
    input_format: DataFormat = Field(..., description="Detected/specified input format")
    output_format: DataFormat = Field(..., description="Output format")
    transformations_applied: Optional[List[str]] = Field(
        default=None,
        description="List of transformations that were applied"
    )
    model: str = Field(..., description="Model used")


class SchemaTransformRequest(BaseModel):
    """
    Request for schema-to-schema transformation.
    
    Transform data from one schema to another, with the LLM
    intelligently mapping fields and handling mismatches.
    """
    data: Union[str, dict, list] = Field(..., description="Input data")
    source_schema: Optional[dict] = Field(
        default=None,
        description="JSON Schema of input data (optional, for validation)"
    )
    target_schema: dict = Field(
        ...,
        description="JSON Schema of desired output"
    )
    mapping_hints: Optional[Dict[str, str]] = Field(
        default=None,
        description="Explicit field mappings: {target_field: source_field_or_expression}"
    )
    fill_defaults: bool = Field(
        default=True,
        description="Fill missing required fields with sensible defaults"
    )
    strict: bool = Field(
        default=False,
        description="Fail if any required field cannot be mapped"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "customer_name": "John Doe",
                    "customer_email": "john@example.com",
                    "order_total": 99.99
                },
                "target_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "total": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"}
                    },
                    "required": ["name", "email", "total"]
                }
            }
        }


class SchemaTransformResponse(BaseModel):
    """Response for schema transformation."""
    success: bool = True
    result: Union[dict, list] = Field(..., description="Transformed data matching target schema")
    mappings_used: Dict[str, str] = Field(
        ...,
        description="Field mappings that were used: {target: source}"
    )
    fields_filled: Optional[List[str]] = Field(
        default=None,
        description="Fields that were filled with defaults"
    )
    validation_passed: bool = Field(
        ...,
        description="Whether output validates against target schema"
    )
    model: str = Field(..., description="Model used")


class FormatConvertRequest(BaseModel):
    """
    Request to convert between data formats.
    
    Intelligent format conversion that handles edge cases
    and can infer structure from unstructured data.
    """
    data: str = Field(..., description="Input data as string")
    source_format: Optional[DataFormat] = Field(
        default=None,
        description="Source format (auto-detected if not specified)"
    )
    target_format: DataFormat = Field(..., description="Target format")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Format-specific options"
    )
    infer_structure: bool = Field(
        default=True,
        description="Use LLM to infer structure from unstructured input"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "data": "Name: John Doe\nEmail: john@example.com\nPhone: 555-1234",
                "source_format": "text",
                "target_format": "json",
                "infer_structure": True
            }
        }


class FormatConvertResponse(BaseModel):
    """Response for format conversion."""
    success: bool = True
    result: str = Field(..., description="Converted data as string")
    source_format: DataFormat = Field(..., description="Source format (detected or specified)")
    target_format: DataFormat = Field(..., description="Target format")
    inferred_schema: Optional[dict] = Field(
        default=None,
        description="Schema inferred from input (if applicable)"
    )
    model: str = Field(..., description="Model used")


class CleanDataRequest(BaseModel):
    """
    Request to clean and normalize data.
    
    Uses LLM to intelligently clean, deduplicate, and normalize data.
    """
    data: Union[str, dict, list] = Field(..., description="Input data to clean")
    operations: List[Literal[
        "trim",
        "normalize_whitespace",
        "fix_encoding",
        "standardize_dates",
        "standardize_phones",
        "standardize_addresses",
        "deduplicate",
        "fill_missing",
        "fix_typos",
        "normalize_case"
    ]] = Field(
        ...,
        description="Cleaning operations to apply",
        min_length=1
    )
    locale: Optional[str] = Field(
        default="en-US",
        description="Locale for formatting (e.g., date formats)"
    )
    model: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"name": "  john DOE  ", "email": "JOHN@example.com", "date": "1/15/2024"},
                    {"name": "John Doe", "email": "john@example.com", "date": "2024-01-15"}
                ],
                "operations": ["trim", "normalize_case", "standardize_dates", "deduplicate"]
            }
        }


class CleanDataResponse(BaseModel):
    """Response for data cleaning."""
    success: bool = True
    result: Union[str, dict, list] = Field(..., description="Cleaned data")
    changes_made: List[str] = Field(..., description="List of changes made")
    records_removed: Optional[int] = Field(
        default=None,
        description="Number of duplicate records removed"
    )
    model: str = Field(..., description="Model used")


class MergeDataRequest(BaseModel):
    """
    Request to intelligently merge multiple data sources.
    
    Uses LLM to understand relationships and merge data from
    multiple sources with different schemas.
    """
    sources: List[Union[str, dict, list]] = Field(
        ...,
        description="Data sources to merge",
        min_length=2
    )
    merge_strategy: Literal["union", "intersection", "left", "smart"] = Field(
        default="smart",
        description="Merge strategy: smart uses LLM to determine best approach"
    )
    key_fields: Optional[List[str]] = Field(
        default=None,
        description="Fields to use as merge keys"
    )
    conflict_resolution: Literal["first", "last", "merge", "ask"] = Field(
        default="merge",
        description="How to resolve conflicts"
    )
    model: Optional[str] = Field(default=None)


class MergeDataResponse(BaseModel):
    """Response for data merge."""
    success: bool = True
    result: Union[dict, list] = Field(..., description="Merged data")
    sources_merged: int = Field(..., description="Number of sources merged")
    conflicts_resolved: int = Field(..., description="Number of conflicts resolved")
    merge_report: Optional[str] = Field(
        default=None,
        description="Summary of merge operations"
    )
    model: str = Field(..., description="Model used")
