# Auditoría de Skills AGY

## 1. Inventario

| Skill | Propósito | Estado | Uso actual | ¿Tiene límites claros? |
| :--- | :--- | :--- | :--- | :--- |
| **domain-peas-ebdi** | Marco metodológico PEAS, eBDI, fronteras de autonomía, invariantes y alcance por semanas para el clasificador. | Núcleo activo | Marco de gobernanza conceptual para Semana 6 (Caso Puro). | Sí (Zonas autónoma, HITL y prohibida delimitadas). |
| **wellprod-domain** | Semántica agronómica de Ethos Terra (intenciones campesinas, recursos: capital/inventario/salud, pureza vs colisión). | Núcleo activo | Soporte semántico de reglas agronómicas y datasets. | Sí (Restricción de escritura y conservación de datos). |
| **senior-software-engineer** | Desarrollo atómico, refactorización limpia, preservación de contratos, pruebas proporcionales y uso seguro de Git. | Núcleo activo | Guía transversal para cambios de código en backend y utilidades. | Sí (Matriz de confirmaciones y cambios atómicos). |
| **backend-fastapi-engineer** | Arquitectura hexagonal, contratos Pydantic V2, asincronía segura, endpoints y observabilidad en FastAPI. | Núcleo activo | Implementación y tipado de endpoints y schemas para Semana 6. | Sí (Routers delgados y DTOs estrictos en fronteras). |
| **llm-prompt-engineer** | Diseño, versionado, parámetros y evaluación A/B de prompts estructurados con mitigación de alucinación. | Núcleo activo | Optimización del prompt del clasificador Gemma 4 para Caso Puro. | Sí (Zero-trust, schema rígido y reintento acotado a 1). |
| **llm-evaluation-engineer** | Evaluación cuantitativa, Golden Datasets, métricas de no-regresión y análisis forense de trazas. | Núcleo activo | Medición en `evals/runner.py` con `real_model` frente al baseline. | Sí (Prohibición de mocks en evaluación de IA). |
| **senior-code-reviewer** | Revisión rigurosa y constructiva de diffs, seguridad, contratos y emisión de veredictos antes de commit. | Núcleo activo | Control de calidad previo a la integración de cualquier cambio. | Sí (Escala de severidad y revisión sin edición simultánea). |
| **task-orchestrator** | Planificación, mínima complejidad, coordinación Hub-and-Spoke y gestión de tareas en el agente principal. | Núcleo activo | Coordinación de flujos de trabajo y delegación con contexto mínimo. | Sí (FSM de tareas y límites duros de autonomía). |
| **ai-systems-architect** | Desacoplamiento entre lógica probabilística y determinista, puertos de modelos y diseño para fallos (ADR). | Núcleo disponible | Soporte para rediseños estructurales o cambio de adaptadores. | Sí (La IA propone, el dominio gobierna y decide). |
| **application-security-engineer** | Threat modeling, protección de secretos, blindaje de APIs y mitigación de OWASP Top 10 para LLMs. | Núcleo disponible | Auditoría de endpoints, validación de inputs y gestión de credenciales. | Sí (Mínimo privilegio y HITL en acciones sensibles). |
| **docker-devops-engineer** | Contenerización multi-stage, Compose, límites de RAM/CPU, healthchecks y preservación de volúmenes. | Núcleo disponible | Operación de servicios locales Docker y Docker Model Runner. | Sí (Prohibición de `down -v` y comandos destructivos). |
| **test-automation-engineer** | Pirámide de pruebas, contratos, fixtures/factories, pruebas de resiliencia y control de flakiness. | Núcleo disponible | Diseño y automatización de pruebas unitarias y de integración. | Sí (Diferenciación de tests de software vs eval de IA). |
| **documentation-engineer** | Manuales operativos, documentación técnica, ADRs, reportes experimentales y formatos Markdown/LaTeX. | Núcleo disponible | Documentación de entregables y reportes científicos reproducibles. | Sí (Cero citas inventadas y reporte honesto de muestras). |
| **static-analysis-engineer** | Linters, type checkers, SAST, escaneo de dependencias y gestión documentada de excepciones. | Candidata a fusión | Soporte de calidad estática; solapable con code review y software engineer. | Sí (Política de excepciones con metadatos obligatorios). |
| **frontend-react-engineer** | Interfaces React/TypeScript accesibles (a11y), matriz de estados de UI y visualización de resultados de IA. | Diferida | Inactiva hasta que los contratos y API de Semana 6 estén congelados. | Sí (Validación bidireccional y cero secretos en cliente). |
| **agent-systems-engineer** | Sistemas multiagente, memoria episódica/semántica y protocolos FIPA inter-agente. | Diferida | Inactiva hasta semanas 7–8 / 10–12 (Semana 6 es un workflow asistido). | Sí (Coordinación Hub-and-Spoke sin redes mesh caóticas). |
| **technical-researcher** | Formulación de preguntas, jerarquía de fuentes primarias y comparación de alternativas técnicas. | Diferida | Inactiva hasta que surja la necesidad de evaluar nuevas dependencias. | Sí (Cero afirmaciones sin contexto de hardware y fuente). |

---

## 2. Revisión de calidad

### 1. `domain-peas-ebdi`
- **Secciones presentes:** 15/15 (Propósito, Cuándo usar, Contexto, Relación con wellprod-domain, Principios arquitectónicos, PEAS, Frontera de autonomía, Invariantes, Alcance por semana, Guía de decisión, Antipatrones, Procedimiento, Validaciones, Formato de salida).
- **Contexto específico:** Totalmente contextualizada al proyecto (WellProdSim, Ethos Terra, Gemma 4 E4B, Semana 6).
- **Política de reutilización:** Presente conceptualmente en la guía de decisión (resolver por reglas deterministas antes de invocar LLM).
- **Política Git / no firma IA:** Implícita en invariantes de baseline y trazabilidad.
- **Riesgos o vacíos:** Requiere incorporación explícita de la cláusula transversal de no-firmas y confirmación previa a commits.

### 2. `wellprod-domain`
- **Secciones presentes:** 4 secciones breves (Contexto, Reglas de dominio, Criterios de clasificación, Uso).
- **Contexto específico:** Altamente específico del dominio agronómico campesino.
- **Política de reutilización:** Ausente.
- **Política Git / no firma IA:** Ausente.
- **Riesgos o vacíos:** Es un archivo conciso heredado (40 líneas) sin estructura estándar formal ni directrices de gobernanza de control de versiones.

### 3. `senior-software-engineer`
- **Secciones presentes:** 15/15 completas (Propósito, Cuándo usar/no usar, Principios, Flujo seguro, Diseño/refactor, Contratos, Pruebas, Seguridad/observabilidad, Git seguro, Matriz de confirmaciones, Antipatrones, Validaciones, Formato de salida).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Muy alta (KISS, YAGNI, regla del Boy Scout, cambios atómicos).
- **Política Git / no firma IA:** Alta en operaciones seguras de Git, pero falta mención expresa a la prohibición de badges/firmas de IA.
- **Riesgos o vacíos:** Actualizar la sección de Git con la lista explícita de términos prohibidos de autoría.

### 4. `ai-systems-architect`
- **Secciones presentes:** 14/14 completas (ADR, Matriz workflow vs agente, Tabla de riesgos, Checklist).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (prioridad determinista antes de IA).
- **Política Git / no firma IA:** Enfocada en trazabilidad técnica; requiere alineación con políticas transversales de Git.
- **Riesgos o vacíos:** Ninguno crítico.

### 5. `agent-systems-engineer`
- **Secciones presentes:** 16/16 completas (PEAS, FSM, herramientas, memoria, subagentes, guardrails, trayectorias).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (evitar multiagente si un agente único o workflow resuelve la tarea).
- **Política Git / no firma IA:** Neutral.
- **Riesgos o vacíos:** Diseñada para sistemas de alta autonomía; debe mantenerse inactiva en la fase actual.

### 6. `llm-prompt-engineer`
- **Secciones presentes:** 16/16 completas (Estructura modular, Few-shot balanceado, JSON Schema, Parámetros, A/B, Inyección, Matriz de errores).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (versionado de prompts como artefactos de primer nivel y reutilización de templates).
- **Política Git / no firma IA:** Neutral.
- **Riesgos o vacíos:** Asegurar que los prompts generados no contengan firmas implícitas en el texto de sistema.

### 7. `llm-evaluation-engineer`
- **Secciones presentes:** 15/15 completas (Niveles de prueba, Datasets, Baselines, Métricas de calidad/seguridad, Trazas, Matriz de validez, Taxonomía de errores).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (preservación inmutable del baseline).
- **Política Git / no firma IA:** Fuerte rigor en honestidad métrica; falta prohibición textual de firmas.
- **Riesgos o vacíos:** Ninguno crítico.

### 8. `backend-fastapi-engineer`
- **Secciones presentes:** 15/15 completas (Hexagonal, Pydantic V2, Endpoints, Async, Depends, Observabilidad, Seguridad, Matriz confirmaciones).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (evitar duplicación de DTOs, inyección de dependencias).
- **Política Git / no firma IA:** Presente en confirmación de cambios de contratos públicos.
- **Riesgos o vacíos:** Sólida y directamente aplicable.

### 9. `frontend-react-engineer`
- **Secciones presentes:** 16/16 completas (Features, Contratos API, Matriz de estados UI, UX para IA, a11y WCAG AA, Pruebas Testing Library).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (colocation de estado, componentes compartidos).
- **Política Git / no firma IA:** Neutral.
- **Riesgos o vacíos:** No debe activarse hasta congelar la API backend de Semana 6.

### 10. `docker-devops-engineer`
- **Secciones presentes:** 15/15 completas (Multi-stage, Compose, Healthchecks, Recursos RAM/CPU, Persistencia, Comandos seguros vs prohibidos).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (reutilización de manifests, caching de capas, centralización en Makefile).
- **Política Git / no firma IA:** Fuerte en prohibición de operaciones destructivas.
- **Riesgos o vacíos:** Totalmente alineada con la infraestructura local.

### 11. `test-automation-engineer`
- **Secciones presentes:** 16/16 completas (Pirámide de pruebas, AAA, Contratos, Resiliencia, Flakiness, Prohibición de mocks en eval IA).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (factories mínimas, no duplicar fixtures).
- **Política Git / no firma IA:** Prohibición de commits con tests rotos.
- **Riesgos o vacíos:** Sólida y complementaria a `llm-evaluation-engineer`.

### 12. `application-security-engineer`
- **Secciones presentes:** 16/16 completas (Threat modeling, Mínimo privilegio, Política de secretos, Datos no confiables, OWASP Top 10 LLM, HITL).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (centralización de políticas en frontera).
- **Política Git / no firma IA:** Muy estricta en exclusión de secretos y `.env` en Git.
- **Riesgos o vacíos:** Excelente madurez defensiva.

### 13. `static-analysis-engineer`
- **Secciones presentes:** 14/14 completas (Categorías de análisis, Matriz P0-P3, Política de excepciones, Quality gates).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (reutilización de herramientas y reglas).
- **Política Git / no firma IA:** Neutral.
- **Riesgos o vacíos:** Se solapa funcionalmente con las revisiones de código de `senior-code-reviewer` y las prácticas de `senior-software-engineer`.

### 14. `technical-researcher`
- **Secciones presentes:** 15/15 completas (Preguntas falsables, Jerarquía de fuentes primarias, Matriz comparativa, Checklist de calidad).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (evitar reinventar dependencias analizadas).
- **Política Git / no firma IA:** Fuerte en prohibición de alucinaciones de citas.
- **Riesgos o vacíos:** Innecesaria en tareas rutinarias de desarrollo.

### 15. `documentation-engineer`
- **Secciones presentes:** 14/14 completas (Matriz de audiencias, Manuales operativos, Reportes científicos, Checklist LaTeX/Markdown).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Alta (trazabilidad a código real y única fuente de verdad).
- **Política Git / no firma IA:** Fuerte en veracidad y sobriedad.
- **Riesgos o vacíos:** Requiere incorporar la prohibición textual de firmas IA en documentos.

### 16. `senior-code-reviewer`
- **Secciones presentes:** 14/14 completas (Checklists multidimensionales, Escala de severidad, Plantilla de hallazgo, Veredictos).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Muy alta (verificar que no se duplique código en el diff).
- **Política Git / no firma IA:** Alta (revisar que no haya secretos ni cambios ajenos).
- **Riesgos o vacíos:** Agregar validación específica de firmas de IA como hallazgo BLOCKER.

### 17. `task-orchestrator`
- **Secciones presentes:** 16/16 completas (Árbol directo vs skill vs subagente, Contexto mínimo, FSM de tareas, Matriz de confirmaciones).
- **Contexto específico:** 100% agnóstica.
- **Política de reutilización:** Máxima (principio de mínima complejidad y reutilización prioritaria).
- **Política Git / no firma IA:** Control riguroso de confirmaciones humanas antes de commits.
- **Riesgos o vacíos:** Es el motor de gobernanza principal del agente.

---

## 3. Matriz de solapamientos

| Skill A | Skill B | Solapamiento | Riesgo | Recomendación |
| :--- | :--- | :--- | :--- | :--- |
| **wellprod-domain** | **domain-peas-ebdi** | Ambas abordan definiciones de Caso Puro vs Conflictivo y reglas de recursos de Ethos Terra. | Divergencia en criterios de clasificación si se modifican por separado. | Mantener `wellprod-domain` exclusivamente como diccionario de datos agronómicos y `domain-peas-ebdi` como gobernanza del sistema y PEAS. |
| **static-analysis-engineer** | **senior-code-reviewer** | Ambas definen priorización de hallazgos (P0-P3 vs BLOCKER-LOW) y políticas de excepciones (`noqa`, `ignore`). | Duplicación de criterios de revisión estática durante el ciclo de desarrollo. | Fusionar o subordinar: `static-analysis-engineer` debe operar como guía de herramientas/linters y `senior-code-reviewer` como el árbitro final de aprobación. |
| **test-automation-engineer** | **llm-evaluation-engineer** | Ambas definen estrategias de pruebas, regresión, reporte de métricas y manejo de mocks. | Confusión entre pruebas de software deterministas y evaluación probabilística del modelo. | Delimitación estricta: `test-automation-engineer` cubre software (unitarias, contratos, API, resiliencia); `llm-evaluation-engineer` cubre exclusivamente benchmarks y calidad del modelo con `real_model`. |
| **ai-systems-architect** | **agent-systems-engineer** | Ambas cubren la frontera entre determinismo e IA, y la matriz de selección workflow vs agente. | Aplicar patrones de multiagentes complejos cuando la arquitectura solo requiere un monolito asistido por LLM. | Mantener `agent-systems-engineer` diferida hasta fases multiagente reales (semanas 10–12); usar `ai-systems-architect` para el diseño de Semana 6. |
| **senior-software-engineer** | **backend-fastapi-engineer** | Ambas tratan modularidad, tipado estático, manejo de errores y pruebas unitarias. | Redundancia de directrices en tareas de backend. | `senior-software-engineer` actúa como estándar de ingeniería agnóstico; `backend-fastapi-engineer` se activa para especificidades de FastAPI y Pydantic V2. |

---

## 4. Núcleo para Semana 6

Para cumplir el objetivo de la **Semana 6** (*formalización de Caso Puro, esquema Pydantic, prompt engineering estructurado y evaluación reproducible*), se recomienda activar estrictamente este núcleo de **6 skills**:

1. **`domain-peas-ebdi`**: Provee el marco de gobierno, la definición de Caso Puro, los invariantes no negociables y el alcance temporal específico de la semana.
2. **`backend-fastapi-engineer`**: Guía la implementación de contratos DTOs en Pydantic V2 (`extra="forbid"`, validadores explícitos) y la integración del endpoint `/classifications:propose`.
3. **`llm-prompt-engineer`**: Diseña el template del prompt estructurado con delimitadores Zero-Trust y esquema JSON rígido para Gemma 4 E4B.
4. **`llm-evaluation-engineer`**: Garantiza que las pruebas canarias y la evaluación completa en `evals/runner.py` se ejecuten en modo `real_model`, midiendo exactitud, latencia y adherencia a esquema sin mocks.
5. **`senior-software-engineer`**: Asegura cambios mínimos y atómicos, principio de reutilización y prevención de abstracciones prematuras.
6. **`senior-code-reviewer`**: Audita los diffs resultantes, verifica la ausencia de secretos y firmas de IA, y emite veredicto formal antes de proponer cualquier commit.

---

## 5. Skills diferidas

Las siguientes skills no deben activarse en la fase inicial de Semana 6; su activación estará supeditada a hitos o eventos específicos:

- **`agent-systems-engineer`**:
  - *Fase de activación:* Semanas 7–8 (manejo complejo de conflictos) o Semanas 10–12 (integración con agentes BESA).
  - *Justificación:* En Semana 6 el sistema es un clasificador determinista asistido por micro-LLM, no una red de agentes autónomos.
- **`frontend-react-engineer`**:
  - *Fase de activación:* Post-congelamiento de contratos de API en Semana 6.
  - *Justificación:* Diseñar la UI antes de estabilizar los esquemas Pydantic y el comportamiento de inferencia genera retrabajo y acoplamiento prematuro.
- **`technical-researcher`**:
  - *Fase de activación:* Bajo demanda, si surge un bloqueo de compatibilidad de runtime (DMR en M4) o se propone evaluar una librería nueva.
  - *Justificación:* El stack actual (FastAPI, uv, Docker, Ollama/DMR, Gemma) ya está seleccionado y operativo en el baseline.
- **`documentation-engineer`**:
  - *Fase de activación:* Al cierre del incremento de Semana 6.
  - *Justificación:* La redacción formal de manuales o reportes finales ocurre tras consolidar los resultados experimentales, no durante la codificación activa.

---

## 6. Automatizaciones existentes

| Necesidad | Recurso existente | Reutilizar/extender/crear | Justificación |
| :--- | :--- | :--- | :--- |
| **Pruebas (Unitarias / Integración)** | `tests/integration/test_dmr_canary.py`, `Makefile` (`canary`) | **Reutilizar** | El target `make canary` ya ejecuta la prueba canaria de integración contra el runner local. |
| **Evaluación LLM** | `evals/runner.py`, `evals/datasets/test-cases.json`, `Makefile` (`test`, `test-verbose`), `run_real_eval.sh` | **Reutilizar** | El harness de evaluación ya está completamente implementado, mide latencia, disponibilidade y genera `report.json`. |
| **Docker / Infraestructura** | `compose.yaml`, `Makefile` (`build`, `start`, `stop`, `health`, `model-check`) | **Reutilizar** | El compose ya parametriza servicios, puertos (8000, 5173), perfiles de modelo y healthchecks. |
| **UI (Desarrollo / Build)** | `apps/ui/package.json`, `apps/ui/vite.config.ts`, `apps/ui/.oxlintrc.json` | **Reutilizar** | La suite de frontend ya cuenta con Vite, Oxlint y scripts de desarrollo (`pnpm dev`, `pnpm build`). |
| **Lint / Formateo** | `apps/ui/.oxlintrc.json` (frontend), `uv` (backend) | **Extender en Makefile** | Falta un target central `make lint` que invoque oxlint para UI y ruff/flake8 para Python sin dependencias complejas. |
| **Seguridad / Auditoría** | No existe script centralizado; solo checklists en skills | **Crear script central** | Se requiere un script determinista que escanee secretos, verifique `.gitignore` y detecte firmas de IA en staged antes de commits. |
| **Git / Quality Gate** | Comandos manuales de Git; no hay hooks instalados | **Crear script central** | Necesario para automatizar el protocolo de validación pre-commit (`git diff --check`, no baseline mutado, no firmas IA). |
| **Documentación** | `MANUAL-USUARIO.md`, `README.md`, `docs/migracion-agy.md` | **Reutilizar y extender** | Documentación viva que se actualiza conforme evolucionan los endpoints y las evaluaciones. |

---

## 7. Scripts recomendados

Para evitar duplicar scripts dentro de cada carpeta de skill y mantener la arquitectura limpia, se proponen únicamente **dos scripts centrales** en la carpeta `scripts/`:

### Script 1: `scripts/verify_integrity.sh`
- **Responsabilidad:** Actuar como Quality Gate pre-commit determinista para auditar higiene del repositorio.
- **Skills consumidoras:** `senior-code-reviewer`, `application-security-engineer`, `senior-software-engineer`.
- **Inputs:** Archivos indexados en Git (`git diff --staged`) y mensaje de commit propuesto.
- **Outputs:** Código de salida `0` (aprobado) o `1` (bloqueado con reporte de infracciones en consola).
- **Criterio de éxito:** Bloquea si detecta:
  1. Firmas de IA prohibidas (*"Generated by AI"*, *"Co-Authored-By"*, etc.).
  2. Secretos o archivos `.env` indexados.
  3. Errores de sintaxis de diff (`git diff --check`).
  4. Alteraciones no autorizadas en archivos baseline de Semana 5.
- **Motivo por el cual no puede reutilizarse algo existente:** No existe actualmente en el repositorio ninguna utilidad que valide reglas de autoría de IA ni integridad de baseline.

### Script 2: `scripts/run_quality_checks.sh`
- **Responsabilidad:** Orquestar en un solo comando determinista la ejecución de linters, chequeo de tipos y pruebas unitarias/canarias locales.
- **Skills consumidoras:** `senior-software-engineer`, `backend-fastapi-engineer`, `test-automation-engineer`.
- **Inputs:** Código fuente en `apps/api/` y `apps/ui/`.
- **Outputs:** Resumen consolidado de estado de calidad (Pass/Fail).
- **Criterio de éxito:** Ejecuta secuencialmente: linter de backend (`uv run ruff/flake8`), linter de frontend (`oxlint`), y prueba canaria (`make canary`).
- **Motivo por el cual no puede reutilizarse algo existente:** Actualmente los comandos están dispersos entre el `Makefile`, `package.json` y scripts bash individuales con lógica redundante de arranque de Docker.

*(No se requiere un tercer script; las tareas de inferencia y evaluación ya están resueltas en `evals/runner.py` y `Makefile`).*

---

## 8. Recomendación de próxima fase

**Opción seleccionada: B. Definir `AGENTS.md`**

### Justificación Técnica:
1. **Punto de Enlace de Gobernanza:** `AGENTS.md` es el contrato de configuración que formaliza qué agentes existen, qué rol desempeñan, qué skills tienen activadas del núcleo de Semana 6 y cuáles tienen prohibidas.
2. **Evita Retrabajo en Skills:** Ajustar las 17 skills (Opción A) en este momento consumiría tiempo en skills que ya han sido auditadas como "diferidas" (ej. `agent-systems-engineer` o `technical-researcher`). Con `AGENTS.md` se delimita con precisión el equipo activo antes de cualquier ajuste fino.
3. **Precondición para Hooks y MCPs:** Los hooks de calidad (Opción E) y las herramientas MCP (Opción C) deben configurarse en función de los permisos y fronteras definidos formalmente en la arquitectura de agentes de `AGENTS.md`.
