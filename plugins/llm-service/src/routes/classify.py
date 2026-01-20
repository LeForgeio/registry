"""
Classification Routes
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models import ClassifyRequest, ClassifyResponse, CategoryScore, ErrorResponse
from ..services import get_vllm_client, VLLMClientError

router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post(
    "",
    response_model=ClassifyResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Classify text",
    description="Classify text into one of the provided categories.",
)
async def classify_text(request: ClassifyRequest):
    """
    Classify text into categories.

    - **text**: The text to classify
    - **categories**: List of possible categories (at least 2)
    - **model**: Model to use (optional)
    - **multi_label**: Allow multiple category assignments
    """
    if len(request.categories) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "At least 2 categories are required",
                "code": "INVALID_CATEGORIES",
            }
        )

    client = get_vllm_client()

    try:
        result = await client.classify(
            text=request.text,
            categories=request.categories,
            model=request.model,
            multi_label=request.multi_label,
        )

        # Convert scores to CategoryScore objects
        scores = [
            CategoryScore(category=s["category"], confidence=s["confidence"])
            for s in result.get("scores", [])
        ]

        return ClassifyResponse(
            success=True,
            category=result["category"],
            confidence=result["confidence"],
            scores=scores if scores else None,
            model=result["model"],
        )

    except VLLMClientError as e:
        logger.error(f"Classification error: {e.message}")
        raise HTTPException(
            status_code=503 if "connect" in e.message.lower() else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Unexpected error in classify")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.post(
    "/sentiment",
    summary="Sentiment analysis",
    description="Analyze sentiment of text (positive, negative, neutral).",
)
async def analyze_sentiment(text: str, detailed: bool = False):
    """
    Analyze sentiment of text.

    - **text**: Text to analyze
    - **detailed**: Include detailed scores
    """
    categories = ["positive", "negative", "neutral"]
    if detailed:
        categories.extend(["very_positive", "very_negative", "mixed"])

    request = ClassifyRequest(text=text, categories=categories)
    return await classify_text(request)


@router.post(
    "/intent",
    summary="Intent classification",
    description="Classify the intent of a user message.",
)
async def classify_intent(text: str, intents: list[str] = None):
    """
    Classify user intent.

    - **text**: User message
    - **intents**: Custom intents (optional)
    """
    default_intents = [
        "question",
        "command",
        "statement",
        "greeting",
        "farewell",
        "complaint",
        "request",
        "other",
    ]
    categories = intents or default_intents

    request = ClassifyRequest(text=text, categories=categories)
    return await classify_text(request)


@router.post(
    "/topic",
    summary="Topic classification",
    description="Classify the topic of a text.",
)
async def classify_topic(text: str, topics: list[str]):
    """
    Classify the topic of text.

    - **text**: Text to classify
    - **topics**: List of possible topics
    """
    if len(topics) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "At least 2 topics are required",
                "code": "INVALID_TOPICS",
            }
        )

    request = ClassifyRequest(text=text, categories=topics)
    return await classify_text(request)
