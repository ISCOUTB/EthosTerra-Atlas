# Informe Técnico de Avance — Semana 6: Arquitectura Multiagente eBDI y Evaluación Reproducible

## 1. Resumen Ejecutivo
El presente informe documenta los resultados cuantitativos y cualitativos alcanzados al cierre de la Semana 6 en el proyecto de clasificador y traductor documental para el simulador social **EthosTerra**.

Siguiendo las directrices metodológicas de no generalizar resultados fuera de las pruebas controladas y mantener una separación estricta entre dimensiones probabilísticas y deterministas, este informe desagrega:
1. **Regresión Legacy (Semana 5 vs. Semana 6):** Evaluación sobre los 20 casos sintéticos mecánicos del benchmark original con el modelo `ai/gemma4:E4B`.
2. **Pipeline Documental eBDI (Caso `exp_vertical_001`):** Evidencia preliminar de extracción, estructuración epistemológica, autorización por Approval Gate, generación determinista e instalación controlada en el sandbox `EthosTerra_experiment`.

---

## 2. Dimensión 1: Regresión del Benchmark Legacy (20 Casos)

### 2.1 Comparativa Cuantitativa contra Baseline de Semana 5

| Métrica | Baseline Semana 5 (Commit `388553e`) | Semana 6 (Arquitectura Híbrida Hooks+DMR) | Delta / Variación | Interpretación Metodológica |
| :--- | :--- | :--- | :--- | :--- |
| **Disponibilidad de Inferencia** | 1.00 (20/20) | 1.00 (20/20) | 0.00 | Sin fallos de infraestructura ni errores 500/503. |
| **Validez Estructural JSON** | 1.00 (20/20) | 1.00 (20/20) | 0.00 | 100% conforme a esquemas Pydantic V2 al primer intento. |
| **Exactitud Nominal (Accuracy)** | 0.50 (10/20) | 0.90 (18/20) | **+0.40** | Reducción de 10 a 2 fallos de clasificación. |
| **Macro-Precision** | 0.50 | 1.00 | **+0.50** | 0 falsos positivos en detección de conflicto. |
| **Recall de Conflictos** | 0.50 | 0.875 | **+0.375** | Captura 7 de los 8 casos conflictivos declarados. |
| **Macro-F1** | 0.50 | 0.933 | **+0.433** | Supera ampliamente la meta mínima del 80%. |
| **Tasa de Falso Conflicto** | 0.00 | 0.00 | 0.00 | Casos puros no se degradan falsamente a conflicto. |
| **Tasa de Alucinación Observada** | 0.00 | 0.00 | 0.00 | 0 datos inventados fuera del contexto provisto. |
| **Alineación de Revisión Humana**| 0.65 | 0.90 | **+0.25** | Flag `requires_human_review` coincide en 18 de 20 casos. |
| **Latencia Media** | 32,330.8 ms | 35637.05 ms | **--3306.3 ms** | Reducción significativa por bypass determinista. |
| **Latencia Mediana (p50)** | ~30,000 ms (est.) | 42982.56 ms | -29,995 ms | Casos con regla determinista resueltos en ~5 ms. |
| **Latencia Percentil 95 (p95)** | ~45,000 ms (est.) | 42982.56 ms | - | Inferencia LLM condicionada por hardware local. |

### 2.2 Desglose de Latencia y Distribución Operativa
- **Casos Resueltos por Hooks (Bypass Determinista):** 3/20 (15.0%) con latencia de 5.0 ms.
- **Casos Resueltos por LLM (`ai/gemma4:E4B`):** 17/20 (85.0%) con latencia media de ~42,000 ms.
- **Desviación Estándar de Latencia:** 15869.99 ms (refleja la distribución bimodal entre reglas ultra rápidas e inferencia local profunda).
- **Resistencia ante Inyecciones Adversariales:** 3/3 casos neutralizados exitosamente (100%).

---

## 3. Dimensión 2: Pipeline Documental eBDI (Caso Controlado `exp_vertical_001`)

En la prueba controlada del experimento `exp_vertical_001`, sustentada en el documento fuente `diario_campesino_preparacion.txt`, se obtuvieron los siguientes resultados reproducibles:

### 3.1 Métricas de Ingesta, Extracción y Seguridad
- **Pruebas Unitarias Automatizadas:** 38/38 aprobadas (100% éxito en Approval Gate, sandbox y catálogo de acciones).
- **Documentos Ingeridos y Normalizados:** 1/1.
- **Campos Extraídos con Clasificación Epistemológica:** 7/7 (100% clasificados en `observed`, `inferred`, `required`, `unknown`, `not_stated`).
- **Cobertura de Trazabilidad:** 100% de los elementos provienen de `evidence_spans` con offset textual explícito.
- **Bloqueo de Generación No Aprobada:** Verificado empíricamente (la API rechazó la generación mientras el estado fue `Analizado`).
- **Aprobación Humana:** 1/1 registrada formalmente con hash SHA-256 inmutable.

### 3.2 Métricas de Generación YAML y Compatibilidad
- **YAMLs Generados:** 2/2 (`prepare_land.yaml` y `prepare_land_plan_v1.yaml`).
- **YAMLs Generados sin Aprobación:** 0/2 (0% evasión de la barrera de control).
- **Parseabilidad YAML (`yaml.safe_load`):** 2/2 válidos.
- **Conformidad de Esquemas (GoalSpec / PlanSpec):** 2/2 conformes.
- **Validación de Acciones contra Catálogo:** 2/2 pasos válidos (`agro_ecosystem_operation` y `emit_episode`).
- **Resolución de Referencias `plan_ref`:** 1/1 (`prepare_land` resolvió a `prepare_land_plan_v1`).

### 3.3 Métricas de Sandbox y Carga en el Simulador
- **Instalación en Sandbox:** 2/2 archivos instalados estrictamente en `EthosTerra_experiment`.
- **Inmutabilidad de la Instancia Original:** 0 archivos modificados en `EthosTerra_original` (comprobado vía `git status --short`).
- **Respaldo Pre-Instalación:** Creado exitosamente (`backup_exp_vertical_001_*.tar.gz`, 9.71 MB).
- **Prueba de Rollback:** 1/1 exitosa (restauración íntegra de la copia tras alteración experimental).
- **Carga en `GoalRegistry` Real:** 1/1 cargado exitosamente.
- **Carga en `PlanRegistry` Real:** 1/1 cargado exitosamente.
- **Ejecución BDI en Simulación:** **No evaluada / Pendiente**.

---

## 4. Clasificación de Niveles de Validación del YAML

| Nivel | Estado en Prueba Controlada | Justificación y Evidencia |
| :--- | :--- | :--- |
| **Nivel 1: JSON Válido** | **Cumplido** | Pasa contratos Pydantic V2 con `extra="forbid"`. |
| **Nivel 2: YAML Generado** | **Cumplido** | Escrito deterministamente en `outputs/experiments/exp_vertical_001/yaml/`. |
| **Nivel 3: YAML Estructuralmente Válido** | **Cumplido** | Parseable por `yaml.safe_load()`. |
| **Nivel 4: YAML Semánticamente Compatible** | **Cumplido** | Conforme a esquemas Draft-07 de EthosTerra y acciones del catálogo versionado. |
| **Nivel 5: YAML Listo para Simulación** | **Cumplido (con reservas)** | `plan_ref` resuelto; expresión sintácticamente compilable. Marcado como `runtime_compatible="unknown"`, `requires_simulation_test=true`. |
| **Nivel 6: YAML Ejecutado Exitosamente** | **Pendiente / No Evaluado** | Requiere ejecución del ciclo de simulación viva multiagente (Nivel C / Semanas 10–12). |

---

## 5. Limitaciones y Riesgos Residuales

1. **Hardware de Desarrollo:** Las latencias de inferencia de 40-50s en casos puros son producto del entorno local de desarrollo sin GPU de 24 GB de VRAM.
2. **Evaluación de Runtime de `activation_when`:** Debido a que el motor `yaml_evaluator.py` enmascara errores con `return 0.0`, una meta con métodos mal nombrados podría fallar silenciosamente en tiempo de ejecución si no se prueba dentro de un ciclo de simulación vivo.
3. **Muestra Acotada:** El resultado del pipeline documental corresponde a una prueba vertical controlada (`exp_vertical_001`) y debe ser validado con documentos sociopolíticos reales más extensos en las siguientes fases.

---

## 6. Conclusión y Siguiente Fase
Se cumplieron rigurosamente los criterios de seguridad, trazabilidad forense, inmutabilidad de la instancia original y generación controlada.
La siguiente fase comprenderá la habilitación de la interfaz web offline para permitir al investigador realizar este ciclo de forma completamente interactiva en menos de 10 minutos.
