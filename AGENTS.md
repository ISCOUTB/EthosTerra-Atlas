# AGENTS.md — Contexto y Gobierno del Proyecto

## 1. Contexto del Repositorio
- **Repositorio Oficial:** `Prueba-llm-local` (repositorio monorepo único con un solo `.git` en la raíz; prohibido anidar otros repositorios).
- **Línea Base (Baseline):** Semana 5 consolidada e inmutable (Commit baseline: `388553e`).
- **Propósito:** Clasificador y evaluador local de intenciones declarativas bajo arquitectura hexagonal y soberanía de datos.
- **Simulador Real:** WellProdSim / EthosTerra / Python BESA se encuentra fuera de este repositorio y permanece estrictamente **fuera de alcance hasta las semanas 10–12**.
- **Modelo Oficial Obligatorio:** `ai/gemma4:E4B` (ejecución offline-first local).
- **Runtime de Inferencia:** Docker Model Runner (DMR) verificado (alternativa con fallback: Ollama local).
- **Backend:** FastAPI en `apps/api/` gestionado con `uv`.
- **Frontend:** React + Vite + TypeScript en `apps/ui/`.
- **Evaluación y Benchmarking:** `evals/runner.py` con dataset `evals/datasets/test-cases.json` y reporte baseline `evals/report.json` (20 casos evaluados en modo `real_model`).
- **Operación Local:** Automatizada mediante [Makefile](file:///Volumes/ADATA%20SD620/Programacion%207.0/universidad/proyecto%20de%20grado/Prueba-llm-local/Makefile) y documentada en [MANUAL-USUARIO.md](file:///Volumes/ADATA%20SD620/Programacion%207.0/universidad/proyecto%20de%20grado/Prueba-llm-local/MANUAL-USUARIO.md) y [README.md](file:///Volumes/ADATA%20SD620/Programacion%207.0/universidad/proyecto%20de%20grado/Prueba-llm-local/README.md).

---

## 2. Skills: Núcleo Activo para Semana 6
Para cualquier tarea en la fase actual, el agente debe activar como máximo las skills pertinentes de este núcleo estricto:

1. **`domain-peas-ebdi`**: Gobierno del modelo PEAS, invariantes del proyecto, frontera de autonomía y definiciones operativas de Caso Puro vs. Conflictivo.
2. **`backend-fastapi-engineer`**: Implementación de contratos Pydantic V2 en `apps/api/src/domain/`, endpoints REST delgados, control de asincronía, timeouts y observabilidad.
3. **`llm-prompt-engineer`**: Diseño, versionado y optimización de prompts estructurados con delimitadores Zero-Trust para Gemma 4 E4B, salida JSON Schema estricta y mitigación de alucinación.
4. **`llm-evaluation-engineer`**: Medición cuantitativa mediante `evals/runner.py` en modo `real_model`, matrices de confusión, trazas completas y comparación estricta contra el baseline.
5. **`senior-software-engineer`**: Estándar de cambios mínimos, reutilización de código existente, tipado estático, refactorización limpia y preservación de contratos.
6. **`senior-code-reviewer`**: Revisión crítica del diff, verificación de seguridad, ausencia de secretos o firmas de IA, y emisión de veredictos (`APPROVE`, `REQUEST_CHANGES`, `NEEDS_DISCUSSION`) antes de proponer commits.

---

## 3. Skills Disponibles pero Diferidas
Las siguientes skills residen en `.agents/skills/` pero **no deben activarse automáticamente** hasta que la fase o el requerimiento lo justifique:

- **`agent-systems-engineer`**: Diferida hasta Semanas 7–8 o 10–12 (Semana 6 es un clasificador determinista asistido por LLM, no un sistema multiagente).
- **`frontend-react-engineer`**: Diferida hasta que los contratos de API y endpoints de Semana 6 estén congelados y probados.
- **`docker-devops-engineer`**: Diferida hasta que se requieran modificaciones reales en `compose.yaml`, `Dockerfile` o límites de hardware.
- **`test-automation-engineer`**: Diferida; activar solo si se requieren pruebas de software complejas no cubiertas por las suites existentes.
- **`static-analysis-engineer`**: Diferida hasta la configuración formal del quality gate automatizado.
- **`technical-researcher`**: Diferida; activar solo si surge una necesidad de investigación documental o evaluación de nuevas dependencias.
- **`documentation-engineer`**: Diferida hasta el cierre del incremento para la redacción final de manuales o reportes.
- **`task-orchestrator`**: Activada solo si el agente principal requiere delegación formal en subagentes aislados.
- **`case-conflict-analyzer`**: Reservada para Semanas 7–8 (Caso Conflictivo).
- **`pdf-document-engineer`**: Reservada solo si se incorpora ingesta de documentos PDF al sistema.
- **`besa-integration-engineer`**: Reservada para Semanas 10–12 (integración con el simulador real).

---

## 4. Reglas de Selección de Skills
- **Principio de Mínima Activación**: Seleccionar únicamente la skill mínima indispensable para la tarea.
- **Límite de Concurrencia**: No activar más de **dos skills simultáneamente** para una tarea normal de desarrollo o mantenimiento.
- **Revisión Cruzada**: Emplear revisión cruzada (ej. `backend-fastapi-engineer` + `senior-code-reviewer`) exclusivamente en cambios de arquitectura, seguridad, contratos de API, esquemas de datos o resultados experimentales.
- **Cero Creación Injustificada**: Prohibido crear skills nuevas si la necesidad puede resolverse con las existentes. La creación de una nueva skill exige:
  1. Necesidad recurrente demostrada.
  2. Frontera funcional no cubierta por las 17 skills auditadas.
  3. Ausencia total de solapamiento.
  4. Propuesta documentada en `docs/`.
  5. Confirmación humana explícita previa.

---

## 5. Principio Obligatorio de Reutilización y Cambio Mínimo
Antes de crear cualquier archivo, módulo, clase, función, componente, endpoint, schema, prompt, script, test, Dockerfile, configuración o dependencia:

1. **Inspección Previa**: Inspeccionar el repositorio de forma no destructiva para mapear implementaciones, utilidades, schemas, fixtures o scripts existentes.
2. **Clasificación Obligatoria de la Acción**:
   - *Reutilizar:* Si el componente existente cumple con el requerimiento.
   - *Extender:* Si una clase o schema puede ampliarse preservando compatibilidad.
   - *Refactorizar mínimamente:* Si se requiere un ajuste cohesivo en el componente más cercano al dominio.
   - *Crear nuevo:* Exclusivamente si no existe equivalente útil, justificando formalmente por qué no basta extender o reutilizar.
3. **Única Fuente de Verdad (Single Source of Truth)**: Prohibido duplicar reglas de negocio, contratos, esquemas JSON/Pydantic, constantes, validadores, prompts versionados o fixtures de prueba.
4. **Prohibición de Carpetas Ambiguas**: Prohibido crear directorios como `utils`, `helpers`, `common`, `shared` o `generic` sin una responsabilidad de dominio específica y autorización humana.
5. **Regla de Tres contra Abstracción Prematura**: No abstraer solo porque dos fragmentos se parecen; abstraer únicamente ante tres o más instancias que compartan la misma semántica, razón de cambio e interfaz clara.

---

## 6. Alcance Estricto de Semana 6
El objetivo único de la Semana 6 es **refinar el experimento aislado de Semana 5 para el Caso Puro**:
- Contrato de entrada estricto (`RequestDTO`).
- Contrato de salida estructurado (`ResponseDTO` validado contra JSON Schema).
- Prompt especializado, delimitado (Zero-Trust) y versionado como artefacto de primer nivel.
- Inferencia real con `ai/gemma4:E4B` mediante Docker Model Runner.
- Validación sintáctica y semántica determinista (Pydantic V2).
- Trazabilidad forense (`trace_id`, latencia, prompt digest, modelo).
- Comparación cuantitativa contra el baseline de 20 casos de Semana 5.

### Lo que NO se debe hacer en Semana 6:
- **NO** tocar el simulador WellProdSim / EthosTerra / Python BESA.
- **NO** modificar el núcleo del simulador.
- **NO** escribir archivos YAML reales de configuración de producción.
- **NO** ejecutar acciones físicas o mutaciones no auditadas.
- **NO** implementar el CRUD de intenciones todavía (reservado a Semanas 8–9).
- **NO** crear herramientas MCP productivas adicionales.
- **NO** implementar bases vectoriales, LangChain, LangGraph ni RAG innecesario.
- **NO** desplegar enjambres multiagente (el clasificador es un monolito modular asistido).
- **NO** cambiar el modelo Gemma 4 E4B ni su configuración de cuantización sin autorización.

---

## 7. Separación de Responsabilidades
- **El LLM propone**: Emite clasificaciones preliminares y razonamiento semántico estructurado. Nunca toma decisiones finales de ejecución.
- **Pydantic / JSON Schema valida**: Fuerza el tipado rígido y rechaza campos inesperados (`extra="forbid"`).
- **Los validadores deterministas verifican**: Evalúan tipos, rangos, procedencia e invariantes lógicas.
- **Las reglas de dominio gobiernan**: Evalúan condiciones formales antes o después de la inferencia; si una regla determinista resuelve el caso, no se invoca al LLM.
- **La API controla**: Gestiona el ciclo HTTP, timeouts, trazabilidad (`trace_id`), códigos de error y límites de recursos.
- **El simulador conserva autoridad**: En la futura integración (Semanas 10–12), el simulador multi-agente decidirá si una propuesta de intención afecta creencias o se ejecuta. El LLM jamás escribe directamente en el simulador.

---

## 8. Métricas y Evidencia Científica
Toda medición cuantitativa debe desagregar rigurosamente sus dimensiones:
1. **Disponibilidad de inferencia:** Proporción de llamadas sin error de infraestructura (500, timeout, OOM).
2. **Validez estructural del JSON:** Porcentaje de respuestas conformes al schema al primer intento.
3. **Calidad semántica:** Accuracy, Precision, Recall y F1 calculadas **exclusivamente sobre respuestas estructuralmente válidas**.
4. **Seguridad:** Resistencia ante inyecciones y tasa de alucinación (0% tolerado en datos inventados).
5. **Abstención:** Tasa de derivación correcta a revisión humana ante ambigüedad o falta de datos.
6. **Rendimiento operativo:** Latencia mediana (p50), percentil p95, consumo de memoria RAM y errores.

### Reglas Metodológicas Inmutables:
- **NUNCA** presentar una prueba con mocks como resultado de evaluación real del modelo.
- **NUNCA** presentar un JSON sintácticamente válido como una decisión semánticamente correcta.
- **NUNCA** registrar un fallo de infraestructura (timeout de Docker, caída de memoria) como exactitud 0% del modelo; debe catalogarse como error de infraestructura y registrarse como `null`.
- **NUNCA** publicar un reporte como evaluación final si `completed_cases < attempted_cases`.
- **Toda evaluación real debe registrar:** `evaluation_mode: "real_model"`, nombre y digest del modelo, `dataset_version`, `prompt_version`, parámetros de inferencia, timestamps UTC, `trace_id`, latencia en milisegundos y taxonomía de errores.

---

## 9. Política Estricta de Git y Autoría
- **No commits sin confirmación:** Prohibido ejecutar `git commit` sin la autorización humana explícita del usuario.
- **No push sin confirmación independiente:** Prohibido ejecutar `git push` sin una autorización humana separada, posterior y explícita, incluso si el commit ya fue autorizado.
- **Inspección Pre-Commit Obligatoria:** Antes de solicitar la confirmación de un commit, el agente debe mostrar obligatoriamente:
  ```bash
  git status --short
  git diff --staged
  git diff --check
  ```
  y proponer un mensaje breve, descriptivo y convencional (ej. `feat: ...`, `fix: ...`, `docs: ...`).
- **Identidad Local:** Usar exclusivamente el `user.name` y `user.email` configurados por el usuario en la máquina. Prohibido usar `--author`, `--trailer` o `-s` sin autorización.
- **Prohibición Total de Firmas de IA:** Queda terminantemente prohibido incorporar textos, badges, metadatos, trailers o enlaces de IA en commits, código, documentación, comentarios, PRs o issues.
  - *Términos estrictamente prohibidos:* `Generated by AI`, `Generated with Antigravity`, `Created by AGY`, `Co-Authored-By`, `Co-authored-by`, `Assisted-by`, `AI-assisted`, `Claude`, `Gemini`, `ChatGPT`, `OpenAI`, `Anthropic`.

---

## 10. Comandos Peligrosos Prohibidos
Salvo autorización humana explícita, individual y adicional para una situación de emergencia justificada, está **terminantemente prohibido ejecutar**:
- `rm -rf` indiscriminado sobre directorios del proyecto o del sistema.
- `git reset --hard`, `git clean -xfd`, `git restore .`, `git checkout --`.
- `docker system prune -a`, `docker builder prune -a`, `docker volume rm`.
- `docker compose down -v` (destrucción de volúmenes persistentes).
- Borrar o purgar imágenes de modelos descargados.
- Escribir en rutas fuera de la raíz del repositorio.
- Acceder, buscar o modificar el código fuente del simulador WellProdSim/BESA.
- `git push` hacia repositorios remotos.

---

## 11. Confirmación Humana Obligatoria
El agente debe detenerse y solicitar confirmación humana previa antes de:
- Modificar contratos públicos de la API o firmas de endpoints.
- Alterar o versionar nuevos schemas JSON / Pydantic.
- Modificar los prompts o configuraciones de inferencia del baseline.
- Modificar o sustituir el dataset de evaluación baseline (`test-cases.json`).
- Modificar `compose.yaml` o Dockerfiles.
- Modificar el [Makefile](file:///Volumes/ADATA%20SD620/Programacion%207.0/universidad/proyecto%20de%20grado/Prueba-llm-local/Makefile).
- Instalar nuevas dependencias en `pyproject.toml` o `package.json`.
- Crear o configurar herramientas MCPs o hooks de Git.
- Disparar suites de evaluación masivas o de larga duración.
- Consolidar commits en Git.
- Mover o eliminar archivos existentes.

---

## 12. Formato Obligatorio de Respuesta de AGY
Para tareas que involucren análisis, planificación o modificaciones de código, las respuestas deben estructurarse en dos fases:

### Fase de Propuesta:
```markdown
## PLAN
- Objetivo:
- Archivos que se inspeccionarán:
- Elementos existentes reutilizables:
- Archivos que se modificarán:
- Archivos que se crearán:
- Riesgos:
- Confirmación requerida:
```

### Fase Posterior a la Aprobación y Ejecución:
```markdown
## RESULTADO
- Cambios realizados:
- Archivos modificados:
- Elementos reutilizados:
- Pruebas ejecutadas:
- Resultados:
- Riesgos pendientes:
- Decisiones pendientes:
- Siguiente acción mínima:
```
*Prohibido declarar tareas como completadas sin evidencia verificable ni ejecutar cambios fuera del alcance formalmente acordado.*
