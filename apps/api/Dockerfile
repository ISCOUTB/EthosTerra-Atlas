# === Construcción de la API BESA-LLM ===
FROM python:3.11-slim

# Configuraciones de Python para entorno Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar uv para resolución ultrarrápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar configuración de dependencias
COPY pyproject.toml ./

# Instalar dependencias a nivel de sistema dentro del contenedor
RUN uv pip install --system -r pyproject.toml

# Instalar curl para el healthcheck de Docker Compose
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar el código fuente (dominio, puertos, adaptadores, api)
COPY src/ ./src/

# Exponer el puerto de FastAPI
EXPOSE 8000

# Ejecutar el servidor con Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
