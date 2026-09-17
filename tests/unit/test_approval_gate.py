from __future__ import annotations

import pytest
from datetime import datetime, timezone
import copy

from src.domain.v2.document_schemas import EvidenceSpan, ExtractedKnowledge
from src.domain.v2.operational_schemas import (
    OperationalDocumentSchema,
    ArtifactSpecSchema,
    GoalSpecArtifact,
    PlanSpecArtifact,
    StepSpecSchema,
    ContributionRulesSchema,
    ApprovalMetadata,
    ValidationSummary,
    ConflictAlternative,
)
from src.application.canonical_hasher import compute_canonical_hash
from src.application.approval_gate import assert_yaml_generation_allowed, YAMLGenerationBlocked


from src.domain.v2.document_schemas import EpistemicItem

def make_valid_document() -> OperationalDocumentSchema:
    knowledge = ExtractedKnowledge(
        actor_alias=EpistemicItem(status="observed", value="peasant_01", evidence_ref="frag_01"),
        territory_context=EpistemicItem(status="not_stated", value=None),
        beliefs=[],
        desires=[EpistemicItem(status="observed", value="alistar suelo fértil", evidence_ref="frag_01")],
        intentions=[EpistemicItem(status="observed", value="prepare_land", evidence_ref="frag_01")],
        requirements=[EpistemicItem(status="required", value={"resource": "tools"}, evidence_ref="frag_01")],
        detected_conflicts=[],
        emotions={
            "happiness": EpistemicItem(status="unknown", value=None),
            "hopeful": EpistemicItem(status="unknown", value=None),
            "secure": EpistemicItem(status="unknown", value=None),
        },
        social_relations=[]
    )

    evidence = EvidenceSpan(
        fragment_id="frag_01",
        source_ref="diario_01.txt",
        start_char=0,
        end_char=100,
        text_quote="El campesino decide preparar el terreno para sembrar..."
    )

    goal_art = GoalSpecArtifact(
        id="prepare_land",
        version="1.0",
        display_name="Preparar Terreno",
        description="Preparar la tierra para el próximo ciclo",
        pyramid_level="ATTENTION_CYCLE",
        sub_level="L3_PRODUCTIVE_DEVELOPMENT",
        activation_when="state.hasLandWithSeason('NONE') || state.hasLandWithSeason('FALLOW')",
        contribution_rules=ContributionRulesSchema(fixed_value=0.6),
        plan_ref="prepare_land_plan_v1",
        effects=None,
        normative_tags=["agro", "land"]
    )

    plan_art = PlanSpecArtifact(
        id="prepare_land_plan_v1",
        version="1.0",
        description="Ejecutar preparación",
        preconditions=[],
        steps=[
            StepSpecSchema(
                id="prepare_op",
                action="agro_ecosystem_operation",
                args={"operation": "PREPARE"}
            ),
            StepSpecSchema(
                id="record_episode",
                action="emit_episode",
                args={"text": "He trabajado en la preparación del terreno para asegurar un suelo fértil."}
            )
        ],
        on_timeout=[],
        on_failure=[]
    )

    artifacts = [
        ArtifactSpecSchema(
            artifact_id="goal_prepare_land",
            artifact_type="goal",
            operation="crear",
            target_rel_path="goals/agro/prepare_land.yaml",
            content=goal_art,
            support_status="supported",
            requires_simulator_extension=False
        ),
        ArtifactSpecSchema(
            artifact_id="plan_prepare_land",
            artifact_type="plan",
            operation="crear",
            target_rel_path="plans/agro/prepare_land_plan_v1.yaml",
            content=plan_art,
            support_status="supported",
            requires_simulator_extension=False
        )
    ]

    doc = OperationalDocumentSchema(
        schema_version="2.0.0",
        experiment_id="exp_vertical_001",
        document_id="doc_diario_001",
        status="Aprobado",
        review_status="approved",
        requires_human_review=False,
        tipo_caso="puro",
        source_refs=["diario_01.txt"],
        evidence_spans=[evidence],
        extracted_knowledge=knowledge,
        artifacts=artifacts,
        selected_alternative=None,
        alternatives=[],
        validation_status=ValidationSummary(has_blocking_errors=False),
        approval_metadata=None
    )

    # Calcular hash canónico y firmar
    h = compute_canonical_hash(doc)
    doc.approval_metadata = ApprovalMetadata(
        approver_id="investigador_principal",
        approved_at=datetime.now(timezone.utc),
        approved_json_hash=h,
        notes="Aprobado formalmente"
    )
    return doc


def test_gate_allows_valid_approved_document():
    doc = make_valid_document()
    # No debe levantar ninguna excepción
    assert_yaml_generation_allowed(doc)


def test_gate_blocks_status_analizado():
    doc = make_valid_document()
    doc.status = "Analizado"
    with pytest.raises(YAMLGenerationBlocked, match="Solo documentos con estado 'Aprobado'"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_status_requiere_revision():
    doc = make_valid_document()
    doc.status = "Requiere_Revision"
    with pytest.raises(YAMLGenerationBlocked, match="Solo documentos con estado 'Aprobado'"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_status_rechazado():
    doc = make_valid_document()
    doc.status = "Rechazado"
    doc.review_status = "rejected"
    with pytest.raises(YAMLGenerationBlocked):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_review_pending():
    doc = make_valid_document()
    doc.review_status = "pending"
    with pytest.raises(YAMLGenerationBlocked, match="revisión humana pendiente"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_review_rejected():
    doc = make_valid_document()
    doc.review_status = "rejected"
    with pytest.raises(YAMLGenerationBlocked, match="revisión humana fue rechazada"):
        assert_yaml_generation_allowed(doc)


def test_gate_allows_previously_flagged_human_review_when_approved():
    doc = make_valid_document()
    # Si el documento originalmente requirió revisión pero el investigador ya lo aprobó
    doc.requires_human_review = True
    doc.review_status = "approved"
    # Recalcular hash para asegurar integridad
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    # Debe permitir la generación
    assert_yaml_generation_allowed(doc)


def test_gate_blocks_modified_hash():
    doc = make_valid_document()
    # Corrompemos el hash guardado
    doc.approval_metadata.approved_json_hash = "hash_alterado_00000000000000000000000"
    with pytest.raises(YAMLGenerationBlocked, match="Violación de integridad"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_unsupported_artifact():
    doc = make_valid_document()
    doc.artifacts[0].support_status = "not_supported"
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    with pytest.raises(YAMLGenerationBlocked, match="not_supported"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_simulator_extension_required():
    doc = make_valid_document()
    doc.artifacts[0].requires_simulator_extension = True
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    with pytest.raises(YAMLGenerationBlocked, match="requiere extensión previa"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_missing_source_refs():
    doc = make_valid_document()
    doc.source_refs = []
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    with pytest.raises(YAMLGenerationBlocked, match="Falta trazabilidad: se requiere al menos una referencia de fuente"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_missing_evidence_spans():
    doc = make_valid_document()
    doc.evidence_spans = []
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    with pytest.raises(YAMLGenerationBlocked, match="Falta trazabilidad: se requiere al menos una evidencia textual"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_conflict_without_alternative():
    doc = make_valid_document()
    doc.tipo_caso = "conflicto"
    doc.selected_alternative = None
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    with pytest.raises(YAMLGenerationBlocked, match="No se ha seleccionado una alternativa para el Caso Conflictivo"):
        assert_yaml_generation_allowed(doc)


def test_gate_allows_conflict_with_selected_alternative():
    doc = make_valid_document()
    doc.tipo_caso = "conflicto"
    doc.selected_alternative = "alt_01"
    doc.alternatives = [
        ConflictAlternative(
            alternative_id="alt_01",
            description="Opción 1",
            trade_offs="Costo balanceado",
            artifacts_proposed=[]
        )
    ]
    h = compute_canonical_hash(doc)
    doc.approval_metadata.approved_json_hash = h
    # Debe permitir
    assert_yaml_generation_allowed(doc)


def test_deterministic_hash_generation():
    doc1 = make_valid_document()
    doc2 = make_valid_document()
    assert compute_canonical_hash(doc1) == compute_canonical_hash(doc2)


@pytest.mark.parametrize("field_to_modify,new_value", [
    ("experiment_id", "exp_tampered_999"),
    ("document_id", "doc_tampered_888"),
    ("schema_version", "2.1.0"),
    ("tipo_caso", "conflicto"),
    ("source_refs", ["otro_archivo.txt"]),
    ("selected_alternative", "alt_modificada"),
])
def test_gate_blocks_tampering_of_each_canonical_field(field_to_modify, new_value):
    doc = make_valid_document()
    original_hash = doc.approval_metadata.approved_json_hash
    # Modificamos el campo en el objeto sin actualizar el hash firmado
    setattr(doc, field_to_modify, new_value)
    # El hash actual ya no debe coincidir con el original_hash
    assert compute_canonical_hash(doc) != original_hash
    with pytest.raises(YAMLGenerationBlocked, match="Violación de integridad"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_tampering_of_artifacts():
    doc = make_valid_document()
    original_hash = doc.approval_metadata.approved_json_hash
    # Alteramos la descripción del plan dentro de los artefactos
    doc.artifacts[1].content.description = "Descripción clandestina alterada"
    assert compute_canonical_hash(doc) != original_hash
    with pytest.raises(YAMLGenerationBlocked, match="Violación de integridad"):
        assert_yaml_generation_allowed(doc)


def test_gate_blocks_tampering_of_extracted_knowledge():
    doc = make_valid_document()
    original_hash = doc.approval_metadata.approved_json_hash
    # Alteramos las intenciones declaradas
    doc.extracted_knowledge.intentions.append(EpistemicItem(status="inferred", value="intencion_no_aprobada"))
    assert compute_canonical_hash(doc) != original_hash
    with pytest.raises(YAMLGenerationBlocked, match="Violación de integridad"):
        assert_yaml_generation_allowed(doc)
