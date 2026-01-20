"""
Pydantic models for LLM Service.
"""
from .common import (
    TokenUsage,
    ErrorResponse,
    MessageRole,
    EntityType,
)
from .generation import (
    GenerateRequest,
    GenerateResponse,
)
from .chat import (
    ChatMessage,
    ChatRequest,
    ChatResponseMessage,
    ChatResponse,
)
from .classification import (
    ClassifyRequest,
    CategoryScore,
    ClassifyResponse,
)
from .extraction import (
    ExtractEntitiesRequest,
    Entity,
    ExtractEntitiesResponse,
)
from .summarization import (
    SummarizeRequest,
    SummarizeResponse,
)
from .embeddings import (
    EmbeddingsRequest,
    EmbeddingsResponse,
)
from .health import (
    ModelInfo,
    HealthResponse,
    ModelsResponse,
    QueueStatus,
)
from .vision import (
    VisionOCRRequest,
    VisionOCRResponse,
    VisionDescribeRequest,
    VisionDescribeResponse,
    VisionExtractRequest,
    VisionExtractResponse,
    OCRRegion,
    ImageInput,
    ExtractedField,
)
from .transform import (
    TransformRequest,
    TransformResponse,
    SchemaTransformRequest,
    SchemaTransformResponse,
    FormatConvertRequest,
    FormatConvertResponse,
    CleanDataRequest,
    CleanDataResponse,
    MergeDataRequest,
    MergeDataResponse,
    DataFormat,
    TransformExample,
)

__all__ = [
    # Common
    "TokenUsage",
    "ErrorResponse",
    "MessageRole",
    "EntityType",
    # Generation
    "GenerateRequest",
    "GenerateResponse",
    # Chat
    "ChatMessage",
    "ChatRequest",
    "ChatResponseMessage",
    "ChatResponse",
    # Classification
    "ClassifyRequest",
    "CategoryScore",
    "ClassifyResponse",
    # Extraction
    "ExtractEntitiesRequest",
    "Entity",
    "ExtractEntitiesResponse",
    # Summarization
    "SummarizeRequest",
    "SummarizeResponse",
    # Embeddings
    "EmbeddingsRequest",
    "EmbeddingsResponse",
    # Health
    "ModelInfo",
    "HealthResponse",
    "ModelsResponse",
    "QueueStatus",
    # Vision
    "VisionOCRRequest",
    "VisionOCRResponse",
    "VisionDescribeRequest",
    "VisionDescribeResponse",
    "VisionExtractRequest",
    "VisionExtractResponse",
    "OCRRegion",
    "ImageInput",
    "ExtractedField",
    # Transform
    "TransformRequest",
    "TransformResponse",
    "SchemaTransformRequest",
    "SchemaTransformResponse",
    "FormatConvertRequest",
    "FormatConvertResponse",
    "CleanDataRequest",
    "CleanDataResponse",
    "MergeDataRequest",
    "MergeDataResponse",
    "DataFormat",
    "TransformExample",
]
