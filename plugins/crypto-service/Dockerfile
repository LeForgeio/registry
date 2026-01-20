# ==============================================================================
# FlowForge Crypto Service - Production Dockerfile
# Multi-stage build for minimal image size (<100MB)
# ==============================================================================

# Stage 1: Build stage
FROM node:20-alpine AS builder

# Install build dependencies for native modules (argon2, bcrypt)
RUN apk add --no-cache python3 make g++ linux-headers

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci --include=dev

# Copy source code
COPY tsconfig.json ./
COPY src ./src

# Build TypeScript to JavaScript
RUN npm run build

# Prune dev dependencies for production
RUN npm prune --production

# ==============================================================================
# Stage 2: Production stage
FROM node:20-alpine AS production

# Security: Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S crypto -u 1001 -G nodejs

# Install runtime dependencies for native modules
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy built application from builder stage
COPY --from=builder --chown=crypto:nodejs /app/dist ./dist
COPY --from=builder --chown=crypto:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=crypto:nodejs /app/package.json ./package.json

# Set environment variables
ENV NODE_ENV=production \
    PORT=3001 \
    HOST=0.0.0.0

# Expose service port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3001/health/live || exit 1

# Switch to non-root user
USER crypto

# Start the service
CMD ["node", "dist/index.js"]

# ==============================================================================
# Stage 3: Development stage
FROM node:20-alpine AS development

# Install build dependencies for native modules
RUN apk add --no-cache python3 make g++ linux-headers

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm ci

# Copy source code
COPY tsconfig.json ./
COPY src ./src

# Environment variables
ENV NODE_ENV=development \
    PORT=3001 \
    HOST=0.0.0.0

EXPOSE 3001 9229

CMD ["npm", "run", "dev"]

# ==============================================================================
# Labels for container metadata
# ==============================================================================
LABEL org.opencontainers.image.title="FlowForge Crypto Service" \
      org.opencontainers.image.description="Production-ready cryptographic operations microservice" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="FlowForge" \
      org.opencontainers.image.source="https://github.com/flowforge/flowforge" \
      org.opencontainers.image.licenses="MIT"
