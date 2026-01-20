"""
Embeddings Routes
"""
from typing import Union, List
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models import EmbeddingsRequest, EmbeddingsResponse, ErrorResponse
from ..services import get_embedding_service, EmbeddingServiceError

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@router.post(
    "",
    response_model=EmbeddingsResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Generate embeddings",
    description="Generate vector embeddings for text.",
)
async def create_embeddings(request: EmbeddingsRequest):
    """
    Generate embeddings for text.

    - **text**: Single text string or list of texts
    - **model**: Embedding model to use (optional)
    - **normalize**: Whether to normalize embeddings (default: true)
    """
    service = get_embedding_service()

    try:
        result = await service.embed(
            texts=request.text,
            normalize=request.normalize,
            model=request.model,
        )

        return EmbeddingsResponse(
            success=True,
            embeddings=result["embeddings"],
            dimensions=result["dimensions"],
            model=result["model"],
            tokens_used=result["tokens_used"],
        )

    except EmbeddingServiceError as e:
        logger.error(f"Embedding error: {e.message}")
        status_code = 503 if e.code == "MODEL_LOAD_ERROR" else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Unexpected error in embeddings")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.post(
    "/similarity",
    summary="Compute similarity",
    description="Compute cosine similarity between two texts.",
)
async def compute_similarity(text1: str, text2: str):
    """
    Compute similarity between two texts.

    - **text1**: First text
    - **text2**: Second text

    Returns a similarity score between 0 and 1.
    """
    service = get_embedding_service()

    try:
        similarity = await service.similarity(text1, text2)

        return {
            "success": True,
            "similarity": similarity,
            "text1": text1[:100] + "..." if len(text1) > 100 else text1,
            "text2": text2[:100] + "..." if len(text2) > 100 else text2,
            "model": service.model_name,
        }

    except EmbeddingServiceError as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": e.message, "code": e.code}
        )


@router.post(
    "/batch",
    summary="Batch embeddings",
    description="Generate embeddings for a batch of texts.",
)
async def batch_embeddings(texts: List[str], normalize: bool = True):
    """
    Generate embeddings for multiple texts.

    - **texts**: List of texts to embed
    - **normalize**: Whether to normalize embeddings
    """
    if not texts:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "No texts provided",
                "code": "EMPTY_INPUT",
            }
        )

    if len(texts) > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Maximum 100 texts per batch",
                "code": "BATCH_TOO_LARGE",
            }
        )

    request = EmbeddingsRequest(text=texts, normalize=normalize)
    return await create_embeddings(request)


@router.post(
    "/search",
    summary="Semantic search",
    description="Find most similar texts from a corpus.",
)
async def semantic_search(
    query: str,
    corpus: List[str],
    top_k: int = 5,
):
    """
    Find most similar texts to a query.

    - **query**: Search query
    - **corpus**: List of texts to search through
    - **top_k**: Number of results to return
    """
    import numpy as np

    if not corpus:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "Corpus is empty", "code": "EMPTY_CORPUS"}
        )

    service = get_embedding_service()

    try:
        # Embed query and corpus together
        all_texts = [query] + corpus
        result = await service.embed(all_texts, normalize=True)

        embeddings = np.array(result["embeddings"])
        query_embedding = embeddings[0]
        corpus_embeddings = embeddings[1:]

        # Compute similarities
        similarities = np.dot(corpus_embeddings, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "text": corpus[idx],
                "score": float(similarities[idx]),
                "index": int(idx),
            })

        return {
            "success": True,
            "query": query,
            "results": results,
            "total_corpus": len(corpus),
            "model": result["model"],
        }

    except EmbeddingServiceError as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": e.message, "code": e.code}
        )


@router.get(
    "/info",
    summary="Embedding model info",
    description="Get information about the embedding model.",
)
async def embedding_info():
    """Get embedding model information."""
    service = get_embedding_service()
    return {
        "success": True,
        "model": service.get_info(),
    }
