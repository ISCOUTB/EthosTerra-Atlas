from __future__ import annotations

from typing import Literal, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from src.domain.v2.document_schemas import EvidenceSpan, ExtractedKnowledge


class ContributionRulesSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    fixed_value: float | None = Field(default=None, ge=0.0, le=1.0)
    fuzzy_variable: str | None = None
    fuzzy_rules: list[dict[str, Any]] | None = None


class GoalSpecArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(default="1.0", pattern=r"^\d+\.\d+$")
    display_name: str
    description: str
    pyramid_level: Literal["SURVIVAL", "DUTY", "OPPORTUNITY", "NEED", "ATTENTION_CYCLE"]
    sub_level: Literal[
        "L1_SURVIVAL", "L2_OBLIGATION", "L3_PRODUCTIVE_DEVELOPMENT",
        "L4_SKILLS_AND_RESOURCES", "L5_SOCIAL", "L6_LEISURE"
    ] | None = None
    activation_when: str
    contribution_rules: ContributionRulesSchema
    plan_ref: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    effects: dict[str, Any] | None = None
    normative_tags: list[str] = Field(default_factory=list)


class StepSpecSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    action: str
    args: dict[str, Any] = Field(default_factory=dict)
    condition: str | None = None


class PlanSpecArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(default="1.0", pattern=r"^\d+\.\d+$")
    description: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[StepSpecSchema] = Field(..., min_length=1)
    on_timeout: list[StepSpecSchema] = Field(default_factory=list)
    on_failure: list[StepSpecSchema] = Field(default_factory=list)


class ArtifactSpecSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    artifact_id: str
    artifact_type: Literal["goal", "plan"]
    operation: Literal["crear", "actualizar", "eliminar"]
    target_rel_path: str
    content: GoalSpecArtifact | PlanSpecArtifact
    support_status: Literal["supported", "not_supported"]
    requires_simulator_extension: bool = False


class ConflictAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    alternative_id: str
    description: str
    trade_offs: str
    artifacts_proposed: list[dict[str, Any]]


class ApprovalMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    approver_id: str
    approved_at: datetime
    approved_json_hash: str
    notes: str | None = None


class ValidationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    has_blocking_errors: bool = False
    blocking_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    syntax_valid: bool = True
    runtime_compatible: Literal["yes", "no", "unknown"] = "unknown"
    requires_simulation_test: bool = True


class OperationalDocumentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["2.0.0"] = "2.0.0"
    experiment_id: str
    document_id: str
    status: Literal["Borrador", "Analizado", "Requiere_Revision", "Rechazado", "Aprobado"]
    review_status: Literal["not_required", "pending", "approved", "rejected"]
    requires_human_review: bool
    tipo_caso: Literal["puro", "conflicto"]

    source_refs: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    extracted_knowledge: ExtractedKnowledge

    artifacts: list[ArtifactSpecSchema] = Field(default_factory=list)
    selected_alternative: str | None = None
    alternatives: list[ConflictAlternative] = Field(default_factory=list)

    validation_status: ValidationSummary = Field(default_factory=ValidationSummary)
    approval_metadata: ApprovalMetadata | None = None
