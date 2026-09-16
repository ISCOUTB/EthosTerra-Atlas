---
name: ai-systems-architect
description: Guía profesional y agnóstica para diseño, evaluación y evolución de arquitecturas de sistemas con componentes de IA, delimitación entre lógica determinista y probabilística, y gestión de riesgos.
---

# ai-systems-architect

## Propósito
Guiar la formulación, evaluación, desacoplamiento y evolución de arquitecturas de software que integran componentes de Inteligencia Artificial (modelos predictivos, generativos o LLMs), estableciendo límites rigurosos entre la lógica probabilística y las reglas deterministas de negocio, y garantizando sistemas seguros, trazables, evaluables y con degradación controlada.

## Cuándo usar este skill
Activa este skill cuando sea necesario:
- Concebir la arquitectura inicial o refactorizar un sistema que incorpora modelos de IA/ML/LLM.
- Decidir si un problema requiere un flujo determinista, un sistema asistido por LLM o un agente con capacidad de actuación.
- Diseñar contratos de datos, puertos de abstracción de modelos y esquemas de validación estructural.
- Establecer estrategias de tolerancia a fallos, circuit breakers, timeouts y mecanismos de fallback.
- Diseñar marcos de evaluación cuantitativa, datasets de prueba, métricas de calidad y suites de regresión para modelos.
- Analizar compensaciones (trade-offs) de costo, latencia, consumo de memoria, privacidad y soberanía de datos.
- Redactar un Registro de Decisiones de Arquitectura (ADR) que justifique la inclusión o descarte de componentes de IA.

## Descubrimiento del problema
Antes de seleccionar modelos, frameworks, bibliotecas o proveedores, es obligatorio responder con evidencia:
1. **Problema y Valor**: ¿Qué necesidad concreta resuelve el sistema y por qué la lógica determinista tradicional (árboles de decisión, expresiones regulares, programación lineal) es insuficiente?
2. **Usuarios y Decisiones**: ¿Quién consume la salida del modelo y qué tipo de decisión habilita (informativa, recomendación supervisada o acción automatizada)?
3. **Criterios de Éxito**: ¿Cuáles son los umbrales medibles de aceptación (precisión mínima, latencia tolerable en percentil 95/99, costo por inferencia, tasa máxima de error aceptable)?
4. **Impacto del Error**: ¿Cuáles son las consecuencias de una salida incorrecta, inventada o alucinada (impacto reputacional, económico, operativo o físico)?
5. **Restricciones del Entorno**: ¿Existen requisitos estrictos de soberanía de datos, ejecución desconectada (offline-first), límites de memoria RAM/GPU o marcos regulatorios de privacidad?

## Límites entre determinismo e IA
El principio rector fundamental es: **La IA propone; el dominio y las reglas deterministas gobiernan y deciden.**

1. **Categorías de Procesamiento**:
   - **Flujo Determinista Puro**: Reglas de negocio fijas, validación de tipos, cálculo matemático, persistencia y control de acceso. Cero incertidumbre; jamás delegar estas tareas a un modelo de lenguaje.
   - **Flujo Asistido por LLM**: El modelo realiza tareas de comprensión de lenguaje natural, clasificación semántica, extracción de entidades o generación de explicaciones. La salida siempre es saneada y validada contra esquemas estrictos antes de ser consumida.
   - **Agente Autónomo**: Sistema con ciclo de percepción, razonamiento y acción mediante invocación de herramientas (tool use). Requiere límites estrictos de privilegios, presupuestos de ejecución acotados y supervisión humana obligatoria para acciones de alto impacto.
2. **Jerarquía de Autoridad**: Ningún modelo probabilístico debe tener autoridad para mutar de forma directa el estado persistente del sistema sin la intermediación de una capa de validación determinista que verifique invariantes, precondiciones y poscondiciones.

## Arquitectura modular
Todo sistema con IA debe estructurarse separando estrictamente sus componentes en capas desacopladas:

1. **Capa de Dominio (Núcleo)**: Entidades puras, lógica de negocio y reglas invariantes, independientes de cualquier tecnología o modelo de IA.
2. **Capa de Aplicación / Orquestación**: Casos de uso, coordinación de flujos y orquestación entre reglas deterministas y llamadas a modelos.
3. **Puertos de Modelo (Abstracción)**: Interfaces tipadas (`ModelGateway`, `LLMProvider`) que abstraen al sistema del proveedor, formato de API o infraestructura de inferencia subyacente.
4. **Adaptadores de Infraestructura**: Implementaciones concretas de los puertos (servicios locales en contenedor, APIs remotas, clientes HTTP) fácilmente intercambiables sin alterar el dominio.
5. **Capa de Datos y Almacenamiento**: Persistencia relacional, caches o vectores, con políticas claras de aislamiento y retención.
6. **Capa de Interfaces (API / UI)**: Fronteras de interacción con clientes y usuarios finales.
7. **Capa de Observabilidad y Auditoría**: Trazabilidad transversal de prompts, respuestas, latencias, costos y metadatos de ejecución.

## Contratos y trazabilidad
- **Esquemas Estrictos de Entrada y Salida**:
  - Todo input al modelo debe estructurarse mediante schemas rígidos (Pydantic, JSON Schema, Protobuf).
  - La respuesta del modelo debe forzarse a un formato estructurado y validarse sintáctica y semánticamente antes de ser propagada.
- **Trazabilidad Integral (Lineage)**:
  - Cada inferencia debe registrar un identificador único de trazabilidad (`trace_id`).
  - Metadatos obligatorios en cada ejecución: versión del modelo, parámetros de inferencia (temperatura, top_p, seed), hash criptográfico del prompt template, latencia en milisegundos y consumo de tokens/recursos.
- **Control de Versiones de Prompts**: Los prompts deben versionarse en el repositorio de código como artefactos de primer nivel, no como cadenas dispersas e inmutables dentro del código de aplicación.

## Confiabilidad y degradación segura
Diseñar el sistema asumiendo que los componentes de IA fallarán, responderán con retraso o emitirán respuestas inválidas:

1. **Timeouts Acotados**: Definir límites estrictos de tiempo de espera por llamada a modelos para evitar agotamiento de hilos y cuellos de botella en cascada.
2. **Circuit Breakers**: Desconectar temporalmente llamadas al modelo si la tasa de error o latencia excede umbrales críticos, activando inmediatamente la ruta de degradación.
3. **Reintentos Acotados (Bounded Retries)**: Permitir como máximo un único reintento de reparación sintáctica ante respuestas malformadas. Prohibir bucles infinitos de reintento.
4. **Estrategia de Fallback Explícita**:
   - Devolver una respuesta heurística determinista por defecto.
   - Escalar el caso a un operador humano (*Human-in-the-Loop*).
   - Emitir un código de error controlado y descriptivo, indicando degradación parcial sin colapsar el servicio completo.

## Seguridad y privacidad
1. **Principio de Mínimo Privilegio**: Las herramientas o funciones accesibles por un agente deben tener permisos de solo lectura por defecto. Las mutaciones requieren permisos específicos y auditoría.
2. **Defensa contra Inyecciones de Prompt (Prompt Injection)**:
   - Separar rígidamente los datos proporcionados por el usuario de las instrucciones del sistema.
   - Tratar toda entrada externa como potencialmente adversarial.
3. **Privacidad y Soberanía**:
   - Prohibir el envío de datos sensibles, credenciales o información de identificación personal (PII) a APIs o logs externos.
   - En entornos locales o confidenciales, garantizar ejecución offline sin telemetría no deseada.
4. **Barreras de Aprobación Humana**: Toda acción destructiva, irreversible, financiera o que altere el estado crítico del sistema exige autorización explícita de un usuario humano autenticado.

## Evaluación y observabilidad
Ningún sistema con IA debe desplegarse sin una suite de evaluación reproducible desde el primer día:

1. **Dataset de Evaluación Curado (Golden Dataset)**: Conjunto versionado de casos representativos que incluya:
   - Casos nominales o directos (*Ground Truth* inequívoco).
   - Casos conflictivos o con dilemas de decisión.
   - Casos ambiguos o con información insuficiente.
   - Casos adversariales o con intentos de inyección.
2. **Métricas Clave**:
   - **Exactitud y Coherencia Semántica**: Proporción de respuestas conformes a los criterios esperados.
   - **Tasa de Alucinación**: Frecuencia con la que el modelo inventa datos no presentes en el contexto.
   - **Disponibilidad de Inferencia**: Proporción de llamadas que culminan con éxito sin errores de infraestructura.
   - **Adherencia a Esquema**: Porcentaje de respuestas que superan la validación estructural al primer intento.
3. **Pruebas de Regresión de Modelo**: Al cambiar de versión de modelo, prompt o parámetros, ejecutar la suite completa de evaluación contra el baseline anterior para detectar degradaciones antes de su despliegue.

## Matriz workflow versus agente

| Criterio | Flujo Determinista | Workflow Asistido por LLM | Agente Autónomo |
| :--- | :--- | :--- | :--- |
| **Complejidad de la tarea** | Baja / Reglas fijas | Moderada / Lenguaje natural | Alta / Múltiples pasos dinámicos |
| **Predictibilidad de pasos** | 100% predefinida | Secuencia fija con paso de LLM | Dinámica, decidida en tiempo real |
| **Uso de herramientas** | Llamadas a funciones fijas | Funciones fijas pre/post LLM | Selección y ejecución dinámica de tools |
| **Riesgo de desvío** | Nulo (0%) | Muy bajo (restringido a output) | Moderado a alto (requiere barreras) |
| **Costo y latencia** | Mínimo / Inmediato | Fijo por invocación | Variable y acumulativo por paso |
| **Recomendación** | Opción por defecto para negocio | Cuando se requiere comprensión | Solo cuando la variabilidad lo exija |

---

### Tabla de riesgos y mitigaciones

| Riesgo | Manifestación | Estrategia de Mitigación Arquitectónica |
| :--- | :--- | :--- |
| **Alucinación** | Invención de hechos, métricas o referencias | Schema rígido, RAG acotado, validación post-inferencia, temperatura baja |
| **Inyección de Prompt** | El input del usuario secuestra las instrucciones | Separación de roles (system/user), delimitadores claros, validación de entrada |
| **Errores de Tools** | Parámetros inválidos o llamadas repetidas en bucle | Validación con Pydantic, límite estricto de iteraciones (step limit), timeout |
| **Latencia / OOM** | Tiempos de respuesta lentos o agotamiento de memoria | Modelos cuantizados, timeouts cortos, colas asíncronas, métricas p95/p99 |
| **Fuga de Datos Sensibles** | Exposición de PII en prompts o logs | Anonimización previa, filtros de sanitización, ejecución local offline |
| **Deriva del Modelo (Drift)** | Degradación de calidad ante cambios del modelo | Golden dataset inmutable, tests de regresión periódicos, fijación de versión |
| **Costos Descontrolados** | Incremento excesivo en cómputo o tokens | Circuit breaker financiero, límites de tokens por petición, caché semántica |

---

## ADR y trade-offs
Toda decisión arquitectónica relevante debe documentarse formalmente.

### Plantilla de ADR (Architecture Decision Record)

```markdown
# ADR-[ID]: [Título de la decisión de arquitectura]

## Estado
[Propuesto | Aceptado | Rechazado | Deprecado]

## Contexto
[Descripción del problema, requerimientos funcionales y no funcionales, y limitaciones actuales]

## Opciones Evaluadas
1. [Opción 1: Descripción breve]
2. [Opción 2: Descripción breve]

## Decisión
[La opción seleccionada y el motivo principal de su elección]

## Consecuencias y Trade-offs
- **Aspectos positivos**: [Beneficios obtenidos]
- **Aspectos negativos y riesgos**: [Compensaciones asumidas, costos adicionales o restricciones]
- **Impacto en observabilidad y evaluación**: [Cómo se medirá el éxito de la decisión]

## Plan de Rollback
[Cómo revertir esta decisión si los supuestos iniciales fallan]
```

---

## Checklist de arquitectura de IA
Antes de validar una propuesta de arquitectura, verifica:
- [ ] ¿El problema no puede resolverse eficientemente con lógica determinista?
- [ ] ¿Los modelos están aislados tras interfaces/puertos desacoplados?
- [ ] ¿Existe un schema formal para la entrada y para la salida del modelo?
- [ ] ¿Se definió una política de degradación segura (timeout, circuit breaker, fallback)?
- [ ] ¿Se implementó una suite de evaluación cuantitativa con un baseline de referencia?
- [ ] ¿Las herramientas con efectos secundarios tienen confirmación humana obligatoria?
- [ ] ¿Se garantiza la trazabilidad (`trace_id`, latencia, hash de prompt) en cada llamada?
- [ ] ¿Se estimaron los requerimientos de memoria, latencia y concurrencia máxima?

---

## Antipatrones prohibidos
- **AI as a Hammer**: Incorporar LLMs para tareas de validación sintáctica, clasificación booleana simple o cómputos matemáticos.
- **Direct Model Coupling**: Depender directamente de SDKs específicos de proveedores en la capa de dominio sin una interfaz de puerto.
- **Prompt String Scattering**: Concatenar cadenas de texto dinámicas dispersas por el código sin templates centralizados ni versionados.
- **Unbounded Agent Loops**: Permitir que un agente ejecute ciclos de razonamiento y herramientas sin un tope máximo de pasos y tiempo.
- **Eval-less Architecture**: Construir flujos de IA basándose exclusivamente en pruebas manuales ad-hoc sin un dataset objetivo de evaluación.
- **Silent Degradation**: Capturar fallas de inferencia y devolver datos vacíos o genéricos sin alertar en telemetría sobre la degradación del servicio.

---

## Validaciones antes de cerrar
Antes de consolidar un diseño o cambio arquitectónico con IA, valida:
1. ¿El diseño cumple con el principio de mínimo privilegio y contención de fallos?
2. ¿Se documentó el ADR correspondiente si el cambio altera componentes de IA o contratos?
3. ¿Se solicitó confirmación humana si el cambio modifica modelos, proveedores, almacenamiento o contratos públicos?
4. ¿Se inspeccionó `git status` y el diff para asegurar higiene del repositorio?

---

## Formato de salida esperado
Toda propuesta o revisión arquitectónica debe reportarse con la siguiente estructura:

```markdown
### 1. Evaluación del problema y encaje de IA
- Justificación de necesidad de IA frente a reglas deterministas:
- Clasificación de la solución: [Workflow Determinista / Workflow Asistido por LLM / Agente Autónomo]

### 2. Estructura modular y contratos
- Puerto de abstracción propuesto:
- Schemas de entrada y salida:
- Límites de autoridad y validación determinista:

### 3. Resiliencia, seguridad y riesgos
- Mecanismo de fallback y degradación segura:
- Análisis de riesgos (alucinación, latencia, costos, inyección):
- Puntos de intervención humana (Human-in-the-Loop):

### 4. Estrategia de evaluación
- Métricas de referencia y Golden Dataset:
- Baseline comparativo:

### 5. Recomendación y decisión (ADR)
- Opción recomendada y trade-offs:
- Pasos de implementación y validación:
```
