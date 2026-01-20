"""
Vision Routes - OCR, image description, and structured extraction.

Uses vision-language models for intelligent image understanding.
"""
import time
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from ..models import (
    VisionOCRRequest,
    VisionOCRResponse,
    VisionDescribeRequest,
    VisionDescribeResponse,
    VisionExtractRequest,
    VisionExtractResponse,
    OCRRegion,
    ExtractedField,
    ErrorResponse,
)
from ..services.vision_service import get_vision_service, VisionServiceError

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.post(
    "/ocr",
    response_model=VisionOCRResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Processing error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
    summary="Vision OCR",
    description="""
Extract text from images using vision-language models.

Unlike traditional OCR, vision-based OCR can:
- Understand context and correct errors
- Handle handwriting and messy documents
- Preserve layout and structure
- Work with complex layouts (tables, forms, etc.)

**When to use:**
- Handwritten documents
- Complex layouts
- Documents needing context understanding
- When traditional OCR fails

**For bulk/fast OCR:** Use the dedicated OCR service (Tesseract-based) instead.
    """,
)
async def vision_ocr(request: VisionOCRRequest, req: Request):
    """
    Perform OCR using vision-language model.
    
    - **image**: Image input (URL or base64)
    - **output_format**: 'text' (plain), 'structured' (with regions), 'markdown'
    - **detail_level**: 'low' (fast), 'medium', 'high' (thorough)
    - **preserve_layout**: Try to maintain original formatting
    - **language_hints**: Languages present in the document
    """
    start_time = time.time()
    request_id = getattr(req.state, "request_id", "unknown")
    
    service = get_vision_service()
    
    try:
        # Prepare image
        image_bytes, media_type = await service.prepare_image(
            url=request.image.url,
            base64_data=request.image.base64,
            media_type=request.image.media_type
        )
        
        logger.info(
            f"Processing vision OCR request",
            extra={
                "request_id": request_id,
                "image_size": len(image_bytes),
                "output_format": request.output_format,
                "detail_level": request.detail_level
            }
        )
        
        # Perform OCR
        result = await service.ocr(
            image_bytes=image_bytes,
            media_type=media_type,
            output_format=request.output_format,
            detail_level=request.detail_level,
            preserve_layout=request.preserve_layout,
            language_hints=request.language_hints,
            model=request.model
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Convert regions to response format
        regions = None
        if result.get("regions"):
            regions = [
                OCRRegion(
                    text=r["text"],
                    confidence=r.get("confidence", 0.8),
                    bbox=r.get("bbox"),
                    line_number=r.get("line_number"),
                    word_count=len(r["text"].split()) if r.get("text") else 0
                )
                for r in result["regions"]
            ]
        
        logger.info(
            f"Vision OCR completed",
            extra={
                "request_id": request_id,
                "word_count": result["word_count"],
                "processing_time_ms": processing_time
            }
        )
        
        return VisionOCRResponse(
            success=True,
            text=result["text"],
            regions=regions,
            confidence=result["confidence"],
            word_count=result["word_count"],
            model=result["model"],
            processing_time_ms=processing_time
        )
        
    except VisionServiceError as e:
        logger.error(f"Vision OCR error: {e.message}", extra={"request_id": request_id})
        status_code = 400 if e.code in ["NO_IMAGE", "INVALID_BASE64", "IMAGE_TOO_LARGE"] else 503
        raise HTTPException(
            status_code=status_code,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Unexpected error in vision_ocr")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.post(
    "/describe",
    response_model=VisionDescribeResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Describe image",
    description="""
Generate a natural language description of an image.

The vision model will analyze the image and produce a detailed
description based on the specified focus area.
    """,
)
async def vision_describe(request: VisionDescribeRequest, req: Request):
    """
    Generate description of an image.
    
    - **image**: Image input (URL or base64)
    - **prompt**: Custom prompt (optional)
    - **max_length**: Maximum description length
    - **focus**: What to focus on ('general', 'objects', 'text', 'people', 'scene')
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_vision_service()
    
    try:
        image_bytes, media_type = await service.prepare_image(
            url=request.image.url,
            base64_data=request.image.base64,
            media_type=request.image.media_type
        )
        
        logger.info(
            f"Processing vision describe request",
            extra={"request_id": request_id, "focus": request.focus}
        )
        
        result = await service.describe(
            image_bytes=image_bytes,
            media_type=media_type,
            prompt=request.prompt,
            max_length=request.max_length,
            focus=request.focus,
            model=request.model
        )
        
        return VisionDescribeResponse(
            success=True,
            description=result["description"],
            objects_detected=result.get("objects_detected"),
            text_detected=result.get("text_detected"),
            model=result["model"]
        )
        
    except VisionServiceError as e:
        logger.error(f"Vision describe error: {e.message}")
        raise HTTPException(
            status_code=400 if "image" in e.code.lower() else 500,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in vision_describe")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/extract",
    response_model=VisionExtractResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Extract structured data from image",
    description="""
Extract specific fields from documents, forms, receipts, invoices, etc.

The vision model understands document context and can extract:
- Invoice fields (number, date, total, line items)
- Receipt data (merchant, items, totals)
- Form fields (name, address, etc.)
- Any custom fields you specify
    """,
)
async def vision_extract(request: VisionExtractRequest, req: Request):
    """
    Extract structured data from image.
    
    - **image**: Image input (URL or base64)
    - **fields**: Field names to extract
    - **document_type**: Document type hint (optional)
    - **schema**: JSON schema for output (optional)
    - **examples**: Few-shot examples (optional)
    """
    request_id = getattr(req.state, "request_id", "unknown")
    service = get_vision_service()
    
    try:
        image_bytes, media_type = await service.prepare_image(
            url=request.image.url,
            base64_data=request.image.base64,
            media_type=request.image.media_type
        )
        
        logger.info(
            f"Processing vision extract request",
            extra={
                "request_id": request_id,
                "fields": request.fields,
                "document_type": request.document_type
            }
        )
        
        result = await service.extract_fields(
            image_bytes=image_bytes,
            media_type=media_type,
            fields=request.fields,
            document_type=request.document_type,
            schema=request.schema,
            examples=request.examples,
            model=request.model
        )
        
        # Convert to response format
        fields = [
            ExtractedField(
                name=f["name"],
                value=f["value"],
                confidence=f.get("confidence", 0.8),
                location=f.get("location")
            )
            for f in result["fields"]
        ]
        
        return VisionExtractResponse(
            success=True,
            fields=fields,
            raw_data=result.get("raw_data"),
            document_type=result.get("document_type"),
            confidence=result["confidence"],
            model=result["model"]
        )
        
    except VisionServiceError as e:
        logger.error(f"Vision extract error: {e.message}")
        raise HTTPException(
            status_code=400 if "image" in e.code.lower() else 500,
            detail={"success": False, "error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in vision_extract")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.post(
    "/analyze",
    summary="Analyze image with custom prompt",
    description="Analyze image using a custom prompt for flexible querying.",
)
async def vision_analyze(
    image_url: str = None,
    image_base64: str = None,
    prompt: str = "Analyze this image and describe what you see.",
    max_tokens: int = 500,
    model: str = None,
    req: Request = None,
):
    """
    Flexible image analysis with custom prompt.
    
    - **image_url**: URL to image
    - **image_base64**: Base64-encoded image
    - **prompt**: Custom analysis prompt
    - **max_tokens**: Maximum response length
    """
    request_id = getattr(req.state, "request_id", "unknown") if req else "unknown"
    service = get_vision_service()
    
    try:
        image_bytes, media_type = await service.prepare_image(
            url=image_url,
            base64_data=image_base64
        )
        
        # Use describe with custom prompt
        result = await service.describe(
            image_bytes=image_bytes,
            media_type=media_type,
            prompt=prompt,
            max_length=max_tokens,
            model=model
        )
        
        return {
            "success": True,
            "analysis": result["description"],
            "model": result["model"]
        }
        
    except VisionServiceError as e:
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
    "/models",
    summary="List available vision models",
    description="Get list of available vision-language models.",
)
async def list_vision_models():
    """List available vision models."""
    from ..config import settings
    
    return {
        "default_model": settings.vision_model,
        "available_models": [
            {
                "name": settings.vision_model,
                "capabilities": ["ocr", "describe", "extract"],
                "max_image_size_mb": settings.max_image_size_mb
            }
        ],
        "supported_formats": ["png", "jpeg", "jpg", "webp", "gif"]
    }
