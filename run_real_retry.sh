#!/bin/bash
set -e

echo "=== PASO 1: VERIFICAR RECURSOS ==="
docker system df
docker model ls || true
docker info | grep -iE "memory|cpus" || true
docker compose version

echo "=== PASO 3: VERIFICAR MODELO ==="
docker model inspect ai/gemma4:E4B || docker model pull ai/gemma4:E4B

echo "=== PASO 4: LIMPIEZA CONTROLADA ==="
docker compose down || true
docker builder prune -f

echo "=== PASO 5: BUILD Y ARRANQUE ==="
docker compose build --no-cache
docker compose up -d

echo "=== ESPERANDO HEALTHCHECK ==="
healthy=false
for i in {1..18}; do
    if curl --fail -s http://localhost:8000/health > /dev/null; then
        echo "API HEALTHY"
        healthy=true
        break
    fi
    sleep 5
done

if [ "$healthy" = false ]; then
    echo "ERROR: El API no está saludable."
    docker compose ps
    docker compose logs --no-log-prefix api
    docker compose logs --no-log-prefix ui
    exit 1
fi

echo "=== PASO 6: EVALUACIÓN REAL ==="
if command -v uv &>/dev/null; then
    uv run python evals/runner.py || true
else
    python3 evals/runner.py || true
fi

echo "=== REPORTE FINAL GENERADO ==="
cat evals/report.json || echo "Sin reporte."
