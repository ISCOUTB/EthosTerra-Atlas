# === Construcción de la API BESA-LLM (EthosTerra Atlas) ===
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:/app/src"

WORKDIR /app

# Instalar utilidades del sistema para OCR, extracción de PDFs y healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para resolución rápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar manifiesto de dependencias de la API
COPY apps/api/pyproject.toml ./pyproject.toml

# Instalar dependencias a nivel de sistema dentro del contenedor
RUN uv pip install --system -r pyproject.toml

# Copiar módulos de código fuente del monorepo requeridos por la API y Atlas
COPY apps/api/src/ ./src/
COPY apps/atlas/ ./apps/atlas/
COPY outputs/ ./outputs/

# Exponer el puerto de FastAPI
EXPOSE 8000

# Ejecutar el servidor con Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
