# Use PyTorch base image to ensure compatibility
FROM pytorch/pytorch:2.1.1-cpu as base

WORKDIR /app

# Install system dependencies needed for the application
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ===== PRODUCTION STAGE =====
FROM base as production

# Install all production dependencies, including torch
COPY requirements-prod-ml.txt .
RUN pip install --no-cache-dir --timeout 1800 --retries 5 --prefer-binary --index-url https://download.pytorch.org/whl/cpu 'torch==2.1.1+cpu' --find-links https://download.pytorch.org/whl/torch_stable.html --no-build-isolation --force-reinstall
RUN pip install --no-cache-dir --timeout 1800 --retries 5 --no-build-isolation -r requirements-prod-ml.txt

# Copiar código da aplicação
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

# Rodar como não-root por segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ===== DEVELOPMENT STAGE =====
FROM pytorch/pytorch:2.1.1-cpu as development

# Install system dependencies needed for development
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências de desenvolvimento (com TensorFlow)
COPY requirements-base.txt .
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-base.txt -r requirements-ml.txt

# Copiar código da aplicação
COPY . .

EXPOSE 8000

# Permitir acesso como root para desenvolvimento
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== LABELS =====
LABEL version="1.0.0"
LABEL maintainer="ClimateAI"
LABEL description="ClimateAI - Framework Integrado de Modelagem Climático-Econômica"
