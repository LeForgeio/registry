"""
Chat Completion Routes
"""
import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from ..models import ChatRequest, ChatResponse, ChatResponseMessage, ErrorResponse
from ..services import get_vllm_client, VLLMClientError

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Chat completion",
    description="Generate a chat response from a conversation history.",
)
async def chat_completion(request: ChatRequest):
    """
    Generate a chat completion.

    - **messages**: List of chat messages with role (system/user/assistant) and content
    - **max_tokens**: Maximum number of tokens to generate
    - **temperature**: Sampling temperature, 0-2
    - **top_p**: Nucleus sampling parameter
    - **model**: Model to use (optional)
    - **stream**: Whether to stream the response
    """
    client = get_vllm_client()

    # Handle streaming
    if request.stream:
        return await chat_stream(request)

    try:
        result = await client.chat(
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            model=request.model,
        )

        return ChatResponse(
            success=True,
            message=ChatResponseMessage(role="assistant", content=result["message"]),
            tokens_used=result["usage"].total_tokens,
            usage=result["usage"],
            model=result["model"],
            finish_reason=result.get("finish_reason"),
        )

    except VLLMClientError as e:
        logger.error(f"Chat error: {e.message}")
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
        logger.exception("Unexpected error in chat")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


async def chat_stream(request: ChatRequest):
    """Stream chat completion using Server-Sent Events."""
    client = get_vllm_client()

    async def event_generator():
        full_message = ""
        try:
            async for chunk in client.chat_stream(
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                model=request.model,
            ):
                full_message += chunk
                yield {
                    "event": "token",
                    "data": json.dumps({"content": chunk}),
                }

            yield {
                "event": "done",
                "data": json.dumps({
                    "finished": True,
                    "message": full_message,
                }),
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
    "/simple",
    summary="Simple chat",
    description="Simple chat endpoint with just a user message.",
)
async def simple_chat(
    message: str,
    system_prompt: str = "You are a helpful assistant.",
    max_tokens: int = 256,
    temperature: float = 0.7,
):
    """
    Simple chat with just a user message.

    - **message**: The user's message
    - **system_prompt**: System prompt to set context
    - **max_tokens**: Maximum tokens to generate
    - **temperature**: Sampling temperature
    """
    from ..models import ChatMessage, MessageRole

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
        ChatMessage(role=MessageRole.USER, content=message),
    ]

    request = ChatRequest(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return await chat_completion(request)
