"""
Summarization Routes
"""
from typing import Literal
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models import SummarizeRequest, SummarizeResponse, ErrorResponse
from ..services import get_vllm_client, VLLMClientError

router = APIRouter(prefix="/summarize", tags=["Summarization"])


@router.post(
    "",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Summarize text",
    description="Generate a summary of the provided text.",
)
async def summarize_text(request: SummarizeRequest):
    """
    Summarize text.

    - **text**: The text to summarize (minimum 10 characters)
    - **max_length**: Maximum summary length in tokens
    - **min_length**: Minimum summary length in tokens
    - **style**: Summary style (bullet, paragraph, tldr)
    - **model**: Model to use (optional)
    """
    if len(request.text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Text must be at least 10 characters",
                "code": "TEXT_TOO_SHORT",
            }
        )

    client = get_vllm_client()

    try:
        result = await client.summarize(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            style=request.style or "paragraph",
            model=request.model,
        )

        return SummarizeResponse(
            success=True,
            summary=result["summary"],
            original_length=result["original_length"],
            summary_length=result["summary_length"],
            compression_ratio=result["compression_ratio"],
            model=result["model"],
        )

    except VLLMClientError as e:
        logger.error(f"Summarization error: {e.message}")
        raise HTTPException(
            status_code=503 if "connect" in e.message.lower() else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Unexpected error in summarize")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.post(
    "/bullets",
    summary="Bullet point summary",
    description="Generate a bullet point summary.",
)
async def summarize_bullets(text: str, max_bullets: int = 5):
    """
    Generate a bullet point summary.

    - **text**: Text to summarize
    - **max_bullets**: Maximum number of bullet points
    """
    request = SummarizeRequest(
        text=text,
        max_length=max_bullets * 30,  # Approximate tokens per bullet
        style="bullet",
    )
    return await summarize_text(request)


@router.post(
    "/tldr",
    summary="TL;DR summary",
    description="Generate a very brief TL;DR summary.",
)
async def summarize_tldr(text: str):
    """
    Generate a TL;DR summary.

    - **text**: Text to summarize
    """
    request = SummarizeRequest(
        text=text,
        max_length=50,
        style="tldr",
    )
    return await summarize_text(request)


@router.post(
    "/executive",
    summary="Executive summary",
    description="Generate an executive summary suitable for business contexts.",
)
async def executive_summary(text: str, max_length: int = 200):
    """
    Generate an executive summary.

    - **text**: Text to summarize
    - **max_length**: Maximum summary length in tokens
    """
    client = get_vllm_client()

    try:
        prompt = f"""Write an executive summary of the following text. 
Focus on key findings, main points, and actionable insights.
Keep the tone professional and concise.

Text:
{text}

Executive Summary:"""

        result = await client.generate(
            prompt=prompt,
            max_tokens=max_length,
            temperature=0.3,
        )

        original_tokens = client.count_tokens(text)
        summary_tokens = client.count_tokens(result["text"])

        return {
            "success": True,
            "summary": result["text"].strip(),
            "original_length": original_tokens,
            "summary_length": summary_tokens,
            "compression_ratio": original_tokens / max(summary_tokens, 1),
            "model": result["model"],
            "style": "executive",
        }

    except VLLMClientError as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": e.message, "code": e.code}
        )


@router.post(
    "/key-points",
    summary="Extract key points",
    description="Extract the key points from text.",
)
async def extract_key_points(text: str, num_points: int = 5):
    """
    Extract key points from text.

    - **text**: Text to analyze
    - **num_points**: Number of key points to extract
    """
    client = get_vllm_client()

    try:
        prompt = f"""Extract exactly {num_points} key points from the following text.
Format each point as a complete, standalone sentence.
Number each point.

Text:
{text}

Key Points:"""

        result = await client.generate(
            prompt=prompt,
            max_tokens=num_points * 50,
            temperature=0.2,
        )

        # Parse the key points
        response_text = result["text"].strip()
        lines = [line.strip() for line in response_text.split("\n") if line.strip()]

        # Extract numbered points
        key_points = []
        for line in lines:
            # Remove numbering
            cleaned = line.lstrip("0123456789.)-: ")
            if cleaned:
                key_points.append(cleaned)

        return {
            "success": True,
            "key_points": key_points[:num_points],
            "count": len(key_points[:num_points]),
            "model": result["model"],
        }

    except VLLMClientError as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": e.message, "code": e.code}
        )
