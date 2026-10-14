import json
import shutil
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.main import app
import src.api.atlas_routes as atlas_routes
from apps.atlas.storage.manifest_manager import ManifestManager

client = TestClient(app)


def test_get_quarantine_artifacts():
    """Valida que el endpoint exponga los artefactos en cuarentena y candidatos registrados."""
    resp = client.get("/v2/atlas/artifacts/quarantine")
    assert resp.status_code == 200
    data = resp.json()

    assert "documents" in data
    assert "registered_candidates" in data
    assert data["count"] >= 3

    source_ids = {d["source_id"] for d in data["documents"]}
    assert "art_resolucion_841_2026" in source_ids
    assert "art_patr_montes_de_maria" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in source_ids

    # Verificar presencia de campos obligatorios en los artefactos expuestos
    for doc in data["documents"]:
        assert "source_id" in doc
        assert "title" in doc
        assert "entity" in doc
        assert "instrument_type" in doc
        assert "territory_scope" in doc
        assert "status" in doc
        assert "approval_status" in doc
        assert "previous_source_id" in doc
        assert "approval_notes" in doc
        assert "canonical_url" in doc
        assert "sha256" in doc
        assert "byte_size" in doc
        assert "allowed_for_training" in doc
        assert "usage_state" in doc
        assert "approval_timestamp" in doc
        assert "reviewer_id" in doc
        assert "reviewer_auth_mode" in doc
        assert "review_events" in doc
        assert doc["allowed_for_training"] is False
        assert doc["usage_state"] == "context_only"

    # Verificar que Opción A (revised_2026) está registrada como candidato no descargado
    cand_ids = {c["source_id"] for c in data["registered_candidates"]}
    assert "art_patr_montes_de_maria_2026" in cand_ids
    cand_a = next(c for c in data["registered_candidates"] if c["source_id"] == "art_patr_montes_de_maria_2026")
    assert cand_a["is_downloaded"] is False
    assert cand_a["status"] in {"revised_2026", "rejected", "approved_for_context"}


def test_review_context_artifact_lifecycle_transitions(tmp_path, monkeypatch):
    """Valida transiciones manuales de revisión humana, bitácora append-only y preservación estricta de 7 campos inmutables."""
    # Aislamiento: crear copia temporal del manifiesto real
    test_atlas_dir = tmp_path / "atlas"
    test_atlas_dir.mkdir(parents=True, exist_ok=True)
    real_manifest_path = Path("outputs/atlas/registry_state.json")
    test_manifest_path = test_atlas_dir / "registry_state.json"
    shutil.copyfile(real_manifest_path, test_manifest_path)

    test_manager = ManifestManager(base_dir=test_atlas_dir)
    monkeypatch.setattr(atlas_routes, "manifest_manager", test_manager)
    if "apps.api.src.api.atlas_routes" in sys.modules:
        monkeypatch.setattr(sys.modules["apps.api.src.api.atlas_routes"], "manifest_manager", test_manager)

    target_id = "art_patr_montes_de_maria"

    # Obtener estado previo del documento
    init_manifest = test_manager.load_manifest()
    init_doc = init_manifest.documents[target_id]
    initial_sha256 = init_doc.sha256
    initial_content_path = init_doc.content_path
    initial_canonical_url = init_doc.canonical_url
    initial_download_date = init_doc.download_date
    initial_provenance_class = init_doc.provenance_class
    initial_allowed_for_training = init_doc.allowed_for_training
    initial_usage_state = init_doc.usage_state
    initial_source_type = init_doc.source_type
    initial_events_count = len(init_doc.review_events)

    # 1. Transición: approved_for_context
    payload_approve = {
        "source_id": target_id,
        "reviewer_id": "investigador_ebdi_01",
        "decision": "approved_for_context",
        "review_notes": "Aprobación contextual para pruebas.",
    }
    resp_app = client.post("/v2/atlas/artifacts/context-review", json=payload_approve)
    assert resp_app.status_code == 200
    doc_app = resp_app.json()

    # Comprobación de estado y modo de autenticación declarado
    assert doc_app["status"] == "approved_for_context"
    assert doc_app["approval_status"] == "approved_for_context"
    assert doc_app["reviewer_id"] == "investigador_ebdi_01"
    assert doc_app["reviewer_auth_mode"] == "declarado_sin_autenticacion"

    # Inmutabilidad estricta de los campos protegidos
    assert doc_app["sha256"] == initial_sha256
    assert doc_app["content_path"] == initial_content_path
    assert doc_app["canonical_url"] == initial_canonical_url
    assert doc_app["download_date"] == initial_download_date
    assert doc_app["provenance_class"] == initial_provenance_class
    assert doc_app["allowed_for_training"] is False
    assert doc_app["usage_state"] == "context_only"
    assert doc_app["source_type"] == initial_source_type

    # Bitácora append-only: acumula el nuevo evento sin perder los anteriores
    assert len(doc_app["review_events"]) == initial_events_count + 1
    new_ev1 = doc_app["review_events"][-1]
    assert new_ev1["event_id"].startswith("rev_")
    assert new_ev1["reviewer_id"] == "investigador_ebdi_01"
    assert new_ev1["reviewer_auth_mode"] == "declarado_sin_autenticacion"
    assert new_ev1["decision"] == "approved_for_context"
    assert new_ev1["previous_status"] == (init_doc.status or init_doc.approval_status)
    assert new_ev1["event_type"] == "human_decision"
    assert new_ev1["is_valid_human_approval"] is True

    # approval_notes contiene únicamente la nota vigente/actual (no concatena todo el historial)
    assert doc_app["approval_notes"] == "Aprobación contextual para pruebas."

    # 2. Transición posterior: rejected
    payload_reject = {
        "source_id": target_id,
        "reviewer_id": "investigador_ebdi_02",
        "decision": "rejected",
        "review_notes": "Rechazo posterior tras análisis adicional.",
    }
    resp_rej = client.post("/v2/atlas/artifacts/context-review", json=payload_reject)
    assert resp_rej.status_code == 200
    doc_rej = resp_rej.json()

    assert doc_rej["status"] == "rejected"
    assert doc_rej["approval_status"] == "rejected"
    assert doc_rej["reviewer_id"] == "investigador_ebdi_02"
    assert doc_rej["reviewer_auth_mode"] == "declarado_sin_autenticacion"

    # Inmutabilidad de campos protegidos tras segunda decisión
    assert doc_rej["sha256"] == initial_sha256
    assert doc_rej["content_path"] == initial_content_path
    assert doc_rej["canonical_url"] == initial_canonical_url
    assert doc_rej["download_date"] == initial_download_date
    assert doc_rej["provenance_class"] == initial_provenance_class
    assert doc_rej["allowed_for_training"] is False
    assert doc_rej["usage_state"] == "context_only"

    # Bitácora append-only: debe acumular sin sobrescribir
    assert len(doc_rej["review_events"]) == initial_events_count + 2
    new_ev2 = doc_rej["review_events"][-1]
    assert new_ev2["event_id"].startswith("rev_")
    assert new_ev2["reviewer_id"] == "investigador_ebdi_02"
    assert new_ev2["decision"] == "rejected"
    assert new_ev2["previous_status"] == "approved_for_context"
    assert new_ev2["event_type"] == "human_decision"
    assert new_ev2["is_valid_human_approval"] is True
    assert doc_rej["approval_notes"] == "Rechazo posterior tras análisis adicional."

    # 3. Transición: retorno a pending_context_review
    payload_pending = {
        "source_id": target_id,
        "reviewer_id": "investigador_ebdi_01",
        "decision": "pending_context_review",
        "review_notes": "Retorno a cuarentena pendiente de mesa de trabajo.",
    }
    resp_pen = client.post("/v2/atlas/artifacts/context-review", json=payload_pending)
    assert resp_pen.status_code == 200
    doc_pen = resp_pen.json()

    assert doc_pen["status"] == "pending_context_review"
    assert doc_pen["approval_status"] == "pending_context_review"
    assert len(doc_pen["review_events"]) == initial_events_count + 3
    new_ev3 = doc_pen["review_events"][-1]
    assert new_ev3["decision"] == "pending_context_review"
    assert new_ev3["previous_status"] == "rejected"
    assert doc_pen["approval_notes"] == "Retorno a cuarentena pendiente de mesa de trabajo."

    # Verificar inmutabilidad continua de campos protegidos
    assert doc_pen["sha256"] == initial_sha256
    assert doc_pen["content_path"] == initial_content_path
    assert doc_pen["canonical_url"] == initial_canonical_url
    assert doc_pen["download_date"] == initial_download_date
    assert doc_pen["provenance_class"] == initial_provenance_class
    assert doc_pen["allowed_for_training"] is False
    assert doc_pen["usage_state"] == "context_only"


def test_review_context_artifact_rejects_promoting_option_a():
    """Opción A (art_patr_montes_de_maria_2026) con status revised_2026 sin descarga no puede ser aprobada."""
    payload = {
        "source_id": "art_patr_montes_de_maria_2026",
        "reviewer_id": "investigador_ebdi_01",
        "decision": "approved_for_context",
        "review_notes": "Intento no autorizado de promover documento no descargado.",
    }
    resp = client.post("/v2/atlas/artifacts/context-review", json=payload)
    assert resp.status_code == 400
    assert "no puede ser promovida" in resp.json()["detail"]


def test_review_context_artifact_rejects_unknown_source():
    """Candidatos inexistentes son rechazados con 404."""
    payload = {
        "source_id": "fuente_fantasma_inexistente",
        "reviewer_id": "investigador_ebdi_01",
        "decision": "approved_for_context",
        "review_notes": "Nota de prueba.",
    }
    resp = client.post("/v2/atlas/artifacts/context-review", json=payload)
    assert resp.status_code == 404


def test_review_context_artifact_rejects_invalid_decision():
    """Decisiones no soportadas o inválidas son rechazadas por Pydantic con 422."""
    payload = {
        "source_id": "art_resolucion_841_2026",
        "reviewer_id": "investigador_ebdi_01",
        "decision": "approved_for_training",  # Prohibido
        "review_notes": "Nota inválida.",
    }
    resp = client.post("/v2/atlas/artifacts/context-review", json=payload)
    assert resp.status_code == 422


def test_get_artifact_content_success():
    """Valida que el endpoint sirva el binario PDF local con headers defensivos si está presente."""
    doc = atlas_routes.manifest_manager.load_manifest().documents.get("adr_pidaret_bolivar_ordenanza_323_2021")
    if not doc or not (atlas_routes.manifest_manager.base_dir / doc.content_path).is_file():
        pytest.skip("Archivo físico PDF real no presente en el entorno (binario pesado de 17MB omitido en VCS).")
    resp = client.get("/v2/atlas/artifacts/adr_pidaret_bolivar_ordenanza_323_2021/content")
    assert resp.status_code == 200
    assert resp.headers.get("content-type") == "application/pdf"
    assert resp.headers.get("x-artifact-sha256") == "712636c7c7d4b0f6ef251b385bb0629fd903cdd39bf37043d28e808283e1c106"
    assert resp.headers.get("x-artifact-source-id") == "adr_pidaret_bolivar_ordenanza_323_2021"
    assert len(resp.content) > 1000000  # Archivo real de 17+ MB


def test_get_artifact_content_with_synthetic_storage():
    """Valida el ciclo completo de entrega binaria soberana y validación criptográfica SHA-256."""
    from apps.atlas.schemas.document_schemas import DocumentMetadataRecord
    from apps.atlas.storage.hashing import compute_file_sha256

    sources_dir = atlas_routes.manifest_manager.sources_dir
    sources_dir.mkdir(parents=True, exist_ok=True)
    test_pdf = sources_dir / "test_artifact_unit_temp.pdf"
    content = b"%PDF-1.4 simulated binary stream with sovereign integrity checks"
    test_pdf.write_bytes(content)
    test_hash = compute_file_sha256(test_pdf)

    manifest = atlas_routes.manifest_manager.load_manifest()
    mock_record = DocumentMetadataRecord(
        source_id="mock_unit_artifact_001",
        entity="Entidad Test",
        title="Documento de Prueba",
        level="municipal",
        territory_scope="MUN_13244",
        pipeline_type="documental",
        document_format="pdf",
        canonical_url="https://ejemplo.gov.co/doc.pdf",
        download_date="2026-10-08T00:00:00+00:00",
        sha256=test_hash,
        byte_size=len(content),
        content_path="sources/test_artifact_unit_temp.pdf",
        source_type="document_context",
        provenance_class="official_government",
        allowed_for_training=False,
        usage_state="context_only",
        status="approved_for_context",
    )
    manifest.documents["mock_unit_artifact_001"] = mock_record
    atlas_routes.manifest_manager.save_manifest(manifest)

    try:
        resp = client.get("/v2/atlas/artifacts/mock_unit_artifact_001/content")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/pdf"
        assert resp.headers.get("x-artifact-sha256") == test_hash
        assert resp.headers.get("x-artifact-source-id") == "mock_unit_artifact_001"
        assert resp.content == content
    finally:
        if test_pdf.exists():
            test_pdf.unlink()
        manifest = atlas_routes.manifest_manager.load_manifest()
        manifest.documents.pop("mock_unit_artifact_001", None)
        atlas_routes.manifest_manager.save_manifest(manifest)


def test_get_artifact_content_not_found():
    """Artefactos no registrados retornan 404."""
    resp = client.get("/v2/atlas/artifacts/fuente_inexistente/content")
    assert resp.status_code == 404


def test_get_artifact_content_traversal_blocked():
    """Intentos de Directory Traversal son bloqueados con 400 o 404."""
    resp = client.get("/v2/atlas/artifacts/..%2F..%2Fetc/content")
    assert resp.status_code in (400, 404)


def test_get_pilots_cascades_returns_five_municipalities():
    """Valida que se expongan los 5 municipios piloto con sus instrumentos de política."""
    resp = client.get("/v2/atlas/pilots/cascades")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pilots_count"] == 5
    codes = {p["divipola"] for p in data["pilots"]}
    assert codes == {"13244", "13654", "13657", "13442", "70717"}
    for pilot in data["pilots"]:
        assert len(pilot["applicable_instruments"]) >= 3
        assert "municipality_name" in pilot
        assert "department_name" in pilot
