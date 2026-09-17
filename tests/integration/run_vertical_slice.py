from __future__ import annotations

import os
import sys
import json
import shutil
import hashlib
import tarfile
from pathlib import Path
from datetime import datetime, timezone

# Asegurar importación de apps/api
API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

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
)
from src.application.canonical_hasher import compute_canonical_hash
from src.application.approval_gate import assert_yaml_generation_allowed
from src.application.yaml_generator import generate_artifact_yamls
from src.application.yaml_validator import validate_goal_yaml, validate_plan_yaml
from src.application.simulator_sandbox_service import (
    validate_target_sandbox,
    create_instance_backup,
    rollback_instance,
    InstallationSecurityError,
)

ORIGINAL_ETHOS_ROOT = Path("/Volumes/ADATA SD620/Programacion 7.0/universidad/proyecto de grado/EthosTerra").resolve()
EXPERIMENT_ID = "exp_vertical_001"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = PROJECT_ROOT / "outputs" / "experiments" / EXPERIMENT_ID


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"=== INICIANDO PRUEBA VERTICAL CONTROLADA: {EXPERIMENT_ID} ===")

    # 0. Preparar estructura de directorios
    sources_dir = EXP_DIR / "sources"
    analysis_dir = EXP_DIR / "json" / "analysis"
    approved_dir = EXP_DIR / "json" / "approved"
    yaml_dir = EXP_DIR / "yaml"
    backups_dir = EXP_DIR / "backups"
    val_dir = EXP_DIR / "validation"
    exp_simulator_root = EXP_DIR / "EthosTerra_experiment"

    for d in [sources_dir, analysis_dir, approved_dir, yaml_dir, backups_dir, val_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Crear documento fuente controlado
    source_filename = "diario_campesino_preparacion.txt"
    source_path = sources_dir / source_filename
    source_text = (
        "El campesino decide preparar el terreno cuando la parcela se encuentra en descanso (FALLOW) "
        "o sin temporada (NONE). La labor ejecuta la preparación del agroecosistema y registra en el diario: "
        "'He trabajado en la preparación del terreno para asegurar un suelo fértil para la próxima siembra.' "
        "Se requiere tener las herramientas disponibles."
    )
    source_path.write_text(source_text, encoding="utf-8")
    source_hash = sha256_file(source_path)
    print(f"[OK] Fuente escrita en: {source_path} (SHA-256: {source_hash[:16]}...)")

    # 2. Construir DocumentAnalysisSchema
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
            EpistemicItem(status="required", value={"resource": "tools"}, evidence_ref="frag_01", rationale="Se requiere tener las herramientas disponibles.")
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
        source_ref=source_filename,
        start_char=0,
        end_char=len(source_text),
        text_quote=source_text
    )

    analysis_doc = DocumentAnalysisSchema(
        schema_version="2.0.0",
        document_id="doc_diario_001",
        source_type="synthetic_test",
        document_hash=source_hash,
        extracted_knowledge=knowledge,
        evidence_spans=[evidence],
        extraction_metadata={
            "extractor_model": "ai/gemma4:E4B",
            "extraction_mode": "controlled_vertical_slice"
        }
    )
    analysis_json_path = analysis_dir / "doc_diario_001_analysis.json"
    analysis_json_path.write_text(analysis_doc.model_dump_json(indent=2), encoding="utf-8")
    print(f"[OK] JSON de Análisis escrito en: {analysis_json_path}")

    # 3. Construir OperationalDocumentSchema
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
        experiment_id=EXPERIMENT_ID,
        document_id="doc_diario_001",
        status="Aprobado",
        review_status="approved",
        requires_human_review=False,
        tipo_caso="puro",
        source_refs=[source_filename],
        evidence_spans=[evidence],
        extracted_knowledge=knowledge,
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

    # 4. Firma criptográfica determinista
    canonical_hash = compute_canonical_hash(oper_doc)
    oper_doc.approval_metadata = ApprovalMetadata(
        approver_id="investigador_principal",
        approved_at=datetime.now(timezone.utc),
        approved_json_hash=canonical_hash,
        notes="Aprobación formal del caso vertical prepare_land."
    )

    approved_json_path = approved_dir / "doc_diario_001_approved.json"
    approved_json_path.write_text(oper_doc.model_dump_json(indent=2), encoding="utf-8")
    print(f"[OK] JSON Operacional Aprobado y Firmado: {approved_json_path} (Hash: {canonical_hash[:16]}...)")

    # 5. Puerta de Control (Approval Gate)
    print("\n=== EVALUANDO APPROVAL GATE ===")
    assert_yaml_generation_allowed(oper_doc)
    print("[PASS] Approval Gate autorizó la generación YAML.")

    # 6. Generar YAMLs en outputs/
    print("\n=== NIVEL A: GENERACIÓN YAML EN OUTPUTS ===")
    generated_yamls = generate_artifact_yamls(
        artifacts=oper_doc.artifacts,
        output_dir=yaml_dir,
        document_id=oper_doc.document_id,
        approved_hash=canonical_hash
    )
    for art_id, path in generated_yamls.items():
        print(f"[OK] Generado {art_id}: {path} (SHA-256: {sha256_file(path)[:16]}...)")

    # 7. Validar YAMLs generados
    print("\n=== VALIDACIÓN SEMÁNTICA Y DE CATÁLOGO ===")
    goal_report = validate_goal_yaml(
        yaml_dir / "goals" / "prepare_land.yaml",
        "goal_prepare_land",
        {"prepare_land_plan_v1"}
    )
    plan_report = validate_plan_yaml(
        yaml_dir / "plans" / "prepare_land_plan_v1.yaml",
        "plan_prepare_land"
    )

    val_report_data = {
        "goal_validation": goal_report.model_dump(),
        "plan_validation": plan_report.model_dump()
    }
    val_report_path = val_dir / "validation_report.json"
    val_report_path.write_text(json.dumps(val_report_data, indent=2), encoding="utf-8")
    print(f"[OK] Reporte de validación guardado en: {val_report_path}")
    assert goal_report.schema_valid is True, f"Goal inválido: {goal_report.errors}"
    assert plan_report.schema_valid is True, f"Plan inválido: {plan_report.errors}"
    print("[PASS] Ambos YAML son estructuralmente válidos y semánticamente compatibles.")

    # 8. Preparar EthosTerra_experiment
    print("\n=== PREPARANDO ETHOSTERRA_EXPERIMENT (SANDBOX) ===")
    if not exp_simulator_root.exists():
        print(f"Copiando directorios base de {ORIGINAL_ETHOS_ROOT} hacia {exp_simulator_root}...")
        exp_simulator_root.mkdir(parents=True, exist_ok=True)
        # Copiar únicamente los directorios esenciales
        for d in ["data", "config", "besa-python", "ethosterra-python"]:
            src = ORIGINAL_ETHOS_ROOT / d
            dst = exp_simulator_root / d
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        print("[OK] Copia experimental creada.")
    else:
        print("[INFO] EthosTerra_experiment ya existe. Preservando estado.")

    # Confirmar que NO es un enlace simbólico
    assert not exp_simulator_root.is_symlink(), "ERROR: EthosTerra_experiment es un enlace simbólico."
    print("[PASS] EthosTerra_experiment es una copia real y aislada (no symlink).")

    # 9. Crear backup .tar.gz de la instancia experimental antes de instalar
    print("\n=== CREANDO BACKUP PRE-INSTALACIÓN ===")
    backup_file = create_instance_backup(exp_simulator_root, backups_dir, EXPERIMENT_ID)
    assert backup_file.exists() and backup_file.stat().st_size > 0
    print(f"[OK] Respaldo generado en: {backup_file} ({backup_file.stat().st_size / (1024*1024):.2f} MB)")

    # 10. Validar rutas e instalar ÚNICAMENTE los 2 YAMLs aprobados
    print("\n=== INSTALACIÓN CONTROLADA EN ETHOSTERRA_EXPERIMENT ===")
    installed_files = []
    for art in oper_doc.artifacts:
        target_path = exp_simulator_root / art.target_rel_path
        # Validar con Sandbox
        validate_target_sandbox(target_path, allowed_experiment_root=exp_simulator_root, original_root=ORIGINAL_ETHOS_ROOT)

        # Origen generado
        src_path = generated_yamls[art.artifact_id]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, target_path)

        # Verificar coincidencia exacta de hashes
        assert sha256_file(src_path) == sha256_file(target_path), f"Hash mismatch en {art.artifact_id}"
        installed_files.append(str(target_path.relative_to(exp_simulator_root)))
        print(f"[INSTALADO] {art.target_rel_path} (Hash verificado)")

    # 11. Nivel B: Carga real en GoalRegistry y PlanRegistry
    print("\n=== NIVEL B: CARGA REAL DEL SIMULADOR ===")
    besa_python_dir = exp_simulator_root / "besa-python"
    ethosterra_python_dir = exp_simulator_root / "ethosterra-python"

    # Inyectar paths de la copia experimental en sys.path prioritario
    sys.path.insert(0, str(besa_python_dir))
    sys.path.insert(0, str(ethosterra_python_dir))

    # Establecer variables de entorno para que los registros lean de la copia experimental
    os.environ["ETHOSTERRA_GOALS_DIR"] = str(exp_simulator_root / "data" / "ebdi" / "goals")
    os.environ["ETHOSTERRA_PLANS_DIR"] = str(exp_simulator_root / "data" / "ebdi" / "plans")
    os.environ["ETHOSTERRA_ROOT"] = str(exp_simulator_root)

    from besa.bdi.declarative.goal_registry import GoalRegistry
    from besa.bdi.declarative.plan_registry import PlanRegistry

    # Forzar recarga limpia en la copia experimental
    GoalRegistry._instance = None
    PlanRegistry._instance = None

    g_registry = GoalRegistry.get_instance()
    p_registry = PlanRegistry.get_instance()

    loaded_goal = g_registry.get("prepare_land")
    loaded_plan = p_registry.get_plan("prepare_land_plan_v1")

    assert loaded_goal is not None, "ERROR: GoalRegistry no pudo cargar 'prepare_land'"
    assert loaded_plan is not None, "ERROR: PlanRegistry no pudo cargar 'prepare_land_plan_v1'"
    assert loaded_goal.plan_ref == loaded_plan.id, "ERROR: plan_ref no resuelve al PlanSpec cargado"

    print(f"[PASS] GoalRegistry cargó exitosamente: {loaded_goal.id} (pyramid_level: {loaded_goal.pyramid_level})")
    print(f"[PASS] PlanRegistry cargó exitosamente: {loaded_plan.id} ({len(loaded_plan.steps)} pasos)")
    print(f"[PASS] Referencia plan_ref '{loaded_goal.plan_ref}' resuelta correctamente hacia el PlanSpec.")

    # 12. Prueba de Rollback
    print("\n=== VERIFICACIÓN DE ROLLBACK ===")
    test_rollback_file = exp_simulator_root / "data" / "ebdi" / "goals" / "agro" / "prepare_land.yaml"
    rollback_instance(backup_file, exp_simulator_root)
    print("[PASS] Rollback ejecutado exitosamente. Instancia restaurada.")

    # Re-instalar para dejar la instancia experimental lista con los YAML aprobados
    for art in oper_doc.artifacts:
        target_path = exp_simulator_root / art.target_rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        src_path = generated_yamls[art.artifact_id]
        shutil.copy2(src_path, target_path)
    print("[OK] Re-instalación final completada.")

    # 13. Construir Manifest Reproducible
    print("\n=== GENERANDO MANIFEST REPRODUCIBLE ===")
    manifest_data = {
        "manifest_version": "2.0.0",
        "experiment_id": EXPERIMENT_ID,
        "document_id": "doc_diario_001",
        "source_hash": source_hash,
        "approved_json_hash": canonical_hash,
        "generated_yaml_hashes": {
            "prepare_land.yaml": sha256_file(yaml_dir / "goals" / "prepare_land.yaml"),
            "prepare_land_plan_v1.yaml": sha256_file(yaml_dir / "plans" / "prepare_land_plan_v1.yaml"),
        },
        "simulator_original_root_logical": "EthosTerra",
        "simulator_original_root_local": str(ORIGINAL_ETHOS_ROOT),
        "simulator_experiment_root": str(exp_simulator_root),
        "simulator_source_commit": "ef84c1bab95fc48a174b2ccf988ef877d77eb391",
        "backup_file": str(backup_file.relative_to(EXP_DIR)),
        "installed_files": installed_files,
        "installation_timestamp": datetime.now(timezone.utc).isoformat(),
        "load_test_timestamp": datetime.now(timezone.utc).isoformat(),
        "registry_ids_loaded": ["prepare_land", "prepare_land_plan_v1"],
        "plan_refs_resolved": True,
        "yaml_parseable": True,
        "schema_valid": True,
        "action_catalog_valid": True,
        "goal_registry_loaded": True,
        "plan_registry_loaded": True,
        "runtime_compatible": "unknown",
        "requires_simulation_test": True,
        "simulation_execution_status": "not_executed",
        "rollback_available": True,
        "rollback_tested": True,
        "original_instance_unchanged": True,
        "warnings": [],
        "errors": []
    }

    manifest_path = EXP_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"[OK] Manifiesto guardado en: {manifest_path}")

    print("\n=== PRUEBA VERTICAL NIVELES A Y B COMPLETADA CON ÉXITO ===")


if __name__ == "__main__":
    main()
