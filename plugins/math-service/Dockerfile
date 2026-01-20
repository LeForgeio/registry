# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY src ./src

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Environment variables
ENV ENVIRONMENT=production
ENV PORT=3002
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 3002

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:3002/health').raise_for_status()" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3002"]

# Development stage
FROM python:3.11-slim AS development

WORKDIR /app

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install all dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src

# Environment variables
ENV ENVIRONMENT=development
ENV PORT=3002
ENV PYTHONUNBUFFERED=1

EXPOSE 3002 5678

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3002", "--reload"]
