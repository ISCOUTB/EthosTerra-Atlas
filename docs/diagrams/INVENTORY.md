# INVENTARIO TÉCNICO Y TRAZABILIDAD DE DIAGRAMAS ARQUITECTÓNICOS

**Proyecto:** Framework Híbrido de Agentes Emocionales eBDI con Micro-LLM para la Simulación de Decisiones Agronómicas en Pequeños Productores
**Institución:** Universidad Tecnológica de Bolívar (UTB) — Maestría en Ingeniería
**Hito Vigente:** Bloques B1 a B5 cerrados (Semana 8). Preparación formal para Bloque B6 (Corpus Agronómico de Campo).
**Entorno de Ejecución:** Offline-first en hardware local Apple Silicon (MacBook Air M4, 16 GB).
**Modelo Oficial:** `ai/gemma4:E4B` (cuantización `MOSTLY_Q4_K_M`, digest `sha256:533eb3ccab62`) sobre Docker Model Runner (DMR).
**Convención Visual de Estados:**
- 🟩 **IMPLEMENTADO (Verde):** Componentes, contratos, flujos y compuertas operativas y probadas en el repositorio.
- 🟨 **PARCIAL / DEV SET / PLANIFICACIÓN (Ámbar):** Casos y fronteras en proceso de diseño o restringidos al conjunto de desarrollo agronómico (dev set).
- ⬜ **PENDIENTE (Gris rayado):** Bloques futuros (B7 integración con simulador BESA en vivo, servidor institucional GPU 24 GB, ciclo BDI en simulación).

---

## 1. Métricas Maestras de Línea Base y Evidencia Científica

Todas las cifras plasmadas en los diagramas y en este inventario provienen estrictamente de los artefactos oficiales de evaluación (`outputs/reports/`):

| Parámetro / Métrica | Valor Exacto Registrado | Fuente de Evidencia en el Repositorio |
| :--- | :--- | :--- |
| **Casos Totales Evaluados** | 30 casos (`v2_week7_30cases`) | `outputs/reports/manifest_week7.json` |
| **Distribución de Casos** | 8 puros, 12 conflictivos, 10 ambiguos/unclear | `outputs/reports/report_week7.json` |
| **Composición Muestral** | 20 casos legacy + 10 casos agronómicos de desarrollo | `outputs/reports/manifest_week7.json` |
| **Pruebas Unitarias** | 53/53 aprobadas (100%) | `outputs/reports/validation_report_week7.json` |
| **Disponibilidad de Inferencia** | 1.00 (30/30 exitosas, 0 caídas, 0 HTTP 500/422) | `outputs/reports/report_week7.json` |
| **Casos Resueltos por Hooks** | 21 casos (bypass determinista sin invocar LLM) | `outputs/reports/report_week7.json` (`latency_breakdown`) |
| **Casos Resueltos por LLM** | 9 casos (inferencia semántica real con Gemma 4 E4B) | `outputs/reports/report_week7.json` (`latency_breakdown`) |
| **Latencia Promedio Global** | 16.518,39 ms (16,52 s) | `outputs/reports/report_week7.json` |
| **Latencia Mediana (p50)** | 5,00 ms (gobernada por el bypass determinista) | `outputs/reports/report_week7.json` |
| **Latencia Percentil 95 Agregada**| 68.480,29 ms (sobre población total $N=30$) | `outputs/reports/report_week7.json` |
| **Latencia Promedio Hooks** | 5,00 ms (p50: 5,00 ms, p95: 5,00 ms) | `outputs/reports/report_week7.json` |
| **Latencia Promedio LLM** | 55.049,64 ms (p50: 55.663,81 ms) | `outputs/reports/report_week7.json` |
| **Latencia Percentil 95 LLM** | 69.124,17 ms (sobre subconjunto LLM $N=9$) | `outputs/reports/report_week7.json` |
| **Tasa de Alucinación** | 0.00% (cero variables ni datos inventados) | `outputs/reports/manifest_week7.json` |
| **Trazabilidad de Fuentes** | 1.00 (100% de casos con source_refs y citas) | `outputs/reports/validation_report_week7.json` |
| **Estado de Compatibilidad** | `runtime_compatible = unknown` | `outputs/reports/manifest_week7.json` |
| **Estado de Ejecución Simulada**| `simulation_execution_status = not_executed` | `outputs/reports/manifest_week7.json` |
| **Salvedad de Generalización** | *Dev set caveat*: 10 casos agronómicos son muestra de desarrollo; exactitud 1.0 no generalizable | `outputs/reports/report_week7.json` (`sample_caveat`) |

### Justificación Estadística de la Discrepancia en p95:
Existe una diferencia numérica aparente entre el **p95 Agregado (68.480,29 ms)** y el **p95 de LLM (69.124,17 ms)**. Esta diferencia es matemáticamente esperada y se origina exclusivamente en la diferencia de poblaciones analizadas ($N = 30$ vs. $N = 9$):
1. **Percentil 95 Agregado ($N = 30$):** Se calcula sobre la mezcla híbrida global compuesta por 21 observaciones con latencia determinista de 5,00 ms y 9 observaciones con inferencia neuronal. Al ordenar las 30 muestras, la posición del percentil 95 ($0.95 \times 30 = 28.5$) se interpola en la distribución combinada, resultando en 68.480,29 ms.
2. **Percentil 95 del Subconjunto LLM ($N = 9$):** Se calcula exclusivamente sobre las 9 llamadas neuronales reales reportadas en `outputs/reports/report_week7.json` (`llm_latency_avg_ms: 55.049,64 ms`, `llm_latency_p50_ms: 55.663,81 ms`, `llm_latency_p95_ms: 69.124,17 ms`). La posición del percentil ($0.95 \times 9 = 8.55$) se evalúa únicamente sobre la población de 9 llamadas al micro-LLM. Los valores individuales ordenados correspondientes (registrados en `outputs/reports/b4_case_traceability.json`) son: 34.231,23 ms, 36.519,42 ms, 50.587,46 ms, 53.507,20 ms, 55.663,81 ms (p50), 61.139,54 ms, 66.193,67 ms, 68.480,29 ms y 69.124,17 ms.

Ambas métricas son reproducibles y reflejan honestamente dos perspectivas complementarias: el comportamiento del sistema monolítico completo frente al costo computacional puro del modelo neuronal.

---

## 2. Inventario Detallado por Diagrama

### Figura D1. Arquitectura General por Capas del Sistema Híbrido eBDI
- **Archivos Fuente:** `docs/diagrams/src/d01_arch_layers_es.mmd`, `d01_arch_layers_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d01_arch_layers_es.svg`, `.png`, `d01_arch_layers_en.svg`, `.png`
- **Propósito:** Mostrar la estructura modular hexagonal en 7 capas funcionales: Presentación (React), Exposición (FastAPI), Aplicación/Servicios, Dominio/Contratos, Inferencia Híbrida (DMR), Almacenamiento/Sandbox local, y la frontera desacoplada hacia el simulador.
- **Evidencia en Repositorio:**
  - `apps/ui/src/App.tsx`, `DocumentPipelineView.tsx`, `Clasificador.tsx`
  - `apps/api/src/api/v2_routes.py`, `apps/api/src/api/main.py`
  - `apps/api/src/application/approval_gate.py`, `canonical_hasher.py`, `yaml_generator.py`, `yaml_validator.py`, `simulator_sandbox_service.py`
  - `apps/api/src/domain/v2/action_catalog_service.py`
  - `apps/api/src/adapters/dmr_gateway.py`, `apps/api/src/application/hooks.py`
  - `outputs/experiments/exp_vertical_001/`
- **Estado de Componentes:**
  - *Implementado:* Capas de UI, API, Servicios, Dominio, Inferencia Híbrida y Almacenamiento Sandbox.
  - *Pendiente:* Simulador WellProdSim/EthosTerra en vivo y ciclo BDI en tiempo de ejecución (diferidos a B7 / Semanas 10–12).
- **Elementos "No Verificado":** *Ninguno*. Todos los componentes existen y fueron inspeccionados en código.

---

### Figura D2. Contexto del Sistema (C4 Nivel 1)
- **Archivos Fuente:** `docs/diagrams/src/d02_c4_context_es.mmd`, `d02_c4_context_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d02_c4_context_es.svg`, `.png`, `d02_c4_context_en.svg`, `.png`
- **Propósito:** Delimitar las fronteras del sistema, sus actores humanos (investigador, evaluadores) y los sistemas externos (fuentes de campo, runtime DMR offline y simulador EthosTerra desacoplado).
- **Evidencia en Repositorio:**
  - `docs/skills-audit.md`, `AGENTS.md` (Gobierno y actores del proyecto)
  - `outputs/experiments/exp_vertical_001/sources/diario_campesino_preparacion.txt` (fuentes de texto)
  - `Makefile` (comandos `doctor`, `pull-model`, `health` hacia DMR)
- **Estado de Componentes:**
  - *Implementado:* Actores, frontera de hardware local, ingestión documental y DMR.
  - *Pendiente:* Integración con simulador WellProdSim/Python BESA (fuera del repositorio).
- **Elementos "No Verificado":** *Ninguno*.

---

### Figura D3. Componentes del Backend (C4 Nivel 3)
- **Archivos Fuente:** `docs/diagrams/src/d03_c4_components_es.mmd`, `d03_c4_components_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d03_c4_components_es.svg`, `.png`, `d03_c4_components_en.svg`, `.png`
- **Propósito:** Detallar los módulos internos del backend en `apps/api/src/`, especificando routers, esquemas Pydantic V2, catálogo de 17 acciones, hasher canónico, compuertas de seguridad y adaptadores.
- **Evidencia en Repositorio:**
  - `apps/api/src/api/main.py`, `v2_routes.py`
  - `apps/api/src/domain/schemas.py`, `v2/document_schemas.py`, `v2/operational_schemas.py`
  - `apps/api/src/domain/v2/action_catalog_service.py` y `catalogs/actions_catalog_v1.json` (17 acciones formales)
  - `apps/api/src/application/canonical_hasher.py`, `approval_gate.py`, `yaml_generator.py`, `yaml_validator.py`, `expression_validator.py`, `simulator_sandbox_service.py`, `metrics_service.py`
  - `apps/api/src/ports/model_gateway.py`, `adapters/dmr_gateway.py`, `application/hooks.py`
- **Estado de Componentes:** *100% Implementado*.
- **Elementos "No Verificado":** *Ninguno*. Todos los imports y clases fueron validados contra el código fuente.

---

### Figura D4. Flujo del Clasificador Híbrido (Vistas D4a y D4b)
- **Archivos Fuente:**
  - Vista Global: `docs/diagrams/src/d04_classifier_flow_es.mmd`, `d04_classifier_flow_en.mmd`
  - Vista D4a (Parte 1): `docs/diagrams/src/d04a_classifier_flow_es.mmd`, `d04a_classifier_flow_en.mmd`
  - Vista D4b (Parte 2): `docs/diagrams/src/d04b_classifier_flow_es.mmd`, `d04b_classifier_flow_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d04a_classifier_flow_*.png`, `d04b_classifier_flow_*.png`
- **Propósito y División:**
  - **D4a (Parte 1):** Ingesta de solicitud, normalización contextual y evaluación determinista mediante hooks in-memory (21/30 casos resueltos a 5,0 ms). Conecta con el nodo de bifurcación neuronal.
  - **D4b (Parte 2):** Retoma desde el nodo de bifurcación ante ambigüedad, modelando la selección de prompt Zero-Trust, inferencia con Gemma 4 E4B vía DMR (9/30 casos a 55 s), validación Pydantic V2 y emisión de veredictos o derivación a revisión humana.
- **Evidencia en Repositorio:**
  - `apps/api/src/adapters/dmr_gateway.py` (método `propose_classification`)
  - `apps/api/src/application/hooks.py` (`validate_invariants`, `should_use_conflict_prompt`, `extract_conflict_sources`)
  - `apps/api/src/domain/prompts/case_pure_v1.txt`, `case_conflict_v1.txt`
  - `outputs/reports/report_week7.json`
- **Estado de Componentes:** *100% Implementado*.
- **Elementos "No Verificado":** *Ninguno*.

---

### Figura D5. Flujo del Caso Conflictivo (Bloque B4 - Vistas D5a y D5b)
- **Archivos Fuente:**
  - Vista Global: `docs/diagrams/src/d05_conflict_flow_es.mmd`, `d05_conflict_flow_en.mmd`
  - Vista D5a (Parte 1): `docs/diagrams/src/d05a_conflict_flow_es.mmd`, `d05a_conflict_flow_en.mmd`
  - Vista D5b (Parte 2): `docs/diagrams/src/d05b_conflict_flow_es.mmd`, `d05b_conflict_flow_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d05a_conflict_flow_*.png`, `d05b_conflict_flow_*.png`
- **Propósito y División:**
  - **D5a (Parte 1):** Detección de colisión de intenciones incompatibles ante detonante común y trazabilidad forense de procedencia (`context_field` vs `document`). Conecta con el nodo de formulación de alternativas.
  - **D5b (Parte 2):** Formulación de alternativas de mitigación (A/B/C), principio inviolable de no-decisión (`selected_alternative = null`) y obligatoriedad de escalamiento hacia arbitraje humano (`requires_human_review = true`).
- **Evidencia en Repositorio:**
  - `contracts/schemas/caso-conflictivo.schema.json`
  - `apps/api/src/domain/schemas.py` (`CasoConflictivo`, `FuenteEnColision`)
  - `apps/api/src/domain/prompts/case_conflict_v1.txt`
  - `outputs/reports/b4_conflict_cases.json`, `b4_case_traceability.json`
- **Estado de Componentes:**
  - *Implementado:* Detección, extracción de fuentes, opciones y escalamiento.
  - *Parcial / Salvedad:* La evaluación agronómica se realizó sobre 10 casos de desarrollo (dev set).
- **Elementos "No Verificado":** *Ninguno*.

---

### Figura D6. Diagrama de Estados del Documento Operativo (Vistas D6a y D6b)
- **Archivos Fuente:**
  - Vista Global: `docs/diagrams/src/d06_document_lifecycle_es.mmd`, `d06_document_lifecycle_en.mmd`
  - Vista D6a (Parte 1): `docs/diagrams/src/d06a_document_lifecycle_es.mmd`, `d06a_document_lifecycle_en.mmd`
  - Vista D6b (Parte 2): `docs/diagrams/src/d06b_document_lifecycle_es.mmd`, `d06b_document_lifecycle_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d06a_document_lifecycle_*.png`, `d06b_document_lifecycle_*.png`
- **Propósito y División:**
  - **D6a (Parte 1):** Ciclo inicial desde `Borrador` hasta `Analizado`, estructuración de artefactos (`GoalSpecArtifact`, `PlanSpecArtifact`) y rutas de bloqueo ante esquemas inválidos o intenciones contradictorias (`Requiere_Revision`, `Rechazado`). Conecta con el punto de control de aprobación.
  - **D6b (Parte 2):** Compuertas criptográficas post-análisis: transición a `Aprobado` vía firma humana con hash canónico SHA-256 de 11 campos, generación de YAML confinado, instalación con respaldo (.tar.gz) en sandbox y bloqueo HTTP 403 / rollback atómico ante alteración posterior (tampering).
- **Evidencia en Repositorio:**
  - `apps/api/src/domain/v2/operational_schemas.py` (`OperationalDocumentSchema`)
  - `apps/api/src/application/approval_gate.py` (`assert_yaml_generation_allowed`, `YAMLGenerationBlocked`)
  - `apps/api/src/application/canonical_hasher.py` (11 campos del hash canónico)
  - `apps/api/src/api/v2_routes.py`
- **Estado de Componentes:** *100% Implementado*.
- **Nota de Sintaxis y Leyenda Tricolor:** Las vistas operativas D6a y D6b están implementadas bajo la gramática `flowchart`, lo que permite incorporar la leyenda tricolor unificada con clases CSS de estado (`:::impl`, `:::partial`, `:::pending`) y bloques de compuertas de seguridad (HTTP 403 / tampering / rollback), preservando estrictamente la correspondencia contractual con los identificadores de estado en español en ambas versiones lingüísticas.

---

### Figura D7. Secuencia del Approval Gate, Compuertas de Seguridad y Sandbox
- **Archivos Fuente:** `docs/diagrams/src/d07_approval_gate_seq_es.mmd`, `d07_approval_gate_seq_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d07_approval_gate_seq_es.svg`, `.png`, `d07_approval_gate_seq_en.svg`, `.png`
- **Propósito:** Ilustrar las interacciones temporales entre el Investigador, la UI, la API, el Approval Gate, el Generador YAML y el Servicio de Sandbox en 5 escenarios: intento no autorizado (403), aprobación legítima, instalación confinada con backup, detección de tampering y rollback atómico.
- **Evidencia en Repositorio:**
  - `apps/api/src/application/approval_gate.py`
  - `apps/api/src/application/canonical_hasher.py`
  - `apps/api/src/application/yaml_generator.py`
  - `apps/api/src/application/simulator_sandbox_service.py` (`validate_target_sandbox`, `InstallationSecurityError`, `create_instance_backup`, `rollback_instance`)
- **Estado de Componentes:** *100% Implementado*.
- **Nota Sintáctica de Mermaid:** Los diagramas de secuencia (`sequenceDiagram`) no soportan bloques visuales de subgrafo ni clases CSS arbitrarias para leyendas tricolores. Todos los participantes y llamadas representadas corresponden a servicios y métodos **100% Implementados**.

---

### Figura D8. Modelo de Datos, Contratos Pydantic V2 y Estados Epistemológicos
- **Archivos Fuente:** `docs/diagrams/src/d08_data_model_contracts_es.mmd`, `d08_data_model_contracts_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d08_data_model_contracts_es.svg`, `.png`, `d08_data_model_contracts_en.svg`, `.png`
- **Propósito:** Diagrama de clases formal que describe las estructuras de datos: `GoalSpecArtifact`, `PlanSpecArtifact`, `StepSpecSchema`, `ContributionRulesSchema`, `OperationalDocumentSchema`, `DocumentAnalysisSchema`, `ExtractedKnowledge`, `EvidenceSpan` y los 6 estados epistemológicos (`observed`, `inferred`, `proposed`, `required`, `unknown`, `not_stated`).
- **Evidencia en Repositorio:**
  - `apps/api/src/domain/v2/document_schemas.py`
  - `apps/api/src/domain/v2/operational_schemas.py`
  - `contracts/schemas/caso-puro.schema.json`, `caso-conflictivo.schema.json`
- **Estado de Componentes:** *100% Implementado*.
- **Nota Sintáctica de Mermaid:** Los diagramas de clases (`classDiagram`) siguen el estándar estricto de UML y no admiten contenedores de leyenda tipo flowchart. Todas las clases, enums y atributos modelados existen físicamente en los esquemas Pydantic V2 del proyecto (**100% Implementados**).

---

### Figura D9. Despliegue y Entorno de Ejecución Local Offline-First (Vistas D9a y D9b)
- **Archivos Fuente:**
  - Vista Global: `docs/diagrams/src/d09_deployment_env_es.mmd`, `d09_deployment_env_en.mmd`
  - Vista D9a (Parte 1): `docs/diagrams/src/d09a_deployment_env_es.mmd`, `d09a_deployment_env_en.mmd`
  - Vista D9b (Parte 2): `docs/diagrams/src/d09b_deployment_env_es.mmd`, `d09b_deployment_env_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d09a_deployment_env_*.png`, `d09b_deployment_env_*.png`
- **Propósito y División:**
  - **D9a (Parte 1):** Topología de procesos locales en la estación de trabajo física: interfaz React Vite (`:5173`), API FastAPI (`:8000`), runtimes de desarrollo (`uv`, `pnpm`) y puertos de conexión inter-proceso.
  - **D9b (Parte 2):** Contenerización y recursos de hardware: asignación de memoria unificada en MacBook Air M4 (16 GB), contenedor Docker Model Runner (`:11434`), carga offline de `ai/gemma4:E4B` y salvedad sobre el servidor institucional GPU de 24 GB reservado para benchmarking futuro.
- **Evidencia en Repositorio:**
  - `Makefile` (objetivos `doctor`, `pull-model`, `start`, `health`)
  - `compose.yaml` (servicios locales)
  - `apps/api/Dockerfile`, `apps/ui/Dockerfile`
  - `docs/skills-audit.md` (especificación de hardware M4)
- **Estado de Componentes:**
  - *Implementado:* Entorno M4, runtimes locales uv/pnpm, puertos y DMR.
  - *Pendiente:* Servidor institucional con GPU de 24 GB.
- **Elementos "No Verificado":** *Ninguno*.

---

### Figura D10. Trazabilidad Forense de Artefactos, Evidencias y Reportes
- **Archivos Fuente:** `docs/diagrams/src/d10_artifact_traceability_es.mmd`, `d10_artifact_traceability_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d10_artifact_traceability_es.svg`, `.png`, `d10_artifact_traceability_en.svg`, `.png`
- **Propósito:** Trazar el hilo conductor desde el texto del diario de campo hasta los manuscritos LaTeX, pasando por los JSON de análisis y aprobación, los YAMLs generados, backups del sandbox, matrices de confusión y reportes cuantitativos.
- **Evidencia en Repositorio:**
  - `outputs/experiments/exp_vertical_001/` (fuentes, análisis, aprobados, yamls, backups)
  - `outputs/reports/manifest_week7.json`, `report_week7.json`, `validation_report_week7.json`, `b4_confusion_matrix.json`, `b4_case_traceability.json`, `b4_conflict_cases.json`
  - `docs/informe_semana_7_es.tex`, `week_7_report_en.tex`
- **Estado de Componentes:** *100% Implementado*.
- **Elementos "No Verificado":** *Ninguno*.

---

### Figura D11. Mapa de Estado y Hoja de Ruta de Desarrollo (Bloques B1 a B13)
- **Archivos Fuente:** `docs/diagrams/src/d11_status_roadmap_es.mmd`, `d11_status_roadmap_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d11_status_roadmap_es.svg`, `.png`, `d11_status_roadmap_en.svg`, `.png`
- **Propósito:** Mostrar la progresión global del proyecto de grado a lo largo de 13 bloques, ubicando con precisión el hito cerrado (B1–B5, con 79/79 pruebas unitarias aprobadas), la etapa inmediata (B6: Corpus agronómico de campo) y los bloques futuros pendientes (B7–B13).
- **Evidencia en Repositorio:**
  - `AGENTS.md` (planificación por semanas)
  - `docs/b5_manual_intents.md` (nota técnica del incremento B5)
  - `tests/unit/test_manual_intents.py` (26 pruebas de B5 aprobadas)
  - `outputs/reports/report_week6.json`, `report_week7.json`
- **Estado de Componentes:**
  - *Cerrado:* B1 a B5 (100% de la suite de 79 pruebas en verde).
  - *Próximo / En Planificación:* B6.
  - *Pendiente:* B7 a B13.
- **Elementos "No Verificado":** *Ninguno*.

---

### Figura D12. Frontera Arquitectónica para la Integración de B5
- **Archivos Fuente:** `docs/diagrams/src/d12_b5_boundary_es.mmd`, `d12_b5_boundary_en.mmd`
- **Artefactos Exportados:** `docs/diagrams/out/d12_b5_boundary_es.svg`, `.png`, `d12_b5_boundary_en.svg`, `.png`
- **Propósito y Estructura:** Delimitar la arquitectura desacoplada del Bloque B5 (CRUD Manual de Intenciones): puntos de montaje en routers (`v2_routes.py` e `intents_routes.py`), control de acceso estricto por lista blanca (`validate_identifier`), persistencia desacoplada en `outputs/intents/` con escrituras atómicas (`ManualIntentService`), papelera de borrado lógico con retención de 30 días (`.trash/`), purga bajo demanda y al arranque, compuertas de seguridad existentes (`Approval Gate`, `validate_target_sandbox`) y la zona protegida de solo lectura del simulador (`EthosTerra_original/`) donde rige la prohibición inmutable de 0 escrituras al núcleo. El diagrama está estructurado en 2 niveles compactos (`flowchart TD`), con $W \approx 770\text{ px}$ y $H \approx 1605\text{ px}$, garantizando texto efectivo $\ge 6,24\text{ pt}$ en página A4.
- **Evidencia en Repositorio:**
  - `apps/api/src/api/intents_routes.py` y `v2_routes.py`
  - `apps/api/src/application/manual_intent_service.py`
  - `apps/api/src/domain/v2/intent_schemas.py`
  - `apps/api/src/application/approval_gate.py`
  - `apps/api/src/application/simulator_sandbox_service.py` (`validate_target_sandbox`)
  - `tests/unit/test_manual_intents.py`
  - `outputs/intents/` (espacio de almacenamiento desacoplado y `.trash/`)
- **Estado de Componentes:**
  - *Existente / Implementado:* Barreras de protección, Approval Gate, zona de solo lectura `EthosTerra_original/`, Registro Desacoplado de Intenciones y Papelera de Borrado Lógico (30 Días).
  - *Punto de Conexión en Planificación (Ámbar):* B6 (Corpus Agronómico de Campo).
- **Elementos "No Verificado":** *Ninguno*.

---

## 3. Distribución Editorial de Figuras en la Tesis

Conforme a la decisión de diseño editorial:
1. **Cuerpo Principal de la Tesis:**
   - **Figura D1:** Arquitectura General por Capas (Capítulo de Marco Arquitectónico).
   - **Figura D4a:** Flujo del Clasificador Híbrido — Parte 1: Ingesta y Bypass Determinista (Capítulo de Metodología de Inferencia eBDI).
   - **Figura D4b:** Flujo del Clasificador Híbrido — Parte 2: Inferencia Micro-LLM y Validación (Capítulo de Metodología de Inferencia eBDI).
   - **Figura D6a:** Flujo de Estados del Documento — Parte 1: Borrador a Analizado y Bloqueos (Capítulo de Gobernanza y Seguridad).
   - **Figura D6b:** Flujo de Estados del Documento — Parte 2: Aprobación, Hash e Instalación (Capítulo de Gobernanza y Seguridad).
   - **Figura D11:** Mapa de Estado y Roadmap B1–B13 (Capítulo de Planificación y Resultados).

2. **Anexo Metodológico y Técnico:**
   - **Figura D2:** Contexto del Sistema (C4 Nivel 1).
   - **Figura D3:** Componentes del Backend (C4 Nivel 3).
   - **Figura D5a:** Flujo del Caso Conflictivo — Parte 1: Detección y Fuentes (Detalle B4).
   - **Figura D5b:** Flujo del Caso Conflictivo — Parte 2: Alternativas y Escalamiento (Detalle B4).
   - **Figura D7:** Secuencia del Approval Gate y Sandbox.
   - **Figura D8:** Modelo de Datos y Contratos Pydantic V2.
   - **Figura D9a:** Despliegue Físico y Runtimes en MacBook Air M4 — Parte 1: Procesos y Puertos.
   - **Figura D9b:** Despliegue Físico y Runtimes en MacBook Air M4 — Parte 2: Contenerización y Recursos.
   - **Figura D10:** Trazabilidad Forense de Artefactos y Manifiestos.
   - **Figura D12:** Vista de Frontera Arquitectónica para Bloque B5.

3. **Artefactos Globales Conservados en `out/` como Referencia Técnica:**
   - **Figuras Globales D4, D5, D6 y D9:** Se excluyen formalmente de `figures.tex` para garantizar el estándar de legibilidad tipográfica en página impresa ($\ge 6\text{ pt}$ en todas las vistas). Sus artefactos completos permanecen compilados y versionados en `docs/diagrams/out/` (`d04_classifier_flow_*`, `d05_conflict_flow_*`, `d06_document_lifecycle_*`, `d09_deployment_env_*`) para consulta técnica integral sin división.

---

## 4. Registro de Ausencia de Secretos y Rutas Absolutas

En estricto cumplimiento de las reglas del proyecto:
1. **Cero Rutas Absolutas:** Ningún diagrama `.mmd`, imagen exportada ni documento Markdown/LaTeX contiene rutas absolutas del sistema de archivos local. Todas las referencias se realizan mediante rutas relativas al repositorio (`apps/api/`, `outputs/`, `data/ebdi/`, etc.).
2. **Cero Secretos y Credenciales:** Ningún archivo contiene tokens, claves API, contraseñas ni variables de entorno sensibles.
3. **Cero Firmas de IA:** Ningún archivo contiene metadatos, firmas ni menciones de herramientas de generación artificial.

---

## 5. Tabla de Mediciones Reales de ViewBox, Escala y Tipografía Efectiva

La siguiente tabla presenta la medición directa de las dimensiones naturales del `viewBox` ($W \times H$) leídas de cada uno de los 40 archivos SVG en `docs/diagrams/out/`. Se calcula la escala de renderizado a PNG ($\text{escala} = 3136 / W$) y el tamaño tipográfico resultante en el documento PDF A4 compilado ($\text{pt} = \text{base\_px} \times \text{escala} \times 0.1277$), evaluado tanto para nodos estándar (12 px) como para nodos prominentes (14 px):

| No | Archivo Exportado | Ancho Natural $W$ | Alto Natural $H$ | Escala ($3136/W$) | Texto 12px | Texto 14px | Estado de Legibilidad |
| :-: | :--- | :-: | :-: | :-: | :-: | :-: | :--- |
| 01 | `d01_arch_layers_en.svg` | 782.4 px | 1132.0 px | 4.01x | 6.14 pt | 7.17 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 02 | `d01_arch_layers_es.svg` | 775.3 px | 1195.0 px | 4.04x | 6.20 pt | 7.23 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 03 | `d02_c4_context_en.svg` | 580.4 px | 1005.0 px | 5.40x | 8.28 pt | 9.66 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 04 | `d02_c4_context_es.svg` | 576.2 px | 1073.3 px | 5.44x | 8.34 pt | 9.73 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 05 | `d03_c4_components_en.svg` | 610.9 px | 990.0 px | 5.13x | 7.87 pt | 9.18 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 06 | `d03_c4_components_es.svg` | 628.6 px | 990.0 px | 4.99x | 7.65 pt | 8.92 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 07 | `d04_classifier_flow_en.svg` | 1272.4 px | 2850.2 px | 2.46x | 3.78 pt | 4.41 pt | Referencia global en `out/` |
| 08 | `d04_classifier_flow_es.svg` | 1289.7 px | 2936.2 px | 2.43x | 3.73 pt | 4.35 pt | Referencia global en `out/` |
| 09 | `d04a_classifier_flow_en.svg` | 553.9 px | 1412.3 px | 5.66x | 8.68 pt | 10.12 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 10 | `d04a_classifier_flow_es.svg` | 564.3 px | 1454.3 px | 5.56x | 8.52 pt | 9.94 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 11 | `d04b_classifier_flow_en.svg` | 653.8 px | 1931.0 px | 4.80x | 7.35 pt | 8.57 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 12 | `d04b_classifier_flow_es.svg` | 653.8 px | 1931.0 px | 4.80x | 7.35 pt | 8.57 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 13 | `d05_conflict_flow_en.svg` | 1004.0 px | 2666.4 px | 3.12x | 4.79 pt | 5.58 pt | Referencia global en `out/` |
| 14 | `d05_conflict_flow_es.svg` | 1004.0 px | 2778.2 px | 3.12x | 4.79 pt | 5.58 pt | Referencia global en `out/` |
| 15 | `d05a_conflict_flow_en.svg` | 620.0 px | 1938.3 px | 5.06x | 7.75 pt | 9.04 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 16 | `d05a_conflict_flow_es.svg` | 620.0 px | 2060.8 px | 5.06x | 7.75 pt | 9.04 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 17 | `d05b_conflict_flow_en.svg` | 600.0 px | 1389.0 px | 5.23x | 8.01 pt | 9.34 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 18 | `d05b_conflict_flow_es.svg` | 600.0 px | 1368.0 px | 5.23x | 8.01 pt | 9.34 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 19 | `d06_document_lifecycle_en.svg` | 1447.4 px | 3051.0 px | 2.17x | 3.32 pt | 3.87 pt | Referencia global en `out/` |
| 20 | `d06_document_lifecycle_es.svg` | 1445.5 px | 3072.0 px | 2.17x | 3.32 pt | 3.88 pt | Referencia global en `out/` |
| 21 | `d06a_document_lifecycle_en.svg` | 778.0 px | 1799.1 px | 4.03x | 6.18 pt | 7.21 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 22 | `d06a_document_lifecycle_es.svg` | 782.8 px | 1787.5 px | 4.01x | 6.14 pt | 7.16 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 23 | `d06b_document_lifecycle_en.svg` | 560.6 px | 1798.9 px | 5.59x | 8.57 pt | 10.00 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 24 | `d06b_document_lifecycle_es.svg` | 560.9 px | 1861.9 px | 5.59x | 8.57 pt | 10.00 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 25 | `d07_approval_gate_seq_en.svg` | 2627.0 px | 2245.0 px | 1.19x | 1.83 pt | 2.13 pt | Apaisado (`pdflscape`) |
| 26 | `d07_approval_gate_seq_es.svg` | 2589.5 px | 2247.0 px | 1.21x | 1.86 pt | 2.17 pt | Apaisado (`pdflscape`) |
| 27 | `d08_data_model_contracts_en.svg` | 1253.4 px | 1054.0 px | 2.50x | 3.83 pt | 4.47 pt | Apaisado (`pdflscape`, $7.82\text{ pt}$) |
| 28 | `d08_data_model_contracts_es.svg` | 1253.4 px | 1054.0 px | 2.50x | 3.83 pt | 4.47 pt | Apaisado (`pdflscape`, $7.82\text{ pt}$) |
| 29 | `d09_deployment_env_en.svg` | 1244.6 px | 2239.6 px | 2.52x | 3.86 pt | 4.50 pt | Referencia global en `out/` |
| 30 | `d09_deployment_env_es.svg` | 1248.8 px | 2313.5 px | 2.51x | 3.85 pt | 4.49 pt | Referencia global en `out/` |
| 31 | `d09a_deployment_env_en.svg` | 692.0 px | 927.0 px | 4.53x | 6.94 pt | 8.10 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 32 | `d09a_deployment_env_es.svg` | 692.0 px | 927.0 px | 4.53x | 6.94 pt | 8.10 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 33 | `d09b_deployment_env_en.svg` | 558.8 px | 1270.0 px | 5.61x | 8.60 pt | 10.03 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 34 | `d09b_deployment_env_es.svg` | 539.1 px | 1270.0 px | 5.82x | 8.91 pt | 10.40 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 35 | `d10_artifact_traceability_en.svg` | 679.8 px | 1767.1 px | 4.61x | 7.07 pt | 8.25 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 36 | `d10_artifact_traceability_es.svg` | 679.8 px | 1806.7 px | 4.61x | 7.07 pt | 8.25 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 37 | `d11_status_roadmap_en.svg` | 655.0 px | 2042.0 px | 4.79x | 7.34 pt | 8.56 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 38 | `d11_status_roadmap_es.svg` | 636.9 px | 2168.0 px | 4.92x | 7.55 pt | 8.80 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 39 | `d12_b5_boundary_en.svg` | 765.2 px | 1563.0 px | 4.10x | 6.28 pt | 7.33 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
| 40 | `d12_b5_boundary_es.svg` | 770.0 px | 1605.0 px | 4.07x | 6.24 pt | 7.28 pt | CUMPLE ($\ge 6.0\text{ pt}$) |
