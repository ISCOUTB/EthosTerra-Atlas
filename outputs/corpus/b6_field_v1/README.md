# Corpus agronómico de campo B6 — `b6_field_v1`

**Esquema:** `1.0.0` · **Pipeline:** `1.0.0` · **Estado:** infraestructura lista, **sin fuentes registradas**.

Este directorio guarda evidencia de investigación. No es texto libre para pasarle al Micro-LLM. Ningún contenido de aquí se ejecuta, se escribe en el simulador ni modifica creencias de agentes.

## Estructura

| Ruta | Contenido | Mutabilidad |
|------|-----------|-------------|
| `sources/` | Copia byte a byte del original (`chmod 444`) | Inmutable |
| `normalized/` | Texto normalizado (`<id>.txt`) y segmentos (`<id>.segments.jsonl`) | Inmutable una vez escrito |
| `annotations/primary/`, `annotations/secondary/` | `AnnotatedSegment` por fuente (`<id>.jsonl`) | Se versiona con `annotation_version` |
| `manifests/sources.jsonl` | Un `SourceRecord` por fuente | Derivado |
| `manifests/transformations.jsonl` | Log de pasos de normalización con hashes de entrada y salida | Solo se agregan entradas |
| `splits/` | `SplitManifest` versionado (por documento, con semilla fija) | Versionado |
| `reports/` | Escaneos de PII e inyección, métricas, desacuerdos, limitaciones | Derivado |
| `schemas/` | JSON Schema exportado de `apps/api/src/domain/v2/corpus_schemas.py` | Generado: **no editar a mano** |

## Reglas

1. **Procedencia.** `provenance_class` puede ser `field`, `synthetic` o `derived`. Los IDs sintéticos usan `synth_NNNN` y los de campo `field_NNNN`. Las métricas siempre se reportan por separado según la procedencia.
2. **Consentimiento.** Solo entran a `splits/` las fuentes con `consent_status = granted` (o las sintéticas).
3. **Campos desconocidos.** Se declaran como `unknown` o `not_stated` y nunca se completan.
4. **Normalización conservadora.** Solo se ajustan la codificación UTF-8 y los espacios. Si la normalización altera alguna palabra, el proceso se aborta.
5. **Offsets.** Son relativos al texto normalizado completo. `verify` comprueba que `text[char_start:char_end] == quote` en segmentos y anotaciones.
6. **Seguridad.** Los escáneres de PII e inyección solo reportan offsets, nunca el texto detectado. Cualquier hallazgo obliga a revisión humana.
7. **Conflictos.** `ConflictRecord.requires_human_review` siempre es `true`. El sistema no resuelve conflictos.
8. **Pre-anotaciones del modelo.** Se registran con `epistemic_status = proposed` y `annotation_status = draft`. No pueden promoverse sin revisión humana.

## Uso

```bash
export PYTHONPATH=apps/api
CLI="uv run --project apps/api python evals/corpus/build_corpus.py"
$CLI init
$CLI register --file RUTA --source-id field_0001 --source-type interview --provenance field \
     --title "Entrevista 01 (anonimizada)" --collector researcher_01 --consent pending
$CLI normalize --source-id field_0001
$CLI segment   --source-id field_0001
$CLI scan      --source-id field_0001
$CLI verify
$CLI split --seed 6 --pin field_0003=hard_cases
```

## Pendientes antes de registrar fuentes

- Fuentes de campo reales y su consentimiento (D3).
- Decidir si `sources/` reales se versionan en git (D5).
- Decidir el tratamiento de `outputs/experiments/exp_vertical_001/sources/diario_campesino_preparacion.txt`, que tiene hashes inconsistentes (D4).

Guía de anotación: [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md).
