from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from apps.atlas.schemas.territory_schemas import TerritoryHierarchy
from apps.atlas.schemas.document_schemas import ISO_DATE_PATTERN

_STRICT = ConfigDict(extra="forbid", strict=True)

InstrumentType = Literal[
    "PATR",
    "PIDARET",
    "PDT",
    "EOT",
    "PBOT",
    "POT",
    "ordenanza",
    "acuerdo_municipal",
    "datos_agricolas",
]

DiscoveryStatus = Literal["candidate", "available", "unavailable", "requires_review"]
ConfidenceLevel = Literal["high", "medium", "low"]
PipelineType = Literal["documental", "api_tabular"]
DocumentFormat = Literal["pdf", "json_api", "geojson", "csv"]


class DiscoveryQuery(BaseModel):
    """Consulta estructurada para el descubrimiento documental en un territorio."""
    model_config = _STRICT

    department: str = Field(..., min_length=2, description="Nombre del departamento")
    municipality: str = Field(..., min_length=2, description="Nombre del municipio")
    divipola: str = Field(..., pattern=r"^\d{5}$", description="Código DIVIPOLA de 5 dígitos")
    subregion: str | None = Field(default=None, description="Subregión formal o PDET si aplica")
    instrument_types: list[InstrumentType] = Field(
        ..., min_length=1, description="Tipos de instrumentos de política o datos requeridos"
    )
    max_candidates: int = Field(default=20, ge=1, le=50, description="Límite máximo de candidatos a retornar")


class CandidateSourceRecord(BaseModel):
    """Ficha de fuente oficial descubierta y propuesta para revisión humana."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100)
    url: str = Field(..., min_length=5)
    entity: str = Field(..., min_length=2)
    title: str = Field(..., min_length=3)
    territory_scope: str = Field(..., description="Ámbito territorial formal")
    instrument_type: InstrumentType
    pipeline_type: PipelineType
    document_format: DocumentFormat
    status: DiscoveryStatus
    confidence_level: ConfidenceLevel
    selection_reason: str
    http_status: int | None = Field(default=None, ge=100, le=599)
    content_type: str | None = None
    query_date: str

    # Invariantes de gobernanza (inmutables, no modificables)
    source_type: Literal["document_context", "tabular_context"]
    allowed_for_training: Literal[False] = False
    usage_state: Literal["context_only"] = "context_only"
    consent_status: Literal["not_applicable"] = "not_applicable"
    approval_status: Literal["pending_review"] = "pending_review"

    @model_validator(mode="after")
    def _validate_pipeline_and_governance(self) -> CandidateSourceRecord:
        """Asegura el acoplamiento estricto entre pipeline, tipo de gobernanza y formato."""
        if self.pipeline_type == "documental":
            if self.source_type != "document_context":
                raise ValueError(
                    f"Incompatibilidad de gobernanza: Para pipeline_type='documental', "
                    f"source_type debe ser estrictamente 'document_context', encontrado '{self.source_type}'."
                )
            if self.document_format not in ("pdf",):
                raise ValueError(
                    f"Incompatibilidad de formato: Para pipeline_type='documental', "
                    f"document_format debe ser 'pdf', encontrado '{self.document_format}'."
                )
        elif self.pipeline_type == "api_tabular":
            if self.source_type != "tabular_context":
                raise ValueError(
                    f"Incompatibilidad de gobernanza: Para pipeline_type='api_tabular', "
                    f"source_type debe ser estrictamente 'tabular_context', encontrado '{self.source_type}'."
                )
            if self.document_format not in ("json_api", "csv", "geojson"):
                raise ValueError(
                    f"Incompatibilidad de formato: Para pipeline_type='api_tabular', "
                    f"document_format debe ser 'json_api', 'csv' o 'geojson', encontrado '{self.document_format}'."
                )
        return self


class DiscoveryResult(BaseModel):
    """Resultado determinista del agente de descubrimiento documental."""
    model_config = _STRICT

    query: DiscoveryQuery
    resolved_hierarchy: TerritoryHierarchy
    candidates: list[CandidateSourceRecord]
    total_candidates: int
    discovery_timestamp: str


MAX_ADAPTIVE_SEARCH_RETRIES = 6

CandidateApprovalStatus = Literal["pending_review", "approved_for_acquisition", "rejected"]


class CandidateReviewDecision(BaseModel):
    """Contrato estricto de entrada para la decisión humana sobre un candidato descubierto."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100, description="Identificador único del candidato")
    reviewer_id: str = Field(..., min_length=3, max_length=64, description="Identificador del revisor humano")
    decision: Literal["approve", "reject"] = Field(..., description="Decisión explícita: approve o reject")
    review_notes: str = Field(
        ..., min_length=5, max_length=2000, description="Justificación obligatoria de la decisión"
    )
    request_alternative_search: bool = Field(
        default=False,
        description="Indica si el investigador solicita al agente una re-búsqueda adaptativa de un documento equivalente",
    )
    instruction_feedback: str | None = Field(
        default=None,
        max_length=1000,
        description="Instrucciones o directrices precisas del investigador para reorientar la búsqueda",
    )
    timestamp: str | None = Field(
        default=None, pattern=ISO_DATE_PATTERN, description="Timestamp UTC ISO 8601 opcional de la decisión"
    )

    @field_validator("review_notes")
    @classmethod
    def _validate_non_empty_notes(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 5:
            raise ValueError(
                "Las notas de revisión no pueden estar vacías ni contener solo espacios en blanco (mínimo 5 caracteres)."
            )
        return clean


class CandidateReviewRecord(BaseModel):
    """Registro inmutable y auditable de la decisión de revisión humana sobre un candidato."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100)
    reviewer_id: str = Field(..., min_length=3, max_length=64)
    decision: Literal["approve", "reject"]
    resulting_status: CandidateApprovalStatus
    review_notes: str = Field(..., min_length=5, max_length=2000)
    timestamp: str = Field(..., pattern=ISO_DATE_PATTERN)

    # Trazabilidad de descarte adaptativo e iteraciones HITL
    request_alternative_search: bool = Field(default=False)
    instruction_feedback: str | None = Field(default=None)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=MAX_ADAPTIVE_SEARCH_RETRIES)
    alternative_found: bool = Field(default=False)
    alternative_candidate: dict[str, Any] | None = Field(default=None)
    search_status: Literal[
        "reviewed",
        "found_alternative",
        "exhausted_no_alternative",
        "no_search_requested",
    ] = Field(default="reviewed")
    adaptive_message: str | None = Field(default=None)

    # Invariantes inmutables de gobernanza y preservación de pipeline
    pipeline_type: PipelineType
    source_type: Literal["document_context", "tabular_context"]
    document_format: DocumentFormat
    allowed_for_training: Literal[False] = False
    usage_state: Literal["context_only"] = "context_only"

    @model_validator(mode="after")
    def _validate_pipeline_and_governance(self) -> CandidateReviewRecord:
        if self.pipeline_type == "documental":
            if self.source_type != "document_context":
                raise ValueError(
                    f"Incompatibilidad de gobernanza: Para pipeline_type='documental', "
                    f"source_type debe ser estrictamente 'document_context', encontrado '{self.source_type}'."
                )
            if self.document_format not in ("pdf",):
                raise ValueError(
                    f"Incompatibilidad de formato: Para pipeline_type='documental', "
                    f"document_format debe ser 'pdf', encontrado '{self.document_format}'."
                )
        elif self.pipeline_type == "api_tabular":
            if self.source_type != "tabular_context":
                raise ValueError(
                    f"Incompatibilidad de gobernanza: Para pipeline_type='api_tabular', "
                    f"source_type debe ser estrictamente 'tabular_context', encontrado '{self.source_type}'."
                )
            if self.document_format not in ("json_api", "csv", "geojson"):
                raise ValueError(
                    f"Incompatibilidad de formato: Para pipeline_type='api_tabular', "
                    f"document_format debe ser 'json_api', 'csv' o 'geojson', encontrado '{self.document_format}'."
                )
        if self.resulting_status not in ("approved_for_acquisition", "rejected"):
            raise ValueError(
                f"Estado de gobernanza inválido en la revisión: '{self.resulting_status}'. "
                f"Solo se admite 'approved_for_acquisition' o 'rejected'."
            )
        return self


CandidateReviewResponse = CandidateReviewRecord


class CandidateReviewAuditState(BaseModel):
    """Estado persistente del registro de auditoría de revisiones humanas."""
    model_config = _STRICT

    version: Literal["1.0.0"] = "1.0.0"
    last_updated: str = Field(..., pattern=ISO_DATE_PATTERN)
    reviews: dict[str, CandidateReviewRecord] = Field(
        default_factory=dict, description="Diccionario de revisiones humanas indexadas por source_id"
    )


class AcquisitionRequest(BaseModel):
    """Contrato de entrada para la solicitud de adquisición documental bajo demanda."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100, description="Identificador único del candidato aprobado")
    requester_id: str = Field(..., min_length=3, max_length=64, description="Identificador del investigador que solicita la adquisición")


class AcquisitionResult(BaseModel):
    """Contrato de salida con el resultado y trazabilidad de la adquisición documental."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100)
    requester_id: str = Field(..., min_length=3, max_length=64)
    status: Literal["acquired_new", "already_present"]
    download_timestamp: str = Field(..., pattern=ISO_DATE_PATTERN)
    canonical_url: str = Field(..., min_length=5)
    sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(..., ge=0)
    content_path: str = Field(..., min_length=5)
    content_type: str = Field(..., min_length=3)

    # Invariantes de gobernanza del documento adquirido
    pipeline_type: Literal["documental"] = "documental"
    source_type: Literal["document_context"] = "document_context"
    document_format: Literal["pdf"] = "pdf"
    allowed_for_training: Literal[False] = False
    usage_state: Literal["context_only"] = "context_only"
    approval_status: Literal["pending_review"] = "pending_review"


class AuthorizedSeedCreate(BaseModel):
    """Contrato para registrar una URL o repositorio institucional semilla para rastreo."""
    model_config = _STRICT

    url: str = Field(..., min_length=5, description="URL oficial o repositorio institucional autorizado")
    entity: str = Field(default="Entidad Oficial Territorial", min_length=2, description="Entidad titular de la fuente")
    title: str = Field(default="Repositorio Oficial de Política Territorial", min_length=2, description="Título o descripción del instrumento")
    territory_scope: str = Field(default="Montes de María", min_length=2, description="Ámbito territorial de cobertura")
    instrument_type: InstrumentType = Field(default="PDM", description="Tipo de instrumento esperado")
    pipeline_type: PipelineType = Field(default="documental", description="Tipo de pipeline")
    document_format: DocumentFormat = Field(default="pdf", description="Formato del documento")
    added_by: str = Field(default="investigador_local", min_length=2, description="Identificador del investigador que autoriza la semilla")


class AuthorizedSeedItem(AuthorizedSeedCreate):
    """Registro inmutable de semilla de rastreo autorizada por el usuario."""
    model_config = _STRICT

    seed_id: str = Field(..., min_length=3, description="Identificador único de la semilla")
    added_at: str = Field(..., pattern=ISO_DATE_PATTERN, description="Fecha UTC de autorización")
    is_active: bool = Field(default=True, description="Indica si la semilla está activa para rastreo")
