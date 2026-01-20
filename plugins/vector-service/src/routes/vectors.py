"""
Vector Operations Routes - Upsert, Search, Recommend
"""
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Path, Query
from loguru import logger

from ..models import (
    UpsertRequest,
    UpsertTextRequest,
    UpsertResponse,
    DeletePointsRequest,
    DeletePointsResponse,
    SearchRequest,
    SearchTextRequest,
    HybridSearchRequest,
    SearchResponse,
    SearchResult,
    RecommendRequest,
    RecommendResponse,
    BatchSearchRequest,
    BatchSearchResponse,
    ErrorResponse,
)
from ..services import (
    get_qdrant_service,
    get_embedding_service,
    QdrantServiceError,
    EmbeddingServiceError,
)

router = APIRouter(tags=["Vectors"])


# =============================================================================
# Upsert Operations
# =============================================================================

@router.post(
    "/collections/{name}/upsert",
    response_model=UpsertResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Upsert vectors",
    description="Insert or update vectors in a collection.",
)
async def upsert_vectors(
    request: UpsertRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Upsert vectors into a collection.

    - **name**: Target collection name
    - **points**: List of points with id, vector, and optional payload
    - **wait**: Wait for indexing to complete
    """
    qdrant = get_qdrant_service()

    try:
        points = [
            {
                "id": p.id,
                "vector": p.vector,
                "payload": p.payload,
            }
            for p in request.points
        ]

        result = await qdrant.upsert_points(
            collection_name=name,
            points=points,
            wait=request.wait,
        )

        return UpsertResponse(
            success=True,
            status=result["status"],
            count=result["count"],
        )

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Upsert failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.post(
    "/collections/{name}/upsert-text",
    response_model=UpsertResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Upsert with text",
    description="Upsert points with automatic text embedding.",
)
async def upsert_text(
    request: UpsertTextRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Upsert points with automatic text embedding.

    Text is automatically converted to vectors using the embedding service.

    - **name**: Target collection name
    - **points**: List of points with id, text, and optional payload
    """
    qdrant = get_qdrant_service()
    embedding_service = get_embedding_service()

    try:
        # Extract texts for batch embedding
        texts = [p.text for p in request.points]

        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings(texts)

        # Build points with vectors
        points = []
        for i, p in enumerate(request.points):
            payload = p.payload or {}
            payload["text"] = p.text  # Store original text
            points.append({
                "id": p.id,
                "vector": embeddings[i],
                "payload": payload,
            })

        result = await qdrant.upsert_points(
            collection_name=name,
            points=points,
            wait=request.wait,
        )

        return UpsertResponse(
            success=True,
            status=result["status"],
            count=result["count"],
        )

    except EmbeddingServiceError as e:
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Upsert text failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.post(
    "/collections/{name}/delete",
    response_model=DeletePointsResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Delete points",
    description="Delete points by their IDs.",
)
async def delete_points(
    request: DeletePointsRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Delete points from a collection.

    - **name**: Collection name
    - **ids**: List of point IDs to delete
    """
    qdrant = get_qdrant_service()

    try:
        count = await qdrant.delete_points(
            collection_name=name,
            ids=request.ids,
            wait=request.wait,
        )

        return DeletePointsResponse(
            success=True,
            count=count,
        )

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Delete failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


# =============================================================================
# Search Operations
# =============================================================================

@router.post(
    "/collections/{name}/search",
    response_model=SearchResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Vector search",
    description="Search for similar vectors.",
)
async def search_vectors(
    request: SearchRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Search for similar vectors.

    - **name**: Collection to search
    - **vector**: Query vector
    - **limit**: Maximum results (default 10)
    - **filter**: Optional Qdrant filter
    - **score_threshold**: Minimum similarity score
    """
    qdrant = get_qdrant_service()

    try:
        start_time = time.time()

        results = await qdrant.search(
            collection_name=name,
            vector=request.vector,
            limit=request.limit,
            offset=request.offset,
            filter=request.filter,
            score_threshold=request.score_threshold,
            with_payload=request.with_payload,
            with_vectors=request.with_vectors,
        )

        query_time = (time.time() - start_time) * 1000

        return SearchResponse(
            success=True,
            results=[SearchResult(**r) for r in results],
            count=len(results),
            query_time_ms=round(query_time, 2),
        )

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.post(
    "/collections/{name}/search-text",
    response_model=SearchResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Text search",
    description="Search using text (auto-generates embedding).",
)
async def search_by_text(
    request: SearchTextRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Search by text with automatic embedding.

    Text is converted to a vector using the embedding service.

    - **name**: Collection to search
    - **text**: Query text
    - **limit**: Maximum results
    - **filter**: Optional filter
    """
    qdrant = get_qdrant_service()
    embedding_service = get_embedding_service()

    try:
        start_time = time.time()

        # Generate embedding for query text
        query_vector = await embedding_service.generate_single(request.text)

        results = await qdrant.search(
            collection_name=name,
            vector=query_vector,
            limit=request.limit,
            offset=request.offset,
            filter=request.filter,
            score_threshold=request.score_threshold,
            with_payload=request.with_payload,
            with_vectors=request.with_vectors,
        )

        query_time = (time.time() - start_time) * 1000

        return SearchResponse(
            success=True,
            results=[SearchResult(**r) for r in results],
            count=len(results),
            query_time_ms=round(query_time, 2),
        )

    except EmbeddingServiceError as e:
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Text search failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.post(
    "/collections/{name}/hybrid-search",
    response_model=SearchResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Hybrid search",
    description="Combine vector search with keyword filtering.",
)
async def hybrid_search(
    request: HybridSearchRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Hybrid search combining vector similarity and keyword matching.

    - **name**: Collection to search
    - **text**: Query text (used for both embedding and keyword match)
    - **keyword_fields**: Payload fields for keyword matching
    - **vector_weight**: Weight for vector similarity (0-1)
    """
    qdrant = get_qdrant_service()
    embedding_service = get_embedding_service()

    try:
        start_time = time.time()

        # Generate embedding for query text
        query_vector = await embedding_service.generate_single(request.text)

        # Build keyword filter
        # Search for query words in specified fields
        query_words = request.text.lower().split()
        keyword_filter = None

        if request.filter:
            keyword_filter = request.filter
        else:
            # Create a simple text match filter
            # Qdrant uses "should" for OR conditions
            should_conditions = []
            for field in request.keyword_fields:
                for word in query_words[:5]:  # Limit to first 5 words
                    should_conditions.append({
                        "key": field,
                        "match": {"text": word}
                    })

            if should_conditions:
                keyword_filter = {"should": should_conditions}

        # Perform vector search with filter
        results = await qdrant.search(
            collection_name=name,
            vector=query_vector,
            limit=request.limit * 2,  # Get more for re-ranking
            filter=keyword_filter,
            with_payload=request.with_payload,
        )

        # Re-rank based on keyword presence
        def score_keywords(payload: dict) -> float:
            if not payload:
                return 0.0
            text_content = ""
            for field in request.keyword_fields:
                if field in payload:
                    text_content += " " + str(payload[field]).lower()
            if not text_content:
                return 0.0
            # Count matching words
            matches = sum(1 for word in query_words if word in text_content)
            return matches / max(len(query_words), 1)

        # Combine scores
        ranked_results = []
        for r in results:
            keyword_score = score_keywords(r.get("payload", {}))
            combined_score = (
                request.vector_weight * r["score"] +
                (1 - request.vector_weight) * keyword_score
            )
            ranked_results.append({
                **r,
                "score": combined_score,
            })

        # Sort by combined score
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        ranked_results = ranked_results[:request.limit]

        query_time = (time.time() - start_time) * 1000

        return SearchResponse(
            success=True,
            results=[SearchResult(**r) for r in ranked_results],
            count=len(ranked_results),
            query_time_ms=round(query_time, 2),
        )

    except EmbeddingServiceError as e:
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Hybrid search failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.post(
    "/collections/{name}/search-batch",
    response_model=BatchSearchResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Batch search",
    description="Execute multiple searches in one request.",
)
async def batch_search(
    request: BatchSearchRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Batch vector search.

    - **name**: Collection to search
    - **searches**: List of search requests
    """
    qdrant = get_qdrant_service()

    try:
        vectors = [s.vector for s in request.searches]
        limit = request.searches[0].limit if request.searches else 10

        results = await qdrant.search_batch(
            collection_name=name,
            vectors=vectors,
            limit=limit,
        )

        return BatchSearchResponse(
            success=True,
            results=[[SearchResult(**r) for r in batch] for batch in results],
            count=len(results),
        )

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Batch search failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


# =============================================================================
# Recommendations
# =============================================================================

@router.post(
    "/collections/{name}/recommend",
    response_model=RecommendResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get recommendations",
    description="Get similar vectors based on positive/negative examples.",
)
async def recommend(
    request: RecommendRequest,
    name: str = Path(..., description="Collection name"),
):
    """
    Get recommendations based on example vectors.

    - **name**: Collection to search
    - **positive**: IDs of vectors to find similar to
    - **negative**: IDs of vectors to find dissimilar to
    - **limit**: Maximum results
    - **strategy**: Recommendation strategy (average_vector, best_score)
    """
    qdrant = get_qdrant_service()

    try:
        results = await qdrant.recommend(
            collection_name=name,
            positive=request.positive,
            negative=request.negative,
            limit=request.limit,
            filter=request.filter,
            with_payload=request.with_payload,
            with_vectors=request.with_vectors,
            strategy=request.strategy,
        )

        return RecommendResponse(
            success=True,
            results=[SearchResult(**r) for r in results],
            count=len(results),
        )

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Recommend failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


# =============================================================================
# Point Retrieval
# =============================================================================

@router.get(
    "/collections/{name}/points",
    summary="Get points",
    description="Retrieve points by their IDs.",
)
async def get_points(
    name: str = Path(..., description="Collection name"),
    ids: str = Query(..., description="Comma-separated point IDs"),
    with_payload: bool = Query(default=True),
    with_vectors: bool = Query(default=False),
):
    """
    Get specific points by IDs.

    - **name**: Collection name
    - **ids**: Comma-separated point IDs
    """
    qdrant = get_qdrant_service()

    try:
        # Parse IDs
        id_list = [id.strip() for id in ids.split(",")]
        # Try to convert to int if possible
        parsed_ids = []
        for id in id_list:
            try:
                parsed_ids.append(int(id))
            except ValueError:
                parsed_ids.append(id)

        points = await qdrant.get_points(
            collection_name=name,
            ids=parsed_ids,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

        return {
            "success": True,
            "points": points,
            "count": len(points),
        }

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Get points failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.get(
    "/collections/{name}/scroll",
    summary="Scroll points",
    description="Scroll through collection points.",
)
async def scroll_points(
    name: str = Path(..., description="Collection name"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: Optional[str] = Query(default=None, description="Pagination offset"),
    with_payload: bool = Query(default=True),
    with_vectors: bool = Query(default=False),
):
    """
    Scroll through collection points.

    - **name**: Collection name
    - **limit**: Points per page
    - **offset**: Pagination offset from previous response
    """
    qdrant = get_qdrant_service()

    try:
        # Parse offset
        parsed_offset = None
        if offset:
            try:
                parsed_offset = int(offset)
            except ValueError:
                parsed_offset = offset

        result = await qdrant.scroll(
            collection_name=name,
            limit=limit,
            offset=parsed_offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

        return {
            "success": True,
            "points": result["points"],
            "count": len(result["points"]),
            "next_offset": result["next_offset"],
        }

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
        raise HTTPException(status_code=500, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.exception("Scroll failed")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})
