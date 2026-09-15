# Manual de Usuario - Clasificador eBDI

## 1. Propósito
El Clasificador eBDI WellProdSim/EthosTerra es un sistema híbrido que integra un orquestador determinista de agentes eBDI con capacidades de micro-LLM local. Evalúa contextos de telemetría de pozos petroleros para detectar casos puros, conflictivos y ambiguos, respetando soberanía de datos.

## 2. Alcance del LLM
El LLM **SÓLO PROPONE** una clasificación de estado basada en telemetría. **NO** ejecuta acciones físicas, ni modifica el núcleo del orquestador eBDI. La validación final recae sobre las reglas semánticas y el experto humano.

## 3. Requisitos de Sistema
- Mac Apple Silicon (M-series), mínimo 16 GB RAM unificada.
- Docker Desktop >= 4.40 con **Docker Model Runner (DMR) habilitado** (Settings -> AI).
- Al menos 10 GB de RAM asignados en Docker Desktop.
- 15 GB libres de almacenamiento.
- Modelo: `ai/gemma4:E4B`.
- `uv` (recomendado) o `python3` (>=3.11).

## 4. Preparación Rápida
Ejecute en orden:
```bash
make doctor
make pull-model
make build
make start
make health
```

## 5. Prueba Canaria
**Obligatorio antes de cualquier experimento completo:**
```bash
make canary
```
Comprueba que el modelo carga en memoria y responde correctamente a la API.

## 6. Evaluación Completa
```bash
make test
# O para ver salida detallada por caso:
make test-verbose
```

## 7. Interpretación de Métricas
En `evals/report.json`:
- **evaluation_mode**: Debe ser `"real_model"`.
- **evaluation_status**: Muestra si la infraestructura falló o si se completó.
- **inference_availability**: Proporción de solicitudes que no arrojaron error 500/timeout (0.0 a 1.0).
- **accuracy, conflict_recall, etc**: Solo son válidos si *completed_cases* = *attempted_cases*.

## 8. Regla Metodológica
**Las métricas sólo son válidas si `evaluation_mode="real_model"` y `completed_cases` corresponde a los evaluados.** Un fallo de conexión (ej. OOM Timeout) NO se cuenta como accuracy 0% a nivel del algoritmo LLM; es un fallo de infraestructura y se documenta como `null`.

## 9. Tipos de Casos en el Dataset
1. **Puro**: Valores nominales o congruentes, sin contradicciones físicas.
2. **Conflictivo**: Sensores reportan realidades físicas incompatibles (ej. RPM altas, flujo 0).
3. **Ambiguo**: Datos incompletos que impiden deducir el estado real.
4. **Alucinación**: Datos engañosos para tentar al modelo a inventar métricas (ej. fechas, presiones no listadas).
5. **Adversarial**: Inyección de prompts maliciosos (ej. "ignora las reglas de seguridad").

## 10. Solución de Problemas
- ¿Falla el healthcheck? Use `make logs` y revise si falta `curl` o si Uvicorn falló.
- ¿Error 500 / Desconexión? Use `make health` y `docker stats` para ver si hay un error OOM (Out of Memory).
- ¿DMR apagado? Habilítelo en la GUI de Docker y use `make model-check` para validar.

## 11. Reproducibilidad
Siempre registre en su bitácora:
- Fecha exacta de ejecución.
- Versión de Docker Desktop.
- Digest del modelo (`docker model inspect ai/gemma4:E4B`).
- Contenido íntegro de `evals/report.json`.

## 12. Limitaciones Conocidas
- Una UI o API marcadas como "Healthy" no garantizan inferencia; el LLM puede colapsar en RAM al procesar el JSON.
- El modelo solo fue evaluado en un subconjunto canónico.
- El LLM es probabilístico, no sustituye la capa de seguridad crítica de BESA eBDI.

## Nota Técnica Importante
El endpoint verificado y funcional para Docker Model Runner en este entorno es `/v1/chat/completions` (compatible OpenAI), no `/api/chat` (compatible Ollama). Latencia observada por inferencia: ~17-18 segundos con ai/gemma4:E4B en MacBook Air M4 de 16GB.
