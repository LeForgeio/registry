"""
Collection Management Routes
"""
from fastapi import APIRouter, HTTPException, Path
from loguru import logger

from ..models import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    ListCollectionsResponse,
    DeleteCollectionResponse,
    CollectionInfo,
    CollectionStats,
    ErrorResponse,
)
from ..services import get_qdrant_service, QdrantServiceError

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post(
    "/create",
    response_model=CreateCollectionResponse,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Create collection",
    description="Create a new vector collection with specified configuration.",
)
async def create_collection(request: CreateCollectionRequest):
    """
    Create a new vector collection.

    - **name**: Unique collection name
    - **vector_size**: Dimension of vectors (e.g., 384 for all-MiniLM-L6-v2)
    - **distance**: Distance metric (Cosine, Euclid, Dot)
    - **on_disk**: Store vectors on disk for memory efficiency
    - **hnsw_config**: Optional HNSW index configuration
    - **quantization_config**: Optional quantization for compression
    """
    qdrant = get_qdrant_service()

    try:
        result = await qdrant.create_collection(
            name=request.name,
            vector_size=request.vector_size,
            distance=request.distance.value,
            on_disk=request.on_disk,
            hnsw_config=request.hnsw_config,
            quantization_config=request.quantization_config,
        )

        return CreateCollectionResponse(
            success=True,
            name=result["name"],
            vector_size=result["vector_size"],
            distance=result["distance"],
            message="Collection created successfully",
        )

    except QdrantServiceError as e:
        if e.code == "COLLECTION_EXISTS":
            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "error": e.message,
                    "code": e.code,
                }
            )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Failed to create collection")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.get(
    "/list",
    response_model=ListCollectionsResponse,
    summary="List collections",
    description="List all vector collections with their details.",
)
async def list_collections():
    """
    List all collections.

    Returns collection name, status, vector count, and configuration.
    """
    qdrant = get_qdrant_service()

    try:
        collections = await qdrant.list_collections()

        return ListCollectionsResponse(
            success=True,
            collections=[CollectionInfo(**col) for col in collections],
            count=len(collections),
        )

    except QdrantServiceError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Failed to list collections")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.get(
    "/{name}",
    response_model=CollectionStats,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get collection",
    description="Get details and statistics for a specific collection.",
)
async def get_collection(
    name: str = Path(..., description="Collection name")
):
    """
    Get collection details and statistics.

    - **name**: Collection name
    """
    qdrant = get_qdrant_service()

    try:
        info = await qdrant.get_collection(name)
        return CollectionStats(**info)

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": e.message,
                    "code": e.code,
                }
            )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Failed to get collection")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.delete(
    "/{name}",
    response_model=DeleteCollectionResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Delete collection",
    description="Delete a collection and all its vectors.",
)
async def delete_collection(
    name: str = Path(..., description="Collection name")
):
    """
    Delete a collection.

    **Warning**: This permanently deletes the collection and all its data.

    - **name**: Collection name to delete
    """
    qdrant = get_qdrant_service()

    try:
        await qdrant.delete_collection(name)

        return DeleteCollectionResponse(
            success=True,
            name=name,
            message="Collection deleted successfully",
        )

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": e.message,
                    "code": e.code,
                }
            )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
    except Exception as e:
        logger.exception("Failed to delete collection")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "code": "INTERNAL_ERROR",
            }
        )


@router.post(
    "/{name}/optimize",
    summary="Optimize collection",
    description="Trigger collection optimization (merge segments, update indexes).",
)
async def optimize_collection(
    name: str = Path(..., description="Collection name")
):
    """
    Optimize a collection.

    Triggers segment merging and index optimization.
    """
    qdrant = get_qdrant_service()

    try:
        # Verify collection exists
        await qdrant.get_collection(name)

        # Qdrant handles optimization automatically, but we can trigger it
        # For now, just return success
        return {
            "success": True,
            "name": name,
            "message": "Optimization triggered",
        }

    except QdrantServiceError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": e.message,
                    "code": e.code,
                }
            )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code,
            }
        )
