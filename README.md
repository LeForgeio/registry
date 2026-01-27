# ForgeHooks Registry

Official registry of ForgeHook plugins for [FlowForge](https://github.com/danstoll/flowforge).

## 🔌 Available Plugins

### ⭐ Featured (Embedded - No Docker Required)

| Plugin                                                       | Category | Description                                         |
| ------------------------------------------------------------ | -------- | --------------------------------------------------- |
| [formula-engine](./plugins/formula-engine/)                  | Data     | 150+ Excel-compatible functions (VLOOKUP, SUMIF, etc.) |
| [string-utils](./plugins/string-utils/)                      | Utility  | String manipulation - slugify, camelCase, sanitize  |
| [date-utils](./plugins/date-utils/)                          | Utility  | Date/time utilities - format, parse, relative time  |

### 🐳 Container Services

| Plugin                                                       | Category | Description                                         |
| ------------------------------------------------------------ | -------- | --------------------------------------------------- |
| [streaming-file-service](./plugins/streaming-file-service/)  | Data     | Large file handling, chunked uploads, cloud storage |
| [crypto-service](./plugins/crypto-service/)                  | Security | Cryptographic operations - hashing, encryption, JWT |
| [math-service](./plugins/math-service/)                      | Data     | Mathematical calculations and statistics            |
| [pdf-service](./plugins/pdf-service/)                        | Media    | PDF generation, merging, splitting                  |
| [ocr-service](./plugins/ocr-service/)                        | AI       | Optical character recognition                       |
| [image-service](./plugins/image-service/)                    | Media    | Image processing and optimization                   |
| [llm-service](./plugins/llm-service/)                        | AI       | LLM chat and text generation                        |
| [vector-service](./plugins/vector-service/)                  | Data     | Vector database for semantic search                 |
| [data-transform-service](./plugins/data-transform-service/)  | Data     | Data format conversions                             |

### 🔧 Local AI Providers

| Plugin                                                       | Category | Description                                         |
| ------------------------------------------------------------ | -------- | --------------------------------------------------- |
| [ollama-local](./plugins/ollama-local/)                      | AI       | Local LLM via Ollama                                |
| [lm-studio](./plugins/lm-studio/)                            | AI       | Local LLM via LM Studio                             |
| [foundry-local](./plugins/foundry-local/)                    | AI       | Microsoft Foundry Local integration                 |

## 📦 Installation Methods

### From Marketplace (Recommended)

The FlowForge UI automatically fetches plugins from this registry.

### From GitHub URL

```text
flowforge/crypto-service
```

### Offline (.fhk Package)

Pre-built packages are available in the `packages/` directory:

**Embedded (Lightweight)**
| Package                           | Size   | Description                      |
| --------------------------------- | ------ | -------------------------------- |
| `formula-engine-1.0.0.fhk`        | 45 KB  | Excel-compatible formulas        |
| `string-utils-1.0.0.fhk`          | 15 KB  | String manipulation utilities    |
| `date-utils-1.0.0.fhk`            | 12 KB  | Date/time utilities              |

**Container Services**
| Package                           | Size   | Description                      |
| --------------------------------- | ------ | -------------------------------- |
| `crypto-service-1.0.0.fhk`        | 200 MB | Cryptographic operations         |
| `math-service-1.0.0.fhk`          | 282 MB | Mathematical calculations        |
| `streaming-file-service-1.0.0.fhk`| 350 MB | Large file handling              |
| `llm-service-1.0.0.fhk`           | 4.2 GB | LLM/AI text generation           |
| `vector-service-1.0.0.fhk`        | 4.2 GB | Vector database/semantic search  |

To install a .fhk package:

1. Go to **Marketplace** → **Upload** tab
2. Drag and drop the .fhk file or click to browse
3. Click **Install**

## 🛠️ Creating Your Own ForgeHook

See [Creating ForgeHooks](./docs/creating-forgehooks.md) for a complete guide.

### Quick Start

1. Create `forgehook.json` manifest:

```json
{
  "$schema": "https://flowforge.dev/schemas/forgehook-v1.json",
  "id": "my-service",
  "name": "My Service",
  "version": "1.0.0",
  "description": "Description of your service",
  "image": {
    "repository": "your-dockerhub/my-service",
    "tag": "latest"
  },
  "port": 3000,
  "endpoints": [
    {
      "method": "POST",
      "path": "/process",
      "description": "Process data"
    }
  ]
}
```

1. Build and push Docker image
2. Add to a registry or install directly from GitHub

## 📋 Registry Format

The registry index (`forgehooks-registry.json`) follows this schema:

```json
{
  "version": "1.0.0",
  "registry": {
    "name": "Registry Name",
    "description": "Registry description",
    "url": "https://github.com/owner/repo"
  },
  "plugins": [
    {
      "id": "plugin-id",
      "manifest": { ... },
      "verified": true,
      "downloads": 1000,
      "rating": 4.8
    }
  ]
}
```

## 🔗 Adding This Registry to FlowForge

This registry is automatically configured as the official source. To add custom registries:

1. Go to **Marketplace** → **Registry Sources**
2. Click **Add Source**
3. Enter the registry URL

## 📄 License

MIT License - see individual plugins for their licenses.
