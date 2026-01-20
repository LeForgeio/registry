# LLM Service

A production-ready FastAPI wrapper around vLLM for on-premise LLM inference.

## Features

- **Text Generation**: Generate text with SSE streaming support
- **Chat Completion**: Multi-turn conversations with streaming
- **Text Classification**: Categorize text into predefined classes
- **Entity Extraction**: Extract structured information from text
- **Text Summarization**: Generate summaries with length control
- **Embeddings**: Generate text embeddings for semantic search
- **Request Queuing**: Redis-based queue for high-throughput scenarios
- **Model Management**: Support for multiple models and switching

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client App    │────▶│   LLM Service   │────▶│   vLLM Server   │
│                 │     │   (FastAPI)     │     │   (GPU/CPU)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     Redis       │
                        │  (Queue/Cache)  │
                        └─────────────────┘
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/generate` | Text generation with streaming |
| POST | `/api/v1/chat` | Chat completion with streaming |
| POST | `/api/v1/classify` | Text classification |
| POST | `/api/v1/extract-entities` | Entity extraction |
| POST | `/api/v1/summarize` | Text summarization |
| POST | `/api/v1/embeddings` | Text embeddings |
| GET | `/health` | Health check |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/health/ready` | Kubernetes readiness probe |
| GET | `/models` | List available models |
| GET | `/queue/status` | Queue status |

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Start all services (CPU mode)
docker compose up -d

# View logs
docker compose logs -f llm-service
```

### 2. Development Mode

```bash
# Start with hot-reload
docker compose -f docker-compose.dev.yml up -d

# Or run locally
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 3. Using Mock vLLM (for testing without GPU)

```bash
# Start with mock vLLM server
docker compose -f docker-compose.dev.yml --profile mock up -d

# Set vLLM URL to mock server
export VLLM_BASE_URL=http://localhost:8002/v1
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_BASE_URL` | `http://localhost:8001/v1` | vLLM server URL |
| `DEFAULT_MODEL` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | Default LLM model |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `ENABLE_QUEUE` | `true` | Enable request queuing |
| `ENABLE_EMBEDDINGS` | `true` | Enable embeddings endpoint |
| `DEFAULT_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `DEFAULT_MAX_TOKENS` | `512` | Default max tokens |
| `MAX_INPUT_TOKENS` | `4096` | Max input token limit |
| `REQUEST_TIMEOUT` | `120` | Request timeout (seconds) |

See [.env.example](.env.example) for all options.

## API Usage Examples

### Text Generation

```bash
# Basic generation
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about coding:",
    "max_tokens": 50,
    "temperature": 0.7
  }'

# Streaming generation
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Tell me a story",
    "stream": true
  }'
```

### Chat Completion

```bash
# Multi-turn conversation
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "max_tokens": 100
  }'
```

### Classification

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I absolutely love this product!",
    "labels": ["positive", "negative", "neutral"]
  }'
```

### Entity Extraction

```bash
curl -X POST http://localhost:8000/api/v1/extract-entities \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Smith from Acme Corp visited New York yesterday.",
    "entity_types": ["PERSON", "ORGANIZATION", "LOCATION", "DATE"]
  }'
```

### Summarization

```bash
curl -X POST http://localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long article text here...",
    "length": "short",
    "format": "paragraph"
  }'
```

### Embeddings

```bash
# Single text
curl -X POST http://localhost:8000/api/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!"
  }'

# Batch texts
curl -X POST http://localhost:8000/api/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "text": ["First sentence", "Second sentence", "Third sentence"]
  }'
```

## Model Configuration

### Available Models

The service supports any model compatible with vLLM. Popular choices:

| Model | Size | Use Case |
|-------|------|----------|
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 1.1B | Development, testing |
| `mistralai/Mistral-7B-Instruct-v0.2` | 7B | General purpose |
| `meta-llama/Llama-2-13b-chat-hf` | 13B | High quality |
| `codellama/CodeLlama-7b-Instruct-hf` | 7B | Code generation |

### Changing Models

Update `DEFAULT_MODEL` in your environment or specify per-request:

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -d '{
    "prompt": "Hello",
    "model": "mistralai/Mistral-7B-Instruct-v0.2"
  }'
```

## GPU Support

### NVIDIA GPU Setup

1. Install NVIDIA Container Toolkit:
```bash
# Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. Verify GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

3. Update docker-compose.yml (see comments in file):
```yaml
vllm-server:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  command:
    - --model
    - mistralai/Mistral-7B-Instruct-v0.2
    - --dtype
    - half
    - --tensor-parallel-size
    - "1"
```

## Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_generate.py -v

# Run with mock vLLM
docker compose -f docker-compose.dev.yml --profile mock up -d
pytest tests/
```

## Project Structure

```
llm-service/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── generate.py      # Text generation
│   │   ├── chat.py          # Chat completion
│   │   ├── classify.py      # Classification
│   │   ├── extract.py       # Entity extraction
│   │   ├── summarize.py     # Summarization
│   │   ├── embeddings.py    # Embeddings
│   │   └── health.py        # Health checks
│   └── services/
│       ├── __init__.py
│       ├── llm_client.py    # vLLM client wrapper
│       ├── embedding_service.py  # Sentence transformers
│       └── queue_service.py # Redis queue
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── mock_vllm_server.py  # Mock vLLM for testing
│   └── test_*.py            # Test files
├── docker-compose.yml       # Production deployment
├── docker-compose.dev.yml   # Development setup
├── Dockerfile               # Multi-stage build
├── requirements.txt         # Python dependencies
├── pytest.ini              # Pytest configuration
├── .env.example            # Environment template
└── README.md
```

## Troubleshooting

### vLLM Server Won't Start

1. **Out of memory**: Use a smaller model or increase memory limit
2. **Model not found**: Check `HF_TOKEN` for gated models
3. **Slow startup**: First run downloads the model, be patient

### Slow Inference

1. Enable GPU if available
2. Use a smaller model for development
3. Reduce `max_tokens` for faster responses
4. Enable request batching via queue

### Embeddings Not Working

1. Check `ENABLE_EMBEDDINGS=true`
2. First request loads model (may be slow)
3. Ensure sufficient memory for embedding model

## License

MIT License - See [LICENSE](../../LICENSE) for details.
