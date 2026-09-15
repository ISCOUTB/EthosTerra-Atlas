# Framework Híbrido de Agentes Emocionales eBDI con Micro-LLM

Este repositorio contiene la integración entre el simulador WellProdSim/EthosTerra (basado en Python BESA) y un Micro-LLM (Gemma 4 E4B) operando de manera estricta bajo una arquitectura hexagonal y determinista.

## Principios de Diseño
- **Privilegio Mínimo**: El agente propone, no ejecuta. El simulador BESA o el humano deciden.
- **Soberanía de Datos**: Todo se ejecuta offline-first vía Docker Model Runner y Ollama.
- **Validación Determinista**: Las respuestas del modelo se mapean rígidamente mediante esquemas `Pydantic` (`CasoPuro` vs `CasoConflictivo`).
- **Trazabilidad**: Toda inferencia guarda latencia, hash del prompt, modelo usado y un `trace_id` único para investigación.

## Instalación Offline-First

Para ejecutar este proyecto en tu MacBook Air M4 (16GB), sigue estos pasos:

1. **Pre-requisitos**:
   - macOS (Sequoia o reciente).
   - [uv](https://github.com/astral-sh/uv) (Gestor de proyectos Python ultrarrápido).
   - Docker Desktop.

2. **Descarga del Modelo (Único paso que requiere internet)**
   Ejecuta el entorno Docker:
   ```bash
   docker compose up -d
   ```
   Luego, ingresa al contenedor (o hazlo vía CLI nativa) para descargar la versión cuantizada de Gemma:
   ```bash
   docker exec -it gemma-local-runner ollama run gemma2
   ```
   *Nota: En una MacBook M4 de 16GB de RAM, la versión de 2B-4B tomará entre 2GB y 3.5GB de RAM, dejando suficiente memoria para BESA y Docker.*

3. **Instalación de Dependencias**:
   Sin necesidad de descargar si ya tienes la caché de `uv`, usa:
   ```bash
   uv sync
   ```
   O para usar los paquetes puros de la raíz:
   ```bash
   source .venv/bin/activate
   ```

## Ejecución de la API Vertical Slice

Levanta el monolito modular:
```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Accede a la documentación OpenAPI autogenerada en: [http://localhost:8000/docs](http://localhost:8000/docs).

## Endpoint POST `/classifications:propose`

**Request:**
```json
{
  "id": "CTX-001",
  "temperatura": 145.2,
  "presion": 2100.5,
  "alarmas": []
}
```

**Response (Caso Puro):**
```json
{
  "contexto_id": "CTX-001",
  "resultado": {
    "tipo": "puro",
    "clasificacion": "Operación Normal",
    "confianza": 0.98,
    "razonamiento": "Las variables de presión y temperatura están en los umbrales nominales de EthosTerra."
  },
  "metadatos": {
    "trace_id": "123e4567-e89b-12d3-a456-426614174000",
    "model": "gemma2",
    "latency_ms": 1250.4,
    "prompt_digest": "a2b4...hash...901e"
  }
}
```
