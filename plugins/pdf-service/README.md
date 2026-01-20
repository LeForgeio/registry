# PDF Service

A high-performance microservice for PDF generation, manipulation, and text extraction. Part of the FlowForge platform.

## Features

- **Generate PDF from HTML** - Convert HTML content to PDF using Puppeteer/Chromium
- **Generate PDF from Templates** - Use Handlebars templates with dynamic data
- **Merge PDFs** - Combine multiple PDF files into a single document
- **Extract Text** - Extract text content from PDF files
- **Fill PDF Forms** - Fill form fields programmatically
- **Get PDF Info** - Retrieve metadata and form field information

## Tech Stack

- **Runtime**: Node.js 20+
- **Framework**: Fastify 4.x
- **PDF Generation**: Puppeteer (Chromium)
- **PDF Manipulation**: pdf-lib
- **Text Extraction**: pdfjs-dist
- **Templating**: Handlebars
- **HTML Sanitization**: DOMPurify

## Quick Start

### Prerequisites

- Node.js 20 or higher
- npm or yarn
- Chromium (installed automatically by Puppeteer for development)

### Installation

```bash
cd services/pdf-service
npm install
```

### Development

```bash
# Start in development mode with hot-reload
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build
```

### Docker

```bash
# Build image
docker build -t pdf-service .

# Run container
docker run -p 3003:3003 pdf-service
```

## API Endpoints

### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Simple health check |
| `/api/v1/health/detailed` | GET | Detailed health with component status |
| `/api/v1/ready` | GET | Kubernetes readiness probe |
| `/api/v1/live` | GET | Kubernetes liveness probe |

### Generate

#### POST /api/v1/generate/html

Generate a PDF from HTML content.

```json
{
  "html": "<html><body><h1>Hello World</h1></body></html>",
  "format": "A4",
  "orientation": "portrait",
  "margin": {
    "top": "20mm",
    "right": "20mm",
    "bottom": "20mm",
    "left": "20mm"
  },
  "printBackground": true
}
```

Response:
```json
{
  "success": true,
  "data": {
    "pdf": "base64-encoded-pdf...",
    "filename": "generated-1234567890.pdf",
    "size": 12345,
    "pages": 1
  }
}
```

#### POST /api/v1/generate/template

Generate a PDF from a Handlebars template.

```json
{
  "template": "<h1>Invoice #{{invoiceNumber}}</h1><p>Total: {{formatCurrency total}}</p>",
  "data": {
    "invoiceNumber": "INV-001",
    "total": 1234.56
  },
  "format": "A4"
}
```

### Merge

#### POST /api/v1/merge

Merge multiple PDFs (JSON/base64).

```json
{
  "files": [
    {
      "data": "base64-pdf-1...",
      "filename": "doc1.pdf",
      "pageRanges": "1-3"
    },
    {
      "data": "base64-pdf-2...",
      "pageRanges": "2,4-6"
    }
  ],
  "metadata": {
    "title": "Merged Document",
    "author": "FlowForge"
  }
}
```

#### POST /api/v1/merge/upload

Merge uploaded PDF files (multipart/form-data).

### Extract

#### POST /api/v1/extract/text

Extract text from a PDF.

```json
{
  "file": "base64-pdf...",
  "pageNumbers": [1, 2, 5],
  "preserveLayout": true,
  "includePageBreaks": false
}
```

Response:
```json
{
  "success": true,
  "data": {
    "text": "Full extracted text...",
    "pages": [
      {
        "pageNumber": 1,
        "text": "Page 1 text...",
        "lines": ["Line 1", "Line 2"]
      }
    ],
    "totalPages": 10,
    "metadata": {
      "title": "Document Title"
    }
  }
}
```

### Forms

#### POST /api/v1/form/fill

Fill PDF form fields.

```json
{
  "file": "base64-pdf...",
  "fields": [
    { "name": "fullName", "type": "text", "value": "John Doe" },
    { "name": "agree", "type": "checkbox", "value": true },
    { "name": "country", "type": "dropdown", "value": "USA" }
  ],
  "flatten": true
}
```

#### POST /api/v1/form/info

Get PDF information and form fields.

```json
{
  "file": "base64-pdf..."
}
```

Response:
```json
{
  "success": true,
  "data": {
    "pageCount": 5,
    "metadata": {
      "title": "Form Document",
      "author": "Creator"
    },
    "isEncrypted": false,
    "hasForm": true,
    "formFields": [
      {
        "name": "fullName",
        "type": "text",
        "required": false,
        "readOnly": false
      }
    ],
    "fileSize": 123456
  }
}
```

## Template Helpers

The template service includes 50+ Handlebars helpers:

### Conditional
- `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `and`, `or`, `not`

### String
- `uppercase`, `lowercase`, `capitalize`, `truncate`, `replace`, `split`, `join`

### Number
- `formatNumber`, `formatCurrency`, `formatPercent`
- `add`, `subtract`, `multiply`, `divide`, `mod`
- `round`, `floor`, `ceil`, `abs`

### Date
- `formatDate`, `now`, `year`, `month`, `day`

### Array
- `first`, `last`, `length`, `includes`, `sum`, `avg`, `range`

### Object
- `keys`, `values`, `lookup`, `json`

### Utility
- `default`, `coalesce`, `repeat`, `safeHtml`

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3003 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `NODE_ENV` | development | Environment |
| `LOG_LEVEL` | info | Logging level |
| `CORS_ORIGINS` | * | Allowed CORS origins (comma-separated) |
| `PDF_MAX_FILE_SIZE` | 52428800 | Max file size in bytes (50MB) |
| `PDF_MAX_MERGE_FILES` | 20 | Max files to merge at once |
| `PDF_TEMP_DIR` | /tmp/pdf-service | Temp file directory |
| `PDF_DEFAULT_FORMAT` | A4 | Default page format |
| `PDF_MARGIN_TOP` | 20mm | Default top margin |
| `PDF_MARGIN_RIGHT` | 20mm | Default right margin |
| `PDF_MARGIN_BOTTOM` | 20mm | Default bottom margin |
| `PDF_MARGIN_LEFT` | 20mm | Default left margin |
| `PDF_PUPPETEER_TIMEOUT` | 30000 | Puppeteer timeout (ms) |

## Security

- All HTML input is sanitized using DOMPurify
- Script tags and event handlers are removed
- JavaScript URLs are blocked
- CSS is sanitized to remove dangerous properties
- File names are sanitized for path traversal prevention

## API Documentation

Swagger UI is available at `/docs` when the service is running.

## Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- tests/sanitizer.test.ts
```

## License

MIT
