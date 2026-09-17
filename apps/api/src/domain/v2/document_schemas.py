from __future__ import annotations

from typing import Literal, Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

EpistemicStatus = Literal[
    "observed",     # Extraído directamente del texto sin ambigüedad
    "inferred",     # Deducido lógicamente a partir de elementos contextuales
    "proposed",     # Propuesto por el modelo como acción o meta hipotética
    "required",     # Requerido como precondición o recurso necesario
    "unknown",      # Evaluado pero desconocido o no determinable
    "not_stated"    # No mencionado en ninguna parte de la fuente
]


class EpistemicItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: EpistemicStatus
    value: Any | None = None
    evidence_ref: str | None = None
    rationale: str | None = None


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    fragment_id: str
    source_ref: str
    start_char: int
    end_char: int
    text_quote: str


class ExtractedKnowledge(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    actor_alias: EpistemicItem
    territory_context: EpistemicItem
    beliefs: list[EpistemicItem] = Field(default_factory=list)
    desires: list[EpistemicItem] = Field(default_factory=list)
    intentions: list[EpistemicItem] = Field(default_factory=list)
    requirements: list[EpistemicItem] = Field(default_factory=list)
    detected_conflicts: list[EpistemicItem] = Field(default_factory=list)
    emotions: dict[str, EpistemicItem] = Field(default_factory=dict)
    social_relations: list[EpistemicItem] = Field(default_factory=list)


class DocumentAnalysisSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["2.0.0"] = "2.0.0"
    document_id: str
    source_type: Literal["synthetic_test", "interview", "peasant_diary", "policy_doc", "pasted_text"]
    document_hash: str
    extracted_knowledge: ExtractedKnowledge
    evidence_spans: list[EvidenceSpan]
    extraction_metadata: dict[str, Any]
