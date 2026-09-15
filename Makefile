.PHONY: help doctor pull-model build start stop restart logs health model-check canary test test-verbose clean

help:
	@echo "Opciones disponibles:"
	@echo "  help           - Muestra este mensaje"
	@echo "  doctor         - Revisa dependencias (Docker, Compose, Python, DMR)"
	@echo "  pull-model     - Descarga ai/gemma4:E4B"
	@echo "  build          - Construye los contenedores sin caché"
	@echo "  start          - Levanta los servicios y espera healthcheck"
	@echo "  stop           - Detiene los servicios"
	@echo "  restart        - Reinicia los servicios"
	@echo "  logs           - Muestra los logs de api y ui"
	@echo "  health         - Verifica estado de /health y /diagnostics/model"
	@echo "  model-check    - Valida que DMR funciona"
	@echo "  canary         - Ejecuta test de integración canario"
	@echo "  test           - Ejecuta evaluación completa (requiere canary previo)"
	@echo "  test-verbose   - Evaluación completa con salida detallada"
	@echo "  clean          - Limpia caché y reportes (no borra imágenes/volúmenes)"

PYTHON_CMD := $(shell command -v uv >/dev/null && echo "uv run python" || echo "python3")

doctor:
	@echo "=== Revisando Dependencias ==="
	@docker --version || (echo "Docker faltante" && exit 1)
	@docker compose version || (echo "Docker Compose faltante" && exit 1)
	@docker desktop status model-runner || echo "Verifique DMR manualmente"
	@$(PYTHON_CMD) --version || (echo "Python3/uv faltante" && exit 1)
	@echo "Dependencias OK."

pull-model:
	docker model pull ai/gemma4:E4B || docker model pull ai/gemma4:4b

build:
	docker compose build --no-cache

start:
	docker compose up -d
	@echo "Esperando API healthy..."
	@for i in $$(seq 1 18); do \
		if curl -s -f http://localhost:8000/health > /dev/null; then \
			echo "API está HEALTHY"; \
			exit 0; \
		fi; \
		echo "Esperando 5s..."; sleep 5; \
	done; \
	echo "Timeout esperando API"; exit 1

stop:
	docker compose down

restart: stop start

logs:
	docker compose logs -f api ui

health:
	curl -s http://localhost:8000/health
	@echo ""
	curl -s http://localhost:8000/diagnostics/model
	@echo ""

model-check:
	docker model ls | grep gemma4

canary:
	$(PYTHON_CMD) tests/integration/test_dmr_canary.py

test: canary
	$(PYTHON_CMD) evals/runner.py

test-verbose: canary
	$(PYTHON_CMD) evals/runner.py --verbose

clean:
	rm -rf .pytest_cache evals/report.json
	find . -type d -name __pycache__ -exec rm -rf {} +
