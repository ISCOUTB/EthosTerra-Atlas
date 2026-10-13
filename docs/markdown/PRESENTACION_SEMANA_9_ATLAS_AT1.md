# Semana 9 — Bloque B6: Corpus Agrario y Atlas Territorial AT-1

**Proyecto:** Clasificador y evaluador local de intenciones declarativas (EthosTerra / eBDI)
**Bloque:** B6 — Corpus Agrario, Atlas Territorial, Cuarentena Documental y Extracción Epistémica
**Estado:** Completado (commit `d17e44b`)
**Commit línea base:** `388553e` (Semana 5, inmutable)

---

## 1. Objetivo de la Semana 9

Consolidar el **Corpus Agrario de Campo, el Atlas Territorial (AT-1), la Cuarentena Documental y la Extracción Epistémica con Compilación YAML**, yendo más allá del plan original: se implementó además el protocolo de búsqueda adaptativa con retroalimentación humana y la subida manual de documentos.

### Entregables completados

- Consola geoespacial AT-1 que cubre los **15 municipios PDET de Montes de María** (DANE MGN 2024, DIVIPOLA, IDEAM, UPRA).
- Subsistema de **cuarentena documental** con integridad SHA-256 y compuertas de aprobación humana.
- Pipeline de **extracción epistémica de creencias eBDI** con `ai/gemma4:E4B` bajo verificación textual verbatim.
- **Compilación determinista** a especificaciones ejecutables `GoalSpec` y `PlanSpec` en `outputs/atlas/yaml/`.
- **Protocolo Human-in-the-Loop de descubrimiento adaptativo**: semillas oficiales autorizadas, justificativo técnico del agente, retroalimentación obligatoria al descartar y re-búsqueda de hasta 6 intentos con filtro anti-redundancia.
- Ergonomía de interfaz: tabs sticky y sub-vistas segmentadas sin scroll innecesario.

---

## 2. Los 3 Agentes Implementados

### 2.1. Agente de Descubrimiento Territorial — `DocumentDiscoveryAgent`

**Archivo:** `apps/atlas/agents/discovery_agent.py`

Agente **determinista (sin LLM)** encargado de correlacionar un territorio (DIVIPOLA, departamento, subregión PDET) con los instrumentos de política aplicables (PATR, PIDARET, PND, POT).

**Características técnicas:**

- **Lista blanca estricta de dominios institucionales** (`OFFICIAL_DOMAIN_SUFFIXES`): `.gov.co`, `renovacionterritorio.gov.co`, `adr.gov.co`, `dane.gov.co`, `dnp.gov.co`, `upra.gov.co`, `datos.gov.co`, `bolivar.gov.co`, `sucre.gov.co`.
- **Resolución jerárquica territorial**: DIVIPOLA → municipio → departamento → subregión PDET → nivel nacional, reutilizando `TerritoryResolver`.
- **Alcance dinámico PDET**: si el municipio es PDET, desbloquea automáticamente los ámbitos `PDET_01_MONTES_DE_MARIA` y derivados.
- **Mapeo fuente → instrumento** (`SOURCE_TO_INSTRUMENTS`): cada fuente registrada declara qué instrumentos ofrece (`PATR`, `PIDARET`, `PDT`, `datos_agricolas`).
- **Separación obligatoria de pipelines**: `documental` → `document_context` / `tabular` → `tabular_context`.
- **No descarga ni aprueba**: solo propone candidatos con estado (`candidate`, `available`, `requires_review`, `unavailable`), nivel de confianza y razón de selección. La aprobación es siempre humana.
- **Endpoints API asociados:** `/v2/atlas/sources`, `/v2/atlas/discover`.

---

### 2.2. Recolector Autónomo Web Respetuoso — `AutonomousWebCollector`

**Archivo:** `apps/atlas/web/autonomous_collector.py`

Agente de rastreo y recolección web con **cortesía técnica** y límites presupuestarios deterministas.

**Características técnicas:**

- **Adaptadores en cascada** (orden de prioridad):
  1. `SocrataCatalogAdapter` — datos abiertos `datos.gov.co`
  2. `DcatAdapter` — catálogos DCAT
  3. `SitemapAdapter` — sitemaps XML
  4. `FeedAdapter` — feeds RSS/Atom
  5. `NativeSearchAdapter` — búsqueda nativa del sitio
  6. `FocusedHtmlCrawler` — crawler HTML focalizado
  7. `PlaywrightFallbackAdapter` — fallback con JavaScript renderizado

- **Cortesía técnica (`politeness.py`):**
  - Respeta `robots.txt` (`RobotsTxtManager` con caché por host).
  - Retraso mínimo entre peticiones: `base_delay = 1.5s` con jitter aleatorio (0.1–0.4s) por host.
  - Disyuntor (`CircuitBreaker`): 3 fallos consecutivos → bloqueo del host por 60s.
  - Presupuesto de rastreo (`CrawlBudgetTracker`): máximo 20 peticiones, 10 candidatos, 100 MB transferidos.
  - User-Agent transparente exigente: requiere `ATLAS_CONTACT_EMAIL` institucional (`AtlasTerritorial-Collector/1.0`).

- **Seguridad (`security.py`):**
  - HTTPS estricto obligatorio.
  - Allowlist explícita de autoridades oficiales (nacional, gobernaciones, alcaldías piloto).
  - Protección anti-SSRF: resolución DNS y bloqueo de IPs privadas, loopback, link-local, multicast y endpoints de metadatos de nube.
  - Validación de firma mágica PDF (`%PDF-` en los primeros bytes).
  - Verificación SHA-256 post-descarga; discrepancia → rechazo.

- **Adquisición soberana:**
  - Streaming con control manual de redirecciones (máx. 5 saltos, validando cada salto).
  - Límite de tamaño: 100 MB.
  - Almacenamiento atómico por contenido: `outputs/atlas/sources/{sha256}.pdf` (elimina duplicados).
  - Priorización de versiones: marca como `is_superseded` la versión histórica del PATR (2019) frente a la vigente (Resolución 000841 de 2026).

---

### 2.3. Extractor de Creencias Territoriales — `TerritorialBeliefExtractor`

**Archivo:** `apps/atlas/extractors/belief_extractor.py`

Agente **cognitivo asistido por el micro-LLM `ai/gemma4:E4B`**. Lee el texto digital del documento oficial aprobado, extrae fragmentos relevantes de política agraria y formula un prompt Zero-Trust. Transforma párrafos normativos en reglas operativas: **[Condición Fáctica en Parcela → Acción Concreta de Catálogo]**.

**Pipeline (7 capas deterministas):**

1. **Compuerta de aprobación humana:** el documento debe estar en estado `approved_for_context`; de lo contrario se lanza `ArtifactNotApprovedError`.
2. **Extracción de texto soberana:** binario Poppler `pdftotext` (sin dependencias pesadas de Python); fallback a OCR local (Tesseract) si no hay texto digital.
3. **Slicing focalizado:** 65+ palabras clave agrarias (crédito, restitución de tierras, ambiente y agua, reserva campesina, ZRC, etc.); partición por artículos/capítulos/ejes normativos; máximo 15 fragmentos por documento.
4. **Prompt Zero-Trust** (`_build_zero_trust_prompt`): 10 reglas inquebrantables — cita literal exacta obligatoria, catálogo de acciones cerrado, prohibición de definiciones burocráticas, sobriedad anti-retórica, salida JSON única.
5. **Compuerta anti-alucinación** (`verify_verbatim_quote`): `raw_excerpt` debe ser **subcadena literal exacta** del texto fuente (normalizada insensible a espaciado). Si falla → `hallucination_rejected` y exclusión del set de creencias.
6. **Desduplicación y detección de colisiones** (3 tipos):
   - **Ambiental:** `DEFOREST` vs. mandatos de protección (RUNAP, áreas protegidas).
   - **Hídrica:** `IRRIGATE` vs. restricciones/vedas/escasez crítica en el mismo territorio.
   - **Agroecológica:** agroquímicos de síntesis vs. transición agroecológica (orgánico, bioinsumos, ZRC).
7. **Persistencia y curaduría humana:** guardado en `outputs/atlas/context/{source_id}_beliefs.json`; edición de campos (`update_belief_item`), admisión/descarte de ruido (`curate_belief`), agregación por municipio piloto (`get_pilot_aggregated_beliefs`).

**Salida final:** compilación determinista a `GoalSpec` y `PlanSpec` YAML ejecutables con validación de sintaxis MVEL contra el vocabulario controlado del simulador.

---

## 3. Las 6 Capas de Validación Determinista del Pipeline

| # | Capa | Mecanismo |
|---|------|-----------|
| 1 | Integridad binaria y aislamiento de cuarentena | Magic bytes `%PDF-`, SHA-256 como identidad inmutable, anti-SSRF |
| 2 | Esquema estructural | Pydantic V2 con `extra="forbid"` — rechaza campos no declarados |
| 3 | Verificación verbatim | `raw_excerpt` ⊆ texto fuente; si falla → alucinación rechazada |
| 4 | Validación MVEL | Sintaxis de reglas de activación y vocabulario controlado |
| 5 | Delimitación anti-inyección | Fragmentos enmarcados en XML, prompts restrictivos, escáneres regex |
| 6 | Descubrimiento adaptativo | Máx. 6 reintentos con retroalimentación humana y filtro anti-redundancia |

---

## 4. Resultados Empíricos

### 4.1. Suite de pruebas

- **247 pruebas unitarias pasando (100%)** — 144 añadidas en el Bloque B6.
- Comando: `make test-unit`; suite B6 específica: `pytest tests/unit/test_atlas_*.py tests/unit/test_corpus_b6.py tests/unit/test_belief_extractor_and_compiler.py tests/unit/test_manual_upload_and_discovery_seeds.py -v`

### 4.2. Eficacia de extracción (corpus PATR Montes de María)

| Métrica | Valor |
|---------|-------|
| Creencias propuestas por Gemma 4 | 9 |
| Verificadas verbatim | 8 (88,9%) |
| Alucinaciones interceptadas | 1 (11,1%) — afirmación numérica sin sustento textual |
| Tasa de alucinación admitida | 0% (las rechazadas se excluyen antes de entrar al set de creencias) |

### 4.3. Convergencia del bucle adaptativo de descubrimiento

- **65%** de las consultas se resuelven en la semilla inicial.
- **25%** convergen en la segunda iteración tras retroalimentación técnica del revisor.
- **2%** alcanzan el techo de 6 reintentos, sin introducir registros duplicados.

### 4.4. Configuración de inferencia local

| Parámetro | Valor |
|-----------|-------|
| Modelo | `ai/gemma4:E4B` (Google Gemma 4, 4B parámetros) |
| Cuantización | GGUF `MOSTLY_Q4_K_M` (4-bit) |
| Huella de memoria | 3,2 GB unificados (Apple Silicon M4, 16 GB host) |
| Latencia promedio | 18.420 ms por pasaje regulatorio de 1.800 tokens |
| Runtime | Docker Model Runner (puerto 12434); fallback Ollama (11434) |
| Rol | Solo genera candidatos; cero autoridad para aprobar o escribir en producción |

### 4.5. Artefactos generados

- `outputs/atlas/sources/` — 8 PDF oficiales verificados por SHA-256.
- `outputs/atlas/context/` — 5 archivos `*_beliefs.json` (PATR histórico, Resolución 841/2026, PIDARET Bolívar, PDM El Carmen de Bolívar, PDM San Jacinto).
- `outputs/atlas/yaml/goals/` — 3 GoalSpec compilados (crédito agrario campesino, demanda de ganado bovino, planificación integral).
- `outputs/atlas/yaml/plans/` — 3 PlanSpec compilados correspondientes.

---

## 5. Ejemplo de YAML Compilado

Excerpt de `outputs/atlas/yaml/goals/credito_agrario_campesino_goal_v1.yaml`:

```yaml
id: credito_agrario_campesino_goal_v1
version: '1.0'
display_name: Microcrédito Agrario Campesino
description: Acceso a microcrédito campesino en El Carmen de Bolívar.
pyramid_level: OPPORTUNITY
sub_level: L3_PRODUCTIVE_DEVELOPMENT
plan_ref: credito_agrario_campesino_plan_v1
activation_when: belief.get('money') < 100000
contribution_rules:
  fixed_value: 0.92
normative_tags:
  - pillar_desarrollo_agrario_y_rural
  - muni_el_carmen_de_bol_var
```

---

## 6. Límites y Limitaciones

1. **Bucle de simulación diferido:** la integración con el runtime multiagente WellProdSim / Python BESA sigue marcada como `not_executed`; reservada para Semanas 10–12.
2. **Alcance territorial:** el atlas está poblado únicamente para los 15 municipios PDET de Montes de María.
3. **Preservación del simulador:** los archivos originales de EthosTerra permanecen intactos; todas las salidas residen en `outputs/atlas/`.

---

## 7. Instrucciones de Reproducción

```bash
# Verificación del entorno
make doctor && make pull-model && make build && make start && make health

# Suite unitaria completa (247 pruebas)
make test-unit

# Cobertura específica del Bloque B6 (144 pruebas)
PYTHONPATH=".:apps/api" uv run --project apps/api --with pytest --with pydantic \
  --with jsonschema --with pyyaml --with fastapi --with httpx \
  pytest tests/unit/test_atlas_*.py tests/unit/test_corpus_b6.py \
  tests/unit/test_belief_extractor_and_compiler.py \
  tests/unit/test_manual_upload_and_discovery_seeds.py -v

# Verificación de build de la interfaz
pnpm --dir apps/ui build
```

---

## 8. Propuesta de Exposición (15 minutos)

| Bloque | Duración | Contenido |
|--------|----------|-----------|
| Alcance y ruta | 2 min | Progresión Semanas 5→9 dentro del plan de 16 semanas |
| Demo en vivo | 3 min | Consola AT-1, panel de cuarentena, vista de creencias |
| Los 3 agentes | 4 min | Discovery (determinista), Collector (cortesía/seguridad), Extractor (LLM + verbatim) |
| Resultados | 3 min | Métricas de extracción, convergencia adaptativa, 247 pruebas |
| Límites y próximos pasos | 3 min | Qué está fuera de alcance, preparación BESA (Semanas 10–12) |

**Preguntas-problema para avivar la exposición:**

- ¿Cómo se garantiza que el LLM no inventa datos? → Compuerta verbatim: subcadena literal o rechazo.
- ¿Quién aprueba los documentos? → Siempre un humano; el agente solo propone con justificativo técnico.
- ¿Qué pasa si el documento no es el correcto? → El revisor descarta con retroalimentación obligatoria y el agente re-busca (máx. 6 intentos).
- ¿Y si dos normas se contradicen? → Detección de colisiones (ambiental, hídrica, agroecológica) escalada a revisión humana.
