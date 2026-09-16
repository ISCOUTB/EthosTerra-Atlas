#!/usr/bin/env bash
set -u

# Detección robusta de la raíz del proyecto
if [ -f "$PWD/compose.yaml" ] || [ -f "$PWD/docker-compose.yml" ] || [ -f "$PWD/Makefile" ]; then
    PROJECT_ROOT="$PWD"
elif [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/Makefile" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
elif [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/Makefile" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

cd "$PROJECT_ROOT"

FAILED=0

echo "=== Verificación Pre-Commit Local ==="

# 1. Ejecución de linter rápido (make lint) si está disponible
if command -v make >/dev/null 2>&1 && make -n lint >/dev/null 2>&1; then
    echo "Ejecutando linter (make lint)..."
    if make lint; then
        echo "[OK] Linter (make lint)"
    else
        echo "[FAIL] Linter (make lint)"
        FAILED=1
    fi
else
    echo "[SKIP] Linter (make lint no disponible en Makefile)"
fi

# 2. Ejecución de chequeo de secretos con Trivy si está disponible
if command -v trivy >/dev/null 2>&1; then
    echo "Ejecutando chequeo de secretos con Trivy..."
    TRIVY_CONFIG=""
    if [ -f "$PROJECT_ROOT/trivy-secret.yaml" ]; then
        TRIVY_CONFIG="$PROJECT_ROOT/trivy-secret.yaml"
    elif [ -f "$PROJECT_ROOT/.trivy-secret.yaml" ]; then
        TRIVY_CONFIG="$PROJECT_ROOT/.trivy-secret.yaml"
    elif [ -f "$PROJECT_ROOT/trivy.yaml" ]; then
        TRIVY_CONFIG="$PROJECT_ROOT/trivy.yaml"
    fi

    if [ -n "$TRIVY_CONFIG" ]; then
        if trivy fs --secret-config "$TRIVY_CONFIG" "$PROJECT_ROOT"; then
            echo "[OK] Secret check (trivy fs --secret-config)"
        else
            echo "[FAIL] Secret check (trivy fs --secret-config)"
            FAILED=1
        fi
    else
        if trivy fs --scanners secret "$PROJECT_ROOT" 2>/dev/null || trivy fs --security-checks secret "$PROJECT_ROOT"; then
            echo "[OK] Secret check (trivy fs)"
        else
            echo "[FAIL] Secret check (trivy fs)"
            FAILED=1
        fi
    fi
else
    echo "[SKIP] Secret check (trivy no está instalado)"
fi

# 3. Resumen y código de salida
echo "====================================="
if [ $FAILED -ne 0 ]; then
    echo "[FAIL] Se encontraron fallos en las verificaciones pre-commit."
    exit 1
else
    echo "[OK] Todas las verificaciones completadas sin errores."
    exit 0
fi
