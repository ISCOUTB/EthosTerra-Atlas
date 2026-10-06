"""Contratos del corpus agronómico de campo (Bloque B6).

Separan tres capas que nunca deben mezclarse:
- fuente (SourceRecord): procedencia, consentimiento y hashes;
- segmentación (SegmentRecord): unidad de evidencia con offsets, sin interpretación;
- anotación (AnnotatedSegment): interpretación humana trazable a evidencia textual.

Todos los offsets son relativos al texto normalizado completo de la fuente.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain.v2.document_schemas import EpistemicStatus

CORPUS_SCHEMA_VERSION = "1.0.0"

SHA256_PATTERN = r"^[0-9a-f]{64}$"
SOURCE_ID_PATTERN = r"^(field|synth)_\d{4}$"
SEGMENT_ID_PATTERN = r"^(field|synth)_\d{4}_seg_\d{4}$"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
ACTOR_ID_PATTERN = r"^[a-z0-9_]{1,64}$"

UNSTATED_MARKERS = ("unknown", "not_stated")

SourceType = Literal[
    "field_real_episode",
    "elicited_vignette",
    "synthetic",
    "document_context",
    "interview",
    "field_diary",
    "peasant_story",
    "technical_assistance_observation",
    "productive_decision",
    "agronomic_conflict",
    "context_document",
]
ProvenanceClass = Literal["field", "synthetic", "derived"]
ConsentStatus = Literal["pending", "granted", "restricted", "withdrawn", "not_applicable"]
UsageState = Literal["context_only", "evaluation_authorized", "training_authorized"]
PiiStatus = Literal["not_scanned", "flagged", "pseudonymized", "clean_verified"]
SourceStatus = Literal["draft", "normalized", "segmented", "annotated", "reviewed", "frozen", "excluded"]
CaseType = Literal["pure", "conflict", "insufficient", "unclear", "not_stated", "out_of_scope"]
AnnotationStatus = Literal["draft", "primary_done", "second_read", "adjudicated", "disputed"]
SpanEvidenceType = Literal["observed", "inferred"]
ConflictType = Literal[
    "productive_vs_household_security",
    "investment_vs_liquidity_debt",
    "plot_labor_vs_off_farm_wage",
    "production_vs_family_care_health",
    "immediate_sale_vs_seed_food_reserve",
    "yield_vs_conservation",
    "individual_vs_community_obligation",
    "technical_recommendation_vs_local_preference",
    "short_term_vs_long_term_resilience",
    "agronomic_goal_vs_risk_emotion",
    "other",
]
SplitName = Literal["train", "validation", "test", "adversarial", "hard_cases"]
TransformationStep = Literal[
    "decode_utf8",
    "strip_bom",
    "unicode_nfc",
    "newline_lf",
    "whitespace_chars_to_space",
    "collapse_inline_spaces",
    "strip_trailing_line_spaces",
    "collapse_blank_lines",
    "strip_document_edges",
]

_STRICT = ConfigDict(extra="forbid", strict=True)


def _validate_relative_path(value: str, required_prefix: str) -> str:
    if not value.startswith(required_prefix):
        raise ValueError(f"La ruta debe comenzar con '{required_prefix}'.")
    if value.startswith("/") or "\\" in value or "\x00" in value or ".." in value.split("/"):
        raise ValueError("La ruta debe ser relativa a la raíz del corpus y sin secuencias de escape.")
    return value


class SourceRecord(BaseModel):
    """Registro de procedencia de una fuente. Los campos desconocidos se declaran, no se completan."""

    model_config = _STRICT

    schema_version: Literal["1.0.0"] = CORPUS_SCHEMA_VERSION
    source_id: str = Field(pattern=SOURCE_ID_PATTERN)
    source_type: SourceType
    provenance_class: ProvenanceClass
    title: str = Field(min_length=1, max_length=200)
    language: str = Field(pattern=r"^[a-z]{2}$")
    collection_date: str = Field(description="Fecha ISO (YYYY-MM-DD), 'unknown' o 'not_stated'.")
    location: str = Field(
        min_length=1,
        max_length=64,
        description="Granularidad máxima regional, 'redacted', 'unknown' o 'not_stated'.",
    )
    collector_id: str = Field(pattern=ACTOR_ID_PATTERN)
    consent_status: ConsentStatus
    participant_code: str = Field(
        default="unknown",
        min_length=1,
        max_length=64,
        description="Código pseudonimizado del participante o 'unknown'/'not_stated'.",
    )
    vereda_code: str = Field(
        default="unknown",
        min_length=1,
        max_length=64,
        description="Código pseudonimizado de vereda o 'unknown'/'not_stated'/'redacted'.",
    )
    consent_scope: list[str] = Field(
        default_factory=list,
        description="Lista de alcances autorizados por el participante (ej. ['research', 'annotation', 'local_model_evaluation']).",
    )
    allowed_for_training: bool = Field(
        default=False,
        description="Autorización explícita para entrenamiento. False por defecto e independiente de consent_scope.",
    )
    usage_state: UsageState = Field(
        default="context_only",
        description="Estado de gobernanza operativa del dato: context_only | evaluation_authorized | training_authorized.",
    )
    pii_status: PiiStatus = "not_scanned"
    raw_path: str
    raw_sha256: str = Field(pattern=SHA256_PATTERN)
    normalized_path: str | None = None
    normalized_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    duplicate_of: str | None = Field(default=None, pattern=SOURCE_ID_PATTERN)
    version: str = Field(pattern=SEMVER_PATTERN)
    status: SourceStatus
    notes: str = Field(default="", max_length=2000)

    @field_validator("collection_date")
    @classmethod
    def _check_date(cls, v: str) -> str:
        if v in UNSTATED_MARKERS:
            return v
        date.fromisoformat(v)
        return v

    @field_validator("raw_path")
    @classmethod
    def _check_raw_path(cls, v: str) -> str:
        return _validate_relative_path(v, "sources/")

    @field_validator("normalized_path")
    @classmethod
    def _check_normalized_path(cls, v: str | None) -> str | None:
        return None if v is None else _validate_relative_path(v, "normalized/")

    @model_validator(mode="after")
    def _check_invariants(self) -> SourceRecord:
        if (self.normalized_path is None) != (self.normalized_sha256 is None):
            raise ValueError("normalized_path y normalized_sha256 deben registrarse juntos.")
        if self.consent_status == "not_applicable" and self.provenance_class != "synthetic":
            raise ValueError("'not_applicable' solo se admite para fuentes sintéticas.")
        if self.provenance_class == "synthetic" and not self.source_id.startswith("synth_"):
            raise ValueError("Las fuentes sintéticas deben usar el prefijo 'synth_'.")
        if self.provenance_class != "synthetic" and not self.source_id.startswith("field_"):
            raise ValueError("Las fuentes de campo o derivadas deben usar el prefijo 'field_'.")
        if self.status not in ("draft", "excluded") and self.normalized_path is None:
            raise ValueError(f"El estado '{self.status}' exige una versión normalizada registrada.")
        if self.duplicate_of == self.source_id:
            raise ValueError("Una fuente no puede ser duplicado de sí misma.")
        if self.usage_state == "training_authorized" and not self.allowed_for_training:
            raise ValueError("usage_state no puede ser 'training_authorized' si allowed_for_training es False.")
        if self.allowed_for_training and self.consent_status not in ("granted", "not_applicable") and self.provenance_class != "synthetic":
            raise ValueError("No se puede autorizar entrenamiento sin consentimiento otorgado.")
        return self


class TransformationRecord(BaseModel):
    """Paso de normalización aplicado a una fuente (registro append-only)."""

    model_config = _STRICT

    source_id: str = Field(pattern=SOURCE_ID_PATTERN)
    step: TransformationStep
    description: str = Field(min_length=1, max_length=500)
    changed: bool
    input_sha256: str = Field(pattern=SHA256_PATTERN)
    output_sha256: str = Field(pattern=SHA256_PATTERN)
    tool_version: str = Field(pattern=SEMVER_PATTERN)
    timestamp_utc: datetime


class SegmentRecord(BaseModel):
    """Unidad de evidencia producida por segmentación. No contiene interpretación."""

    model_config = _STRICT

    segment_id: str = Field(pattern=SEGMENT_ID_PATTERN)
    source_id: str = Field(pattern=SOURCE_ID_PATTERN)
    text: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    segmentation_method: str = Field(min_length=1, max_length=64)
    segmentation_version: str = Field(pattern=SEMVER_PATTERN)

    @model_validator(mode="after")
    def _check_offsets(self) -> SegmentRecord:
        _check_segment_identity(self.segment_id, self.source_id, self.text, self.char_start, self.char_end)
        return self


class CorpusEvidenceSpan(BaseModel):
    """Cita textual exacta que sustenta una anotación."""

    model_config = _STRICT

    quote: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    evidence_type: SpanEvidenceType
    inference_warning: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _check_span(self) -> CorpusEvidenceSpan:
        if self.char_end - self.char_start != len(self.quote):
            raise ValueError("La longitud de 'quote' no coincide con los offsets.")
        if self.evidence_type == "inferred" and not self.inference_warning:
            raise ValueError("Toda evidencia inferida exige 'inference_warning' (no es observación directa).")
        if self.evidence_type == "observed" and self.inference_warning:
            raise ValueError("Una evidencia observada no debe llevar advertencia de inferencia.")
        return self


class ConflictRecord(BaseModel):
    """Colisión entre dos intenciones ante un detonante común. Nunca se resuelve automáticamente."""

    model_config = _STRICT

    common_trigger: str = Field(min_length=1, max_length=500)
    intent_a: str = Field(min_length=1, max_length=200)
    intent_b: str = Field(min_length=1, max_length=200)
    evidence_a: list[str] = Field(min_length=1, description="Citas textuales del lado A del conflicto.")
    evidence_b: list[str] = Field(min_length=1, description="Citas textuales del lado B del conflicto.")
    conflict_type: ConflictType = Field(
        default="other",
        description="Taxonomía de conflicto según el informe de campo eBDI en Bolívar.",
    )
    incompatibility_reason: str = Field(min_length=1, max_length=1000)
    requires_human_review: Literal[True] = True

    @model_validator(mode="after")
    def _check_distinct(self) -> ConflictRecord:
        if self.intent_a.strip().casefold() == self.intent_b.strip().casefold():
            raise ValueError("Un conflicto exige dos intenciones distintas.")
        if any(not q for q in (*self.evidence_a, *self.evidence_b)):
            raise ValueError("La evidencia de conflicto no admite citas vacías.")
        return self


class AnnotatedSegment(BaseModel):
    """Anotación humana (o pre-anotación propuesta) de un segmento."""

    model_config = _STRICT

    schema_version: Literal["1.0.0"] = CORPUS_SCHEMA_VERSION
    segment_id: str = Field(pattern=SEGMENT_ID_PATTERN)
    source_id: str = Field(pattern=SOURCE_ID_PATTERN)
    text: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    evidence_spans: list[CorpusEvidenceSpan] = Field(default_factory=list)
    case_type: CaseType
    trigger: str | None = Field(default=None, max_length=500)
    intent_candidate: str | None = Field(default=None, max_length=200)
    conflict_trigger: str | None = Field(default=None, max_length=500)
    conflicting_intents: list[str] = Field(default_factory=list)
    conflict: ConflictRecord | None = None
    conflict_type: ConflictType | None = Field(
        default=None,
        description="Tipo de conflicto categorizado según la taxonomía.",
    )
    epistemic_status: EpistemicStatus
    injection_suspected: bool = False
    requires_human_review: bool
    annotation_status: AnnotationStatus
    annotator_id: str = Field(pattern=ACTOR_ID_PATTERN)
    annotation_version: str = Field(pattern=SEMVER_PATTERN)
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def _check_invariants(self) -> AnnotatedSegment:
        _check_segment_identity(self.segment_id, self.source_id, self.text, self.char_start, self.char_end)
        for span in self.evidence_spans:
            if span.char_start < self.char_start or span.char_end > self.char_end:
                raise ValueError("Toda evidencia debe estar contenida en el segmento.")
            local = self.text[span.char_start - self.char_start : span.char_end - self.char_start]
            if local != span.quote:
                raise ValueError(f"La cita no coincide con el texto del segmento: {span.quote!r}")

        has_observed = any(s.evidence_type == "observed" for s in self.evidence_spans)
        has_inferred = any(s.evidence_type == "inferred" for s in self.evidence_spans)

        if self.case_type == "pure":
            if not self.intent_candidate or not self.trigger:
                raise ValueError("'pure' exige detonante e intención candidata.")
            if self.conflict is not None or self.conflicting_intents or self.conflict_trigger or self.conflict_type is not None:
                raise ValueError("'pure' no admite intenciones en conflicto.")
            if not has_observed:
                raise ValueError("'pure' exige al menos una evidencia observada.")
        elif self.case_type == "conflict":
            if self.conflict is None:
                raise ValueError("'conflict' exige un ConflictRecord.")
            if self.intent_candidate is not None:
                raise ValueError("'conflict' no admite una intención candidata única.")
            if self.conflict_trigger != self.conflict.common_trigger:
                raise ValueError("'conflict_trigger' debe coincidir con 'common_trigger'.")
            if self.conflict_type is not None and self.conflict_type != self.conflict.conflict_type:
                raise ValueError("'conflict_type' debe coincidir con el del ConflictRecord.")
            if not {self.conflict.intent_a, self.conflict.intent_b}.issubset(self.conflicting_intents):
                raise ValueError("'conflicting_intents' debe incluir intent_a e intent_b.")
            quotes = {s.quote for s in self.evidence_spans}
            if not set(self.conflict.evidence_a) | set(self.conflict.evidence_b) <= quotes:
                raise ValueError("La evidencia del conflicto debe estar registrada en evidence_spans.")
            if not self.requires_human_review:
                raise ValueError("Todo conflicto exige revisión humana.")
        else:
            if self.intent_candidate is not None or self.conflict is not None or self.conflicting_intents or self.conflict_type is not None:
                raise ValueError(f"'{self.case_type}' no admite intención ni conflicto registrados.")
            if self.case_type in ("unclear", "insufficient") and not self.requires_human_review:
                raise ValueError(f"'{self.case_type}' exige revisión humana.")

        if self.injection_suspected and not self.requires_human_review:
            raise ValueError("Una sospecha de inyección exige revisión humana.")
        if has_inferred and not self.requires_human_review:
            raise ValueError("Una anotación con evidencia inferida exige revisión humana.")
        if self.epistemic_status == "proposed":
            if self.annotation_status != "draft" or not self.requires_human_review:
                raise ValueError("Una pre-anotación propuesta debe permanecer en borrador y bajo revisión humana.")
        return self


class SplitManifest(BaseModel):
    """Asignación reproducible de fuentes completas a particiones (sin fuga de participante)."""

    model_config = _STRICT

    split_version: str = Field(pattern=SEMVER_PATTERN)
    corpus_version: str = Field(pattern=SEMVER_PATTERN)
    strategy: Literal["by_source_id", "by_participant_code"] = "by_participant_code"
    seed: int
    ratios: dict[str, float]
    assignments: dict[SplitName, list[str]]
    participant_assignments: dict[SplitName, list[str]] = Field(default_factory=dict)
    pinned: dict[str, SplitName] = Field(default_factory=dict)
    listing_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def _check_disjoint(self) -> SplitManifest:
        seen: set[str] = set()
        for ids in self.assignments.values():
            for sid in ids:
                if sid in seen:
                    raise ValueError(f"La fuente '{sid}' aparece en más de una partición.")
                seen.add(sid)
        seen_parts: set[str] = set()
        for parts in self.participant_assignments.values():
            for pid in parts:
                if pid in seen_parts:
                    raise ValueError(f"El participante '{pid}' aparece en más de una partición (fuga de participante).")
                seen_parts.add(pid)
        return self


def is_gold_candidate(segment: AnnotatedSegment, source: SourceRecord) -> bool:
    """Evalúa si un segmento es elegible para el conjunto oro binario.

    Criterios metodológicos estrictos:
    1. Exclusión total de fuentes o datos sintéticos (provenance_class == 'synthetic' o source_type == 'synthetic').
    2. Solo las etiquetas 'pure' y 'conflict' entran al oro binario; 'insufficient', 'unclear', 'not_stated' y 'out_of_scope' quedan excluidas.
    3. La anotación debe estar formalmente adjudicada ('adjudicated').
    """
    if source.provenance_class == "synthetic" or source.source_type == "synthetic":
        return False
    if segment.case_type not in ("pure", "conflict"):
        return False
    if segment.annotation_status != "adjudicated":
        return False
    return True


def _check_segment_identity(segment_id: str, source_id: str, text: str, char_start: int, char_end: int) -> None:
    if not segment_id.startswith(f"{source_id}_seg_"):
        raise ValueError("segment_id debe derivarse de source_id.")
    if char_end <= char_start:
        raise ValueError("char_end debe ser mayor que char_start.")
    if char_end - char_start != len(text):
        raise ValueError("La longitud del texto no coincide con los offsets.")
