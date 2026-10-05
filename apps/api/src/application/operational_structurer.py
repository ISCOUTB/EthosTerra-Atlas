from __future__ import annotations

import logging
from typing import Any

from src.domain.v2.document_schemas import EvidenceSpan, ExtractedKnowledge
from src.domain.v2.operational_schemas import (
    OperationalDocumentSchema,
    ArtifactSpecSchema,
    GoalSpecArtifact,
    PlanSpecArtifact,
    StepSpecSchema,
    ContributionRulesSchema,
    ValidationSummary,
)
from src.domain.v2.action_catalog_service import ActionCatalogService

logger = logging.getLogger("operational_structurer")


def structure_operational_document(
    doc_id: str,
    experiment_id: str,
    tipo_caso: str,
    source_filename: str,
    source_hash: str,
    evidence_spans: list[EvidenceSpan],
    extracted_knowledge: ExtractedKnowledge,
    actor_alias_override: str | None = None,
) -> OperationalDocumentSchema:
    """
    Estructura dinámicamente artefactos GoalSpec y PlanSpec a partir
    del conocimiento epistemológico extraído, validando cada acción contra el catálogo.
    """
    # 1. Determinar actor de forma fundamentada
    actor = "unknown_peasant"
    if extracted_knowledge.actor_alias.status == "observed" and extracted_knowledge.actor_alias.value:
        actor = extracted_knowledge.actor_alias.value
    elif actor_alias_override:
        actor = actor_alias_override

    # 2. Determinar si hay conflictos, inyecciones o ambigüedad
    has_conflicts = len(extracted_knowledge.detected_conflicts) > 0
    primary_intention_item = (
        extracted_knowledge.intentions[0] if extracted_knowledge.intentions else None
    )
    intention_val = primary_intention_item.value if primary_intention_item else None
    is_unknown_intention = (
        primary_intention_item is None
        or primary_intention_item.status == "unknown"
        or not intention_val
    )

    # Si hay conflicto o intención ambigua, requerir revisión humana obligatoria
    if has_conflicts or is_unknown_intention or tipo_caso == "conflicto":
        blocking_reasons = []
        if has_conflicts:
            for c in extracted_knowledge.detected_conflicts:
                blocking_reasons.append(c.rationale or f"Conflicto detectado: {c.value}")
        if is_unknown_intention:
            blocking_reasons.append(
                "La intención no pudo ser determinada con certeza o no corresponde a una acción soportada."
            )

        return OperationalDocumentSchema(
            schema_version="2.0.0",
            experiment_id=experiment_id,
            document_id=doc_id,
            status="Requiere_Revision",
            review_status="pending",
            requires_human_review=True,
            tipo_caso="conflicto",
            source_refs=[source_filename],
            evidence_spans=evidence_spans,
            extracted_knowledge=extracted_knowledge,
            artifacts=[],
            selected_alternative=None,
            alternatives=[],
            validation_status=ValidationSummary(
                has_blocking_errors=True,
                blocking_errors=blocking_reasons,
                warnings=[],
                syntax_valid=True,
                runtime_compatible="unknown",
                requires_simulation_test=True,
            ),
            approval_metadata=None,
        )

    # 3. Derivación dinámica según intención
    artifacts: list[ArtifactSpecSchema] = []

    if intention_val == "prepare_land":
        goal_art = GoalSpecArtifact(
            id="prepare_land",
            version="1.0",
            display_name="Preparar Terreno",
            description=f"Preparar la tierra para el próximo ciclo agrícola ({actor}).",
            pyramid_level="ATTENTION_CYCLE",
            sub_level="L3_PRODUCTIVE_DEVELOPMENT",
            activation_when="state.hasLandWithSeason('NONE') || state.hasLandWithSeason('FALLOW')",
            contribution_rules=ContributionRulesSchema(fixed_value=0.6),
            plan_ref="prepare_land_plan_v1",
            effects=None,
            normative_tags=["agro", "land"],
        )
        plan_art = PlanSpecArtifact(
            id="prepare_land_plan_v1",
            version="1.0",
            description=f"Ejecutar labores de preparación del agroecosistema ({actor}).",
            preconditions=[],
            steps=[
                StepSpecSchema(
                    id="prepare_op",
                    action="agro_ecosystem_operation",
                    args={"operation": "PREPARE"},
                ),
                StepSpecSchema(
                    id="record_episode",
                    action="emit_episode",
                    args={
                        "text": f"He trabajado en la preparación del terreno para asegurar un suelo fértil ({actor}).",
                        "tags": ["agro", "land"],
                    },
                ),
            ],
            on_timeout=[],
            on_failure=[],
        )
        artifacts = [
            ArtifactSpecSchema(
                artifact_id="goal_prepare_land",
                artifact_type="goal",
                operation="crear",
                target_rel_path="data/ebdi/goals/agro/prepare_land.yaml",
                content=goal_art,
                support_status="supported",
                requires_simulator_extension=False,
            ),
            ArtifactSpecSchema(
                artifact_id="plan_prepare_land",
                artifact_type="plan",
                operation="crear",
                target_rel_path="data/ebdi/plans/agro/prepare_land_plan_v1.yaml",
                content=plan_art,
                support_status="supported",
                requires_simulator_extension=False,
            ),
        ]

    elif intention_val in ("sell_crop", "sell_harvest"):
        goal_art = GoalSpecArtifact(
            id="sell_crop",
            version="1.0",
            display_name="Vender Cosecha",
            description=f"Venta de cosecha en el mercado local para sustentar el hogar ({actor}).",
            pyramid_level="OPPORTUNITY",
            sub_level="L3_PRODUCTIVE_DEVELOPMENT",
            activation_when="state.hasHarvestedWeight()",
            contribution_rules=ContributionRulesSchema(fixed_value=0.98),
            plan_ref="sell_crop_plan_v1",
            effects=None,
            normative_tags=["agro", "market"],
        )
        plan_art = PlanSpecArtifact(
            id="sell_crop_plan_v1",
            version="1.0",
            description=f"Ejecutar venta de cosecha en el mercado ({actor}).",
            preconditions=[],
            steps=[
                StepSpecSchema(
                    id="sell_op",
                    action="agro_ecosystem_operation",
                    args={"operation": "SELL", "crop_type": "frijol"},
                ),
                StepSpecSchema(
                    id="record_sell_episode",
                    action="emit_episode",
                    args={
                        "text": f"He vendido la cosecha en el mercado local para cubrir necesidades familiares ({actor}).",
                        "tags": ["agro", "sell", "market"],
                    },
                ),
            ],
            on_timeout=[],
            on_failure=[],
        )
        artifacts = [
            ArtifactSpecSchema(
                artifact_id="goal_sell_crop",
                artifact_type="goal",
                operation="crear",
                target_rel_path="data/ebdi/goals/agro/sell_crop.yaml",
                content=goal_art,
                support_status="supported",
                requires_simulator_extension=False,
            ),
            ArtifactSpecSchema(
                artifact_id="plan_sell_crop",
                artifact_type="plan",
                operation="crear",
                target_rel_path="data/ebdi/plans/agro/sell_crop_plan_v1.yaml",
                content=plan_art,
                support_status="supported",
                requires_simulator_extension=False,
            ),
        ]

    elif intention_val in ("fertilize_crop", "organic_fertilization", "fertilizar_cultivo"):
        # Determinar si requiere apoyo de jornales
        has_jornales = any(
            isinstance(req.value, dict) and req.value.get("resource") == "jornales"
            for req in extracted_knowledge.requirements
        )

        steps = []
        if has_jornales:
            steps.append(
                StepSpecSchema(
                    id="request_labor",
                    action="send_society_collaboration",
                    args={"flag": "fertilize_labor", "amount": 2, "guard": "request"},
                )
            )
        else:
            steps.append(
                StepSpecSchema(
                    id="consume_tools",
                    action="consume_resource",
                    args={"key": "tools", "amount": 1},
                )
            )

        steps.append(
            StepSpecSchema(
                id="record_fertilize_episode",
                action="emit_episode",
                args={
                    "text": f"He aplicado fertilizante orgánico para recuperar la productividad del suelo ({actor}).",
                    "tags": ["agro", "fertilizer", "soil"],
                },
            )
        )

        goal_art = GoalSpecArtifact(
            id="fertilize_crop",
            version="1.0",
            display_name="Fertilización Orgánica de Cultivo",
            description=f"Aplicar fertilizante orgánico para recuperar productividad del suelo ({actor}).",
            pyramid_level="ATTENTION_CYCLE",
            sub_level="L3_PRODUCTIVE_DEVELOPMENT",
            activation_when="state.hasLandWithSeason('NONE') || state.hasLandWithSeason('FALLOW')",
            contribution_rules=ContributionRulesSchema(fixed_value=0.75),
            plan_ref="fertilize_crop_plan_v1",
            effects=None,
            normative_tags=["agro", "soil", "fertilizer"],
        )
        plan_art = PlanSpecArtifact(
            id="fertilize_crop_plan_v1",
            version="1.0",
            description=f"Labores de fertilización orgánica en parcela ({actor}).",
            preconditions=[],
            steps=steps,
            on_timeout=[],
            on_failure=[],
        )
        artifacts = [
            ArtifactSpecSchema(
                artifact_id="goal_fertilize_crop",
                artifact_type="goal",
                operation="crear",
                target_rel_path="data/ebdi/goals/agro/fertilize_crop.yaml",
                content=goal_art,
                support_status="supported",
                requires_simulator_extension=False,
            ),
            ArtifactSpecSchema(
                artifact_id="plan_fertilize_crop",
                artifact_type="plan",
                operation="crear",
                target_rel_path="data/ebdi/plans/agro/fertilize_crop_plan_v1.yaml",
                content=plan_art,
                support_status="supported",
                requires_simulator_extension=False,
            ),
        ]

    else:
        # Intención no reconocida o no soportada en el catálogo
        return OperationalDocumentSchema(
            schema_version="2.0.0",
            experiment_id=experiment_id,
            document_id=doc_id,
            status="Requiere_Revision",
            review_status="pending",
            requires_human_review=True,
            tipo_caso="conflicto",
            source_refs=[source_filename],
            evidence_spans=evidence_spans,
            extracted_knowledge=extracted_knowledge,
            artifacts=[],
            selected_alternative=None,
            alternatives=[],
            validation_status=ValidationSummary(
                has_blocking_errors=True,
                blocking_errors=[
                    f"Intención '{intention_val}' no se puede mapear de forma determinista al catálogo de acciones soportadas."
                ],
                warnings=[],
                syntax_valid=True,
                runtime_compatible="unknown",
                requires_simulation_test=True,
            ),
            approval_metadata=None,
        )

    # 4. Validar cada paso contra ActionCatalogService
    validation_errors = []
    for art in artifacts:
        if isinstance(art.content, PlanSpecArtifact):
            for step in art.content.steps:
                ok, errs = ActionCatalogService.validate_step(step.action, step.args)
                if not ok:
                    validation_errors.extend(errs)

    has_errors = len(validation_errors) > 0

    return OperationalDocumentSchema(
        schema_version="2.0.0",
        experiment_id=experiment_id,
        document_id=doc_id,
        status="Analizado" if not has_errors else "Error_Validacion",
        review_status="not_required" if (tipo_caso == "puro" and not has_errors) else "pending",
        requires_human_review=tipo_caso == "conflicto" or has_errors,
        tipo_caso=tipo_caso,
        source_refs=[source_filename],
        evidence_spans=evidence_spans,
        extracted_knowledge=extracted_knowledge,
        artifacts=artifacts,
        selected_alternative=None,
        alternatives=[],
        validation_status=ValidationSummary(
            has_blocking_errors=has_errors,
            blocking_errors=validation_errors,
            warnings=[],
            syntax_valid=not has_errors,
            runtime_compatible="unknown",
            requires_simulation_test=True,
        ),
        approval_metadata=None,
    )
