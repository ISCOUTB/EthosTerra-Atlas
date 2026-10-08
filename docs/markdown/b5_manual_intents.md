# Bloque B5: CRUD Manual de Intenciones Declarativas

## 1. Propósito y Alcance
El **Bloque B5** implementa el subsistema de gestión manual directa (CRUD) de intenciones declarativas para el framework híbrido eBDI, garantizando paridad contractual estricta con el clasificador probabilístico micro-LLM (Gemma 4 E4B) sin sobreingeniería (sin bases de datos relacionales, sin colas, sin planificadores en background).

El sistema permite a operadores humanos crear, consultar, listar, editar, eliminar lógicamente y restaurar intenciones operativas correspondientes a **Caso Puro** (`CasoPuro`) y **Caso Conflictivo** (`CasoConflictivo`).

---

## 2. Decisiones de Diseño y Arquitectura

1. **Paridad de Contratos (Single Source of Truth):**
   - Una intención manual y una intención inferida por el modelo cumplen exactamente el mismo contrato Pydantic V2 (`apps/api/src/domain/schemas.py`).
   - Se diseñaron modelos separados para frontera de entrada y salida (`CreateIntentRequest`, `UpdateIntentRequest`, `IntentResponse`, `TrashIntentResponse`) con `extra="forbid"` y validación estricta de identificadores.

2. **Formato de Almacenamiento y Confinamiento:**
   - Persistencia determinista en archivos `.json` dentro del directorio dedicado `outputs/intents/`.
   - El cliente **nunca** suministra rutas de archivo; únicamente un identificador (`id`) validado contra una lista blanca regex estricta (`^[a-zA-Z0-9_-]{1,64}$`), rechazando secuencias `..`, `/`, `\`, caracteres de control, espacios y puntos.
   - La ruta en el servidor se normaliza con `resolve()` y se comprueba mediante `is_relative_to()` contra el directorio raíz autorizado. Se rechazan categóricamente enlaces simbólicos.

3. **Invariante Crítica de Cero Mutación al Núcleo:**
   - Prohibición absoluta de escrituras hacia la instancia original del simulador (`EthosTerra_original/`). Cualquier intento dispara `IntentSecurityError` (HTTP 403).
   - Comprobación criptográfica automatizada: el árbol de `EthosTerra_original/` mantiene su hash invariante al 100%.

4. **Escrituras Atómicas y Robustez:**
   - Toda mutación escribe primero a un archivo temporal `.tmp_{id}_{uuid}.json` en el mismo directorio.
   - Ejecución de `flush()` y `os.fsync()` sobre el descriptor de archivo antes del reemplazo atómico con `os.replace()`.
   - Si ocurre cualquier error, el temporal se purga y el archivo previo permanece inalterado.
   - No-sobreescritura en creación: si el ID ya existe, se emite HTTP 409 Conflict.
   - En actualización: se valida el payload con el esquema antes de escribir; si es inválido (HTTP 422), el archivo activo no se toca.

5. **Borrado Lógico y Ventana de Retención (30 Días):**
   - La operación de eliminación traslada el archivo activo a la subcarpeta `.trash/` adjuntando metadatos de auditoría (`deleted_at`, `deleted_by`, `retention_days`, `expires_at`).
   - Ventana de retención por defecto: **30 días**, configurable mediante la variable de entorno `INTENT_RETENTION_DAYS`.
   - Restauración: Permitida únicamente dentro de la ventana de retención. Si expiró, responde HTTP 410 Gone. Si el ID ya fue reutilizado por una intención activa, responde HTTP 409 Conflict.
   - Purga definitiva: Operación sin demonios ni cron jobs. Se ejecuta (a) automáticamente al iniciar la API (`lifespan` de FastAPI) y (b) bajo demanda vía `POST /v2/intents/trash/purge`.

6. **Auditoría Append-Only:**
   - Registro de toda operación (`CREATE`, `UPDATE`, `DELETE_SOFT`, `RESTORE`, `PURGE_EXPIRED`) en `outputs/intents/audit.log` con timestamp UTC, usuario, hash canónico determinista SHA-256 e ID del caso.

---

## 3. Endpoints REST (API v2)

| Método | Endpoint | Código Éxito | Códigos Error | Descripción |
|---|---|---|---|---|
| `POST` | `/v2/intents` | 201 Created | 409, 422, 403 | Crea una intención manual (Puro o Conflicto) |
| `GET` | `/v2/intents` | 200 OK | - | Lista todas las intenciones activas |
| `GET` | `/v2/intents/{id}` | 200 OK | 404, 422, 403 | Consulta una intención activa por ID |
| `PUT` | `/v2/intents/{id}` | 200 OK | 404, 422, 403 | Actualiza una intención existente (validación previa) |
| `DELETE` | `/v2/intents/{id}` | 200 OK | 404, 422, 403 | Borrado lógico: mueve a `.trash/` con 30 días de retención |
| `GET` | `/v2/intents/trash` | 200 OK | - | Lista intenciones en papelera y estado de expiración |
| `POST` | `/v2/intents/{id}/restore` | 200 OK | 404, 409, 410, 403 | Restaura una intención si está en ventana |
| `POST` | `/v2/intents/trash/purge` | 200 OK | 403 | Purga irrecuperable de intenciones vencidas |

*Nota:* Los endpoints están montados simultáneamente en `/v2/intents` y `/intents`.

---

## 4. Ejecución y Pruebas

### Pruebas Automatizadas
Ejecutar la suite completa de pruebas unitarias y de integración:
```bash
PYTHONPATH=apps/api uv run --project apps/api --with pytest --with pydantic --with jsonschema --with pyyaml --with fastapi --with httpx pytest tests/unit/test_manual_intents.py -v
```

Ejecución de la suite total del repositorio (79 pruebas):
```bash
PYTHONPATH=apps/api uv run --project apps/api --with pytest --with pydantic --with jsonschema --with pyyaml --with fastapi --with httpx pytest tests/unit
```

### Configuración del Entorno
- `INTENT_RETENTION_DAYS`: Días de retención en papelera antes de purga (por defecto: `30`).
- `INTENTS_DIR`: Ruta alternativa al directorio raíz de intenciones (por defecto: `<project_root>/outputs/intents`).
- `ORIGINAL_ETHOS_ROOT`: Ruta a la instancia original protegida de solo lectura de EthosTerra.

### Interfaz Web (React)
La UI React en `apps/ui/` dispone de la pestaña interactiva **"Intenciones Manuales (B5)"** con formulario tipado para Caso Puro y Conflictivo, tabla de intenciones activas con edición y borrado lógico, y panel de papelera con conteo regresivo de retención, restauración y purga.
