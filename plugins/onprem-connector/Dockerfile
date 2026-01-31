# On-Premises Connector - LeForge Plugin
# Multi-stage build for smaller image size

# ============================================================================
# Stage 1: Build Oracle Instant Client dependencies
# ============================================================================
FROM node:20-alpine AS oracle-builder

# Install build tools for Oracle client
RUN apk add --no-cache libaio libnsl libc6-compat curl unzip

# Download Oracle Instant Client (optional - only if Oracle support needed)
# Uncomment these lines if Oracle database support is required:
# ENV ORACLE_HOME=/opt/oracle/instantclient
# ENV LD_LIBRARY_PATH=$ORACLE_HOME
# RUN mkdir -p /opt/oracle && \
#     cd /opt/oracle && \
#     curl -o instantclient.zip https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linux.x64-21.12.0.0.0dbru.zip && \
#     unzip instantclient.zip && \
#     rm instantclient.zip && \
#     mv instantclient* instantclient

# ============================================================================
# Stage 2: Install dependencies
# ============================================================================
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production --ignore-scripts

# ============================================================================
# Stage 3: Production image
# ============================================================================
FROM node:20-alpine

LABEL maintainer="LeForge <support@leforge.io>"
LABEL description="On-Premises Connector - Access databases, APIs, file shares via LeForge"
LABEL version="1.0.0"

# Install runtime dependencies
RUN apk add --no-cache \
    libaio \
    libnsl \
    libc6-compat \
    curl \
    ca-certificates \
    tzdata

# Create non-root user
RUN addgroup -g 1001 -S leforge && \
    adduser -S leforge -u 1001 -G leforge

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy Oracle Instant Client (if needed)
# COPY --from=oracle-builder /opt/oracle /opt/oracle
# ENV ORACLE_HOME=/opt/oracle/instantclient
# ENV LD_LIBRARY_PATH=$ORACLE_HOME

# Copy application code
COPY src/ ./src/
COPY package.json ./

# Create data directory for connections persistence
RUN mkdir -p /app/data && chown -R leforge:leforge /app

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3001
ENV CONNECTIONS_FILE=/app/data/connections.json

# Switch to non-root user
USER leforge

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Start the service
CMD ["node", "src/index.js"]
