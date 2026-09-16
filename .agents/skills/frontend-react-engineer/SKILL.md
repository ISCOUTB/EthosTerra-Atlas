---
name: frontend-react-engineer
description: Guía profesional y agnóstica para diseño e implementación de interfaces React/TypeScript accesibles, tipadas, observables, con manejo integral de estados y UX para sistemas de IA.
---

# frontend-react-engineer

## Propósito
Establecer un estándar técnico riguroso y agnóstico para concebir, diseñar, estructurar, probar y mantener aplicaciones web frontend construidas con React y TypeScript, priorizando flujos de usuario reales, accesibilidad universal (a11y), tipado estricto sincronizado con contratos de backend, robustez ante fallos de red y patrones de experiencia de usuario (UX) específicos para sistemas basados en Inteligencia Artificial.

## Cuándo usar este skill
Activa este skill cuando el sistema deba:
- Diseñar la arquitectura frontend o estructurar módulos y pantallas basados en características (*features*).
- Sincronizar y tipar interfaces TypeScript reflejando contratos y DTOs de API REST.
- Modelar estados exhaustivos de interfaz (carga, error, datos vacíos, datos obsoletos, reintentos).
- Diseñar componentes de interfaz para presentar resultados probabilísticos de IA (confianza, explicabilidad, advertencias y metadatos de trazabilidad).
- Garantizar accesibilidad según las pautas WCAG 2.1 AA (navegación por teclado, foco, roles ARIA, lectores de pantalla).
- Implementar formularios robustos con validación en cliente y mapeo seguro de errores del servidor.
- Gestionar peticiones asíncronas con cancelación (`AbortController`), timeouts y prevención de condiciones de carrera (*race conditions*).
- Establecer suites de pruebas de componentes y flujos de usuario con selectores accesibles.

## Diseño por flujos y features
El diseño de interfaces debe partir del flujo de interacción del usuario y no de componentes visuales aislados:

1. **Estructura Modular Orientada a Features**:
   - Organizar el código por dominio o funcionalidad (`features/<nombre-feature>/`) agrupando componentes, hooks, tipos y pruebas específicas de esa pantalla o caso de uso.
   - Mantener componentes visuales genéricos y agnósticos en una capa compartida (`components/ui/` o primitivas de diseño).
2. **Ubicación del Estado (Colocation)**:
   - Mantener el estado lo más cerca posible de donde se utiliza.
   - Preferir estado local (`useState`, `useReducer`) antes de escalar a gestores de estado global.
   - El estado global debe reservarse estrictamente para datos que trascienden múltiples características independientes (ej. sesión de usuario, preferencias globales de tema).

## Tipado y contratos API
El frontend no debe adivinar la forma de los datos del servidor:

- **TypeScript Estricto**:
  - Habilitar `strict: true` en la configuración de TypeScript. Prohibir el uso de `any`.
  - Definir tipos de entrada (`PayloadDTO`) y salida (`ResponseDTO`) equivalentes a los esquemas del backend (Pydantic / OpenAPI).
- **Validación en Tiempo de Ejecución (Opcional pero Recomendada)**:
  - En interfaces críticas, validar datos externos que ingresan a la aplicación mediante bibliotecas de validación de esquemas (ej. Zod) para asegurar que una respuesta anómala del backend no rompa la interfaz con errores de tipo `TypeError: Cannot read properties of undefined`.

## Estados de interfaz
Todo componente que consuma datos asíncronos debe modelar explícitamente la **Matriz de Estados de UI**, evitando interfaces en blanco o bloqueadas:

---

### Matriz de Estados de UI

| Estado de UI | Condición de Activación | Comportamiento Visual Esperado | Accesibilidad (a11y) |
| :--- | :--- | :--- | :--- |
| **Carga Inicial (Loading)** | Solicitud en curso por primera vez | Skeletons o indicadores de carga no intrusivos; deshabilitar botones de acción | `aria-busy="true"`, `aria-live="polite"` |
| **Éxito (Success)** | Datos válidos recibidos del servidor | Renderizado limpio del contenido principal con jerarquía visual clara | Foco lógico; anuncios breves si hubo mutación |
| **Vacío (Empty State)** | Consulta exitosa pero sin registros | Mensaje explicativo claro y botón o acción sugerida para crear/iniciar datos | Texto legible con rol informativo |
| **Error (Error State)** | Fallo de red (4xx/5xx) o timeout | Mensaje descriptivo comprensible (sin stack traces) y botón de reintento | `role="alert"`, `aria-live="assertive"` |
| **Reintentando (Retrying)** | Solicitud disparada tras fallo previo | Indicador de reintento en curso manteniendo el contexto previo | Notificación discreta de reintento |
| **Datos Obsoletos (Stale)** | Revalidación en segundo plano | Mantener datos anteriores con indicador sutil de actualización en progreso | No interrumpir el foco del lector de pantalla |

---

## UX para sistemas de IA
Presentar inferencias de modelos probabilísticos exige patrones visuales específicos de transparencia y confianza:

1. **Diferenciación de Fuente**:
   - Indicar explícitamente si una decisión fue tomada por una **regla determinista** (certeza absoluta) o sugerida por un **modelo de IA** (predicción probabilística).
2. **Visualización de Incertidumbre**:
   - Mostrar niveles de confianza con códigos de color semánticos accesibles (alto, moderado, bajo) o barras de probabilidad calibradas.
   - Cuando la confianza sea baja o el modelo sugiera ambigüedad/conflicto, resaltar una advertencia visual prominente invitando a la supervisión humana (*Human-in-the-Loop*).
3. **Explicabilidad y Citas**:
   - Presentar el razonamiento del modelo y las fuentes o evidencias específicas que fundamentan la sugerencia.
4. **Metadatos de Trazabilidad**:
   - Disponer de un panel desplegable o tooltip técnico que exponga metadatos forenses: identificador de traza (`trace_id`), modelo y versión utilizados, y latencia de respuesta en milisegundos.

### Checklist de UX para Resultados de IA
- [ ] ¿La interfaz deja claro que el resultado es una sugerencia generada por IA?
- [ ] ¿Se muestra la confianza de la inferencia con soporte para casos de incertidumbre?
- [ ] ¿Los casos conflictivos o ambiguos presentan un llamado claro a revisión humana?
- [ ] ¿Se permite inspeccionar el razonamiento o citas que justifican la decisión?
- [ ] ¿Están accesibles los metadatos técnicos (`trace_id`, modelo, latencia) para soporte y auditoría?
- [ ] ¿El usuario tiene control para aceptar, descartar o corregir la propuesta del modelo?

## Accesibilidad
La accesibilidad web (WCAG 2.1 Nivel AA) no es un añadido estético, sino un requisito técnico estructural:

- **HTML Semántico**:
  - Utilizar elementos nativos (`<button>`, `<main>`, `<nav>`, `<header>`, `<section>`, `<article>`) en lugar de `<div>` con manejadores `onClick`.
  - Los encabezados (`<h1>` a `<h6>`) deben seguir un orden jerárquico estricto sin saltos.
- **Navegación por Teclado y Manejo del Foco**:
  - Todo elemento interactivo debe ser operable mediante `Tab`, `Enter` y `Espacio`.
  - Los estilos de foco (`:focus-visible`) deben ser claramente perceptibles y no eliminarse con `outline: none`.
  - Al abrir un modal o diálogo, atrapar el foco dentro del contenedor y restaurarlo al elemento detonador al cerrar.
- **Formularios Accesibles**:
  - Todo campo de formulario debe estar asociado inequívocamente a un `<label>` mediante el atributo `htmlFor` / `id`.
  - Los mensajes de error de validación deben vincularse con `aria-describedby` y los campos inválidos marcarse con `aria-invalid="true"`.
- **Contraste de Color**:
  - Asegurar un contraste mínimo de 4.5:1 para texto normal y 3:1 para texto grande o controles de interfaz sobre su fondo.
  - La información crítica (ej. errores o estados de éxito) no debe transmitirse exclusivamente mediante el color; acompañar siempre con iconos y texto explicativo.

### Checklist de Accesibilidad (a11y)
- [ ] ¿La página es completamente navegable y funcional usando únicamente el teclado?
- [ ] ¿Todos los botones interactivos son elementos `<button>` nativos o tienen `role="button"` con manejo de eventos de teclado?
- [ ] ¿Las imágenes informativas tienen textos alternativos (`alt`) descriptivos y las decorativas `alt=""`?
- [ ] ¿Los campos con errores están asociados a su mensaje mediante `aria-describedby`?
- [ ] ¿Las alertas dinámicas usan `role="alert"` o `aria-live` para ser anunciadas por lectores de pantalla?
- [ ] ¿El contraste cromático cumple con el estándar WCAG AA?

## Formularios y validación
- **Validación Bidireccional (Defensa en Profundidad)**:
  - Validar en el cliente para dar retroalimentación inmediata (campos obligatorios, formatos de correo, longitudes).
  - Tratar la validación del servidor como la autoridad final; jamás asumir que el cliente filtró todas las anomalías.
- **Mapeo Claro de Errores**:
  - Mapear los errores 422 de backend directamente sobre los campos específicos que fallaron, indicando el motivo exacto al lado del control.
  - Los errores globales no atribuibles a un campo puntual deben mostrarse en un banner de alerta en la parte superior del formulario.
- **Prevención de Doble Envío**:
  - Deshabilitar el botón de envío y mostrar un estado de carga mientras la petición esté en tránsito para evitar mutaciones duplicadas por clics repetidos.

## Datos remotos y errores
- **Gestión del Ciclo de Vida Asíncrono**:
  - Emplear librerías de gestión de datos del servidor (ej. TanStack Query / SWR) o hooks bien controlados con `useEffect`.
- **Cancelación con `AbortController`**:
  - Vincular una señal de cancelación (`AbortSignal`) a cada llamada `fetch` dentro de efectos o componentes que puedan desmontarse, previniendo fugas de memoria y actualizaciones sobre componentes desmontados.
- **Resiliencia ante Timeouts**:
  - Configurar timeouts de red en las peticiones cliente para alertar al usuario si el servidor tarda más de lo esperado en responder, en lugar de dejar la pantalla congelada indefinidamente.

## Seguridad del frontend
1. **Cero Secretos en el Código**: Prohibir terminantemente incrustar claves de API privadas, credenciales de bases de datos o secretos en el código fuente o variables de entorno de cliente (`VITE_*`, `REACT_APP_*`). Todo lo que se empaqueta en el bundle es visible por el usuario en el navegador.
2. **Prevención de XSS**: Evitar el uso de `dangerouslySetInnerHTML`. Si es indispensable renderizar contenido enriquecido generado por LLMs (Markdown), utilizar librerías de saneamiento probadas (ej. DOMPurify) antes de la inyección en el DOM.
3. **Manejo Seguro de Enlaces Externos**: Todo enlace que abra una nueva pestaña (`target="_blank"`) debe incluir `rel="noopener noreferrer"` para evitar accesos indebidos al objeto `window.opener`.

## Pruebas de UI y E2E
Las pruebas de interfaz deben reflejar el comportamiento del usuario y no los detalles de implementación interna:

1. **Filosofía de Selección Accesible (Testing Library)**:
   - Priorizar selectores por rol y nombre accesible (`getByRole('button', { name: /enviar/i })`), por etiqueta de formulario (`getByLabelText`) o por texto visible (`getByText`).
   - Evitar selectores frágiles basados en clases CSS o etiquetas de componentes internos. Usar `data-testid` solo cuando no exista un rol semántico accesible.
2. **Pruebas de Componentes y Flujos**:
   - Probar que cada componente transiciona correctamente por los estados de carga, éxito, vacío y error simulando respuestas de red con herramientas como MSW (Mock Service Worker).
3. **Pruebas de Extremo a Extremo (E2E)**:
   - Probar los flujos críticos de negocio de punta a punta (ej. iniciar análisis, visualizar resultado de IA, confirmar acción o reintentar ante error de red) sobre navegadores reales.

---

### Guía de Pruebas de Componentes y E2E

```typescript
// Ejemplo de prueba de componente con Testing Library (orientado a accesibilidad)
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormularioAnalisis } from './FormularioAnalisis';

test('muestra estado de carga y renderiza resultado con trazabilidad al enviar', async () => {
  const user = userEvent.setup();
  render(<FormularioAnalisis onSubmitMock={vi.fn()} />);

  // Llenar campos mediante etiquetas accesibles
  await user.type(screen.getByLabelText(/identificador de contexto/i), 'CTX-001');
  
  // Enviar formulario mediante rol accesible
  const botonEnviar = screen.getByRole('button', { name: /analizar/i });
  await user.click(botonEnviar);

  // Verificar estado accesible de carga
  expect(botonEnviar).toBeDisabled();
  expect(screen.getByRole('alert', { name: /procesando/i })).toBeInTheDocument();

  // Verificar resultado exitoso y metadatos
  await waitFor(() => {
    expect(screen.getByRole('heading', { level: 2, name: /resultado del análisis/i })).toBeInTheDocument();
    expect(screen.getByText(/trace_id:/i)).toBeInTheDocument();
  });
});
```

---

## Matriz de confirmaciones
Antes de realizar modificaciones en el frontend, consulta esta matriz de gobernanza:

| Tipo de cambio | Acción requerida | ¿Pedir confirmación? |
| :--- | :--- | :--- |
| **Corrección cosmética de estilo** | Ajuste menor de espaciado o tipografía en CSS | **No** (si respeta las reglas de diseño) |
| **Nuevo componente visual interno** | Creación de componente modular dentro de una feature | **No** (si incluye pruebas y tipos estrictos) |
| **Cambio de contrato con API** | Modificación en DTOs o endpoints consumidos | **Sí** (obligatorio antes de alterar sincronización con backend) |
| **Rediseño integral de interfaz** | Modificación sustancial del layout o flujos de usuario | **Sí** (requiere aprobación previa de diseño/producto) |
| **Adición o cambio de dependencias UI** | Instalación de nuevas librerías de componentes o estado | **Sí** (requiere justificación técnica y análisis de peso) |
| **Cambios de alto impacto en a11y** | Reestructuración profunda de foco, formularios o navegación | **Sí** (para asegurar no regresión en conformidad WCAG) |

## Antipatrones prohibidos
- **Div Soups with onClick**: Crear botones falsos usando `<div>` o `<span>` sin soporte de teclado, foco ni roles de accesibilidad.
- **Swallowing Asynchronous Errors**: Capturar errores de peticiones y silenciarlos en la UI, dejando al usuario frente a un spinner de carga infinito.
- **Leaking Secrets to Client**: Exponer tokens de administración o llaves privadas en variables de entorno accesibles por el navegador.
- **Unsanitized Markdown Injection**: Renderizar texto crudo generado por LLMs directamente en el DOM mediante `innerHTML` sin desinfección contra XSS.
- **Premature Micro-optimization**: Envolver cada función o valor trivial en `useCallback` y `useMemo` sin un problema medido de rendimiento, complejizando la lectura del código.
- **Testing Implementation Details**: Probar el estado interno de componentes o nombres de funciones privadas en lugar del comportamiento perceptible por el usuario.

## Validaciones antes de cerrar
Antes de declarar una tarea de frontend como completada, verifica:
1. ¿El código compila limpiamente en TypeScript sin errores de tipos ni uso de `any`?
2. ¿Se modelaron y verificaron visualmente los estados de carga, vacío, error y éxito?
3. ¿La interfaz es completamente operable mediante el teclado y cumple con las directrices de accesibilidad (a11y)?
4. ¿Los componentes que exponen inferencias de IA muestran confianza, origen de decisión y trazabilidad?
5. ¿Se limpiaron los efectos asíncronos para prevenir fugas de memoria y condiciones de carrera?
6. ¿Se ejecutaron las pruebas unitarias y de componentes con selectores accesibles?
7. ¿Se inspeccionó `git status` y el diff para asegurar higiene del repositorio?

## Formato de salida esperado
Toda entrega de desarrollo, refactorización o diseño frontend debe presentarse con la siguiente estructura:

```markdown
### 1. Resumen de la Feature o Componente
- Pantallas o flujos intervenidos:
- Contratos de datos (TypeScript DTOs):
- Justificación de UX y arquitectura de componentes:

### 2. Manejo de Estados y Resiliencia
- Estados de UI cubiertos (Carga, Éxito, Vacío, Error, Reintento):
- Estrategia de cancelación y timeouts de red:

### 3. Accesibilidad y Experiencia de IA (si aplica)
- Navegación por teclado y etiquetas accesibles (a11y):
- Presentación de inferencias de IA (confianza, trazabilidad, escalamiento humano):

### 4. Pruebas y Verificación
- Pruebas de componentes ejecutadas con Testing Library / E2E:
- Selectores accesibles utilizados:

### 5. Compatibilidad y Pasos Siguientes
- Impacto en contratos con el backend: [Sincronizado / Requiere ajuste]
- Acciones pendientes recomendadas:
```
