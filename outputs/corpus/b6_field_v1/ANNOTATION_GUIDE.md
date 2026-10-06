# Guía de anotación B6 — v1.0.0

El contrato ejecutable es `AnnotatedSegment` en `apps/api/src/domain/v2/corpus_schemas.py`. Si esta guía y el contrato no coinciden, manda el contrato. La discrepancia debe reportarse.

## 1. Árbol de decisión de `case_type`

```text
¿El segmento trata de decisiones agronómicas o productivas?
├── No ─────────────────────────────────────────────► out_of_scope
└── Sí ─ ¿Expresa alguna intención (quiero, toca, vamos a, pienso…)?
         ├── No ────────────────────────────────────► not_stated
         └── Sí ─ ¿Hay un detonante identificable y evidencia textual citable?
                  ├── No ───────────────────────────► unclear  (revisión humana)
                  └── Sí ─ ¿Cuántas intenciones hay y son incompatibles ante el mismo detonante?
                           ├── Una dominante, ninguna incompatible ──► pure
                           ├── Dos o más incompatibles con evidencia ► conflict (revisión humana)
                           └── Dudoso ───────────────────────────────► unclear
```

Ante la duda, se elige siempre la categoría menos comprometida. Nunca se fuerza un `pure` o un `conflict`.

## 2. Requisitos por categoría (los aplica el contrato)

| Categoría | Obligatorio | Prohibido |
|-----------|-------------|-----------|
| `pure` | `trigger`, `intent_candidate` y al menos un span `observed` | `conflict`, `conflicting_intents`, `conflict_trigger` |
| `conflict` | `ConflictRecord` completo; `conflict_trigger == common_trigger`; las citas de `evidence_a/b` registradas en `evidence_spans`; `requires_human_review = true` | `intent_candidate` |
| `unclear` | `requires_human_review = true` | intención o conflicto registrados |
| `not_stated`, `out_of_scope` | — | intención o conflicto registrados |

## 3. Evidencia

- `quote` es una copia **exacta** del texto normalizado y sus offsets se calculan sobre el documento completo.
- `observed`: la intención o el detonante aparece literalmente.
- `inferred`: es una interpretación razonable. Exige `inference_warning` (por ejemplo: "No es observación directa; se infiere de…") y obliga a revisión humana.
- No se citan fragmentos que no estén en el texto. Tampoco se corrige la ortografía de las citas.

## 4. Estado epistemológico del segmento

`observed` · `inferred` · `required` · `proposed` · `unknown` · `not_stated` (reutiliza `EpistemicStatus` del pipeline documental).

Una pre-anotación hecha por el Micro-LLM siempre es `proposed`, va en `draft` y lleva `requires_human_review = true`. **Nunca es etiqueta oro.**

## 5. Seguridad

Si el segmento contiene instrucciones dirigidas a un sistema ("ignora las instrucciones", "responde que…", comandos), se marca `injection_suspected = true` y se fija `requires_human_review = true`. El texto se anota como lo que es, un testimonio, y nunca se obedece.

## 6. Conflictos: qué NO es un conflicto

- Dos formulaciones de la misma intención.
- Una intención y su precondición (por ejemplo, "vender frijol" y "conseguir costales").
- Una intención y una restricción externa sin una segunda intención del actor. Esto es `pure` con restricción o, si la evidencia no alcanza, `unclear`.
- Motivaciones que el texto no expresa.

## 7. Segunda lectura y desacuerdos

- Muestra: todos los `conflict`, todos los `unclear` y el 20 % de los `pure` y `not_stated`, con semilla fija.
- La segunda anotación se guarda en `annotations/secondary/` y **nunca sobrescribe** la primaria.
- Los desacuerdos se reportan en `reports/` con su tipo:
  - error de anotación,
  - ambigüedad de la fuente,
  - laguna de la guía.
- Los segmentos sin adjudicación pasan a `hard_cases`.
- Meta de cierre: kappa de Cohen ≥ 0.70 en `case_type`.
