"""
Text Generation Routes
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from ..models import GenerateRequest, GenerateResponse, ErrorResponse
from ..services import get_vllm_client, VLLMClientError

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post(
    "",
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Generate text completion",
    description="Generate text from a prompt using the LLM.",
)
async def generate_text(request: GenerateRequest):
    """
    Generate text completion from a prompt.

    - **prompt**: The input prompt to generate from
    - **max_tokens**: Maximum number of tokens to generate (default: 256)
    - **temperature**: Sampling temperature, 0-2 (default: 0.7)
    - **top_p**: Nucleus sampling parameter (default: 0.95)
    - **stop**: List of stop sequences
    - **model**: Model to use (optional, uses default)
    - **stream**: Whether to stream the response
    """
    client = get_vllm_client()

    # Handle streaming
    if request.stream:
        return await generate_stream(request)

    try:
        result = await client.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            stop=request.stop,
            model=request.model,
        )

        return GenerateResponse(
            success=True,
            text=result["text"],
            tokens_used=result["usage"].total_tokens,
            usage=result["usage"],
            model=result["model"],
            finish_reason=result.get("finish_reason"),
        )

    except VLLMClientError as e:
        logger.error(f"Generation error: {e.message}")
        raise HTTPException(
            status_code=503 if "connect" in e.message.lower() else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
                "details": e.details,
            }
        )
    except Exception as e:
        logger.exception("Unexpected error in generate")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


async def generate_stream(request: GenerateRequest):
    """Stream text generation using Server-Sent Events."""
    client = get_vllm_client()

    async def event_generator():
        try:
            async for chunk in client.generate_stream(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop,
                model=request.model,
            ):
                yield {
                    "event": "token",
                    "data": json.dumps({"text": chunk}),
                }

            yield {
                "event": "done",
                "data": json.dumps({"finished": True}),
            }

        except VLLMClientError as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": e.message, "code": e.code}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e), "code": "STREAM_ERROR"}),
            }

    return EventSourceResponse(event_generator())


@router.post(
    "/batch",
    summary="Batch text generation",
    description="Generate text for multiple prompts in a batch.",
)
async def generate_batch(prompts: list[str], max_tokens: int = 256, temperature: float = 0.7):
    """
    Generate text for multiple prompts.

    - **prompts**: List of prompts to generate from
    - **max_tokens**: Maximum tokens per generation
    - **temperature**: Sampling temperature
    """
    client = get_vllm_client()
    results = []

    for prompt in prompts:
        try:
            result = await client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            results.append({
                "prompt": prompt,
                "text": result["text"],
                "tokens_used": result["usage"].total_tokens,
                "success": True,
            })
        except Exception as e:
            results.append({
                "prompt": prompt,
                "error": str(e),
                "success": False,
            })

    return {
        "success": True,
        "results": results,
        "total": len(prompts),
        "successful": sum(1 for r in results if r["success"]),
    }
