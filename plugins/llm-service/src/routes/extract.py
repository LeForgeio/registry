"""
Entity Extraction Routes
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models import ExtractEntitiesRequest, ExtractEntitiesResponse, Entity, ErrorResponse
from ..services import get_vllm_client, VLLMClientError

router = APIRouter(prefix="/extract-entities", tags=["Extraction"])


@router.post(
    "",
    response_model=ExtractEntitiesResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Extract entities",
    description="Extract named entities from text.",
)
async def extract_entities(request: ExtractEntitiesRequest):
    """
    Extract named entities from text.

    - **text**: The text to extract entities from
    - **entity_types**: Types of entities to extract (optional)
      - person, organization, location, date, time
      - money, percentage, email, phone, url
      - product, event, custom
    - **model**: Model to use (optional)
    """
    client = get_vllm_client()

    try:
        result = await client.extract_entities(
            text=request.text,
            entity_types=request.entity_types,
            model=request.model,
        )

        # Convert to Entity objects
        entities = [
            Entity(
                text=e["text"],
                type=e["type"],
                start=e["start"],
                end=e["end"],
                confidence=e.get("confidence"),
            )
            for e in result["entities"]
        ]

        return ExtractEntitiesResponse(
            success=True,
            entities=entities,
            text=result["text"],
            model=result["model"],
        )

    except VLLMClientError as e:
        logger.error(f"Entity extraction error: {e.message}")
        raise HTTPException(
            status_code=503 if "connect" in e.message.lower() else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Unexpected error in extract_entities")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.post(
    "/pii",
    summary="Extract PII",
    description="Extract personally identifiable information from text.",
)
async def extract_pii(text: str, mask: bool = False):
    """
    Extract PII (Personally Identifiable Information) from text.

    - **text**: Text to analyze
    - **mask**: Whether to return masked text
    """
    pii_types = ["person", "email", "phone", "date", "location", "organization"]

    request = ExtractEntitiesRequest(text=text, entity_types=pii_types)
    result = await extract_entities(request)

    if mask:
        # Mask the PII in the text
        masked_text = text
        # Sort by position descending to preserve indices
        sorted_entities = sorted(result.entities, key=lambda e: e.start, reverse=True)
        for entity in sorted_entities:
            mask_str = f"[{entity.type.upper()}]"
            masked_text = masked_text[:entity.start] + mask_str + masked_text[entity.end:]

        return {
            "success": True,
            "entities": result.entities,
            "original_text": text,
            "masked_text": masked_text,
            "model": result.model,
        }

    return result


@router.post(
    "/contacts",
    summary="Extract contact information",
    description="Extract contact details like emails, phones, and addresses.",
)
async def extract_contacts(text: str):
    """
    Extract contact information from text.

    - **text**: Text to extract contacts from
    """
    contact_types = ["email", "phone", "url", "location"]

    request = ExtractEntitiesRequest(text=text, entity_types=contact_types)
    return await extract_entities(request)


@router.post(
    "/custom",
    summary="Extract custom entities",
    description="Extract custom entity types from text.",
)
async def extract_custom_entities(
    text: str,
    entity_types: list[str],
    examples: dict[str, list[str]] = None,
):
    """
    Extract custom entity types.

    - **text**: Text to extract from
    - **entity_types**: Custom entity types to find
    - **examples**: Optional examples for each type
    """
    if not entity_types:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "At least one entity type is required",
                "code": "INVALID_ENTITY_TYPES",
            }
        )

    # For now, use the standard extraction
    # Future: Could enhance with examples for few-shot learning
    request = ExtractEntitiesRequest(text=text, entity_types=entity_types)
    return await extract_entities(request)
