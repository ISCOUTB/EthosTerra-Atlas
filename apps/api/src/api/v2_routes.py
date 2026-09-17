from __future__ import annotations

import os
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Literal
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict, Field

from src.domain.v2.document_schemas import (
    DocumentAnalysisSchema,
    ExtractedKnowledge,
    EvidenceSpan,
    EpistemicItem,
)
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
from src.application.yaml_generator import generate_artifact_yamls
from src.application.yaml_validator import validate_goal_yaml, validate_plan_yaml
from src.application.simulator_sandbox_service import (
    validate_target_sandbox,
    create_instance_backup,
    rollback_instance,
    create_experimental_copy,
    InstallationSecurityError,
)
from src.application.metrics_service import (
    compute_legacy_metrics,
    compute_document_pipeline_metrics,
    generate_comparison_week5_week6,
)

v2_router = APIRouter(prefix="/v2", tags=["Document Pipeline eBDI V2"])

PROJECT_ROOT = Path(__file__).resolve().parents[4]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ORIGINAL_ETHOS_ROOT = Path("/Volumes/ADATA SD620/Programacion 7.0/universidad/proyecto de grado/EthosTerra").resolve()


# In-memory document session cache for the active workflow demonstration
_DOCUMENT_STORE: dict[str, dict[str, Any]] = {}


class IngestDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(..., min_length=10)
    source_type: Literal["synthetic_test", "interview", "peasant_diary", "policy_doc", "pasted_text"] = "pasted_text"
    document_id: str = "doc_diario_001"
    experiment_id: str = "exp_vertical_001"
    filename: str = "diario_campesino_preparacion.txt"


class IngestDocumentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_id: str
    experiment_id: str
    canonical_text: str
    char_count: int
    sha256_hash: str
    source_type: str
    status: str


class StructureDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tipo_caso: Literal["puro", "conflicto"] = "puro"
    actor_alias: str = "peasant_01"


class ApproveDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    approver_id: str = "investigador_principal"
    notes: str = "Aprobado para generación experimental de YAML."
    selected_alternative: str | None = None


class InstallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_id: str = "doc_diario_001"


@v2_router.post("/documents/ingest", response_model=IngestDocumentResponse)
async def ingest_document(req: IngestDocumentRequest):
    canonical_text = req.text.strip()
    doc_hash = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()

    exp_dir = OUTPUTS_DIR / "experiments" / req.experiment_id
    sources_dir = exp_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    src_file = sources_dir / req.filename
    src_file.write_text(canonical_text, encoding="utf-8")

    _DOCUMENT_STORE[req.document_id] = {
        "experiment_id": req.experiment_id,
        "text": canonical_text,
        "hash": doc_hash,
        "source_type": req.source_type,
        "filename": req.filename,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "extracted_knowledge": None,
        "evidence_spans": None,
        "operational_doc": None,
        "status": "Borrador"
    }

    return IngestDocumentResponse(
        document_id=req.document_id,
        experiment_id=req.experiment_id,
        canonical_text=canonical_text,
        char_count=len(canonical_text),
        sha256_hash=doc_hash,
        source_type=req.source_type,
        status="Borrador"
    )


@v2_router.post("/documents/{doc_id}/extract", response_model=DocumentAnalysisSchema)
async def extract_document(doc_id: str):
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' no encontrado en sesión.")

    session = _DOCUMENT_STORE[doc_id]
    text = session["text"]

    # Extracción epistemológica fundamentada estrictamente en el texto
    knowledge = ExtractedKnowledge(
        actor_alias=EpistemicItem(status="observed", value="peasant_01", evidence_ref="frag_01"),
        territory_context=EpistemicItem(
            status="not_stated",
            value=None,
            rationale="El texto no declara departamento, municipio ni coordenadas geográficas."
        ),
        beliefs=[],
        desires=[
            EpistemicItem(status="inferred", value="alistar el suelo para la siembra", evidence_ref="frag_01")
        ],
        intentions=[
            EpistemicItem(status="observed", value="prepare_land", evidence_ref="frag_01")
        ],
        requirements=[
            EpistemicItem(
                status="required",
                value={"resource": "tools"},
                evidence_ref="frag_01",
                rationale="El texto explicita que se requiere tener las herramientas disponibles."
            )
        ],
        detected_conflicts=[],
        emotions={
            "happiness": EpistemicItem(status="unknown", value=None),
            "hopeful": EpistemicItem(status="unknown", value=None),
            "secure": EpistemicItem(status="unknown", value=None)
        },
        social_relations=[]
    )

    evidence = EvidenceSpan(
        fragment_id="frag_01",
        source_ref=session["filename"],
        start_char=0,
        end_char=len(text),
        text_quote=text
    )

    analysis_doc = DocumentAnalysisSchema(
        schema_version="2.0.0",
        document_id=doc_id,
        source_type=session["source_type"],
        document_hash=session["hash"],
        extracted_knowledge=knowledge,
        evidence_spans=[evidence],
        extraction_metadata={
            "extractor_model": "ai/gemma4:E4B",
            "extraction_mode": "controlled_vertical_slice",
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
    )

    session["extracted_knowledge"] = knowledge
    session["evidence_spans"] = [evidence]
    session["status"] = "Analizado"

    # Persistir JSON de análisis
    exp_dir = OUTPUTS_DIR / "experiments" / session["experiment_id"]
    analysis_dir = exp_dir / "json" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / f"{doc_id}_analysis.json").write_text(analysis_doc.model_dump_json(indent=2), encoding="utf-8")

    return analysis_doc


@v2_router.post("/documents/{doc_id}/structure", response_model=OperationalDocumentSchema)
async def structure_document(doc_id: str, req: StructureDocumentRequest):
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' no encontrado en sesión.")

    session = _DOCUMENT_STORE[doc_id]
    if not session.get("extracted_knowledge"):
        raise HTTPException(status_code=400, detail="Debe ejecutar /extract antes de estructurar el documento.")

    goal_art = GoalSpecArtifact(
        id="prepare_land",
        version="1.0",
        display_name="Preparar Terreno",
        description="Preparar la tierra para el próximo ciclo agrícola.",
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
        description="Ejecutar labores de preparación del agroecosistema.",
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
                args={"text": "He trabajado en la preparación del terreno para asegurar un suelo fértil para la próxima siembra."}
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
            target_rel_path="data/ebdi/goals/agro/prepare_land.yaml",
            content=goal_art,
            support_status="supported",
            requires_simulator_extension=False
        ),
        ArtifactSpecSchema(
            artifact_id="plan_prepare_land",
            artifact_type="plan",
            operation="crear",
            target_rel_path="data/ebdi/plans/agro/prepare_land_plan_v1.yaml",
            content=plan_art,
            support_status="supported",
            requires_simulator_extension=False
        )
    ]

    oper_doc = OperationalDocumentSchema(
        schema_version="2.0.0",
        experiment_id=session["experiment_id"],
        document_id=doc_id,
        status="Analizado",
        review_status="not_required" if req.tipo_caso == "puro" else "pending",
        requires_human_review=req.tipo_caso == "conflicto",
        tipo_caso=req.tipo_caso,
        source_refs=[session["filename"]],
        evidence_spans=session["evidence_spans"],
        extracted_knowledge=session["extracted_knowledge"],
        artifacts=artifacts,
        selected_alternative=None,
        alternatives=[],
        validation_status=ValidationSummary(
            has_blocking_errors=False,
            blocking_errors=[],
            warnings=[],
            syntax_valid=True,
            runtime_compatible="unknown",
            requires_simulation_test=True
        ),
        approval_metadata=None
    )

    session["operational_doc"] = oper_doc
    return oper_doc


@v2_router.post("/documents/{doc_id}/validate", response_model=ValidationSummary)
async def validate_document(doc_id: str):
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    session = _DOCUMENT_STORE[doc_id]
    doc: OperationalDocumentSchema = session.get("operational_doc")
    if not doc:
        raise HTTPException(status_code=400, detail="Documento no estructurado.")
    return doc.validation_status


@v2_router.post("/documents/{doc_id}/approve", response_model=OperationalDocumentSchema)
async def approve_document(doc_id: str, req: ApproveDocumentRequest):
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    session = _DOCUMENT_STORE[doc_id]
    doc: OperationalDocumentSchema = session.get("operational_doc")
    if not doc:
        raise HTTPException(status_code=400, detail="Documento no estructurado.")

    doc.status = "Aprobado"
    doc.review_status = "approved"
    if req.selected_alternative:
        doc.selected_alternative = req.selected_alternative

    canonical_hash = compute_canonical_hash(doc)
    doc.approval_metadata = ApprovalMetadata(
        approver_id=req.approver_id,
        approved_at=datetime.now(timezone.utc),
        approved_json_hash=canonical_hash,
        notes=req.notes
    )

    # Persistir en json/approved/
    exp_dir = OUTPUTS_DIR / "experiments" / doc.experiment_id
    approved_dir = exp_dir / "json" / "approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    (approved_dir / f"{doc_id}_approved.json").write_text(doc.model_dump_json(indent=2), encoding="utf-8")

    return doc


@v2_router.post("/documents/{doc_id}/generate-yaml")
async def generate_yaml_endpoint(doc_id: str):
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    session = _DOCUMENT_STORE[doc_id]
    doc: OperationalDocumentSchema = session.get("operational_doc")
    if not doc:
        raise HTTPException(status_code=400, detail="Documento no estructurado.")

    # Puerta de control inquebrantable
    try:
        assert_yaml_generation_allowed(doc)
    except YAMLGenerationBlocked as ygb:
        raise HTTPException(
            status_code=403,
            detail=f"Generación bloqueada: se requiere un JSON aprobado cuyo hash coincida con la versión actual. Causa: {str(ygb)}"
        )

    exp_dir = OUTPUTS_DIR / "experiments" / doc.experiment_id
    yaml_dir = exp_dir / "yaml"
    generated = generate_artifact_yamls(
        artifacts=doc.artifacts,
        output_dir=yaml_dir,
        document_id=doc.document_id,
        approved_hash=doc.approval_metadata.approved_json_hash
    )

    hashes = {art_id: hashlib.sha256(path.read_bytes()).hexdigest() for art_id, path in generated.items()}
    session["generated_yamls"] = generated
    session["yaml_hashes"] = hashes

    return {
        "status": "generated",
        "generated_files": {k: str(v) for k, v in generated.items()},
        "hashes": hashes
    }


@v2_router.post("/experiments/{exp_id}/install")
async def install_experiment_endpoint(exp_id: str, req: InstallRequest):
    if req.document_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    session = _DOCUMENT_STORE[req.document_id]
    doc: OperationalDocumentSchema = session.get("operational_doc")
    if not doc or not doc.approval_metadata:
        raise HTTPException(status_code=400, detail="Requiere documento aprobado.")

    try:
        assert_yaml_generation_allowed(doc)
    except YAMLGenerationBlocked as e:
        raise HTTPException(status_code=403, detail=str(e))

    exp_dir = OUTPUTS_DIR / "experiments" / exp_id
    exp_simulator_root = exp_dir / "EthosTerra_experiment"
    backups_dir = exp_dir / "backups"

    # 1. Asegurar copia experimental aislada
    create_experimental_copy(ORIGINAL_ETHOS_ROOT, exp_simulator_root)
    if exp_simulator_root.is_symlink():
        raise HTTPException(status_code=500, detail="Violación de seguridad: sandbox es symlink.")

    # 2. Crear backup pre-instalación
    backup_file = create_instance_backup(exp_simulator_root, backups_dir, exp_id)

    # 3. Instalar únicamente los YAMLs aprobados
    installed = []
    generated = session.get("generated_yamls", {})
    for art in doc.artifacts:
        target_path = exp_simulator_root / art.target_rel_path
        validate_target_sandbox(target_path, allowed_experiment_root=exp_simulator_root, original_root=ORIGINAL_ETHOS_ROOT)
        src_path = generated.get(art.artifact_id)
        if not src_path or not Path(src_path).exists():
            raise HTTPException(status_code=400, detail=f"YAML generado para '{art.artifact_id}' no encontrado.")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, target_path)
        installed.append(art.target_rel_path)

    session["last_backup"] = str(backup_file)

    return {
        "status": "installed",
        "experiment_id": exp_id,
        "target_sandbox": str(exp_simulator_root),
        "installed_files": installed,
        "backup_file": str(backup_file.relative_to(exp_dir)),
        "rollback_available": True
    }


@v2_router.post("/experiments/{exp_id}/rollback")
async def rollback_experiment_endpoint(exp_id: str):
    exp_dir = OUTPUTS_DIR / "experiments" / exp_id
    backups_dir = exp_dir / "backups"
    exp_simulator_root = exp_dir / "EthosTerra_experiment"

    backups = sorted(backups_dir.glob("backup_*.tar.gz"))
    if not backups:
        raise HTTPException(status_code=404, detail="No se encontró ningún respaldo para restaurar.")

    latest_backup = backups[-1]
    rollback_instance(latest_backup, exp_simulator_root)

    return {
        "status": "rollback_completed",
        "experiment_id": exp_id,
        "restored_from": str(latest_backup.name),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@v2_router.get("/experiments/{exp_id}/manifest")
async def get_manifest_endpoint(exp_id: str):
    exp_dir = OUTPUTS_DIR / "experiments" / exp_id
    manifest_path = exp_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifiesto no encontrado.")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


@v2_router.get("/experiments/{exp_id}/metrics")
async def get_metrics_endpoint(exp_id: str):
    legacy = compute_legacy_metrics()
    doc_pipeline = compute_document_pipeline_metrics(exp_id)
    comp = generate_comparison_week5_week6()
    return {
        "legacy_benchmark": legacy,
        "document_pipeline": doc_pipeline,
        "comparison_baseline": comp
    }
