FROM node:20-alpine

# Install FFmpeg for video transcoding
RUN apk add --no-cache ffmpeg

# Install poppler-utils for PDF processing
RUN apk add --no-cache poppler-utils

# Install additional tools
RUN apk add --no-cache \
    curl \
    ca-certificates \
    python3 \
    py3-pip

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Copy integration assets for air-gapped distribution (if exists)
# COPY integrations/ /integrations/

# Create data directory
RUN mkdir -p /data/files /data/chunks /data/transforms

# Set environment
ENV NODE_ENV=production
ENV STORAGE_PATH=/data/files

EXPOSE 3020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3020/health || exit 1

CMD ["node", "src/server.js"]
