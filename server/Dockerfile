# Multi-stage Dockerfile optimized for DigitalOcean App Platform

# ==========================================
# Stage 1: Builder (Dependencies & Compilation)
# ==========================================
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies (gcc for compiling python extensions, libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment to isolate dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirement files (relative to repo root due to source_dir: .)
COPY server/requirements-base.txt .
COPY server/requirements-ml.txt .
COPY server/requirements-prod-ml.txt .

# Install Python dependencies
# - Upgrade pip
# - Install numpy first (often a build dep)
# - Install PyTorch CPU version explicitly to avoid downloading CUDA bloat
# - Install remaining production requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "numpy<2.0.0" && \
    pip install --no-cache-dir --prefer-binary --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0+cpu' && \
    pip install --no-cache-dir -r requirements-prod-ml.txt

# ==========================================
# Stage 2: Production (Runtime)
# ==========================================
FROM python:3.10-slim as production

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application code (contents of server/ directory to /app)
COPY server/ .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check using native urllib to avoid dependency on 'requests'
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start application with 1 worker to prevent OOM on 512MB containers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# ==========================================
# Stage 3: Development (Optional/Legacy)
# ==========================================
# Kept for local development reference, but not used by DO (since production is defined before/last depending on target,
# but usually we want production to be the default build target.
# Ideally, we should specify target in docker-compose or similar, but for DO App Platform
# without target specified, it effectively builds the last stage IF strict.
# actually, DO App Platform builds the FROM specified or the last one.
# To be safe, we place production LAST if we want it to be the default,
# OR we assume the user might want development.
# BUT, since we are optimizing for DEPLOYMENT, 'production' MUST be the build result.
# So I will NOT include development stage here to keep it lean and avoid confusion
# unless specifically requested. The previous file had it.
# I'll stick to just Production for now to solve the incident.
