---
name: senior-code-reviewer
description: Guía profesional y agnóstica para revisión rigurosa, constructiva y basada en evidencia de cambios de código, contratos, seguridad y sistemas con IA.
---

# senior-code-reviewer

## Propósito
Establecer un estándar profesional, riguroso, constructivo e imparcial para auditar y revisar cambios de código (*Code Reviews* / Pull Requests), priorizando la detección de riesgos reales de negocio, vulnerabilidades de seguridad, regresiones funcionales, degradación de contratos y deuda técnica oculta, sustentando cada observación en evidencia técnica reproducible y separando tajantemente los defectos bloqueantes de las sugerencias cosméticas.

## Cuándo usar este skill
Activa este skill cuando el sistema deba:
- Revisar un diff o propuesta de cambio antes de su integración a la rama principal.
- Evaluar la solidez y compatibilidad de modificaciones en contratos de API, bases de datos o esquemas.
- Auditar la seguridad de un cambio (gestión de secretos, validación de entradas, control de permisos).
- Evaluar cambios que incorporan modelos de IA o agentes autónomos (inyección de prompts, presupuestos, guardrails).
- Verificar que una refactorización no introduzca regresiones en la suite de pruebas.
- Emitir un dictamen formal de revisión (`APPROVE`, `REQUEST_CHANGES`, `NEEDS_DISCUSSION`).

## Preparación de revisión
Antes de formular comentarios u objeciones en el diff, el revisor debe ejecutar un protocolo previo de comprensión:

1. **Entender el Objetivo y Alcance**:
   - ¿Qué problema resuelve este cambio y cuál es el comportamiento esperado?
   - ¿El diff se limita estrictamente a resolver dicho problema o introduce cambios no relacionados (*scope creep*)?
2. **Inspección Integral del Diff**:
   - Analizar el diff completo (`git diff`) prestando atención a archivos añadidos, modificados o eliminados.
   - Verificar la ausencia de archivos accidentales: binarios, cachés (`__pycache__`, `.DS_Store`), logs, credenciales o directorios locales (`.venv/`, `node_modules/`).
3. **Regla de No Modificación Simultánea**:
   - **El revisor inspecciona y diagnostica primero; jamás modifica código concurrentemente.** Cualquier propuesta de cambio debe presentarse como recomendación estructurada para ser aplicada en un paso posterior.

## Checklist de corrección
- [ ] **Lógica de Negocio**: ¿La implementación resuelve el requerimiento funcional en todos los casos nominales?
- [ ] **Casos Límite (Edge Cases)**: ¿Se manejan colecciones vacías, valores nulos, números negativos o entradas de longitud máxima?
- [ ] **Concurrencia y Asincronía**: ¿Existen posibles condiciones de carrera, bloqueos mutuos (*deadlocks*) o llamadas síncronas bloqueantes en hilos asíncronos?
- [ ] **Manejo de Excepciones**: ¿Se capturan excepciones específicas en lugar de bloques genéricos `except Exception:`? ¿Se limpian recursos en bloques `finally` o context managers?
- [ ] **Compatibilidad Hacia Atrás**: ¿Se rompe algún contrato público, firma de función o endpoint sin una estrategia de migración?
- [ ] **Fugas de Recursos**: ¿Se cierran adecuadamente archivos, conexiones de red, cursores de base de datos o pools de clientes?

## Checklist de seguridad
- [ ] **Cero Secretos**: ¿El diff está 100% libre de contraseñas, tokens de API, certificados o archivos `.env` reales?
- [ ] **Validación en Fronteras**: ¿Toda entrada del usuario o cliente HTTP se valida mediante esquemas estrictos (ej. `extra="forbid"`)?
- [ ] **Path Traversal e Inyecciones**: ¿Las operaciones de archivos y queries están protegidas contra manipulaciones maliciosas de rutas o inyecciones de comandos/SQL?
- [ ] **Principio de Mínimo Privilegio**: ¿Las nuevas funciones, contenedores o servicios se ejecutan con los mínimos permisos necesarios?
- [ ] **Manejo Seguro de Errores**: ¿Los errores devueltos a clientes externos omiten *stack traces*, rutas del sistema o detalles confidenciales de infraestructura?

## Checklist de IA y agentes
Cuando el cambio involucre modelos de lenguaje o componentes agénticos:
- [ ] **Aislamiento de Contexto (Zero-Trust)**: ¿Los datos externos no confiables están encapsulados bajo delimitadores estrictos en el prompt?
- [ ] **Validación Estricta de Salida**: ¿La respuesta del modelo pasa por un validador determinista (Pydantic / Schema) antes de propagarse al dominio?
- [ ] **Límites de Autonomía y Herramientas**: ¿Las herramientas accesibles por el agente son de solo lectura por defecto? ¿Las acciones destructivas exigen confirmación humana (*Human-in-the-Loop*)?
- [ ] **Presupuestos y Bounded Loops**: ¿Existe un límite máximo e inmutable de pasos (`max_steps`), tokens y timeout global para evitar bucles infinitos?
- [ ] **Honestidad en Evaluaciones**: ¿Se garantiza que los reportes de calidad del modelo se obtuvieron contra el modelo real y no contra mocks estáticos?

## Calidad, pruebas y documentación
- [ ] **Pruebas Proporcionales**: ¿El cambio incluye pruebas unitarias o de integración que demuestren que el nuevo código funciona y previene regresiones?
- [ ] **No Desactivación de Controles**: ¿Se mantuvieron intactas las reglas de linting y tipado sin introducir directivas `# type: ignore` o `# noqa` injustificadas?
- [ ] **Claridad y Mantenibilidad**: ¿El código es legible y autoexplicativo sin requerir comentarios que solo parafraseen la sintaxis?
- [ ] **Documentación Sincronizada**: ¿Se actualizaron los manuales, especificaciones OpenAPI, README o ADRs asociados al cambio?

## Severidad y evidencia
Los hallazgos deben fundamentarse en hechos técnicos verificables y clasificarse según su gravedad real:

---

### Escala de Severidad de Hallazgos

| Nivel de Severidad | Definición Técnica | Impacto en el Veredicto |
| :--- | :--- | :--- |
| **BLOCKER (Bloqueante)** | Vulnerabilidad de seguridad crítica, fuga de credenciales, corrupción de datos, caída en runtime o ruptura no pactada de contratos públicos. | **Impide la aprobación** (`REQUEST_CHANGES` obligatorio). Debe resolverse antes del merge. |
| **HIGH (Alta)** | Bug funcional evidente en casos de borde, fuga de recursos (conexiones abiertas), falta de pruebas en lógica crítica o bucles agénticos sin límite. | **Requiere corrección** salvo justificación técnica excepcional acordada. |
| **MEDIUM (Media)** | Inconsistencia de diseño, falta de tipado en funciones internas, manejo deficiente de timeouts o pruebas con datos compartidos frágiles. | **Recomendada su resolución**; no bloquea si existe plan de deuda técnica documentado. |
| **LOW (Baja)** | Oportunidad menor de simplificación de código, documentación imprecisa o inconsistencia menor de nombres. | **Opcional**; sugerencia constructiva para el autor. |
| **NITPICK (Cosmética)** | Preferencia estilística subjetiva o reformulación de texto sin impacto funcional ni de rendimiento. | **Totalmente opcional**; jamás debe retrasar la entrega ni bloquear un cambio. |

---

## Formato de hallazgos
Todo hallazgo debe comunicarse con claridad, respeto y precisión, facilitando la acción inmediata del autor:

```markdown
### [BLOCKER | HIGH | MEDIUM | LOW | NITPICK] Título descriptivo del hallazgo

- **Ubicación:** `ruta/al/archivo.ext:línea`
- **Condición de Disparo:** [Bajo qué circunstancias o entradas exactas se manifiesta el problema]
- **Impacto Técnico:** [Qué consecuencia negativa produce: caída, fuga de memoria, bypass de seguridad]
- **Evidencia / Causa Raíz:** [Explicación técnica de por qué el código actual es vulnerable o incorrecto]
- **Propuesta de Solución:**
```python
# Ejemplo de código sugerido o enfoque de corrección
```
```

## Veredicto de revisión
Al concluir la revisión, el revisor debe emitir un veredicto formal inequívoco:

1. **`APPROVE` (Aprobado)**:
   - El cambio cumple con los estándares de corrección, seguridad, pruebas y diseño. No existen hallazgos de nivel `BLOCKER` ni `HIGH`. Las observaciones `LOW` o `NITPICK` quedan a criterio del autor.
2. **`REQUEST_CHANGES` (Requiere Cambios)**:
   - Se detectó al menos un hallazgo de nivel `BLOCKER` o `HIGH` que pone en riesgo la estabilidad, seguridad o integridad del sistema. El merge queda condicionado a su resolución.
3. **`NEEDS_DISCUSSION` (Requiere Discusión / Alineación)**:
   - El cambio plantea un dilema arquitectónico, un trade-off de alto impacto o una ambigüedad de requisitos que debe debatirse y acordarse antes de proseguir.

---

### Formato Estándar de Veredicto

```markdown
# Dictamen de Code Review: [ID-PR o Tarea]

- **Veredicto:** [APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]
- **Resumen Ejecutivo:** [Síntesis de 2-3 oraciones del estado general del cambio]

## 1. Conteo de Hallazgos
- Bloqueantes (BLOCKER): 0
- Severidad Alta (HIGH): 0
- Severidad Media (MEDIUM): 1
- Severidad Baja / Nitpicks: 2

## 2. Detalle de Hallazgos Priorizados
[Listado de hallazgos según la plantilla formal]

## 3. Acciones Requeridas para Desbloqueo (si aplica)
- [Paso 1 requerido antes de re-evaluación]
```

---

## Antipatrones prohibidos
- **Bikeshedding (Ley de Trivialidad)**: Gastar el 90% del tiempo de revisión debatiendo el nombre de una variable o espaciados cosméticos mientras se pasa por alto una falla de concurrencia o una inyección de prompt.
- **Inventing Hypothetical Bugs**: Señalar errores hipotéticos sin fundamentar bajo qué condiciones reales de entrada o ejecución podrían ocurrir.
- **Gatekeeping Destructivo**: Rechazar cambios basándose en preferencias personales de estilo ("yo lo habría escrito de otra forma") en lugar de criterios técnicos objetivos.
- **Modifying Code In-Review**: Editar directamente el código del autor mientras se revisa, generando conflictos de versión y diluyendo la responsabilidad del cambio.
- **Rubber-Stamping (Aprobación a Ciegas)**: Emitir un `APPROVE` instantáneo sin haber leído el diff, revisado las pruebas ni evaluado los impactos de seguridad.
- **Vague Hand-Waving Feedback**: Escribir comentarios vagos como "esto no me gusta" o "arregla esto" sin indicar la causa técnica ni sugerir una alternativa viable.

## Validaciones antes de cerrar
Antes de emitir el dictamen formal de revisión, verifica:
1. ¿Se evaluó el diff en su totalidad sin limitarse a una sola sección?
2. ¿Cada hallazgo incluye ubicación, condición de disparo, impacto y propuesta concreta?
3. ¿Se clasificó adecuadamente cada hallazgo según la escala de severidad (sin inflar nitpicks a blockers)?
4. ¿Se verificaron los aspectos de seguridad, observabilidad y manejo de errores?
5. ¿Se confirmó que las pruebas cubren los cambios y no se desactivaron controles de calidad?
6. ¿Se emitió uno de los tres veredictos formales estandarizados?

## Formato de salida esperado
Toda entrega de revisión de código debe estructurarse conforme al siguiente estándar:

```markdown
### 1. Resumen de la Revisión
- Propósito del cambio evaluado:
- Archivos y componentes auditados:
- Veredicto formal emitido: [APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]

### 2. Hallazgos Identificados (ordenados por severidad)
- [Listado de hallazgos con ubicación, impacto y propuesta]

### 3. Aspectos Positivos Destacados
- [Reconocimiento explícito de buenas prácticas o soluciones elegantes encontradas]

### 4. Condiciones para Aprobación y Próximos Pasos
- [Acciones específicas requeridas del autor para proceder al merge]
```
