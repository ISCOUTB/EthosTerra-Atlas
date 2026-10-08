from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid", strict=True)
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?$"


class TerritorialBeliefItem(BaseModel):
    """Creencia territorial formalizada para el sistema eBDI a partir de un instrumento oficial."""
    model_config = _STRICT

    belief_id: str = Field(..., min_length=4, max_length=64, description="Identificador único de la creencia")
    source_id: str = Field(..., min_length=3, max_length=100, description="source_id del documento oficial fuente")
    pillar: str = Field(..., min_length=2, max_length=100, description="Pilar de política o eje estratégico")
    topic: str = Field(..., min_length=3, max_length=200, description="Tema o subeje temático específico")

    # Dupla Estricta eBDI: [Condición Fáctica -> Acción Ejecutable del Catálogo]
    belief_key: str = Field(
        default="creencia_territorial_general",
        description="Identificador snake_case del predicado en el repositorio de creencias (ej. 'acceso_distrito_riego')",
    )
    trigger_condition: str = Field(
        default="",
        description="CONDICIÓN FÁCTICA DIRECTA del campesino o su entorno para que la creencia aplique (sin siglas)",
    )
    executable_action: str = Field(
        default="agro_ecosystem_operation",
        description="Acción formal del catálogo de EthosTerra (ej. 'agro_ecosystem_operation', 'send_society_collaboration')",
    )
    action_operation_type: str | None = Field(
        default=None,
        description="Sub-operación agronómica si aplica (ej. 'PREPARE', 'IRRIGATE', 'BUY_SEEDS', 'BUY_WATER')",
    )
    behavioral_effect: str = Field(
        default="",
        description="EFECTO CONDUCTUAL DIRECTO: qué hace o qué decide el campesino a partir de esta creencia",
    )
    activation_rule_template: str = Field(
        default="",
        description="Plantilla de condición lógica orientada a MVEL para el activation_when de GoalSpec",
    )

    raw_excerpt: str = Field(..., min_length=5, description="Cita textual exacta literal extraída del documento fuente")
    ebdi_belief_assertion: str = Field(..., min_length=10, description="Proposición formal de creencia territorial para el agente eBDI")
    target_municipalities: list[str] = Field(default_factory=list, description="Municipios explícitamente afectados o mencionados")
    applicable_divipolas: list[str] = Field(default_factory=list, description="Códigos DIVIPOLA resueltos determinísticamente")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza probabilístico reportado por el extractor")
    verification_status: Literal["verified_verbatim", "hallucination_rejected"] = Field(
        ..., description="Resultado del gate determinista de verificación de cita literal"
    )
    # Detección de Colisiones / Inconsistencias Normativas
    collision_detected: bool = Field(
        default=False,
        description="Indica si el sistema detectó colisión, incompatibilidad o contradicción con otra creencia",
    )
    collision_reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Detalle o justificación de la colisión o incompatibilidad detectada",
    )
    # Curación Humana Granular
    curation_status: Literal["admitted_ebdi", "dismissed_noise", "pending"] = Field(
        default="pending",
        description="Decisión humana individual: 'admitted_ebdi' para admitir en el agente, 'dismissed_noise' para descartar acrónimo/ruido",
    )
    curation_notes: str | None = Field(default=None, max_length=2000, description="Justificación del curador humano")
    curator_id: str | None = Field(default=None, max_length=64, description="Identificador del curador humano")
    curation_timestamp_utc: str | None = Field(default=None, pattern=ISO_DATE_PATTERN, description="Marca de tiempo UTC de la curación")


class BeliefCurationRequest(BaseModel):
    """Petición humana para curar o descartar una creencia eBDI específica."""
    model_config = _STRICT

    decision: Literal["admitted_ebdi", "dismissed_noise", "pending"]
    curator_id: str = Field(..., min_length=3, max_length=64)
    notes: str = Field(default="", max_length=2000)


class BeliefEditRequest(BaseModel):
    """Petición humana de edición granular de una creencia territorial (soporta modo no programador y programador)."""
    model_config = _STRICT

    editor_id: str = Field(..., min_length=3, max_length=64)
    topic: str | None = Field(default=None, min_length=3, max_length=200)
    trigger_condition: str | None = Field(default=None, min_length=3)
    executable_action: str | None = Field(default=None, min_length=3)
    action_operation_type: str | None = Field(default=None)
    behavioral_effect: str | None = Field(default=None, min_length=3)
    activation_rule_template: str | None = Field(default=None)
    raw_excerpt: str | None = Field(default=None, min_length=5)
    ebdi_belief_assertion: str | None = Field(default=None, min_length=10)
    target_municipalities: list[str] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    edit_notes: str = Field(default="", max_length=2000)


class TerritorialBeliefExtractionResult(BaseModel):
    """Artefacto completo de extracción de creencias eBDI de un documento oficial aprobado."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100)
    instrument_title: str = Field(..., min_length=3)
    document_sha256: str = Field(..., min_length=64, max_length=64)
    extraction_timestamp_utc: str = Field(..., pattern=ISO_DATE_PATTERN)
    model_used: str = Field(..., min_length=2)
    extraction_method: Literal[
        "poppler_pdftotext_plus_micro_llm",
        "local_tesseract_ocr_plus_micro_llm",
    ] = "poppler_pdftotext_plus_micro_llm"
    total_beliefs_extracted: int = Field(..., ge=0)
    verified_beliefs_count: int = Field(..., ge=0)
    rejected_hallucinations_count: int = Field(..., ge=0)
    beliefs: list[TerritorialBeliefItem] = Field(default_factory=list)


class PilotAggregatedBeliefs(BaseModel):
    """Conjunto de creencias eBDI consolidadas y heredadas por un municipio piloto."""
    model_config = _STRICT

    divipola: str = Field(..., min_length=5, max_length=5)
    municipality_name: str
    department_name: str
    is_pdet: bool
    pdet_subregion: str | None
    total_applicable_beliefs: int = Field(..., ge=0)
    contributing_sources: list[str] = Field(default_factory=list)
    beliefs: list[TerritorialBeliefItem] = Field(default_factory=list)
