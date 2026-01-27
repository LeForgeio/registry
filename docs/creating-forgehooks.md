# Creating ForgeHooks

> A step-by-step guide to building your own FlowForge plugins

## Quick Start

ForgeHooks come in two flavors - pick the one that fits your use case:

| Type | Best For | Size | Startup |
|------|----------|------|---------|
| **Embedded** | Simple utilities, text/data transforms | < 100 KB | Instant |
| **Container** | Complex services, AI/ML, external dependencies | MBs-GBs | Seconds |

---

## Option A: Create an Embedded Plugin (Lightweight)

Perfect for simple utilities that don't need external dependencies.

### Step 1: Create project structure

```
my-string-tools/
├── forgehook.json    # Plugin manifest
├── index.js          # Your code
└── README.md         # Documentation
```

### Step 2: Write your manifest (`forgehook.json`)

```json
{
  "$schema": "https://flowforge.dev/schemas/forgehook-v1.json",
  "id": "my-string-tools",
  "name": "My String Tools",
  "version": "1.0.0",
  "description": "Custom string manipulation utilities",
  "author": {
    "name": "Your Name"
  },
  "license": "MIT",
  "icon": "type",
  "category": "utility",
  "tags": ["string", "text", "utility"],
  "runtime": "embedded",
  "embedded": {
    "entrypoint": "index.js",
    "exports": ["reverse", "countWords", "extractEmails"],
    "timeout": 1000,
    "memoryLimit": 32
  },
  "endpoints": [
    {
      "method": "POST",
      "path": "/reverse",
      "description": "Reverse a string"
    },
    {
      "method": "POST",
      "path": "/countWords",
      "description": "Count words in text"
    },
    {
      "method": "POST",
      "path": "/extractEmails",
      "description": "Extract email addresses from text"
    }
  ],
  "resources": {
    "memory": "32Mi",
    "cpu": "0.1"
  }
}
```

### Step 3: Implement your functions (`index.js`)

```javascript
/**
 * Reverse a string
 * @param {object} input - { text: string }
 * @param {object} context - Execution context
 * @returns {Promise<{result: string}>}
 */
export async function reverse(input, context) {
  const { text } = input;
  
  if (!text || typeof text !== 'string') {
    throw new Error('Input "text" is required and must be a string');
  }
  
  return {
    result: text.split('').reverse().join('')
  };
}

/**
 * Count words in text
 * @param {object} input - { text: string }
 * @returns {Promise<{count: number, words: string[]}>}
 */
export async function countWords(input, context) {
  const { text } = input;
  
  if (!text) {
    return { count: 0, words: [] };
  }
  
  const words = text.trim().split(/\s+/).filter(w => w.length > 0);
  
  return {
    count: words.length,
    words
  };
}

/**
 * Extract email addresses from text
 * @param {object} input - { text: string }
 * @returns {Promise<{emails: string[], count: number}>}
 */
export async function extractEmails(input, context) {
  const { text } = input;
  
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  const emails = text.match(emailRegex) || [];
  
  return {
    emails: [...new Set(emails)], // Remove duplicates
    count: emails.length
  };
}

export default { reverse, countWords, extractEmails };
```

### Step 4: Test locally

```bash
# Install from your local folder
curl -X POST http://localhost:3000/api/v1/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/my-string-tools"}'

# Test your function
curl -X POST http://localhost:8000/api/v1/my-string-tools/reverse \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

---

## Option B: Create a Container Plugin (Full Service)

For services that need Docker, Python, external libraries, or complex processing.

### Step 1: Create project structure

```
my-image-processor/
├── forgehook.json    # Plugin manifest
├── Dockerfile        # Container build
├── package.json      # Dependencies
├── src/
│   └── index.ts      # Main entry
├── tests/
└── README.md
```

### Step 2: Write your manifest (`forgehook.json`)

```json
{
  "$schema": "https://flowforge.dev/schemas/forgehook-v1.json",
  "id": "my-image-processor",
  "name": "My Image Processor",
  "version": "1.0.0",
  "description": "Custom image processing with Sharp",
  "author": {
    "name": "Your Name"
  },
  "license": "MIT",
  "icon": "image",
  "category": "media",
  "tags": ["image", "processing", "resize"],
  "image": {
    "repository": "your-dockerhub/my-image-processor",
    "tag": "latest"
  },
  "port": 3001,
  "basePath": "/api/v1/my-image-processor",
  "endpoints": [
    {
      "method": "POST",
      "path": "/grayscale",
      "description": "Convert image to grayscale"
    },
    {
      "method": "POST",
      "path": "/blur",
      "description": "Apply blur effect",
      "requestBody": {
        "sigma": 5
      }
    },
    {
      "method": "GET",
      "path": "/health",
      "description": "Health check",
      "authentication": false
    }
  ],
  "environment": [
    {
      "name": "MAX_FILE_SIZE_MB",
      "description": "Maximum file size in MB",
      "required": false,
      "default": "10"
    }
  ],
  "resources": {
    "memory": "512m",
    "cpu": "1.0"
  },
  "healthCheck": {
    "path": "/health",
    "interval": 30,
    "timeout": 10,
    "retries": 3
  }
}
```

### Step 3: Create your Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install native dependencies for sharp
RUN apk add --no-cache vips-dev

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY src/ ./src/
COPY tsconfig.json ./

# Build TypeScript
RUN npm run build

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget -qO- http://localhost:3001/health || exit 1

# Run as non-root
USER node

EXPOSE 3001

CMD ["node", "dist/index.js"]
```

### Step 4: Implement your service (`src/index.ts`)

```typescript
import Fastify from 'fastify';
import multipart from '@fastify/multipart';
import sharp from 'sharp';

const app = Fastify({ logger: true });

// Enable file uploads
app.register(multipart, {
  limits: {
    fileSize: (parseInt(process.env.MAX_FILE_SIZE_MB || '10')) * 1024 * 1024
  }
});

// Health check
app.get('/health', async () => ({ status: 'ok' }));

// Grayscale conversion
app.post('/grayscale', async (request, reply) => {
  const data = await request.file();
  if (!data) {
    return reply.code(400).send({ error: 'No file uploaded' });
  }
  
  const buffer = await data.toBuffer();
  const result = await sharp(buffer).grayscale().toBuffer();
  
  reply.header('Content-Type', 'image/png');
  return result;
});

// Blur effect
app.post('/blur', async (request, reply) => {
  const data = await request.file();
  if (!data) {
    return reply.code(400).send({ error: 'No file uploaded' });
  }
  
  const sigma = parseInt(request.query.sigma as string) || 5;
  const buffer = await data.toBuffer();
  const result = await sharp(buffer).blur(sigma).toBuffer();
  
  reply.header('Content-Type', 'image/png');
  return result;
});

// Start server
const PORT = parseInt(process.env.PORT || '3001');
app.listen({ port: PORT, host: '0.0.0.0' }, (err) => {
  if (err) {
    app.log.error(err);
    process.exit(1);
  }
});
```

### Step 5: Build and push your image

```bash
# Build the image
docker build -t your-dockerhub/my-image-processor:latest .

# Test locally
docker run -p 3001:3001 your-dockerhub/my-image-processor:latest

# Push to Docker Hub
docker push your-dockerhub/my-image-processor:latest
```

### Step 6: Install in FlowForge

```bash
# Install from GitHub (if you pushed your code there)
curl -X POST http://localhost:3000/api/v1/plugins/install/github \
  -H "Content-Type: application/json" \
  -d '{"repository": "your-username/my-image-processor", "autoStart": true}'

# Or install from manifest URL
curl -X POST http://localhost:3000/api/v1/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"manifestUrl": "https://raw.githubusercontent.com/your-username/my-image-processor/main/forgehook.json"}'
```

---

## Publishing to the Registry

### 1. Create a GitHub Repository

Push your ForgeHook to a public GitHub repository with `forgehook.json` at the root.

### 2. Submit a Pull Request

Add your plugin to the official registry:

1. Fork [forgehooks-registry](https://github.com/danstoll/forgehooks-registry)
2. Add your plugin folder to `plugins/`
3. Update `forgehooks-registry.json` with your manifest
4. Submit a PR

### 3. Build a Package (Optional)

Create a `.fhk` package for offline installation:

```bash
# For container plugins
./scripts/build-plugin-image.sh my-plugin-folder

# This creates: packages/my-plugin-1.0.0.fhk
```

---

## Manifest Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique identifier (lowercase, hyphens) |
| `name` | ✅ | Display name |
| `version` | ✅ | Semantic version (X.Y.Z) |
| `description` | ✅ | Brief description |
| `endpoints` | ✅ | API endpoint definitions |
| `image` | Container only | Docker image reference |
| `port` | Container only | Container port |
| `runtime` | Embedded only | Set to `"embedded"` |
| `embedded` | Embedded only | Embedded configuration |
| `author` | ⭐ | Author information |
| `license` | ⭐ | License identifier |
| `icon` | ⭐ | Lucide icon name |
| `category` | ⭐ | Plugin category |
| `tags` | ⭐ | Searchable tags |

⭐ = Recommended

For the complete specification, see [FORGEHOOK_SPECIFICATION.md](./FORGEHOOK_SPECIFICATION.md).

---

## Categories

Choose the most appropriate category for your plugin:

| Category | Description |
|----------|-------------|
| `security` | Encryption, authentication, access control |
| `ai` | Machine learning, NLP, computer vision |
| `data` | Data processing, storage, transformation |
| `media` | Images, video, audio, documents |
| `integration` | External APIs, webhooks, connectors |
| `utility` | General-purpose tools |
| `analytics` | Metrics, reporting, visualization |
| `communication` | Email, SMS, notifications |

---

## Best Practices

### All Plugins

- ✅ Use semantic versioning (`1.0.0`, `1.0.1`, `1.1.0`)
- ✅ Write clear descriptions
- ✅ Include example request bodies in endpoints
- ✅ Set appropriate resource limits
- ✅ Add helpful tags for discoverability

### Embedded Plugins

- ✅ Keep code simple and focused
- ✅ Bundle all dependencies (no external imports)
- ✅ Validate all inputs
- ✅ Return clear error messages
- ✅ Stay under 100KB total

### Container Plugins

- ✅ Use multi-stage Docker builds
- ✅ Run as non-root user
- ✅ Implement `/health` endpoint
- ✅ Handle SIGTERM gracefully
- ✅ Log to stdout/stderr
- ✅ Use environment variables for config

---

## Troubleshooting

### Plugin won't install

- Check `forgehook.json` syntax with a JSON validator
- Verify `id` is lowercase with only alphanumeric and hyphens
- Ensure all required fields are present

### Container won't start

- Check Docker logs: `docker logs flowforge-my-plugin`
- Verify the port in manifest matches your app
- Test the image locally: `docker run -p 3001:3001 your-image`

### Embedded function errors

- Check the browser console for detailed errors
- Ensure exported function names match `exports` array
- Verify input/output formats

---

## Examples

Browse complete working examples in the registry:

- [string-utils](../plugins/string-utils/) - Embedded string manipulation
- [date-utils](../plugins/date-utils/) - Embedded date utilities
- [formula-engine](../plugins/formula-engine/) - Embedded Excel functions
- [crypto-service](../plugins/crypto-service/) - Container cryptography
- [llm-service](../plugins/llm-service/) - Container AI service

---

## Need Help?

- 📖 [Full Specification](./FORGEHOOK_SPECIFICATION.md)
- 💬 [GitHub Discussions](https://github.com/danstoll/flowforge/discussions)
- 🐛 [Report Issues](https://github.com/danstoll/forgehooks-registry/issues)
