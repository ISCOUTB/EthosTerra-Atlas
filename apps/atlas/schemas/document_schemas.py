from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SHA256_PATTERN = r"^[0-9a-f]{64}$"
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?$"

_STRICT = ConfigDict(extra="forbid", strict=True)


class SourceRegistryEntry(BaseModel):
    """Esquema de validación para entradas del registro curado de fuentes."""
    model_config = _STRICT

    id: str = Field(..., min_length=3, max_length=100, description="Identificador único de la fuente")
    entity: str = Field(..., min_length=2, description="Entidad gubernamental u oficial responsable")
    name: str = Field(..., min_length=3, description="Nombre formal del instrumento o dataset")
    level: Literal["nacional", "subregional_pdet", "departamental", "municipal"] = Field(
        ..., description="Nivel territorial de emisión"
    )
    territory_scope: str = Field(..., description="Ámbito territorial formal (ej. PDET_01_MONTES_DE_MARIA)")
    pipeline_type: Literal["documental", "api_tabular"] = Field(
        ..., description="Tipo de pipeline de procesamiento"
    )
    document_format: Literal["pdf", "json_api", "geojson", "csv"] = Field(
        ..., description="Formato del artefacto original"
    )
    adoption_norm: str = Field(..., description="Norma jurídica o administrativa de adopción")
    validity_start_year: int = Field(..., ge=1990, le=2050, description="Año inicial de vigencia")
    validity_end_year: int | None = Field(default=None, ge=1990, le=2050, description="Año final de vigencia si aplica")
    status: Literal["vigente", "derogado", "transitorio"] = Field(..., description="Estado normativo actual")
    canonical_url: str = Field(..., description="URL oficial canónica de acceso")
    access_type: Literal["descarga_directa", "api_socrata", "navegador"] = Field(
        ..., description="Modalidad de acceso técnico"
    )
    rate_limit: str = Field(..., description="Límite de tasa documentado")
    license: str = Field(..., description="Condición de uso o licencia pública")
    provenance_class: Literal["official_government"] | None = "official_government"
    source_type: Literal["document_context"] | None = "document_context"
    consent_status: Literal["not_applicable"] | None = "not_applicable"
    allowed_for_training: Literal[False] | None = False
    usage_state: Literal["context_only"] | None = "context_only"
    approval_status: Literal["pending_review", "approved", "rejected", "pending_context_review", "approved_for_context"] | None = "pending_review"
    sha256: str | None = Field(default=None, pattern=SHA256_PATTERN, description="Hash SHA-256 verificado")
    byte_size: int | None = Field(default=None, ge=0, description="Tamaño verificado en bytes")
    content_type: str | None = Field(default=None, description="Content-Type HTTP verificado")


class ReviewEventRecord(BaseModel):
    """Evento individual e inmutable dentro de la bitácora append-only de revisiones humanas."""
    model_config = _STRICT

    event_id: str = Field(..., min_length=3, max_length=64, description="Identificador único del evento de revisión")
    timestamp_utc: str = Field(..., pattern=ISO_DATE_PATTERN, description="Marca temporal ISO 8601 UTC")
    reviewer_id: str = Field(..., min_length=3, max_length=64, description="Identificador del revisor humano declarado")
    reviewer_auth_mode: Literal["declarado_sin_autenticacion"] = "declarado_sin_autenticacion"
    decision: Literal["approved_for_context", "rejected", "pending_context_review"] = Field(..., description="Decisión emitida")
    review_notes: str = Field(..., min_length=1, max_length=2000, description="Justificación o notas de la decisión")
    previous_status: str | None = Field(default=None, description="Estado previo del documento antes de este evento")
    event_type: Literal["human_decision", "test"] = Field(
        default="human_decision",
        description="Naturaleza del evento: 'human_decision' para decisiones reales, 'test' para pruebas automatizadas",
    )
    is_valid_human_approval: bool = Field(
        default=True,
        description="False si es evento de prueba o técnico que no constituye aprobación humana",
    )


class DocumentMetadataRecord(BaseModel):
    """Metadatos formales de un documento descargado y verificado en el Atlas.

    Invariante: Todo documento es estrictamente 'document_context', nunca testimonio ni corpus oro.
    """
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=100)
    entity: str = Field(..., min_length=2)
    title: str = Field(..., min_length=3)
    level: Literal["nacional", "subregional_pdet", "departamental", "municipal"]
    territory_scope: str
    pipeline_type: Literal["documental", "api_tabular"]
    document_format: Literal["pdf", "json_api", "geojson", "csv"]
    canonical_url: str
    download_date: str = Field(..., pattern=ISO_DATE_PATTERN, description="Fecha ISO de descarga o captura")
    sha256: str = Field(..., pattern=SHA256_PATTERN, description="Hash SHA-256 criptográfico verificado del contenido")
    byte_size: int = Field(..., ge=0, description="Tamaño exacto del archivo en bytes")
    content_path: str = Field(..., description="Ruta relativa del archivo almacenado (ej. sources/{sha256}.pdf)")

    # Invariantes de Soberanía y Gobernanza Epistémica (No modificables)
    source_type: Literal["document_context"] = "document_context"
    provenance_class: Literal["official_government"] = "official_government"
    consent_status: Literal["not_applicable"] = "not_applicable"
    allowed_for_training: Literal[False] = False
    usage_state: Literal["context_only"] = "context_only"

    # Puerta de Aprobación Humana (Human Gate) y Estado de Cuarentena
    approval_status: Literal["pending_review", "approved", "rejected", "pending_context_review", "approved_for_context"] = "pending_review"
    status: Literal["pending_review", "approved", "rejected", "pending_context_review", "approved_for_context", "revised_2026"] | None = None
    instrument_type: str | None = None
    previous_source_id: str | None = None
    approval_notes: str = Field(default="", max_length=10000)
    approval_timestamp: str | None = Field(default=None, pattern=ISO_DATE_PATTERN)
    reviewer_id: str | None = Field(default=None, min_length=3, max_length=64)
    reviewer_auth_mode: Literal["declarado_sin_autenticacion"] | None = None
    review_events: list[ReviewEventRecord] = Field(default_factory=list, description="Historial append-only de decisiones humanas")
    review_history_recovery: Literal["recovered_from_logs", "unavailable", "pristine"] | None = Field(
        default=None,
        description="Estado de recuperación forense del historial de revisiones si hubo intervención",
    )


class VerificationPolicyResult(BaseModel):
    """Resultado determinista de la verificación de políticas e invariantes de un documento."""
    model_config = _STRICT

    source_id: str
    is_official: bool
    sha256_verified: bool
    governance_verified: bool
    territory_matches: bool
    is_valid: bool
    violations: list[str] = Field(default_factory=list)


class AtlasManifestState(BaseModel):
    """Estado persistente del manifiesto de documentos recolectados en el Atlas."""
    model_config = _STRICT

    version: Literal["1.0.0"] = "1.0.0"
    last_updated: str = Field(..., pattern=ISO_DATE_PATTERN)
    documents: dict[str, DocumentMetadataRecord] = Field(
        default_factory=dict, description="Diccionario de documentos indexados por source_id"
    )
