from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from apps.atlas.schemas.document_schemas import ISO_DATE_PATTERN

_STRICT = ConfigDict(extra="forbid", strict=True)

AcquisitionLifecycleStatus = Literal[
    "discovered",
    "authority_verified",
    "queued_for_acquisition",
    "acquired_unreviewed",
    "integrity_verified",
    "pending_context_review",
    "superseded_candidate",
    "revised_2026",
    "approved_for_context",
    "rejected",
]


class WebDiscoveryQuery(BaseModel):
    """Consulta de entrada para el descubrimiento territorial autónomo en la web."""
    model_config = _STRICT

    department: str = Field(..., min_length=2)
    municipality: str = Field(..., min_length=2)
    divipola: str = Field(..., pattern=r"^\d{5}$")
    subregion: str | None = None
    instrument_types: list[str] = Field(..., min_length=1)
    max_documents_to_acquire: int = Field(default=1, ge=1, le=5)


class CandidateProvenanceRecord(BaseModel):
    """Registro de trazabilidad de un candidato a través de la cascada de adquisición."""
    model_config = _STRICT

    source_id: str = Field(..., min_length=3, max_length=120)
    url: str = Field(..., min_length=5)
    final_url: str | None = None
    title: str = Field(..., min_length=2)
    entity: str = Field(..., min_length=2)
    instrument_type: str
    territory_scope: str
    discovery_adapter: str
    provenance_chain: list[str] = Field(default_factory=list)
    status: AcquisitionLifecycleStatus = "discovered"
    is_superseded: bool = False
    http_status: int | None = None
    content_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    byte_size: int | None = None
    sha256: str | None = None
    content_path: str | None = None
    discard_reason: str | None = None
    timestamp_utc: str = Field(..., pattern=ISO_DATE_PATTERN)

    # Invariantes de gobernanza
    source_type: Literal["document_context", "tabular_context"] = "document_context"
    allowed_for_training: Literal[False] = False
    usage_state: Literal["context_only"] = "context_only"
