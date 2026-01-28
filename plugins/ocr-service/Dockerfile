FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS production
WORKDIR /app
RUN useradd --create-home appuser
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr poppler-utils \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
COPY src ./src
# Copy integration assets for air-gapped distribution
COPY --chown=appuser:appuser integrations/ /integrations/
RUN chown -R appuser:appuser /app
USER appuser
ENV ENVIRONMENT=production PORT=3004
EXPOSE 3004
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3004"]

FROM python:3.11-slim AS development
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential tesseract-ocr poppler-utils \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV ENVIRONMENT=development PORT=3004
EXPOSE 3004 5678
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3004", "--reload"]
