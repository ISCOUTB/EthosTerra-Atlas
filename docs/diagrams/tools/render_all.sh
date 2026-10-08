#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "=== Compilando diagramas Mermaid en docs/diagrams/ ==="
python3 "${SCRIPT_DIR}/render_all.py"
