# Image Service

Node.js/TypeScript microservice for image processing using Sharp.

## Features

- Resize images
- Convert formats (JPEG, PNG, WebP, AVIF)
- Crop and rotate
- Apply filters and effects
- Generate thumbnails

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/image/resize` | Resize image |
| POST | `/api/v1/image/convert` | Convert format |
| POST | `/api/v1/image/optimize` | Optimize for web |

## Quick Start

```bash
npm install
npm run dev
```
