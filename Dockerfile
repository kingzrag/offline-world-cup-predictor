# ==========================================
# Production-Grade Multi-stage Slim Dockerfile
# ==========================================

# --- Stage 1: Build & Dependency Resolver ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a separate wheels cache folder to shrink image size
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# --- Stage 2: Runtime Environment ---
FROM python:3.11-slim

WORKDIR /app

# Install essential postgres runtime dependency
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Retrieve wheels and requirements compiled in builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

# Copy full application code tree
COPY . .

# Secure permissions (avoid running as root in standard production containers)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run FastAPI using production-ready uvicorn configurations
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
