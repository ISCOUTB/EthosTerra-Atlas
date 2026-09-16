#!/usr/bin/env bash
set -u

# Detección robusta de la raíz del proyecto
if [ -f "$PWD/compose.yaml" ] || [ -f "$PWD/docker-compose.yml" ] || [ -f "$PWD/evals/runner.py" ]; then
    PROJECT_ROOT="$PWD"
elif [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/evals/runner.py" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
elif [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/evals/runner.py" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

cd "$PROJECT_ROOT"

# Argumentos posicionales con valores por defecto
DATASET="${1:-evals/datasets/test-cases.json}"
PROMPT_VERSION="${2:-case_pure_v1}"
MODEL_VERSION="${3:-ai/gemma4:E4B}"
OUTPUT_REPORT="${4:-evals/report.json}"

# Resolver rutas si son relativas
if [ ! -f "$DATASET" ] && [ -f "$PROJECT_ROOT/$DATASET" ]; then
    DATASET="$PROJECT_ROOT/$DATASET"
fi

if [ ! -f "$DATASET" ]; then
    echo "ERROR: El archivo de dataset no existe: $DATASET" >&2
    exit 1
fi

DEFAULT_DATASET="$PROJECT_ROOT/evals/datasets/test-cases.json"
DEFAULT_REPORT="$PROJECT_ROOT/evals/report.json"
RESTORE_DATASET=0
BACKUP_DATASET=""

cleanup() {
    if [ "$RESTORE_DATASET" -eq 1 ] && [ -n "$BACKUP_DATASET" ] && [ -f "$BACKUP_DATASET" ]; then
        cp "$BACKUP_DATASET" "$DEFAULT_DATASET"
        rm -f "$BACKUP_DATASET"
    fi
}
trap cleanup EXIT INT TERM

# Si el dataset proporcionado es diferente al default, respaldar y sustituir temporalmente
REAL_DATASET_PATH="$(cd "$(dirname "$DATASET")" && pwd)/$(basename "$DATASET")"
REAL_DEFAULT_DATASET_PATH="$(cd "$(dirname "$DEFAULT_DATASET")" && pwd)/$(basename "$DEFAULT_DATASET")"

if [ "$REAL_DATASET_PATH" != "$REAL_DEFAULT_DATASET_PATH" ]; then
    BACKUP_DATASET="$(mktemp)"
    cp "$DEFAULT_DATASET" "$BACKUP_DATASET"
    cp "$REAL_DATASET_PATH" "$DEFAULT_DATASET"
    RESTORE_DATASET=1
fi

# Ejecutar el runner de evaluación
echo "Ejecutando evaluación de modelo..."
echo "  Dataset: $DATASET"
echo "  Prompt Version: $PROMPT_VERSION"
echo "  Model Version: $MODEL_VERSION"
echo "  Output Report: $OUTPUT_REPORT"

RUNNER_EXIT=0
if command -v uv >/dev/null 2>&1; then
    uv run python evals/runner.py || RUNNER_EXIT=$?
elif command -v python3 >/dev/null 2>&1; then
    python3 evals/runner.py || RUNNER_EXIT=$?
elif command -v python >/dev/null 2>&1; then
    python evals/runner.py || RUNNER_EXIT=$?
else
    echo "ERROR: No se encontró intérprete de Python (uv, python3 o python)" >&2
    exit 1
fi

if [ ! -f "$DEFAULT_REPORT" ]; then
    echo "ERROR: No se generó el archivo de reporte en $DEFAULT_REPORT" >&2
    exit 1
fi

# Enriquecer reporte con parámetros y verificar conformidad de métricas
POST_PROCESS_EXIT=0
python3 - "$DEFAULT_REPORT" "$PROMPT_VERSION" "$MODEL_VERSION" << 'EOF' || POST_PROCESS_EXIT=$?
import sys
import json

report_path = sys.argv[1]
prompt_version = sys.argv[2]
model_version = sys.argv[3]

with open(report_path, "r") as f:
    data = json.load(f)

data["prompt_version"] = prompt_version
data["model_name"] = model_version

with open(report_path, "w") as f:
    json.dump(data, f, indent=2)

status = data.get("evaluation_status", "")
completed = data.get("completed_cases", 0)
total = data.get("total_cases", data.get("attempted_cases", 0))

# Fallar si la infraestructura falló o no se completaron todos los casos
if status != "success" or completed < total or total == 0:
    print(f"Evaluación fallida o incompleta: status={status}, completados={completed}/{total}", file=sys.stderr)
    sys.exit(2)

print("Evaluación completada exitosamente.")
sys.exit(0)
EOF

# Guardar reporte en el destino especificado si es distinto
REAL_OUTPUT_REPORT_DIR="$(cd "$(dirname "$OUTPUT_REPORT")" 2>/dev/null && pwd || echo "")"
if [ -z "$REAL_OUTPUT_REPORT_DIR" ]; then
    mkdir -p "$(dirname "$OUTPUT_REPORT")"
fi

if [ "$OUTPUT_REPORT" != "evals/report.json" ] && [ "$OUTPUT_REPORT" != "$DEFAULT_REPORT" ]; then
    cp "$DEFAULT_REPORT" "$OUTPUT_REPORT"
    echo "Reporte guardado en: $OUTPUT_REPORT"
fi

if [ $RUNNER_EXIT -ne 0 ] || [ $POST_PROCESS_EXIT -ne 0 ]; then
    echo "ERROR: La ejecución de evaluaciones finalizó con errores." >&2
    exit 1
fi

exit 0
