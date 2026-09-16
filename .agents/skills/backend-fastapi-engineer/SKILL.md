---
name: backend-fastapi-engineer
description: Guía profesional y agnóstica para desarrollo, arquitectura limpia, contratos Pydantic V2, asincronía segura, observabilidad y pruebas en aplicaciones FastAPI.
---

# backend-fastapi-engineer

## Propósito
Establecer un estándar técnico profesional y agnóstico para diseñar, implementar, auditar y mantener servicios backend de alto rendimiento construidos con Python y FastAPI, asegurando tipado estático riguroso con Pydantic V2, arquitectura limpia hexagonal, asincronía sin bloqueos, observabilidad estructurada y resiliencia en dependencias externas.

## Cuándo usar este skill
Activa este skill cuando el sistema deba:
- Diseñar o estructurar una API REST o servicios asíncronos con FastAPI.
- Definir esquemas de datos de entrada/salida (DTOs) y validaciones complejas con Pydantic V2.
- Implementar la separación hexagonal: routers delgados, casos de uso/servicios, dominio, puertos y adaptadores.
- Configurar clientes HTTP asíncronos (`httpx.AsyncClient`) con pools de conexiones, timeouts y reintentos defensivos.
- Diseñar endpoints de diagnóstico, health y readiness diferenciados.
- Gestionar middlewares de observabilidad, inyección de dependencias (`Depends`), correlación de trazas (`request_id`/`trace_id`) y logging estructurado.
- Definir esquemas consistentes de manejo global de excepciones y respuestas de error HTTP.

## Arquitectura de backend
FastAPI debe organizarse siguiendo una arquitectura limpia y modular que evite el acoplamiento entre el protocolo de transporte (HTTP) y la lógica de negocio:

```text
[API Layer / Routers]
       │ (DTOs / Request Models)
       ▼
[Application Services / Use Cases]
       │ (Domain Entities & Value Objects)
       ▼
[Domain Core] ◄──────────────┐ (Interfaces / Ports)
       ▲                     │
       │                     ▼
[Infrastructure Adapters] (HTTP Clients, Repositories, Caches, Event Brokers)
```

1. **Routers Delgados (Thin Controllers)**:
   - Su única responsabilidad es deserializar la petición, invocar la inyección de dependencias, delegar al caso de uso correspondiente y mapear el resultado al DTO de respuesta con el código HTTP apropiado.
   - **Prohibido**: Escribir lógica de negocio, consultas directas a bases de datos o llamadas directas a APIs externas dentro de las funciones de ruta.
2. **DTOs (Data Transfer Objects)**:
   - Modelos Pydantic dedicados exclusivamente a la frontera de entrada (`RequestDTO`) y de salida (`ResponseDTO`). No exponer entidades de dominio crudas.
3. **Casos de Uso / Servicios de Aplicación**:
   - Orquestan el flujo de negocio, coordinan llamadas a puertos y aplican reglas invariantes. Son independientes de FastAPI (`Request`, `Response`, `Depends` no deben invadir esta capa).
4. **Puertos y Adaptadores**:
   - Definir interfaces abstractas (`Protocol` o `ABC`) para interactuar con sistemas externos (modelos, pasarelas, almacenamiento). Las implementaciones concretas residen en adaptadores reemplazables.

## Contratos y Pydantic V2
Pydantic V2 ofrece validaciones de alto rendimiento basadas en Rust. Debe configurarse con máxima rigurosidad:

- **Configuración Estricta**:
  - Usar `ConfigDict(extra="forbid", str_strip_whitespace=True)` por defecto en esquemas de entrada para rechazar campos no reconocidos y evitar inyecciones inesperadas.
  - Usar `frozen=True` en Value Objects inmutables para garantizar consistencia.
- **Validadores Explícitos**:
  - Emplear `@field_validator` con `mode="before"` o `mode="after"` para validaciones de formato o normalizaciones.
  - Emplear `@model_validator(mode="after")` para validaciones cruzadas entre múltiples campos.
- **Tipado Explícito**:
  - No usar tipos genéricos `Any` o `dict` no tipado.
  - Usar `Annotated` con restricciones de `Field` (`ge`, `le`, `min_length`, `max_length`, `pattern`).

### Checklist de Pydantic V2
- [ ] ¿Se definió `extra="forbid"` en los modelos de entrada donde se exige contrato estricto?
- [ ] ¿Los campos de texto tienen `str_strip_whitespace=True` o validaciones de longitud mínima/máxima?
- [ ] ¿Se utilizan `Enum` para categorías restringidas y tipos primitivos precisos (`UUID`, `HttpUrl`, `EmailStr`)?
- [ ] ¿Los campos opcionales tienen valor por defecto explícito (`Field(default=None)`) y tipo unión (`T | None`)?
- [ ] ¿Las validaciones cruzadas entre campos utilizan `@model_validator(mode="after")`?

## Endpoints y errores
Los endpoints deben ser predecibles, descriptivos y consistentes en su respuesta ante fallas:

- **Estructura Estándar de Respuesta de Error**:
  Toda respuesta de error HTTP (4xx y 5xx) debe responder contractualmente con una estructura unificada que incluya correlación forense:

```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND | VALIDATION_ERROR | DEPENDENCY_TIMEOUT | INTERNAL_ERROR",
    "message": "Descripción clara y segura para el cliente (sin filtrar stack traces)",
    "details": [],
    "correlation_id": "req-0191e4c2-7a2c-7b23-8bc1-123456789abc",
    "timestamp": "2026-09-15T16:42:00Z"
  }
}
```

- **Manejadores Globales de Excepciones**:
  - Registrar handlers específicos para `RequestValidationError` (422 estructurado), excepciones de dominio tipadas (400/404/409) y una captura final de excepciones genéricas no controladas (500 con log forense).

### Plantilla de Endpoint Seguro
```python
from typing import Annotated
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/items", tags=["Items"])

class ItemCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nombre: Annotated[str, Field(min_length=3, max_length=50)]
    cantidad: Annotated[int, Field(ge=1, le=1000)]

class ItemResponse(BaseModel):
    id: str
    nombre: str
    cantidad: int
    estado: str

@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo ítem validado",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Violación de regla de negocio"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Error de validación de contrato"},
        status.HTTP_504_GATEWAY_TIMEOUT: {"description": "Timeout en dependencia remota"}
    }
)
async def create_item(
    payload: ItemCreateRequest,
    use_case: Annotated[CreateItemUseCase, Depends(get_create_item_use_case)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> ItemResponse:
    result = await use_case.execute(payload, correlation_id=correlation_id)
    return ItemResponse.model_validate(result)
```

---

### Taxonomía de Errores de API

| Código HTTP | Categoría de Error | Origen Típico | Comportamiento del Sistema |
| :--- | :--- | :--- | :--- |
| **400 Bad Request** | Regla de negocio inválida | Dominio / Caso de uso | Retornar código de error específico sin reintentar |
| **401 / 403** | Autenticación / Permiso | Seguridad / Tokens | Denegar acceso y loguear evento de seguridad |
| **404 Not Found** | Recurso no existente | Repositorio / Datos | Retornar identificador no localizado |
| **422 Unprocessable** | Violación sintáctica | Pydantic / Schema | Detallar campos faltantes o tipos incorrectos |
| **429 Too Many Req** | Límite de tasa superado | Rate Limiter | Informar `Retry-After` en cabeceras HTTP |
| **502 Bad Gateway** | Error en dependencia remota | Adaptador de cliente HTTP | Aislar fallo y activar fallback si existe |
| **504 Gateway Timeout** | Timeout en dependencia remota | Adaptador de cliente HTTP | Abortar llamada y preservar recursos locales |
| **500 Internal Error** | Excepción no controlada | Bug de código / Fallo crítico | Loguear stack trace con `trace_id` y emitir mensaje genérico |

---

## Async, timeouts y concurrencia
FastAPI está construido sobre Starlette y `asyncio`. El mal uso de la asincronía degrada gravemente el rendimiento del sistema:

1. **Prohibición de Bloqueo del Event Loop**:
   - Jamás utilizar bibliotecas de I/O síncronas bloqueantes (`requests`, `time.sleep()`, drivers de DB síncronos) dentro de funciones `async def`.
   - Si una operación intensiva en CPU o una biblioteca síncrona heredada es inevitable, delegarla al threadpool usando `asyncio.to_thread()` o `starlette.concurrency.run_in_threadpool()`.
2. **Timeouts Defensivos en Dependencias**:
   - Toda llamada externa (HTTP, base de datos, caché) debe contar con un timeout explícito y acotado (`connect_timeout`, `read_timeout`, `write_timeout`).
3. **Control de Concurrencia**:
   - Usar semáforos (`asyncio.Semaphore`) para limitar el número de llamadas concurrentes hacia servicios descendentes que tengan límites de capacidad de cómputo o memoria.

### Checklist de Cliente HTTP Asíncrono
- [ ] ¿Se utiliza una única instancia compartida de `httpx.AsyncClient` mediante ciclo de vida (`lifespan`) en lugar de crear un cliente por petición?
- [ ] ¿Se configuraron límites de pool de conexiones (`limits=httpx.Limits(max_keepalive_connections=..., max_connections=...)`)?
- [ ] ¿Se definieron timeouts explícitos (`timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0)`)?
- [ ] ¿El cliente captura excepciones específicas de transporte (`httpx.TimeoutException`, `httpx.NetworkError`) y las traduce a excepciones de dominio tipadas?
- [ ] ¿Se inyecta el `correlation_id` / `trace_id` en las cabeceras HTTP hacia servicios externos?

## Dependencias y configuración
- **Inyección de Dependencias Idiomática (`Depends`)**:
  - Emplear `Depends()` para resolver dependencias de base de datos, clientes HTTP, casos de uso y autenticación.
  - Facilita la sustitución por implementaciones simuladas (*fakes/mocks*) durante pruebas unitarias e integración sin parchear módulos con `unittest.mock`.
- **Configuración Tipada con `pydantic-settings`**:
  - Centralizar las variables de configuración en una clase derivada de `BaseSettings`.
  - Inyectar variables de entorno con prefijos claros y valores por defecto seguros para desarrollo local.
  - Tratar datos sensibles con tipos `SecretStr` para prevenir su impresión accidental en logs o mensajes de consola.

## Salud y observabilidad
El servicio debe exponer endpoints de ciclo de vida claramente diferenciados:

1. **Liveness Probe (`/health/live`)**:
   - Verifica únicamente que el proceso del servidor está vivo y el event loop responde. Retorna `200 OK` inmediato sin verificar dependencias.
2. **Readiness Probe (`/health/ready`)**:
   - Verifica que el servicio está listo para recibir tráfico, comprobando la conectividad de dependencias críticas (base de datos, modelo cargado en memoria, colas).
   - Debe diferenciar explícitamente: `app_ready: true` vs. `dependencies_ready: true/false`.
3. **Observabilidad y Trazabilidad**:
   - Middleware de correlación que asigne o propague una cabecera `X-Correlation-ID` / `X-Trace-ID` en cada solicitud y respuesta.
   - Logs en formato estructurado (JSON) que incluyan timestamp ISO, nivel, logger, correlation_id, endpoint, código HTTP y latencia en milisegundos.
   - **Regla Estricta**: Jamás registrar tokens de autorización, contraseñas ni datos sensibles en logs.

## Seguridad de API
1. **Validación de Entradas en Frontera**: Todo parámetro de URL, query string, cabecera y cuerpo debe validarse estrictamente mediante tipos Pydantic.
2. **Límites de Tamaño de Payload**: Configurar middlewares o límites en el servidor web (Uvicorn / Nginx) para rechazar cuerpos de petición que excedan el tamaño esperado (prevención de DoS).
3. **CORS Explícito**:
   - Prohibir el uso de comodines permisivos (`allow_origins=["*"]`) en entornos productivos. Declarar orígenes explícitos permitidos.
4. **Protección de Cabeceras de Seguridad**:
   - Incluir cabeceras defensivas estándar (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`).

## Pruebas de backend
La suite de pruebas debe asegurar calidad sin requerir servicios externos en vivo:

1. **Pruebas Unitarias de Casos de Uso**:
   - Prueban la lógica pura de negocio inyectando adaptadores falsos (*Fake Adapters*) en memoria. Rápidas e independientes de red.
2. **Pruebas de Contrato de API**:
   - Usan `TestClient` (Starlette) o `httpx.AsyncClient` sobre la app de FastAPI.
   - Validan códigos de estado HTTP, esquemas de serialización JSON y manejo de errores 422 ante payloads malformados.
3. **Pruebas de Integración de Adaptadores**:
   - Validan la comunicación real de adaptadores contra contenedores efímeros o servicios locales de prueba.

## Matriz de confirmaciones
Antes de realizar cambios en componentes de backend, consulta esta matriz:

| Tipo de cambio | Acción requerida | ¿Pedir confirmación? |
| :--- | :--- | :--- |
| **Corrección interna en caso de uso** | Arreglo de bug sin modificar DTOs ni firmas | **No** (si las pruebas existentes pasan) |
| **Cambio en schema de entrada/salida** | Modificación de campos, tipos o nombres en DTOs | **Sí** (obligatorio antes de alterar contratos públicos) |
| **Nuevo endpoint o cambio de ruta** | Modificación en URIs, métodos HTTP o tags | **Sí** (requiere validación de diseño de API) |
| **Cambio de cliente/dependencia externa** | Adición o cambio de librerías de infraestructura | **Sí** (requiere justificación de dependencias) |
| **Cambio en autenticación o CORS** | Modificación de políticas de seguridad o acceso | **Sí** (crítico para la seguridad del sistema) |
| **Refactorización de inyección de deps** | Reestructuración de proveedores o lifespans | **No** (si se preservan contratos y pruebas) |

## Antipatrones prohibidos
- **Bloating Routers**: Escribir lógica de orquestación, transformaciones masivas o llamadas I/O directamente dentro de los métodos del router.
- **Sync Blocking in Async Handlers**: Usar funciones síncronas de red o `time.sleep()` dentro de un endpoint `async def`, congelando el event loop de todos los usuarios.
- **Global Client Instantiation**: Crear clientes HTTP (`httpx.Client()`) dentro de cada función de endpoint en lugar de reutilizar un pool gestionado por el ciclo de vida.
- **Generic Catch-All 500 Silence**: Atrapar `except Exception:` y devolver un mensaje genérico vacío sin registrar la traza y el correlation_id en el logger.
- **Exposing Internal Domain Models**: Devolver directamente entidades de base de datos o de dominio interno como respuesta HTTP en lugar de mapear a un `ResponseDTO`.
- **Wildcard CORS in Production**: Configurar orígenes permitidos `*` con credenciales habilitadas.

## Validaciones antes de cerrar
Antes de declarar una tarea de backend como completada, verifica:
1. ¿Las rutas son delgadas y delegan exclusivamente a casos de uso o servicios?
2. ¿Los esquemas Pydantic V2 tienen validación estricta y control de campos desconocidos?
3. ¿Las llamadas asíncronas no bloquean el event loop y cuentan con timeouts explícitos?
4. ¿Los endpoints de `/health` diferencian el estado del proceso de sus dependencias?
5. ¿Las respuestas de error incluyen identificadores de correlación y no filtran secretos?
6. ¿Se ejecutaron las pruebas automatizadas y pasaron limpiamente?
7. ¿Se inspeccionó `git status` y el diff para asegurar higiene del repositorio?

## Formato de salida esperado
Toda propuesta, refactorización o desarrollo de backend debe presentarse con la siguiente estructura:

```markdown
### 1. Resumen de Diseño de API / Backend
- Endpoints o casos de uso intervenidos:
- Contratos de entrada y salida (DTOs Pydantic V2):
- Justificación técnica y desacoplamiento:

### 2. Manejo de Concurrencia y Resiliencia
- Estrategia asíncrona y timeouts definidos:
- Control de fallos en dependencias externas:

### 3. Observabilidad y Seguridad
- Identificadores de correlación y logs estructurados:
- Validaciones en frontera y políticas de seguridad:

### 4. Pruebas y Verificación
- Pruebas unitarias y de contrato ejecutadas:
- Códigos HTTP y respuestas de error verificadas:

### 5. Próximos Pasos y Compatibilidad
- Impacto en consumidores de la API: [Compatible / Requiere migración]
- Tareas pendientes recomendadas:
```
