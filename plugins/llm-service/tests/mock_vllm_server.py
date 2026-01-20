"""
Mock vLLM Server for Testing

Implements OpenAI-compatible API endpoints for testing without actual model.
"""
import asyncio
import json
import os
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Mock vLLM Server")

RESPONSE_DELAY = float(os.getenv("RESPONSE_DELAY", "0.1"))
MODEL_NAME = os.getenv("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")


# =============================================================================
# Models
# =============================================================================

class Message(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    model: str = MODEL_NAME
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    stop: Optional[list[str]] = None


class ChatCompletionRequest(BaseModel):
    model: str = MODEL_NAME
    messages: list[Message]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    stop: Optional[list[str]] = None


# =============================================================================
# Mock Responses
# =============================================================================

MOCK_RESPONSES = {
    "classify": '{"label": "positive", "confidence": 0.85}',
    "extract": '{"entities": [{"text": "John Doe", "type": "PERSON"}, {"text": "Acme Corp", "type": "ORGANIZATION"}]}',
    "summarize": "This is a concise summary of the provided text, capturing the main points and key information in a condensed format.",
    "default": "This is a mock response from the vLLM server. The actual model would generate contextually relevant text based on your prompt.",
}


def get_mock_response(prompt: str) -> str:
    """Generate mock response based on prompt content."""
    prompt_lower = prompt.lower()

    if "classify" in prompt_lower or "sentiment" in prompt_lower:
        return MOCK_RESPONSES["classify"]
    elif "extract" in prompt_lower or "entities" in prompt_lower:
        return MOCK_RESPONSES["extract"]
    elif "summarize" in prompt_lower or "summary" in prompt_lower:
        return MOCK_RESPONSES["summarize"]

    return MOCK_RESPONSES["default"]


def create_completion_response(prompt: str, model: str) -> dict:
    """Create a completion response."""
    response_text = get_mock_response(prompt)

    return {
        "id": f"cmpl-{uuid.uuid4().hex[:12]}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "text": response_text,
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(response_text.split()),
            "total_tokens": len(prompt.split()) + len(response_text.split()),
        },
    }


def create_chat_response(messages: list[Message], model: str) -> dict:
    """Create a chat completion response."""
    # Get last user message for context
    last_message = ""
    for msg in reversed(messages):
        if msg.role == "user":
            last_message = msg.content
            break

    response_text = get_mock_response(last_message)

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.content.split()) for m in messages),
            "completion_tokens": len(response_text.split()),
            "total_tokens": sum(len(m.content.split()) for m in messages) + len(response_text.split()),
        },
    }


async def stream_completion(prompt: str, model: str):
    """Stream completion response."""
    response_text = get_mock_response(prompt)
    words = response_text.split()

    for i, word in enumerate(words):
        await asyncio.sleep(RESPONSE_DELAY / len(words))

        chunk = {
            "id": f"cmpl-{uuid.uuid4().hex[:12]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "text": word + " " if i < len(words) - 1 else word,
                    "logprobs": None,
                    "finish_reason": None if i < len(words) - 1 else "stop",
                }
            ],
        }

        yield f"data: {json.dumps(chunk)}\n\n"

    yield "data: [DONE]\n\n"


async def stream_chat_completion(messages: list[Message], model: str):
    """Stream chat completion response."""
    last_message = ""
    for msg in reversed(messages):
        if msg.role == "user":
            last_message = msg.content
            break

    response_text = get_mock_response(last_message)
    words = response_text.split()

    for i, word in enumerate(words):
        await asyncio.sleep(RESPONSE_DELAY / len(words))

        chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": "assistant" if i == 0 else None,
                        "content": word + " " if i < len(words) - 1 else word,
                    },
                    "logprobs": None,
                    "finish_reason": None if i < len(words) - 1 else "stop",
                }
            ],
        }

        # Remove None values from delta
        chunk["choices"][0]["delta"] = {
            k: v for k, v in chunk["choices"][0]["delta"].items() if v is not None
        }

        yield f"data: {json.dumps(chunk)}\n\n"

    yield "data: [DONE]\n\n"


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": int(time.time()) - 86400,
                "owned_by": "mock",
                "permission": [],
                "root": MODEL_NAME,
                "parent": None,
            }
        ],
    }


@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """Text completion endpoint."""
    await asyncio.sleep(RESPONSE_DELAY)

    if request.stream:
        return StreamingResponse(
            stream_completion(request.prompt, request.model),
            media_type="text/event-stream",
        )

    return create_completion_response(request.prompt, request.model)


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Chat completion endpoint."""
    await asyncio.sleep(RESPONSE_DELAY)

    if request.stream:
        return StreamingResponse(
            stream_chat_completion(request.messages, request.model),
            media_type="text/event-stream",
        )

    return create_chat_response(request.messages, request.model)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
