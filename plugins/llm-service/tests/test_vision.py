"""
Tests for Vision OCR and Image Understanding endpoints.
"""
import base64
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import io

# Create a minimal test image (1x1 PNG)
MINIMAL_PNG = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
    b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
    b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
).decode()


@pytest.fixture
def mock_vision_service():
    """Mock the vision service."""
    with patch('src.routes.vision.get_vision_service') as mock:
        service = MagicMock()
        
        # Mock prepare_image
        service.prepare_image = AsyncMock(return_value=(b'fake_image_bytes', 'image/png'))
        
        # Mock OCR
        service.ocr = AsyncMock(return_value={
            "text": "Hello World\nThis is a test document.",
            "regions": [
                {"text": "Hello World", "confidence": 0.95, "position": "top"},
                {"text": "This is a test document.", "confidence": 0.92, "position": "bottom"}
            ],
            "confidence": 0.93,
            "word_count": 6,
            "model": "llava-hf/llava-1.5-7b-hf"
        })
        
        # Mock describe
        service.describe = AsyncMock(return_value={
            "description": "A document containing text that says 'Hello World'.",
            "objects_detected": ["document", "text"],
            "model": "llava-hf/llava-1.5-7b-hf"
        })
        
        # Mock extract_fields
        service.extract_fields = AsyncMock(return_value={
            "fields": [
                {"name": "invoice_number", "value": "INV-001", "confidence": 0.95},
                {"name": "total", "value": 150.00, "confidence": 0.90},
                {"name": "date", "value": "2024-01-18", "confidence": 0.88}
            ],
            "raw_data": {"invoice_number": "INV-001", "total": 150.00, "date": "2024-01-18"},
            "document_type": "invoice",
            "confidence": 0.91,
            "model": "llava-hf/llava-1.5-7b-hf"
        })
        
        mock.return_value = service
        yield service


@pytest.mark.asyncio
async def test_vision_ocr_with_base64(mock_vision_service):
    """Test OCR with base64 image."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/ocr",
            json={
                "image": {"base64": MINIMAL_PNG},
                "output_format": "text",
                "detail_level": "medium"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Hello World" in data["text"]
    assert data["word_count"] == 6
    assert data["confidence"] > 0
    assert data["model"] is not None


@pytest.mark.asyncio
async def test_vision_ocr_structured_output(mock_vision_service):
    """Test OCR with structured output format."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/ocr",
            json={
                "image": {"base64": MINIMAL_PNG},
                "output_format": "structured",
                "detail_level": "high",
                "preserve_layout": True
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["regions"] is not None
    assert len(data["regions"]) > 0
    assert "text" in data["regions"][0]
    assert "confidence" in data["regions"][0]


@pytest.mark.asyncio
async def test_vision_ocr_with_language_hints(mock_vision_service):
    """Test OCR with language hints."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/ocr",
            json={
                "image": {"base64": MINIMAL_PNG},
                "language_hints": ["en", "es"],
                "output_format": "text"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_vision_describe(mock_vision_service):
    """Test image description."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/describe",
            json={
                "image": {"base64": MINIMAL_PNG},
                "focus": "general",
                "max_length": 200
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "description" in data
    assert len(data["description"]) > 0
    assert data["model"] is not None


@pytest.mark.asyncio
async def test_vision_describe_with_prompt(mock_vision_service):
    """Test image description with custom prompt."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/describe",
            json={
                "image": {"base64": MINIMAL_PNG},
                "prompt": "Describe the main elements in this image",
                "focus": "objects"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_vision_extract(mock_vision_service):
    """Test structured field extraction."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/extract",
            json={
                "image": {"base64": MINIMAL_PNG},
                "fields": ["invoice_number", "total", "date"],
                "document_type": "invoice"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "fields" in data
    assert len(data["fields"]) > 0
    
    # Check field structure
    field = data["fields"][0]
    assert "name" in field
    assert "value" in field
    assert "confidence" in field


@pytest.mark.asyncio
async def test_vision_extract_with_schema(mock_vision_service):
    """Test extraction with JSON schema validation."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/vision/extract",
            json={
                "image": {"base64": MINIMAL_PNG},
                "fields": ["name", "email", "amount"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "amount": {"type": "number"}
                    }
                }
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["raw_data"] is not None


@pytest.mark.asyncio
async def test_vision_models_list():
    """Test listing available vision models."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/vision/models")
    
    assert response.status_code == 200
    data = response.json()
    assert "default_model" in data
    assert "available_models" in data
    assert "supported_formats" in data


@pytest.mark.asyncio
async def test_vision_ocr_no_image():
    """Test OCR without providing an image."""
    from src.main import app
    from src.services.vision_service import VisionServiceError
    
    with patch('src.routes.vision.get_vision_service') as mock:
        service = MagicMock()
        service.prepare_image = AsyncMock(side_effect=VisionServiceError(
            message="No image provided",
            code="NO_IMAGE"
        ))
        mock.return_value = service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/vision/ocr",
                json={
                    "image": {},
                    "output_format": "text"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "NO_IMAGE"


@pytest.mark.asyncio
async def test_vision_ocr_image_too_large():
    """Test OCR with oversized image."""
    from src.main import app
    from src.services.vision_service import VisionServiceError
    
    with patch('src.routes.vision.get_vision_service') as mock:
        service = MagicMock()
        service.prepare_image = AsyncMock(side_effect=VisionServiceError(
            message="Image too large. Maximum size: 10MB",
            code="IMAGE_TOO_LARGE"
        ))
        mock.return_value = service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/vision/ocr",
                json={
                    "image": {"base64": MINIMAL_PNG},
                    "output_format": "text"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "IMAGE_TOO_LARGE"
