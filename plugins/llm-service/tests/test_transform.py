"""
Tests for Transform endpoints.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_transform_service():
    """Mock the transform service."""
    with patch('src.routes.transform.get_transform_service') as mock:
        service = MagicMock()
        
        # Mock transform
        service.transform = AsyncMock(return_value={
            "result": {
                "fullName": "John Doe",
                "age_group": "adult"
            },
            "input_format": "json",
            "output_format": "json",
            "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        })
        
        # Mock transform_to_schema
        service.transform_to_schema = AsyncMock(return_value={
            "result": {
                "name": "John Doe",
                "email": "john@example.com",
                "total": 99.99,
                "currency": "USD"
            },
            "mappings_used": {
                "name": "customer_name",
                "email": "customer_email",
                "total": "order_total"
            },
            "fields_filled": ["currency"],
            "validation_passed": True,
            "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        })
        
        # Mock convert_format
        service.convert_format = AsyncMock(return_value={
            "result": '{"name": "John Doe", "email": "john@example.com", "phone": "555-1234"}',
            "source_format": "text",
            "target_format": "json",
            "inferred_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"}
                }
            },
            "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        })
        
        # Mock clean_data
        service.clean_data = AsyncMock(return_value={
            "result": [
                {"name": "John Doe", "email": "john@example.com", "date": "2024-01-15"}
            ],
            "changes_made": [
                "Trimmed whitespace from names",
                "Normalized email to lowercase",
                "Standardized date format",
                "Removed 1 duplicate record"
            ],
            "records_removed": 1,
            "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        })
        
        # Mock merge_data
        service.merge_data = AsyncMock(return_value={
            "result": [
                {"id": 1, "name": "John", "email": "john@example.com", "age": 30}
            ],
            "sources_merged": 2,
            "conflicts_resolved": 0,
            "merge_report": "Merged 2 sources with 1 common record",
            "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        })
        
        mock.return_value = service
        yield service


@pytest.mark.asyncio
async def test_transform_data(mock_transform_service):
    """Test basic data transformation."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform",
            json={
                "data": {"firstName": "John", "lastName": "Doe", "age": 30},
                "instruction": "Combine firstName and lastName into fullName, categorize age as 'child', 'adult', or 'senior'",
                "output_format": "json"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "result" in data
    assert data["result"]["fullName"] == "John Doe"
    assert data["result"]["age_group"] == "adult"


@pytest.mark.asyncio
async def test_transform_with_examples(mock_transform_service):
    """Test transformation with few-shot examples."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform",
            json={
                "data": {"name": "Jane Smith"},
                "instruction": "Format the name as 'LASTNAME, First'",
                "examples": [
                    {
                        "input": {"name": "John Doe"},
                        "output": {"formatted_name": "DOE, John"}
                    }
                ],
                "output_format": "json"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_transform_to_schema(mock_transform_service):
    """Test schema-based transformation."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/schema",
            json={
                "data": {
                    "customer_name": "John Doe",
                    "customer_email": "john@example.com",
                    "order_total": 99.99
                },
                "target_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "total": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"}
                    },
                    "required": ["name", "email", "total"]
                }
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["validation_passed"] is True
    assert "mappings_used" in data
    assert data["mappings_used"]["name"] == "customer_name"
    assert data["result"]["currency"] == "USD"


@pytest.mark.asyncio
async def test_transform_to_schema_with_hints(mock_transform_service):
    """Test schema transformation with mapping hints."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/schema",
            json={
                "data": {"cust_nm": "John Doe"},
                "target_schema": {
                    "type": "object",
                    "properties": {
                        "full_name": {"type": "string"}
                    },
                    "required": ["full_name"]
                },
                "mapping_hints": {"full_name": "cust_nm"}
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_convert_format_text_to_json(mock_transform_service):
    """Test format conversion from text to JSON."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/convert",
            json={
                "data": "Name: John Doe\nEmail: john@example.com\nPhone: 555-1234",
                "source_format": "text",
                "target_format": "json",
                "infer_structure": True
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["source_format"] == "text"
    assert data["target_format"] == "json"
    assert "inferred_schema" in data


@pytest.mark.asyncio
async def test_convert_format_auto_detect(mock_transform_service):
    """Test format conversion with auto-detection."""
    from src.main import app
    
    # Mock for this specific test
    mock_transform_service.convert_format = AsyncMock(return_value={
        "result": "name: John Doe\nemail: john@example.com",
        "source_format": "json",
        "target_format": "yaml",
        "inferred_schema": None,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    })
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/convert",
            json={
                "data": '{"name": "John Doe", "email": "john@example.com"}',
                "target_format": "yaml"  # No source_format - auto-detect
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["source_format"] == "json"
    assert data["target_format"] == "yaml"


@pytest.mark.asyncio
async def test_clean_data(mock_transform_service):
    """Test data cleaning."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/clean",
            json={
                "data": [
                    {"name": "  john DOE  ", "email": "JOHN@example.com", "date": "1/15/2024"},
                    {"name": "John Doe", "email": "john@example.com", "date": "2024-01-15"}
                ],
                "operations": ["trim", "normalize_case", "standardize_dates", "deduplicate"],
                "locale": "en-US"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "changes_made" in data
    assert len(data["changes_made"]) > 0
    assert data["records_removed"] == 1


@pytest.mark.asyncio
async def test_clean_data_single_operation(mock_transform_service):
    """Test data cleaning with single operation."""
    from src.main import app
    
    mock_transform_service.clean_data = AsyncMock(return_value={
        "result": [{"name": "John Doe"}],
        "changes_made": ["Trimmed whitespace"],
        "records_removed": None,
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    })
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/clean",
            json={
                "data": [{"name": "  John Doe  "}],
                "operations": ["trim"]
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_merge_data(mock_transform_service):
    """Test data merging."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/merge",
            json={
                "sources": [
                    [{"id": 1, "name": "John", "email": "john@example.com"}],
                    [{"id": 1, "age": 30}]
                ],
                "merge_strategy": "smart",
                "key_fields": ["id"],
                "conflict_resolution": "merge"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["sources_merged"] == 2
    assert "result" in data


@pytest.mark.asyncio
async def test_merge_data_union_strategy(mock_transform_service):
    """Test data merging with union strategy."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/merge",
            json={
                "sources": [
                    [{"id": 1, "name": "John"}],
                    [{"id": 2, "name": "Jane"}]
                ],
                "merge_strategy": "union"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_query_data(mock_transform_service):
    """Test natural language data querying."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/transform/query",
            params={
                "query": "find all users over 30"
            },
            json=[
                {"name": "John", "age": 35},
                {"name": "Jane", "age": 25},
                {"name": "Bob", "age": 40}
            ]
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_list_formats():
    """Test listing supported formats."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/transform/formats")
    
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    assert len(data["formats"]) > 0
    
    # Check format structure
    format_names = [f["name"] for f in data["formats"]]
    assert "json" in format_names
    assert "xml" in format_names
    assert "yaml" in format_names
    assert "csv" in format_names


@pytest.mark.asyncio
async def test_transform_error_handling():
    """Test error handling in transform."""
    from src.main import app
    from src.services.transform_service import TransformServiceError
    
    with patch('src.routes.transform.get_transform_service') as mock:
        service = MagicMock()
        service.transform = AsyncMock(side_effect=TransformServiceError(
            message="Failed to parse JSON from LLM response",
            code="JSON_PARSE_ERROR"
        ))
        mock.return_value = service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/transform",
                json={
                    "data": {"test": "data"},
                    "instruction": "transform this"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "JSON_PARSE_ERROR"
