from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal, Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.schemas import CasoPuro, CasoConflictivo

INTENT_ID_REGEX = r"^[a-zA-Z0-9_-]{1,64}$"
_ID_PATTERN = re.compile(INTENT_ID_REGEX)


def validate_identifier(v: str) -> str:
    """Valida estrictamente el identificador con lista blanca para prevenir path traversal o inyecciones."""
    if not v or not isinstance(v, str):
        raise ValueError("El identificador no puede estar vacío.")
    v_clean = v.strip()
    if v_clean != v:
        raise ValueError("El identificador no debe contener espacios al inicio ni al final.")
    if ".." in v or "/" in v or "\\" in v or "\x00" in v:
        raise ValueError("El identificador contiene secuencias o caracteres de ruta prohibidos.")
    if not _ID_PATTERN.match(v):
        raise ValueError(
            f"El identificador '{v}' no cumple la lista blanca: debe ser alfanumérico, guion o guion bajo (1-64 caracteres)."
        )
    return v


# Unión discriminada estricta para Caso Puro y Caso Conflictivo
IntentPayload = Annotated[CasoPuro | CasoConflictivo, Field(discriminator="tipo")]


class HumanReviewMetadata(BaseModel):
    """Metadatos formales de revisión humana experta para el Bloque B5."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["pendiente", "aprobado", "observado", "rechazado"] = Field(
        default="pendiente",
        description="Estado de la revisión epistemológica y metodológica",
    )
    reviewer: str = Field(
        default="investigador_principal",
        min_length=1,
        max_length=64,
        description="Identidad del evaluador o investigador humano responsable",
    )
    reviewed_at: datetime | None = Field(
        default=None,
        description="Marca temporal UTC de la última evaluación formal",
    )
    comments: str = Field(
        default="",
        max_length=2000,
        description="Observaciones metodológicas y notas contextuales del investigador",
    )
    decision_rationale: str = Field(
        default="",
        max_length=2000,
        description="Justificación formal de la decisión de aprobación/observación/rechazo",
    )
    requires_additional_review: bool = Field(
        default=False,
        description="Indica si el caso requiere una segunda revisión o escalamiento metodológico",
    )


class CreateIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., description="Identificador único del intento (alfanumérico, '-', '_', 1-64 chars)")
    author: str = Field(default="operador_manual", min_length=1, max_length=64, description="Identidad del autor o creador")
    intent: IntentPayload = Field(..., description="Cuerpo del caso (Caso Puro o Caso Conflictivo)")
    human_review: HumanReviewMetadata | None = Field(
        default=None,
        description="Revisión humana experta opcional al momento de creación",
    )

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_identifier(v)


class UpdateIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    author: str = Field(default="operador_manual", min_length=1, max_length=64, description="Identidad del editor")
    intent: IntentPayload = Field(..., description="Cuerpo actualizado del caso")
    human_review: HumanReviewMetadata | None = Field(
        default=None,
        description="Revisión humana experta actualizada",
    )


class IntentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    canonical_hash: str
    version: int = 1


class IntentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    intent: IntentPayload
    metadata: IntentMetadata
    human_review: HumanReviewMetadata = Field(default_factory=HumanReviewMetadata)


class TrashMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deleted_at: datetime
    deleted_by: str
    retention_days: int
    expires_at: datetime
    is_expired: bool


class TrashIntentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    intent: IntentPayload
    metadata: IntentMetadata
    trash_metadata: TrashMetadata
    human_review: HumanReviewMetadata = Field(default_factory=HumanReviewMetadata)


class RestoreIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    restored_by: str = Field(default="operador_manual", min_length=1, max_length=64)


class PurgeTrashRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    purged_by: str = Field(default="operador_manual", min_length=1, max_length=64)


class PurgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purged_count: int
    purged_ids: list[str]
    timestamp: datetime
    triggered_by: str

