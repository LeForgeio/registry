# ForgeHook Specification

> **Version 1.1** | Complete technical specification for FlowForge plugins

## Overview

A **ForgeHook** is a plugin for the FlowForge platform. ForgeHooks extend FlowForge with new capabilities by packaging services as self-contained, API-accessible modules. They can run as Docker containers for full isolation or as embedded JavaScript for lightweight operations.

### Key Characteristics

| Aspect | Description |
| ------ | ----------- |
| **Self-contained** | Each ForgeHook is a complete, runnable unit with all dependencies |
| **API-first** | Functionality is exposed through well-defined REST endpoints |
| **Discoverable** | Manifests declare capabilities, enabling auto-discovery and UI generation |
| **Portable** | Can be distributed via registries, GitHub, or `.fhk` packages |
| **Dual Runtime** | Supports Docker containers (full isolation) or embedded JS (lightweight) |

---

## Runtime Types

### Container Runtime (`runtime: "container"`)

Container-based ForgeHooks run as Docker containers. This is the **default** runtime and provides:

- **Full isolation** - Separate process, filesystem, and network namespace
- **Any language** - Python, Node.js, Go, Rust, or any language with a Docker image
- **Resource control** - Memory limits, CPU quotas, GPU access
- **Complex dependencies** - Native libraries, ML models, system tools

**Best for:** Heavy computation, ML/AI, services with native dependencies, multi-language support

### Embedded Runtime (`runtime: "embedded"`)

Embedded ForgeHooks run as JavaScript functions within FlowForge's Node.js process:

- **Zero overhead** - No container startup, instant execution
- **Shared memory** - Direct access to FlowForge internals (sandboxed)
- **Tiny footprint** - Functions are kilobytes, not megabytes
- **Fast iteration** - No image builds during development

**Best for:** String utilities, data transformations, simple calculations, lightweight helpers

---

## Manifest Specification (`forgehook.json`)

Every ForgeHook requires a `forgehook.json` manifest file. This declares the plugin's identity, capabilities, requirements, and configuration.

### Complete Schema

```json
{
  "$schema": "https://leforge.io/schemas/forgehook-v1.json",
  
  // === REQUIRED FIELDS ===
  "id": "my-service",           // Unique identifier (lowercase, alphanumeric, hyphens)
  "name": "My Service",         // Display name (2-50 chars)
  "version": "1.0.0",           // Semantic version (X.Y.Z or X.Y.Z-prerelease)
  "description": "...",         // Brief description (max 500 chars)
  "endpoints": [...],           // API endpoint definitions
  
  // === RUNTIME (choose one) ===
  // For container runtime:
  "image": {
    "repository": "flowforge/my-service",
    "tag": "latest",
    "digest": "sha256:..."      // Optional: pin to specific digest
  },
  "port": 3001,                 // Container port (1024-65535)
  
  // For embedded runtime:
  "runtime": "embedded",
  "embedded": {
    "entrypoint": "index.js",   // Main JavaScript file
    "exports": ["fn1", "fn2"],  // Exported function names
    "timeout": 5000,            // Execution timeout (ms)
    "memoryLimit": 128          // Memory limit (MB)
  },
  
  // === OPTIONAL METADATA ===
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://example.com"
  },
  "license": "MIT",
  "repository": "https://github.com/owner/repo",
  "documentation": "https://docs.example.com",
  "icon": "lock",               // Lucide icon name or URL
  "category": "security",       // See categories below
  "tags": ["tag1", "tag2"],     // Searchable tags (max 10)
  
  // === ROUTING (container only) ===
  "basePath": "/api/v1/my-service",  // API gateway route
  "hostPort": 5001,                   // Fixed host port (auto if omitted)
  
  // === HEALTH CHECKS ===
  "healthCheck": {
    "path": "/health",
    "interval": 30,
    "timeout": 10,
    "retries": 3
  },
  
  // === CONFIGURATION ===
  "config": {
    "schema": {                 // JSON Schema for settings
      "type": "object",
      "properties": {
        "setting1": { "type": "string", "default": "value" }
      }
    },
    "defaults": {
      "setting1": "value"
    }
  },
  
  // === ENVIRONMENT VARIABLES ===
  "environment": [
    {
      "name": "API_KEY",
      "description": "External API key",
      "required": true,
      "secret": true,           // Masked in UI
      "default": "",
      "validation": "^[A-Za-z0-9]{32}$"  // Regex pattern
    }
  ],
  
  // === VOLUMES (container only) ===
  "volumes": [
    {
      "name": "data",
      "containerPath": "/app/data",
      "description": "Persistent data storage",
      "readOnly": false
    }
  ],
  
  // === RESOURCE LIMITS ===
  "resources": {
    "memory": "512m",           // Memory limit (256m, 1g, 2g)
    "cpu": "1.0",               // CPU cores (0.5, 1, 2)
    "gpu": false                // GPU access required
  },
  
  // === DEPENDENCIES ===
  "dependencies": {
    "forgehooks": [             // Other ForgeHooks required
      { "id": "crypto-service", "version": ">=1.0.0", "optional": false }
    ],
    "services": ["redis", "postgres", "qdrant"]  // Core services
  },
  
  // === SPECIAL CAPABILITIES ===
  "capabilities": [
    "network-host",             // Host network access
    "privileged",               // Privileged container
    "gpu"                       // GPU passthrough
  ],
  
  // === LIFECYCLE HOOKS ===
  "hooks": {
    "onInstall": "npm run migrate",
    "onStart": "node init.js",
    "onStop": "node cleanup.js",
    "onUninstall": "npm run rollback"
  }
}
```

### Categories

| Category | Description | Examples |
| -------- | ----------- | -------- |
| `security` | Authentication, encryption, access control | crypto-service, auth-service |
| `ai` | Machine learning, NLP, computer vision | llm-service, ocr-service |
| `data` | Data processing, storage, transformation | vector-service, data-transform |
| `media` | Images, video, audio, documents | pdf-service, image-service |
| `integration` | External APIs, webhooks, connectors | slack-connector, github-hooks |
| `utility` | General-purpose tools | string-utils, date-utils |
| `analytics` | Metrics, reporting, visualization | metrics-service |
| `communication` | Email, SMS, notifications | email-service |

---

## Endpoint Definitions

Endpoints define the API surface of your ForgeHook:

```json
{
  "endpoints": [
    {
      "method": "POST",                    // HTTP method
      "path": "/hash",                     // Path (relative to basePath)
      "description": "Hash data using SHA, bcrypt, or argon2",
      "authentication": true,              // Require auth (default: true)
      "requestBody": {                     // Example for playground/docs
        "data": "string to hash",
        "algorithm": "sha256"
      },
      "rateLimit": {                       // Custom rate limiting
        "requests": 100,
        "period": "minute"
      }
    },
    {
      "method": "GET",
      "path": "/health",
      "description": "Health check",
      "authentication": false              // Public endpoint
    }
  ]
}
```

### Standard Endpoints

All ForgeHooks should implement:

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/health` | GET | Returns `{ "status": "ok" }` when healthy |
| `/metrics` | GET | Prometheus metrics (optional) |

---

## Container ForgeHook Structure

```
my-forgehook/
├── forgehook.json          # Manifest (required)
├── Dockerfile              # Container build (required)
├── README.md               # Documentation
├── openapi.yaml            # OpenAPI spec (optional)
├── src/                    # Source code
│   ├── index.ts
│   ├── routes/
│   └── services/
├── tests/                  # Test files
└── package.json            # Dependencies (Node.js)
```

### Dockerfile Guidelines

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (layer caching)
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

# Build if needed
RUN npm run build

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1

# Non-root user
USER node

EXPOSE 3001

CMD ["node", "dist/index.js"]
```

### Example Implementation (Node.js/Fastify)

```typescript
import Fastify from 'fastify';

const app = Fastify({ logger: true });

// Health check
app.get('/health', async () => ({ status: 'ok' }));

// Main endpoint
app.post('/process', async (request, reply) => {
  const { data } = request.body as { data: string };
  
  // Your logic here
  const result = await processData(data);
  
  return { success: true, result };
});

// Start server
app.listen({ port: 3001, host: '0.0.0.0' });
```

---

## Embedded ForgeHook Structure

```
my-embedded-forgehook/
├── forgehook.json          # Manifest with runtime: "embedded"
├── index.js                # Main entry point (bundled JS)
├── README.md               # Documentation
└── src/                    # Source (if using build step)
    └── index.ts
```

### Embedded Module Format

The entrypoint file must export functions that match the `exports` array:

```javascript
// index.js - Embedded ForgeHook

/**
 * Slugify a string
 * @param {object} input - { text: string, separator?: string }
 * @param {object} context - Execution context (pluginId, requestId, config)
 * @returns {Promise<string>}
 */
export async function slugify(input, context) {
  const { text, separator = '-' } = input;
  
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, separator)
    .replace(/^-+|-+$/g, '');
}

/**
 * Convert to camelCase
 */
export async function camelCase(input, context) {
  const { text } = input;
  
  return text
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, char) => char.toUpperCase());
}

// Export all functions
export default { slugify, camelCase };
```

### Execution Context

Every embedded function receives a context object:

```typescript
interface EmbeddedExecutionContext {
  pluginId: string;       // "string-utils"
  functionName: string;   // "slugify"
  requestId: string;      // UUID for tracing
  timeout: number;        // Timeout in ms
  config: Record<string, unknown>;  // Plugin config
}
```

### Sandbox Restrictions

Embedded plugins run in a V8 isolate with restrictions:

- ✅ Standard JavaScript (ES2022+)
- ✅ `Promise`, `async/await`
- ✅ Built-in objects (`Array`, `Object`, `String`, `Math`, `Date`, `JSON`)
- ❌ `require()` / `import` (bundle dependencies)
- ❌ `process`, `Buffer`, `fs`, `path` (no Node.js APIs)
- ❌ `fetch`, `XMLHttpRequest` (no network access)
- ❌ `eval`, `Function` constructor

---

## Registry Index Format

Registries publish a `forgehooks-registry.json` index:

```json
{
  "version": "1.1.0",
  "registry": {
    "name": "My Registry",
    "description": "Custom ForgeHook plugins",
    "url": "https://github.com/owner/registry",
    "maintainer": "Your Name"
  },
  "lastUpdated": "2026-01-19T18:00:00Z",
  "plugins": [
    {
      "id": "my-service",
      "verified": true,           // Registry-verified
      "featured": false,          // Featured in marketplace
      "downloads": 1250,          // Download count
      "rating": 4.8,              // Average rating (1-5)
      "repository": "https://github.com/owner/my-service",
      "manifest": { /* full forgehook.json */ }
    }
  ],
  "packages": {                   // Pre-built packages
    "my-service": {
      "version": "1.0.0",
      "file": "packages/my-service-1.0.0.fhk",
      "size": "200MB",
      "runtime": "container"
    }
  }
}
```

---

## Package Format (`.fhk`)

ForgeHook packages (`.fhk`) are tar.gz archives containing:

### Container Package

```
my-service-1.0.0.fhk (tar.gz)
├── manifest.json           # forgehook.json content
├── image.tar               # Docker image (docker save)
├── checksum.sha256         # File checksums
└── metadata.json           # Package metadata
```

### Embedded Package

```
string-utils-1.0.0.fhk (tar.gz)
├── manifest.json           # forgehook.json content
├── module.js               # Bundled JavaScript
├── checksum.sha256         # File checksums
└── metadata.json           # Package metadata
```

---

## API Response Format

All ForgeHooks should follow this response format:

### Success Response

```json
{
  "success": true,
  "data": { /* result */ },
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-19T18:00:00.000Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input: 'data' is required",
    "details": [
      { "field": "data", "message": "Required field missing" }
    ]
  },
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-19T18:00:00.000Z"
}
```

### Standard Error Codes

| Code | HTTP Status | Description |
| ---- | ----------- | ----------- |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Installation Methods

### 1. Marketplace (UI)

Users browse and install from the FlowForge Marketplace UI.

### 2. GitHub URL

Install directly from a GitHub repository:

```
owner/repo                    # Default branch, root forgehook.json
owner/repo/path/to/plugin     # Subfolder
owner/repo@v1.0.0             # Specific tag
owner/repo#branch-name        # Specific branch
```

### 3. Package Upload (`.fhk`)

Upload a pre-built package file through the UI or API.

### 4. API

```bash
# Install from GitHub
curl -X POST http://flowforge:4000/api/v1/plugins/install/github \
  -H "Content-Type: application/json" \
  -d '{"repository": "owner/my-forgehook", "autoStart": true}'

# Install from manifest URL
curl -X POST http://flowforge:4000/api/v1/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"manifestUrl": "https://example.com/forgehook.json"}'
```

---

## Best Practices

### General

1. **Use semantic versioning** - Follow `MAJOR.MINOR.PATCH` strictly
2. **Write clear descriptions** - Help users understand what your plugin does
3. **Include example requests** - Populate `requestBody` in endpoints
4. **Set appropriate resource limits** - Don't over-provision
5. **Implement health checks** - Enable proper lifecycle management

### Container Plugins

1. **Use multi-stage builds** - Keep images small
2. **Run as non-root** - Security best practice
3. **Handle signals** - Graceful shutdown on SIGTERM
4. **Log to stdout/stderr** - Enables log aggregation
5. **Use environment variables** - Don't hardcode configuration

### Embedded Plugins

1. **Keep it simple** - Complex logic belongs in containers
2. **Bundle dependencies** - No external requires
3. **Validate input** - Don't trust user data
4. **Handle errors** - Return meaningful error messages
5. **Stay synchronous when possible** - Avoid complex async chains

---

## Examples

### Minimal Container ForgeHook

```json
{
  "$schema": "https://leforge.io/schemas/forgehook-v1.json",
  "id": "hello-world",
  "name": "Hello World",
  "version": "1.0.0",
  "description": "Simple hello world service",
  "image": { "repository": "flowforge/hello-world", "tag": "latest" },
  "port": 3001,
  "endpoints": [
    { "method": "GET", "path": "/hello", "description": "Returns hello world" },
    { "method": "GET", "path": "/health", "description": "Health check", "authentication": false }
  ]
}
```

### Minimal Embedded ForgeHook

```json
{
  "$schema": "https://leforge.io/schemas/forgehook-v1.json",
  "id": "simple-math",
  "name": "Simple Math",
  "version": "1.0.0",
  "description": "Basic math operations",
  "runtime": "embedded",
  "embedded": {
    "entrypoint": "index.js",
    "exports": ["add", "subtract", "multiply", "divide"],
    "timeout": 1000,
    "memoryLimit": 32
  },
  "endpoints": [
    { "method": "POST", "path": "/add", "description": "Add two numbers" },
    { "method": "POST", "path": "/subtract", "description": "Subtract two numbers" }
  ]
}
```

---

## Resources

- **Schema**: `https://leforge.io/schemas/forgehook-v1.json`
- **Official Registry**: `https://github.com/LeForgeio/registry`
- **FlowForge Core**: `https://github.com/LeForgeio/leforge`
- **Examples**: See `plugins/` directory in the registry

---

*Last updated: January 2026*
