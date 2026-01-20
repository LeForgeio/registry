# OCR Service

Python/FastAPI microservice for optical character recognition.

## Features

- Extract text from images (PaddleOCR/Tesseract)
- Support for multiple languages
- Bounding box detection
- Confidence scores

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ocr/extract` | Extract text from image |
| GET | `/api/v1/ocr/languages` | List supported languages |

## Quick Start

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 3004
```
