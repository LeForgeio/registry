# Vector Service

Python/FastAPI microservice for vector storage and semantic search using Qdrant vector database. Provides RAG-ready capabilities with support for local and remote embedding generation.

## Features

- **Collection Management**: Create, list, and delete vector collections
- **Vector Operations**: Upsert, search, and delete vectors with batch support
- **Semantic Search**: Text-based search with automatic embedding generation
- **Hybrid Search**: Combine dense vector and sparse keyword search
- **Recommendations**: Vector-based similarity recommendations
- **Flexible Embeddings**: Local sentence-transformers or remote llm-service
- **Rich Filtering**: Full filter query support (must, should, must_not, range, geo)
- **Connection Pooling**: Efficient Qdrant connection management

## Tech Stack

- **Python 3.11+**
- **FastAPI** - High-performance async web framework
- **Qdrant** - Vector similarity search engine
- **sentence-transformers** - Local embedding generation
- **httpx** - Async HTTP client for remote embeddings
- **numpy** - Vector operations
- **loguru** - Structured logging

## API Endpoints

### Collection Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/collections/create` | Create a new collection |
| GET | `/api/v1/collections/list` | List all collections |
| GET | `/api/v1/collections/{name}` | Get collection info |
| DELETE | `/api/v1/collections/{name}` | Delete a collection |

### Vector Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/collections/{name}/upsert` | Upsert vectors |
| POST | `/api/v1/collections/{name}/search` | Search by vector |
| POST | `/api/v1/collections/{name}/search-text` | Search by text (auto-embed) |
| POST | `/api/v1/collections/{name}/hybrid-search` | Hybrid vector + keyword search |
| POST | `/api/v1/collections/{name}/recommend` | Get recommendations |
| DELETE | `/api/v1/collections/{name}/points` | Delete vectors |

### Health Checks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Overall health status |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |
| GET | `/health/qdrant` | Qdrant connection status |

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Qdrant (using Docker)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.7.4

# Run the service
uvicorn src.main:app --reload --port 8000
```

### Docker Compose

```bash
# Development mode (with hot-reload)
docker-compose -f docker-compose.dev.yml up

# Production mode
docker-compose up -d
```

### Environment Variables

```bash
# Application
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
USE_LOCAL_EMBEDDINGS=true
LLM_SERVICE_URL=http://localhost:8001

# Defaults
DEFAULT_VECTOR_SIZE=384
DEFAULT_DISTANCE=Cosine
```

## Usage Examples

### Create a Collection

```bash
curl -X POST http://localhost:8000/api/v1/collections/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "documents",
    "vector_size": 384,
    "distance": "Cosine"
  }'
```

**Response:**
```json
{
  "success": true,
  "collection_name": "documents",
  "message": "Collection created successfully"
}
```

### Upsert Vectors

```bash
curl -X POST http://localhost:8000/api/v1/collections/documents/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {
        "id": "doc_1",
        "vector": [0.1, 0.2, ...],
        "payload": {
          "text": "Machine learning is a subset of AI",
          "category": "technology",
          "source": "article"
        }
      },
      {
        "id": "doc_2",
        "vector": [0.3, 0.4, ...],
        "payload": {
          "text": "Natural language processing enables text understanding",
          "category": "technology",
          "source": "paper"
        }
      }
    ]
  }'
```

### Search by Vector

```bash
curl -X POST http://localhost:8000/api/v1/collections/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.15, 0.25, ...],
    "limit": 10,
    "score_threshold": 0.7,
    "with_payload": true
  }'
```

**Response:**
```json
{
  "results": [
    {
      "id": "doc_1",
      "score": 0.95,
      "payload": {
        "text": "Machine learning is a subset of AI",
        "category": "technology"
      }
    },
    {
      "id": "doc_2", 
      "score": 0.82,
      "payload": {
        "text": "Natural language processing enables text understanding",
        "category": "technology"
      }
    }
  ],
  "total": 2,
  "took_ms": 12.5
}
```

### Search by Text (Auto-Embed)

```bash
curl -X POST http://localhost:8000/api/v1/collections/documents/search-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "artificial intelligence applications",
    "limit": 10,
    "filter": {
      "must": [
        {"key": "category", "match": {"value": "technology"}}
      ]
    }
  }'
```

### Hybrid Search

```bash
curl -X POST http://localhost:8000/api/v1/collections/documents/hybrid-search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "machine learning algorithms",
    "sparse_field": "text",
    "alpha": 0.7,
    "limit": 10
  }'
```

The `alpha` parameter controls the balance:
- `alpha = 0.0`: Pure keyword/sparse search
- `alpha = 0.5`: Balanced hybrid
- `alpha = 1.0`: Pure semantic/dense search

### Get Recommendations

```bash
curl -X POST http://localhost:8000/api/v1/collections/documents/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "positive": ["doc_1", "doc_2"],
    "negative": ["doc_5"],
    "limit": 5,
    "score_threshold": 0.6
  }'
```

### Filter Queries

Supports complex filter conditions:

```json
{
  "filter": {
    "must": [
      {"key": "category", "match": {"value": "technology"}},
      {"key": "year", "range": {"gte": 2020, "lte": 2024}}
    ],
    "should": [
      {"key": "source", "match": {"value": "article"}},
      {"key": "source", "match": {"value": "paper"}}
    ],
    "must_not": [
      {"key": "status", "match": {"value": "draft"}}
    ]
  }
}
```

### Delete Vectors

```bash
# By IDs
curl -X DELETE http://localhost:8000/api/v1/collections/documents/points \
  -H "Content-Type: application/json" \
  -d '{
    "point_ids": ["doc_1", "doc_2"]
  }'

# By filter
curl -X DELETE http://localhost:8000/api/v1/collections/documents/points \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "must": [{"key": "status", "match": {"value": "deprecated"}}]
    }
  }'
```

## RAG Integration Example

```python
import httpx
import asyncio

async def rag_pipeline(query: str, collection: str = "documents"):
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Search for relevant documents
        response = await client.post(
            f"{base_url}/api/v1/collections/{collection}/search-text",
            json={
                "text": query,
                "limit": 5,
                "score_threshold": 0.6
            }
        )
        results = response.json()["results"]
        
        # 2. Extract context from results
        context = "\n".join([
            r["payload"]["text"] 
            for r in results 
            if "text" in r.get("payload", {})
        ])
        
        # 3. Use context with LLM (example with llm-service)
        llm_response = await client.post(
            "http://localhost:8001/api/v1/generate",
            json={
                "prompt": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:",
                "max_tokens": 500
            }
        )
        
        return {
            "answer": llm_response.json()["text"],
            "sources": [r["id"] for r in results]
        }

# Usage
result = asyncio.run(rag_pipeline("What is machine learning?"))
print(result)
```

## Embedding Configuration

### Local Embeddings (Default)

Uses sentence-transformers for local embedding generation:

```bash
USE_LOCAL_EMBEDDINGS=true
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 384 dimensions
```

Supported models:
- `all-MiniLM-L6-v2` (384 dim, fast)
- `all-mpnet-base-v2` (768 dim, better quality)
- `multi-qa-MiniLM-L6-cos-v1` (384 dim, optimized for QA)

### Remote Embeddings (via llm-service)

Use the FlowForge llm-service for embedding generation:

```bash
USE_LOCAL_EMBEDDINGS=false
LLM_SERVICE_URL=http://llm-service:8000
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m embedding
```

## Project Structure

```
vector-service/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── qdrant_service.py    # Qdrant operations
│   │   └── embedding_service.py # Embedding generation
│   └── routes/
│       ├── __init__.py
│       ├── collections.py   # Collection endpoints
│       ├── vectors.py       # Vector endpoints
│       └── health.py        # Health endpoints
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_collections.py  # Collection tests
│   ├── test_vectors.py      # Vector tests
│   ├── test_health.py       # Health tests
│   └── test_embeddings.py   # Embedding tests
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── requirements.txt
├── openapi.yaml
├── pytest.ini
├── .env.example
└── README.md
```

## Performance Tuning

### HNSW Configuration

```json
{
  "name": "optimized_collection",
  "vector_size": 384,
  "hnsw_config": {
    "m": 32,              // More links = better recall, slower indexing
    "ef_construct": 200,  // Higher = better index quality
    "on_disk": false      // Keep in memory for speed
  }
}
```

### Batch Operations

For bulk inserts, use batching:

```python
# Recommended batch size: 100-1000 vectors
batch_size = 500
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i+batch_size]
    await upsert_vectors(collection, batch)
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## License

MIT License - see LICENSE file for details
