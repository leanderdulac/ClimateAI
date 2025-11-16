FROM python:3.11-slim as base

WORKDIR /app

# Instalar dependências de sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ===== PRODUCTION STAGE =====
FROM base as production

# Instalar dependências de produção (com PyTorch, sem TensorFlow)
COPY requirements-prod-ml.txt .
RUN pip install --no-cache-dir -r requirements-prod-ml.txt

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
FROM base as development

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