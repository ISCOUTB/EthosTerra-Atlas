from __future__ import annotations

import base64
import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.main import app
from apps.atlas.storage.manifest_manager import ManifestManager
from apps.atlas.storage.seed_manager import SeedManager
from apps.atlas.schemas.discovery_schemas import CandidateSourceRecord
import src.api.atlas_routes as atlas_routes

client = TestClient(app)


def test_direct_upload_pdf_success(tmp_path: Path, monkeypatch):
    test_atlas_dir = tmp_path / "atlas"
    test_atlas_dir.mkdir(parents=True, exist_ok=True)
    manifest_mgr = ManifestManager(base_dir=test_atlas_dir)
    monkeypatch.setattr(atlas_routes, "manifest_manager", manifest_mgr)

    # Contenido binario PDF mínimo válido
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")

    payload = {
        "filename": "pdm_san_jacinto_manual.pdf",
        "file_base64": b64_pdf,
        "title": "Plan de Desarrollo Municipal de San Jacinto 2024-2027",
        "entity": "Alcaldía Municipal de San Jacinto",
        "territory_scope": "13654",
        "instrument_type": "PDM",
        "reviewer_id": "investigador_juan",
    }

    resp = client.post("/v2/atlas/artifacts/upload", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["source_id"].startswith("manual_")
    assert data["title"] == "Plan de Desarrollo Municipal de San Jacinto 2024-2027"
    assert data["approval_status"] == "approved_for_context"
    assert data["status"] == "approved_for_context"
    assert data["allowed_for_training"] is False
    assert data["usage_state"] == "context_only"
    assert len(data["sha256"]) == 64

    # Verificar que el archivo fue escrito en sources
    saved_file = manifest_mgr.sources_dir / f"{data['sha256']}.pdf"
    assert saved_file.is_file()
    assert saved_file.read_bytes() == pdf_bytes


def test_direct_upload_pdf_rejects_non_pdf():
    fake_bytes = b"Este no es un archivo PDF."
    b64_fake = base64.b64encode(fake_bytes).decode("ascii")

    payload = {
        "filename": "falso.pdf",
        "file_base64": b64_fake,
        "title": "Falso",
    }

    resp = client.post("/v2/atlas/artifacts/upload", json=payload)
    assert resp.status_code == 400
    assert "no es un PDF válido" in resp.json()["detail"]


def test_seeds_lifecycle_and_scan(tmp_path: Path, monkeypatch):
    test_atlas_dir = tmp_path / "atlas"
    test_atlas_dir.mkdir(parents=True, exist_ok=True)
    seed_mgr = SeedManager(storage_dir=test_atlas_dir)
    monkeypatch.setattr(atlas_routes, "seed_manager", seed_mgr)

    # 1. Listar semillas por defecto
    resp_list = client.get("/v2/atlas/seeds")
    assert resp_list.status_code == 200
    seeds = resp_list.json()["seeds"]
    assert len(seeds) >= 1

    # 2. Registrar nueva semilla autorizada
    new_seed_payload = {
        "url": "https://www.renovacionterritorio.gov.co/descargas/patr_montes_de_maria_nueva.pdf",
        "entity": "Agencia de Renovación del Territorio",
        "title": "PATR Montes de María Adición",
        "territory_scope": "Montes de María",
        "instrument_type": "PATR",
        "pipeline_type": "documental",
        "document_format": "pdf",
        "added_by": "tesista_jesus",
    }
    resp_create = client.post("/v2/atlas/seeds", json=new_seed_payload)
    assert resp_create.status_code == 200
    created_seed = resp_create.json()
    assert created_seed["added_by"] == "tesista_jesus"
    seed_id = created_seed["seed_id"]

    # 3. Escanear semillas (Human-in-the-Loop)
    resp_scan = client.post("/v2/atlas/seeds/scan")
    assert resp_scan.status_code == 200
    scan_data = resp_scan.json()
    assert scan_data["status"] == "completed"
    assert scan_data["count"] >= 1
    for c in scan_data["discovered_candidates"]:
        assert c["approval_status"] == "pending_review"  # Cero aprobación automática

    # 4. Listar candidatos unificados
    resp_cands = client.get("/v2/atlas/candidates")
    assert resp_cands.status_code == 200
    cands_data = resp_cands.json()
    assert cands_data["count"] >= 1
    cand_urls = [c["canonical_url"] for c in cands_data["candidates"]]
    assert new_seed_payload["url"] in cand_urls

    # 5. Eliminar semilla
    resp_del = client.delete(f"/v2/atlas/seeds/{seed_id}")
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "deleted"


def test_reject_candidate_with_feedback_adaptive_search_and_retries(tmp_path: Path, monkeypatch):
    test_atlas_dir = tmp_path / "atlas"
    test_atlas_dir.mkdir(parents=True, exist_ok=True)
    review_mgr = atlas_routes.CandidateReviewManager(storage_dir=test_atlas_dir)
    seed_mgr = SeedManager(storage_dir=test_atlas_dir)
    monkeypatch.setattr(atlas_routes, "review_manager", review_mgr)
    monkeypatch.setattr(atlas_routes, "seed_manager", seed_mgr)

    # 1. Registrar una semilla inicial
    seed_mgr.add_seed(
        atlas_routes.AuthorizedSeedCreate(
            url="https://www.renovacionterritorio.gov.co/descargas/patr_montes_de_maria_test.pdf",
            entity="Agencia de Renovación del Territorio",
            title="PATR Montes de María Test",
            territory_scope="Montes de María",
            instrument_type="PATR",
            added_by="investigador_juan",
        )
    )
    # Escanear para generar candidato
    seed_mgr.scan_authorized_seeds(review_mgr)

    cands = review_mgr.list_all_candidates()
    target_cand = next(c for c in cands if "patr_montes_de_maria_test" in c["source_id"])

    # 2. Descartar con retroalimentación y solicitud de búsqueda adaptativa
    decision_payload = {
        "source_id": target_cand["source_id"],
        "reviewer_id": "investigador_juan",
        "decision": "reject",
        "review_notes": "Documento desactualizado, se requiere instrumento PIDARET o PATR complementario.",
        "request_alternative_search": True,
        "instruction_feedback": "Buscar plan departamental con componente agrario.",
    }
    resp = client.post("/v2/atlas/candidates/review", json=decision_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "reject"
    assert data["resulting_status"] == "rejected"
    assert data["retry_count"] == 1
    assert data["max_retries"] == 6
    assert data["request_alternative_search"] is True
    assert data["instruction_feedback"] == "Buscar plan departamental con componente agrario."
    # Debe haber encontrado alternativa oficial compatible en catálogo o semillas
    assert data["alternative_found"] is True
    assert data["alternative_candidate"] is not None
    assert data["search_status"] == "found_alternative"
    assert "Alternativa oficial propuesta" in data["adaptive_message"]


def test_reject_candidate_exhaustion_after_max_retries(tmp_path: Path, monkeypatch):
    test_atlas_dir = tmp_path / "atlas"
    test_atlas_dir.mkdir(parents=True, exist_ok=True)
    review_mgr = atlas_routes.CandidateReviewManager(storage_dir=test_atlas_dir)
    monkeypatch.setattr(atlas_routes, "review_manager", review_mgr)

    cand_id = "cand_test_exhaustion"
    cand_record = CandidateSourceRecord(
        source_id=cand_id,
        url="https://www.renovacionterritorio.gov.co/descargas/test_exhaustion.pdf",
        entity="ART",
        title="Test Exhaustion",
        territory_scope="Montes de María",
        instrument_type="PATR",
        pipeline_type="documental",
        document_format="pdf",
        status="candidate",
        confidence_level="high",
        selection_reason="Para prueba de agotamiento",
        http_status=None,
        content_type=None,
        query_date="2026-10-08",
        source_type="document_context",
        allowed_for_training=False,
        usage_state="context_only",
        consent_status="not_applicable",
        approval_status="pending_review",
    )
    review_mgr.register_discovered_candidate(cand_record)
    # Simular que ya alcanzó el límite de 6 intentos
    review_mgr._adaptive_state[cand_id] = {"retry_count": 6}

    decision_payload = {
        "source_id": cand_id,
        "reviewer_id": "investigador_juan",
        "decision": "reject",
        "review_notes": "Rechazado definitivamente, no contiene enfoque agrario.",
        "request_alternative_search": True,
        "instruction_feedback": "Reintentar pero ya alcanzó el límite.",
    }
    resp = client.post("/v2/atlas/candidates/review", json=decision_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "reject"
    assert data["retry_count"] == 6
    assert data["search_status"] == "exhausted_no_alternative"
    assert "El agente agotó los 6 intentos" in data["adaptive_message"]
    assert data["alternative_found"] is False
