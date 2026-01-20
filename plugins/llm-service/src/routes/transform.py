"""
Transform Routes - LLM-powered data transformation.

Use for intelligent transformations that require understanding
context, semantics, and complex mappings.
"""
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from ..models import (
    TransformRequest,
    TransformResponse,
    SchemaTransformRequest,
    SchemaTransformResponse,
    FormatConvertRequest,
    FormatConvertResponse,
    CleanDataRequest,
    CleanDataResponse,
    MergeDataRequest,
    MergeDataResponse,
    DataFormat,
    ErrorResponse,
)
from ..services.transform_service import get_transform_service, TransformServiceError

router = APIRouter(prefix="/transform", tags=["Transform"])


@router.post(
    "",
    response_model=TransformResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Transform data",
    description="""
Transform data using natural language instructions.

The LLM understands your intent and applies the transformation
intelligently. Great for:
- Restructuring data
- Adding/removing/renaming fields
- Computing derived values
- Complex conditional logic

**Example instruction:** "Combine firstName and lastName into fullName, 
convert age to age_group (child: 0-17, adult: 18-64, senior: 65+)"
    """,
)
async def transform_data(request: TransformRequest, req: Request):
    """
    Transform data using natural language instructions.
    
    - **data**: Input data (JSON, string, etc.)
    - **instruction**: Natural language transformation instruction
    - **input_format**: Input format (auto-detected if not specified)
    - **output_format**: Desired output format
    - **examples**: Few-shot examples for complex transformations
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_transform_service()
    
    try:
        logger.info(
            f"Processing transform request",
            extra={
                "request_id": request_id,
                "instruction_preview": request.instruction[:100]
            }
        )
        
        # Convert examples to dict format
        examples = None
        if request.examples:
            examples = [
                {"input": ex.input, "output": ex.output}
                for ex in request.examples
            ]
        
        result = await service.transform(
            data=request.data,
            instruction=request.instruction,
            input_format=request.input_format.value if request.input_format else None,
            output_format=request.output_format.value if request.output_format else "json",
            examples=examples,
            model=request.model
        )
        
        return TransformResponse(
            success=True,
            result=result["result"],
            input_format=DataFormat(result["input_format"]),
            output_format=DataFormat(result["output_format"]),
            model=result["model"]
        )
        
    except TransformServiceError as e:
        logger.error(f"Transform error: {e.message}")
        raise HTTPException(
            status_code=400 if "parse" in e.code.lower() else 500,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in transform_data")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/schema",
    response_model=SchemaTransformResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Transform to target schema",
    description="""
Transform data to match a target JSON schema.

The LLM intelligently maps fields from source to target:
- Handles different field names (e.g., 'customer_name' → 'name')
- Converts types as needed
- Fills required fields with sensible defaults
- Validates output against schema
    """,
)
async def transform_to_schema(request: SchemaTransformRequest, req: Request):
    """
    Transform data to match target schema.
    
    - **data**: Input data
    - **target_schema**: JSON Schema of desired output
    - **source_schema**: Input schema (optional)
    - **mapping_hints**: Explicit field mappings
    - **fill_defaults**: Fill missing required fields
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_transform_service()
    
    try:
        logger.info(
            f"Processing schema transform",
            extra={"request_id": request_id}
        )
        
        result = await service.transform_to_schema(
            data=request.data,
            target_schema=request.target_schema,
            source_schema=request.source_schema,
            mapping_hints=request.mapping_hints,
            fill_defaults=request.fill_defaults,
            model=request.model
        )
        
        return SchemaTransformResponse(
            success=True,
            result=result["result"],
            mappings_used=result["mappings_used"],
            fields_filled=result.get("fields_filled"),
            validation_passed=result["validation_passed"],
            model=result["model"]
        )
        
    except TransformServiceError as e:
        logger.error(f"Schema transform error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in transform_to_schema")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/convert",
    response_model=FormatConvertResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Convert data format",
    description="""
Convert data between formats (JSON, XML, YAML, CSV, etc.).

For structured data, this performs format conversion.
For unstructured text, it can infer structure and create
organized output.

**Example:** Convert plain text contact info to structured JSON.
    """,
)
async def convert_format(request: FormatConvertRequest, req: Request):
    """
    Convert between data formats.
    
    - **data**: Input data as string
    - **source_format**: Source format (auto-detected if not specified)
    - **target_format**: Target format
    - **infer_structure**: Infer structure from unstructured input
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_transform_service()
    
    try:
        logger.info(
            f"Processing format conversion",
            extra={
                "request_id": request_id,
                "target_format": request.target_format.value
            }
        )
        
        result = await service.convert_format(
            data=request.data,
            source_format=request.source_format.value if request.source_format else None,
            target_format=request.target_format.value,
            infer_structure=request.infer_structure,
            model=request.model
        )
        
        return FormatConvertResponse(
            success=True,
            result=result["result"],
            source_format=DataFormat(result["source_format"]),
            target_format=DataFormat(result["target_format"]),
            inferred_schema=result.get("inferred_schema"),
            model=result["model"]
        )
        
    except TransformServiceError as e:
        logger.error(f"Format conversion error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in convert_format")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/clean",
    response_model=CleanDataResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Clean and normalize data",
    description="""
Clean and normalize data intelligently.

Available operations:
- **trim**: Remove whitespace
- **normalize_whitespace**: Fix spacing
- **fix_encoding**: Fix character encoding
- **standardize_dates**: Convert dates to ISO format
- **standardize_phones**: Normalize phone numbers
- **standardize_addresses**: Format addresses
- **deduplicate**: Remove duplicates
- **fill_missing**: Fill missing values
- **fix_typos**: Correct obvious typos
- **normalize_case**: Fix text casing
    """,
)
async def clean_data(request: CleanDataRequest, req: Request):
    """
    Clean and normalize data.
    
    - **data**: Input data
    - **operations**: Cleaning operations to apply
    - **locale**: Locale for formatting (e.g., 'en-US')
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_transform_service()
    
    try:
        logger.info(
            f"Processing data cleaning",
            extra={
                "request_id": request_id,
                "operations": request.operations
            }
        )
        
        result = await service.clean_data(
            data=request.data,
            operations=request.operations,
            locale=request.locale,
            model=request.model
        )
        
        return CleanDataResponse(
            success=True,
            result=result["result"],
            changes_made=result["changes_made"],
            records_removed=result.get("records_removed"),
            model=result["model"]
        )
        
    except TransformServiceError as e:
        logger.error(f"Data cleaning error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in clean_data")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/merge",
    response_model=MergeDataResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Merge multiple data sources",
    description="""
Intelligently merge multiple data sources.

The LLM understands relationships between sources and merges
them appropriately, handling:
- Different schemas
- Conflicting values
- Missing data
    """,
)
async def merge_data(request: MergeDataRequest, req: Request):
    """
    Merge multiple data sources.
    
    - **sources**: Data sources to merge
    - **merge_strategy**: 'union', 'intersection', 'left', 'smart'
    - **key_fields**: Fields to use for matching
    - **conflict_resolution**: How to handle conflicts
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_transform_service()
    
    try:
        logger.info(
            f"Processing data merge",
            extra={
                "request_id": request_id,
                "source_count": len(request.sources),
                "strategy": request.merge_strategy
            }
        )
        
        result = await service.merge_data(
            sources=request.sources,
            merge_strategy=request.merge_strategy,
            key_fields=request.key_fields,
            conflict_resolution=request.conflict_resolution,
            model=request.model
        )
        
        return MergeDataResponse(
            success=True,
            result=result["result"],
            sources_merged=result["sources_merged"],
            conflicts_resolved=result["conflicts_resolved"],
            merge_report=result.get("merge_report"),
            model=result["model"]
        )
        
    except TransformServiceError as e:
        logger.error(f"Data merge error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in merge_data")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/query",
    summary="Query data with natural language",
    description="Query/filter data using natural language.",
)
async def query_data(
    data: dict | list,
    query: str,
    model: str = None,
    req: Request = None,
):
    """
    Query data using natural language.
    
    - **data**: Data to query
    - **query**: Natural language query (e.g., "find all users over 30")
    """
    request_id = getattr(req.state, "request_id", "unknown") if req else "unknown"
    service = get_transform_service()
    
    try:
        instruction = f"Filter/query this data: {query}. Return only the matching results as JSON."
        
        result = await service.transform(
            data=data,
            instruction=instruction,
            output_format="json",
            model=model
        )
        
        return {
            "success": True,
            "result": result["result"],
            "query": query,
            "model": result["model"]
        }
        
    except TransformServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.get(
    "/formats",
    summary="List supported formats",
    description="Get list of supported data formats.",
)
async def list_formats():
    """List supported data formats."""
    return {
        "formats": [
            {"name": "json", "description": "JavaScript Object Notation"},
            {"name": "xml", "description": "Extensible Markup Language"},
            {"name": "yaml", "description": "YAML Ain't Markup Language"},
            {"name": "csv", "description": "Comma-Separated Values"},
            {"name": "markdown", "description": "Markdown text format"},
            {"name": "text", "description": "Plain text"},
            {"name": "html", "description": "HyperText Markup Language"},
            {"name": "sql", "description": "SQL statements"}
        ],
        "auto_detection": True,
        "structure_inference": True
    }
