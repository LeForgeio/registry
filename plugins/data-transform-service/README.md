# Data Transform Service

Node.js/TypeScript microservice for data transformation operations.

## Features

- JSON transformations (JMESPath, JSONata)
- XML to JSON conversion
- CSV parsing and generation
- YAML processing
- Data mapping and validation

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/data/transform/json` | Transform JSON |
| POST | `/api/v1/data/convert` | Convert between formats |
| POST | `/api/v1/data/validate` | Validate data against schema |

## Quick Start

```bash
npm install
npm run dev
```
