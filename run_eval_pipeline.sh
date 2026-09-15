#!/bin/bash
set -e

echo "=== VERIFICANDO MODELO ==="
if docker model ls &>/dev/null; then
    echo "Comando 'docker model' disponible."
    docker model pull ai/gemma4:E4B || docker model pull ai/gemma4:4b
else
    echo "ALERTA: 'docker model' no es un comando nativo en este entorno. Se delega la orquestación a la imagen base del compose."
fi

echo "=== RECONSTRUYENDO SERVICIOS (NO CACHE) ==="
docker compose build --no-cache

echo "=== LEVANTANDO SERVICIOS ==="
docker compose up -d

echo "=== ESPERANDO HEALTHCHECK (MAX 90s) ==="
healthy=false
for i in {1..18}; do
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo "API está HEALTHY!"
        healthy=true
        break
    fi
    echo "Esperando 5s... intento $i"
    sleep 5
done

if [ "$healthy" = false ]; then
    echo "ERROR: El API nunca alcanzó estado healthy."
    docker compose logs api
fi

echo "=== EJECUTANDO EVALUACION REAL ==="
if command -v uv >/dev/null; then
    echo "Usando uv run python..."
    uv run python evals/runner.py || true
elif command -v python3 >/dev/null; then
    echo "Usando python3 nativo..."
    python3 evals/runner.py || true
else
    echo "ERROR: No se encontró uv ni python3 para ejecutar la prueba."
fi

echo "=== RESULTADO DEL REPORTE ==="
cat evals/report.json || echo "No se generó el reporte."
