#!/bin/bash
set -e

echo "=== 1. VERIFICANDO DMR ==="
docker desktop status model-runner || true

echo "=== 2. DESCARGANDO MODELO ==="
START_TIME=$SECONDS
TAG=""
if docker model pull ai/gemma4:E4B; then
    TAG="ai/gemma4:E4B"
elif docker model pull ai/gemma4:4b; then
    TAG="ai/gemma4:4b"
else
    echo "Ambos pulls fallaron."
    exit 1
fi
ELAPSED=$(($SECONDS - $START_TIME))
echo "TAG_EXITOSO=$TAG"
echo "TIEMPO_DESCARGA_SEGUNDOS=$ELAPSED"
docker model ls | grep -i "gemma4" || true

echo "=== 3. LIMPIEZA Y BUILD ==="
docker compose down -v
docker compose build --no-cache

echo "=== 4. LEVANTANDO SERVICIOS ==="
docker compose up -d

echo "=== 5. ESPERANDO HEALTHCHECK ==="
healthy=false
for i in {1..18}; do
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo "API HEALTHY"
        healthy=true
        break
    fi
    sleep 5
done

if [ "$healthy" = false ]; then
    echo "ERROR: El API no está saludable."
    docker compose logs api
    exit 1
fi

echo "=== 6. EJECUTANDO EVALUACION REAL ==="
# Intentando priorizar uv para compatibilidad con el ecosistema
if command -v uv &>/dev/null; then
    uv run python evals/runner.py || true
else
    python3 evals/runner.py || true
fi

echo "=== RESULTADO DE EVALUACION ==="
cat evals/report.json || echo "No se encontró reporte."
