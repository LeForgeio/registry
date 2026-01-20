"""
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class DistanceMetric(str, Enum):
    """Vector distance metrics."""
    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"


class CollectionStatus(str, Enum):
    """Collection status."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# =============================================================================
# Common Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None)


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str = Field(default="Operation completed successfully")


# =============================================================================
# Collection Models
# =============================================================================

class VectorParams(BaseModel):
    """Vector configuration parameters."""
    size: int = Field(..., description="Vector dimensions", ge=1)
    distance: DistanceMetric = Field(default=DistanceMetric.COSINE)
    on_disk: bool = Field(default=False, description="Store vectors on disk")


class CreateCollectionRequest(BaseModel):
    """Request to create a collection."""
    name: str = Field(..., description="Collection name", min_length=1, max_length=255)
    vector_size: int = Field(
        default=384,
        description="Vector dimensions",
        ge=1,
        le=65535
    )
    distance: DistanceMetric = Field(default=DistanceMetric.COSINE)
    on_disk: bool = Field(default=False)
    hnsw_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="HNSW index configuration"
    )
    quantization_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Quantization configuration"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "documents",
                "vector_size": 384,
                "distance": "Cosine"
            }
        }


class CreateCollectionResponse(BaseModel):
    """Response for collection creation."""
    success: bool = True
    name: str
    vector_size: int
    distance: str
    message: str = "Collection created successfully"


class CollectionInfo(BaseModel):
    """Information about a collection."""
    name: str
    status: CollectionStatus
    vectors_count: int
    points_count: int
    indexed_vectors_count: int
    vector_size: int
    distance: str
    on_disk: bool


class ListCollectionsResponse(BaseModel):
    """Response for listing collections."""
    success: bool = True
    collections: List[CollectionInfo]
    count: int


class DeleteCollectionResponse(BaseModel):
    """Response for collection deletion."""
    success: bool = True
    name: str
    message: str = "Collection deleted successfully"


# =============================================================================
# Point/Vector Models
# =============================================================================

class PointPayload(BaseModel):
    """Payload attached to a point."""
    # Allow any key-value pairs
    class Config:
        extra = "allow"


class Point(BaseModel):
    """A point to upsert."""
    id: Union[str, int] = Field(..., description="Unique point identifier")
    vector: List[float] = Field(..., description="Vector embedding")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc-1",
                "vector": [0.1, 0.2, 0.3],
                "payload": {"text": "Hello world", "source": "example"}
            }
        }


class PointWithText(BaseModel):
    """A point with text to be embedded."""
    id: Union[str, int] = Field(..., description="Unique point identifier")
    text: str = Field(..., description="Text to embed")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Metadata")


class UpsertRequest(BaseModel):
    """Request to upsert points."""
    points: List[Point] = Field(..., description="Points to upsert", min_length=1)
    wait: bool = Field(default=True, description="Wait for indexing")

    class Config:
        json_schema_extra = {
            "example": {
                "points": [
                    {
                        "id": "doc-1",
                        "vector": [0.1, 0.2, 0.3],
                        "payload": {"text": "Document text"}
                    }
                ]
            }
        }


class UpsertTextRequest(BaseModel):
    """Request to upsert points with text (auto-embed)."""
    points: List[PointWithText] = Field(..., min_length=1)
    wait: bool = Field(default=True)

    class Config:
        json_schema_extra = {
            "example": {
                "points": [
                    {
                        "id": "doc-1",
                        "text": "Hello world, this is a document.",
                        "payload": {"source": "example"}
                    }
                ]
            }
        }


class UpsertResponse(BaseModel):
    """Response for upsert operation."""
    success: bool = True
    status: str = "completed"
    count: int = Field(..., description="Number of points upserted")


class DeletePointsRequest(BaseModel):
    """Request to delete points."""
    ids: List[Union[str, int]] = Field(..., description="Point IDs to delete")
    wait: bool = Field(default=True)


class DeletePointsResponse(BaseModel):
    """Response for point deletion."""
    success: bool = True
    count: int = Field(..., description="Number of points deleted")


# =============================================================================
# Search Models
# =============================================================================

class FilterCondition(BaseModel):
    """A single filter condition."""
    key: str = Field(..., description="Payload field key")
    match: Optional[Any] = Field(default=None, description="Exact match value")
    range: Optional[Dict[str, float]] = Field(
        default=None,
        description="Range filter (gte, lte, gt, lt)"
    )


class SearchFilter(BaseModel):
    """Search filter."""
    must: Optional[List[FilterCondition]] = Field(default=None)
    should: Optional[List[FilterCondition]] = Field(default=None)
    must_not: Optional[List[FilterCondition]] = Field(default=None)


class SearchRequest(BaseModel):
    """Request for vector search."""
    vector: List[float] = Field(..., description="Query vector")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Qdrant filter")
    score_threshold: Optional[float] = Field(default=None)
    with_payload: bool = Field(default=True)
    with_vectors: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "vector": [0.1, 0.2, 0.3],
                "limit": 10
            }
        }


class SearchTextRequest(BaseModel):
    """Request for text-based search (auto-embed)."""
    text: str = Field(..., description="Query text", min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filter: Optional[Dict[str, Any]] = Field(default=None)
    score_threshold: Optional[float] = Field(default=None)
    with_payload: bool = Field(default=True)
    with_vectors: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "What is machine learning?",
                "limit": 5
            }
        }


class HybridSearchRequest(BaseModel):
    """Request for hybrid search (vector + keyword)."""
    text: str = Field(..., description="Query text")
    limit: int = Field(default=10, ge=1, le=100)
    filter: Optional[Dict[str, Any]] = Field(default=None)
    keyword_fields: List[str] = Field(
        default=["text", "content"],
        description="Fields for keyword matching"
    )
    vector_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for vector similarity (keyword weight = 1 - this)"
    )
    with_payload: bool = Field(default=True)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "machine learning algorithms",
                "limit": 10,
                "vector_weight": 0.7
            }
        }


class SearchResult(BaseModel):
    """A single search result."""
    id: Union[str, int]
    score: float
    payload: Optional[Dict[str, Any]] = None
    vector: Optional[List[float]] = None


class SearchResponse(BaseModel):
    """Response for search operation."""
    success: bool = True
    results: List[SearchResult]
    count: int = Field(..., description="Number of results")
    query_time_ms: Optional[float] = Field(default=None)


# =============================================================================
# Recommendation Models
# =============================================================================

class RecommendRequest(BaseModel):
    """Request for recommendations."""
    positive: List[Union[str, int]] = Field(
        ...,
        description="IDs of positive examples",
        min_length=1
    )
    negative: Optional[List[Union[str, int]]] = Field(
        default=None,
        description="IDs of negative examples"
    )
    limit: int = Field(default=10, ge=1, le=100)
    filter: Optional[Dict[str, Any]] = Field(default=None)
    with_payload: bool = Field(default=True)
    with_vectors: bool = Field(default=False)
    strategy: str = Field(
        default="average_vector",
        description="Recommendation strategy"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "positive": ["doc-1", "doc-2"],
                "negative": ["doc-3"],
                "limit": 5
            }
        }


class RecommendResponse(BaseModel):
    """Response for recommendations."""
    success: bool = True
    results: List[SearchResult]
    count: int


# =============================================================================
# Batch Models
# =============================================================================

class BatchSearchRequest(BaseModel):
    """Request for batch search."""
    searches: List[SearchRequest] = Field(..., min_length=1, max_length=100)


class BatchSearchResponse(BaseModel):
    """Response for batch search."""
    success: bool = True
    results: List[List[SearchResult]]
    count: int


# =============================================================================
# Health & Status Models
# =============================================================================

class QdrantStatus(BaseModel):
    """Qdrant connection status."""
    connected: bool
    version: Optional[str] = None
    collections_count: int = 0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="healthy, degraded, unhealthy")
    timestamp: str
    version: str
    uptime: float
    checks: Dict[str, Any]


class CollectionStats(BaseModel):
    """Collection statistics."""
    name: str
    vectors_count: int
    points_count: int
    indexed_vectors_count: int
    segments_count: int
    status: str
