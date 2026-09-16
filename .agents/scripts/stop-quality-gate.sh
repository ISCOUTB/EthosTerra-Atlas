#!/usr/bin/env bash
set -u

# Determinar la ruta raíz del proyecto de forma robusta
if [ -f "$PWD/docker-compose.yml" ] || [ -f "$PWD/compose.yaml" ]; then
    PROJECT_ROOT="$PWD"
elif [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/docker-compose.yml" ] || [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/compose.yaml" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
elif [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docker-compose.yml" ] || [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/compose.yaml" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

cd "$PROJECT_ROOT"

# El bypass (permitir cierre sin verificación) solo aplica hasta completar la Fase 6 del PLAN.md.
# A partir de la Fase 7 (Dockerización Final) o habiendo un Dockerfile en la raíz, docker-compose.yml o compose.yaml es OBLIGATORIO.
IS_PHASE_7_OR_LATER=0
if [ -f "$PROJECT_ROOT/Dockerfile" ]; then
    IS_PHASE_7_OR_LATER=1
elif [ -f "$PROJECT_ROOT/PLAN.md" ] && grep -E '### \[✅\] Fase 6' "$PROJECT_ROOT/PLAN.md" >/dev/null 2>&1; then
    IS_PHASE_7_OR_LATER=1
elif [ -f "$PROJECT_ROOT/PLAN.md" ] && grep -E '### \[✅🔄\] Fase 7' "$PROJECT_ROOT/PLAN.md" >/dev/null 2>&1; then
    IS_PHASE_7_OR_LATER=1
fi

COMPOSE_FILE=""
if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
elif [ -f "$PROJECT_ROOT/compose.yaml" ]; then
    COMPOSE_FILE="$PROJECT_ROOT/compose.yaml"
fi

if [ -z "$COMPOSE_FILE" ]; then
    if [ $IS_PHASE_7_OR_LATER -eq 1 ]; then
        BLOCK_MSG="GARANTÍA DETERMINISTA DE CALIDAD BLOQUEADA: A partir de la Fase 7 (Dockerización Final) o habiendo un Dockerfile en la raíz, se requiere obligatoriamente 'docker-compose.yml' o 'compose.yaml' para ejecutar 'make test', 'make lint' y 'make security'. Debes crear y configurar docker-compose.yml antes de dar por finalizada la tarea."
        if command -v jq >/dev/null 2>&1; then
            jq -n --arg reason "$BLOCK_MSG" '{"decision": "continue", "reason": $reason}'
        elif command -v python3 >/dev/null 2>&1; then
            python3 -c 'import sys, json; print(json.dumps({"decision": "continue", "reason": sys.argv[1]}))' "$BLOCK_MSG"
        else
            printf '{"decision": "continue", "reason": "%s"}\n' "$BLOCK_MSG"
        fi
        exit 0
    else
        echo "Aviso: docker-compose.yml no existe aún en la raíz (Fase 0-6 previa a Dockerización). Omitiendo verificación de calidad (bypass temporal)." >&2
        if command -v jq >/dev/null 2>&1; then
            jq -n '{"decision": "allow"}'
        else
            echo '{"decision": "allow"}'
        fi
        exit 0
    fi
fi

FAILED=0
ERROR_LOG=""

# 1. Ejecutar la suite de pruebas unitarias dentro del contenedor
TEST_OUTPUT=$(docker compose run --rm test 2>&1)
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    FAILED=1
    ERROR_LOG="${ERROR_LOG}=== FALLÓ: docker compose run --rm test (exit code: ${TEST_EXIT_CODE}) ===\n${TEST_OUTPUT}\n\n"
fi

# 2. Ejecutar el análisis estático / linter dentro del contenedor
LINT_OUTPUT=$(docker compose run --rm lint 2>&1)
LINT_EXIT_CODE=$?

if [ $LINT_EXIT_CODE -ne 0 ]; then
    FAILED=1
    ERROR_LOG="${ERROR_LOG}=== FALLÓ: docker compose run --rm lint (exit code: ${LINT_EXIT_CODE}) ===\n${LINT_OUTPUT}\n\n"
fi

# 3. Ejecutar el escaneo de seguridad y análisis estático completo (ruff, bandit, semgrep, trivy)
SEC_OUTPUT=""
SEC_EXIT_CODE=0

if [ -f "$PROJECT_ROOT/.agents/skills/static-analyzer-fixer/scripts/run_security_scan.sh" ]; then
    SEC_OUTPUT=$(bash "$PROJECT_ROOT/.agents/skills/static-analyzer-fixer/scripts/run_security_scan.sh" 2>&1)
    SEC_EXIT_CODE=$?
elif [ -f "$PROJECT_ROOT/scripts/run_security_scan.sh" ]; then
    SEC_OUTPUT=$(bash "$PROJECT_ROOT/scripts/run_security_scan.sh" 2>&1)
    SEC_EXIT_CODE=$?
fi

if [ $SEC_EXIT_CODE -ne 0 ]; then
    # El hook bloquea si hay hallazgos CRITICAL, HIGH o detección de secretos en Trivy
    if echo "$SEC_OUTPUT" | grep -Ei "(CRITICAL|HIGH|secret|secreto|password|token|api[_-]?key)" >/dev/null; then
        FAILED=1
        ERROR_LOG="${ERROR_LOG}=== FALLÓ: security scan (Hallazgos CRITICAL / HIGH o Secretos expuestos) ===\n${SEC_OUTPUT}\n\n"
    else
        # Permitir el cierre si solo son hallazgos MEDIUM o LOW documentados en el reporte final
        echo "Aviso: Se detectaron hallazgos de severidad MEDIUM o LOW en security scan; se permite el cierre condicionado a su documentación." >&2
    fi
fi

# 4. Evaluar resultados y emitir payload JSON de decisión
if [ $FAILED -ne 0 ]; then
    MESSAGE=$(printf "GARANTÍA DETERMINISTA DE CALIDAD BLOQUEADA:\nSe detectaron fallos en las pruebas unitarias, en el linter, o hallazgos de seguridad CRITICAL/HIGH / secretos expuestos.\nDebes corregir estos errores antes de dar por finalizada la tarea:\n\n%b" "$ERROR_LOG")
    
    if command -v jq >/dev/null 2>&1; then
        jq -n --arg reason "$MESSAGE" '{"decision": "continue", "reason": $reason}'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c 'import sys, json; print(json.dumps({"decision": "continue", "reason": sys.argv[1]}))' "$MESSAGE"
    else
        # Escape básico para comillas y saltos de línea
        ESCAPED_MSG=$(echo "$MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')
        printf '{"decision": "continue", "reason": "%s"}\n' "$ESCAPED_MSG"
    fi
else
    # Todo en orden (o únicamente hallazgos MEDIUM/LOW documentados): permitir cierre
    if command -v jq >/dev/null 2>&1; then
        jq -n '{"decision": "allow"}'
    else
        echo '{"decision": "allow"}'
    fi
fi
