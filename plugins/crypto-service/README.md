# FlowForge Crypto Service

A production-ready Node.js/TypeScript microservice providing comprehensive cryptographic operations. Built with Fastify for high performance and designed as the reference implementation for all FlowForge services.

## Features

- 🔐 **Symmetric Encryption**: AES-128/256-GCM, AES-128/256-CBC with authenticated encryption
- 🔑 **Password Hashing**: bcrypt, Argon2id with configurable work factors
- #️⃣ **Cryptographic Hashing**: SHA-256, SHA-384, SHA-512
- 🎫 **JWT Operations**: Generate, verify, decode, and validate JSON Web Tokens
- ✍️ **HMAC Signatures**: Sign and verify message authentication codes
- 🎲 **Key Generation**: Cryptographically secure random key generation
- 📊 **Observability**: Health checks, metrics, structured logging with Pino
- 📚 **OpenAPI Documentation**: Interactive Swagger UI at `/docs`

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Start development server
npm run dev

# Open API documentation
open http://localhost:3001/docs
```

## API Endpoints

### Health & Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Comprehensive health check |
| GET | `/health/ready` | Kubernetes readiness probe |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/metrics` | Service metrics |
| GET | `/docs` | Swagger UI documentation |

### Encryption
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/encrypt` | Encrypt data with AES |
| POST | `/api/v1/decrypt` | Decrypt AES-encrypted data |

### Hashing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/hash` | Create hash (SHA/bcrypt/Argon2) |
| POST | `/api/v1/hash/verify` | Verify password against hash |

### JWT
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jwt/generate` | Generate JWT token |
| POST | `/api/v1/jwt/verify` | Verify JWT token |
| POST | `/api/v1/jwt/decode` | Decode JWT without verification |

### HMAC
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/hmac/sign` | Create HMAC signature |
| POST | `/api/v1/hmac/verify` | Verify HMAC signature |

### Keys
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/keys/generate` | Generate random key |

## Usage Examples

### Encrypt and Decrypt Data

```bash
# Encrypt
curl -X POST http://localhost:3001/api/v1/encrypt \
  -H "Content-Type: application/json" \
  -d '{
    "data": "Secret message",
    "key": "my-encryption-key-12345",
    "algorithm": "aes-256-gcm"
  }'

# Response:
# {
#   "success": true,
#   "data": {
#     "encrypted": "base64-encrypted-data",
#     "iv": "base64-iv",
#     "tag": "base64-auth-tag",
#     "algorithm": "aes-256-gcm"
#   }
# }

# Decrypt
curl -X POST http://localhost:3001/api/v1/decrypt \
  -H "Content-Type: application/json" \
  -d '{
    "encrypted": "base64-encrypted-data",
    "iv": "base64-iv",
    "tag": "base64-auth-tag",
    "key": "my-encryption-key-12345"
  }'
```

### Password Hashing with bcrypt

```bash
# Hash password
curl -X POST http://localhost:3001/api/v1/hash \
  -H "Content-Type: application/json" \
  -d '{
    "data": "user-password",
    "algorithm": "bcrypt"
  }'

# Verify password
curl -X POST http://localhost:3001/api/v1/hash/verify \
  -H "Content-Type: application/json" \
  -d '{
    "data": "user-password",
    "hash": "$2b$12$..."
  }'
```

### JWT Token Operations

```bash
# Generate JWT
curl -X POST http://localhost:3001/api/v1/jwt/generate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"userId": "123", "role": "admin"},
    "expiresIn": "1h",
    "secret": "your-32-character-secret-key!!!"
  }'

# Verify JWT
curl -X POST http://localhost:3001/api/v1/jwt/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "secret": "your-32-character-secret-key!!!"
  }'
```

### HMAC Signatures

```bash
# Sign data
curl -X POST http://localhost:3001/api/v1/hmac/sign \
  -H "Content-Type: application/json" \
  -d '{
    "data": "message to sign",
    "secret": "hmac-secret",
    "algorithm": "sha256"
  }'

# Verify signature
curl -X POST http://localhost:3001/api/v1/hmac/verify \
  -H "Content-Type: application/json" \
  -d '{
    "data": "message to sign",
    "signature": "hex-signature",
    "secret": "hmac-secret"
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `development` |
| `PORT` | Server port | `3001` |
| `HOST` | Server host | `0.0.0.0` |
| `LOG_LEVEL` | Logging level | `info` |
| `JWT_SECRET` | Default JWT signing secret | - |
| `JWT_DEFAULT_EXPIRY` | Default JWT expiration | `1h` |
| `JWT_DEFAULT_ALGORITHM` | Default JWT algorithm | `HS256` |
| `JWT_ISSUER` | JWT issuer claim | `flowforge` |
| `BCRYPT_ROUNDS` | bcrypt work factor | `12` |
| `ARGON2_MEMORY_COST` | Argon2 memory (KB) | `65536` |
| `ARGON2_TIME_COST` | Argon2 iterations | `3` |
| `ARGON2_PARALLELISM` | Argon2 parallelism | `4` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## Development

```bash
# Install dependencies
npm install

# Start with hot reload
npm run dev

# Build TypeScript
npm run build

# Run production
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Type checking
npm run typecheck

# Lint code
npm run lint
npm run lint:fix
```

## Docker

```bash
# Build image
docker build -t flowforge/crypto-service:latest .

# Run container
docker run -p 3001:3001 \
  -e JWT_SECRET="your-secret-key" \
  flowforge/crypto-service:latest

# Build and run with docker-compose
docker-compose up crypto-service
```

## Architecture

```
crypto-service/
├── src/
│   ├── config.ts          # Configuration management
│   ├── app.ts             # Fastify application setup
│   ├── index.ts           # Server entry point
│   ├── routes/            # Route handlers
│   │   ├── encryption.routes.ts
│   │   ├── hash.routes.ts
│   │   ├── jwt.routes.ts
│   │   ├── hmac.routes.ts
│   │   ├── keys.routes.ts
│   │   └── health.routes.ts
│   ├── services/          # Business logic
│   │   └── crypto.service.ts
│   ├── schemas/           # Joi validation schemas
│   ├── types/             # TypeScript interfaces
│   └── utils/             # Utilities (logger, etc.)
├── tests/                 # Jest test suites
├── Dockerfile             # Multi-stage Docker build
└── package.json
```

## Response Format

All endpoints return a consistent JSON response:

```json
{
  "success": true,
  "data": { ... },
  "requestId": "uuid",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Description",
    "details": [...]
  },
  "requestId": "uuid",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Security Considerations

- ⚠️ **Never log sensitive data** - keys, passwords, encrypted content
- 🔑 **Use strong secrets** - JWT secret must be at least 32 characters
- 🛡️ **Use authenticated encryption** - AES-GCM preferred over AES-CBC
- 🔐 **Use Argon2id for passwords** - more resistant to GPU attacks than bcrypt
- 🕐 **Set appropriate token expiry** - short-lived tokens reduce risk
- 🌐 **Configure CORS properly** - restrict origins in production

## License

MIT License - see [LICENSE](../../LICENSE)
