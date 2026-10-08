from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.main import app
from apps.atlas.schemas.discovery_schemas import (
    CandidateApprovalStatus,
    CandidateReviewDecision,
    CandidateReviewRecord,
    CandidateReviewAuditState,
    CandidateSourceRecord,
)
from apps.atlas.storage.candidate_review_manager import (
    CandidateReviewManager,
    CandidateNotFoundError,
    CandidateAlreadyReviewedError,
    CandidateGovernanceError,
)
import src.api.atlas_routes as atlas_routes_module


@pytest.fixture
def tmp_review_manager(tmp_path: Path) -> CandidateReviewManager:
    """Fixture de gestor de revisiones aislado con almacenamiento temporal."""
    storage_dir = tmp_path / "atlas"
    return CandidateReviewManager(storage_dir=storage_dir)


@pytest.fixture
def test_client(tmp_path: Path):
    """TestClient de FastAPI con gestor de revisión aislado en directorio temporal."""
    storage_dir = tmp_path / "atlas_api"
    mock_manager = CandidateReviewManager(storage_dir=storage_dir)
    original_manager = atlas_routes_module.review_manager
    atlas_routes_module.review_manager = mock_manager
    try:
        client = TestClient(app)
        yield client, mock_manager
    finally:
        atlas_routes_module.review_manager = original_manager


# ==============================================================================
# Pruebas Unitarias del Gestor (CandidateReviewManager)
# ==============================================================================

def test_approve_documental_candidate(tmp_review_manager: CandidateReviewManager):
    """Verifica la aprobación humana de un candidato documental a 'approved_for_acquisition'."""
    decision = CandidateReviewDecision(
        source_id="adr_pidaret_bolivar_ordenanza_323_2021",
        reviewer_id="investigador_01",
        decision="approve",
        review_notes="Instrumento departamental oficial validado mediante Ordenanza 323 de 2021.",
    )

    record = tmp_review_manager.review_candidate(decision)

    assert record.source_id == "adr_pidaret_bolivar_ordenanza_323_2021"
    assert record.reviewer_id == "investigador_01"
    assert record.decision == "approve"
    assert record.resulting_status == "approved_for_acquisition"
    assert record.pipeline_type == "documental"
    assert record.source_type == "document_context"
    assert record.document_format == "pdf"
    assert record.allowed_for_training is False
    assert record.usage_state == "context_only"
    assert record.review_notes == "Instrumento departamental oficial validado mediante Ordenanza 323 de 2021."
    assert record.timestamp is not None

    # Verificar persistencia en archivo de auditoría
    audit_state = tmp_review_manager.load_audit_state()
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in audit_state.reviews
    persisted = audit_state.reviews["adr_pidaret_bolivar_ordenanza_323_2021"]
    assert persisted.resulting_status == "approved_for_acquisition"


def test_approve_tabular_candidate(tmp_review_manager: CandidateReviewManager):
    """Verifica la aprobación humana de un candidato tabular preservando 'tabular_context'."""
    decision = CandidateReviewDecision(
        source_id="datos_gov_co_eva_agricola",
        reviewer_id="investigador_02",
        decision="approve",
        review_notes="Dataset estadístico oficial del MADR aplicable a Montes de María.",
    )

    record = tmp_review_manager.review_candidate(decision)

    assert record.source_id == "datos_gov_co_eva_agricola"
    assert record.resulting_status == "approved_for_acquisition"
    assert record.pipeline_type == "api_tabular"
    assert record.source_type == "tabular_context"
    assert record.document_format == "json_api"
    assert record.allowed_for_training is False
    assert record.usage_state == "context_only"


def test_reject_candidate_with_justification(tmp_review_manager: CandidateReviewManager):
    """Verifica el rechazo explícito de un candidato con notas obligatorias."""
    decision = CandidateReviewDecision(
        source_id="pnd_colombia_2022_2026",
        reviewer_id="investigador_03",
        decision="reject",
        review_notes="Instrumento nacional descartado por granularidad insuficiente para el análisis a nivel predio.",
    )

    record = tmp_review_manager.review_candidate(decision)

    assert record.source_id == "pnd_colombia_2022_2026"
    assert record.decision == "reject"
    assert record.resulting_status == "rejected"
    assert record.pipeline_type == "documental"
    assert record.source_type == "document_context"
    assert record.allowed_for_training is False
    assert record.usage_state == "context_only"


def test_reject_nonexistent_candidate(tmp_review_manager: CandidateReviewManager):
    """Impide revisar un candidato con source_id inexistente."""
    decision = CandidateReviewDecision(
        source_id="fuente_inexistente_999",
        reviewer_id="investigador_01",
        decision="approve",
        review_notes="Intento de aprobar fuente inexistente.",
    )

    with pytest.raises(CandidateNotFoundError) as exc_info:
        tmp_review_manager.review_candidate(decision)

    assert "fuente_inexistente_999" in str(exc_info.value)


def test_prevent_double_review_on_same_candidate(tmp_review_manager: CandidateReviewManager):
    """Impide revisar dos veces un candidato ya aprobado o rechazado."""
    decision1 = CandidateReviewDecision(
        source_id="adr_pidaret_bolivar_ordenanza_323_2021",
        reviewer_id="investigador_01",
        decision="approve",
        review_notes="Primera aprobación válida.",
    )
    tmp_review_manager.review_candidate(decision1)

    decision2 = CandidateReviewDecision(
        source_id="adr_pidaret_bolivar_ordenanza_323_2021",
        reviewer_id="investigador_02",
        decision="reject",
        review_notes="Intento de re-evaluación no permitida.",
    )
    with pytest.raises(CandidateAlreadyReviewedError) as exc_info:
        tmp_review_manager.review_candidate(decision2)

    assert "ya fue revisado" in str(exc_info.value)


def test_prevent_empty_or_whitespace_review_notes():
    """Rechaza decisiones sin notas o con solo espacios en blanco."""
    with pytest.raises(ValidationError):
        CandidateReviewDecision(
            source_id="adr_pidaret_bolivar_ordenanza_323_2021",
            reviewer_id="investigador_01",
            decision="approve",
            review_notes="",
        )

    with pytest.raises(ValidationError):
        CandidateReviewDecision(
            source_id="adr_pidaret_bolivar_ordenanza_323_2021",
            reviewer_id="investigador_01",
            decision="approve",
            review_notes="    ",
        )

    with pytest.raises(ValidationError):
        CandidateReviewDecision(
            source_id="adr_pidaret_bolivar_ordenanza_323_2021",
            reviewer_id="investigador_01",
            decision="approve",
            review_notes="abc",  # menor a 5 caracteres
        )


def test_prevent_extra_fields_in_decision_contract():
    """Garantiza extra='forbid' en el contrato de entrada."""
    with pytest.raises(ValidationError):
        CandidateReviewDecision(
            source_id="adr_pidaret_bolivar_ordenanza_323_2021",
            reviewer_id="investigador_01",
            decision="approve",
            review_notes="Notas válidas.",
            campo_no_autorizado="inyeccion",  # type: ignore
        )


def test_prevent_pipeline_and_governance_mismatch():
    """Impide combinaciones cruzadas no autorizadas en CandidateReviewRecord."""
    # documental con tabular_context
    with pytest.raises(ValidationError) as exc:
        CandidateReviewRecord(
            source_id="test_doc",
            reviewer_id="rev_01",
            decision="approve",
            resulting_status="approved_for_acquisition",
            review_notes="Notas válidas para test",
            timestamp="2026-10-06T12:00:00Z",
            pipeline_type="documental",
            source_type="tabular_context",  # mismatch
            document_format="pdf",
        )
    assert "Incompatibilidad de gobernanza" in str(exc.value)

    # api_tabular con document_context
    with pytest.raises(ValidationError) as exc:
        CandidateReviewRecord(
            source_id="test_tab",
            reviewer_id="rev_01",
            decision="approve",
            resulting_status="approved_for_acquisition",
            review_notes="Notas válidas para test",
            timestamp="2026-10-06T12:00:00Z",
            pipeline_type="api_tabular",
            source_type="document_context",  # mismatch
            document_format="json_api",
        )
    assert "Incompatibilidad de gobernanza" in str(exc.value)


def test_prevent_using_state_approved_in_candidate_review():
    """Impide el uso del estado 'approved' a secas en este flujo (solo approved_for_acquisition o rejected)."""
    with pytest.raises(ValidationError):
        CandidateReviewRecord(
            source_id="test_doc",
            reviewer_id="rev_01",
            decision="approve",
            resulting_status="approved",  # no permitido aquí
            review_notes="Notas válidas para test",
            timestamp="2026-10-06T12:00:00Z",
            pipeline_type="documental",
            source_type="document_context",
            document_format="pdf",
        )


def test_atomic_persistence_and_file_integrity(tmp_review_manager: CandidateReviewManager):
    """Verifica que la persistencia del archivo de auditoría sea atómica y serializable."""
    decision = CandidateReviewDecision(
        source_id="art_patr_montes_de_maria",
        reviewer_id="investigador_04",
        decision="approve",
        review_notes="PATR oficial subregional de Montes de María.",
    )
    tmp_review_manager.review_candidate(decision)

    assert tmp_review_manager.reviews_file.is_file()
    # Asegurar que no quedan archivos temporales colgados
    temp_file = tmp_review_manager.reviews_file.with_suffix(".json.tmp")
    assert not temp_file.exists()

    content = json.loads(tmp_review_manager.reviews_file.read_text(encoding="utf-8"))
    assert content["version"] == "1.0.0"
    assert "art_patr_montes_de_maria" in content["reviews"]
    persisted_record = content["reviews"]["art_patr_montes_de_maria"]
    assert persisted_record["resulting_status"] == "approved_for_acquisition"
    assert persisted_record["allowed_for_training"] is False
    assert persisted_record["usage_state"] == "context_only"


def test_confirm_zero_downloads_zero_network_zero_documents_written(tmp_review_manager: CandidateReviewManager):
    """Confirma que la revisión humana no escribe en sources/, raw/, ni ejecuta descargas."""
    decision = CandidateReviewDecision(
        source_id="adr_pidaret_bolivar_ordenanza_323_2021",
        reviewer_id="investigador_01",
        decision="approve",
        review_notes="Aprobación para adquisición posterior sin descarga.",
    )
    tmp_review_manager.review_candidate(decision)

    # Verificar que no existen subcarpetas sources ni archivos pdf
    sources_dir = tmp_review_manager.storage_dir / "sources"
    raw_dir = tmp_review_manager.storage_dir / "raw"
    context_dir = tmp_review_manager.storage_dir / "context"

    assert not sources_dir.exists()
    assert not raw_dir.exists()
    assert not context_dir.exists()


# ==============================================================================
# Pruebas de Integración HTTP (FastAPI Endpoint POST /v2/atlas/candidates/review)
# ==============================================================================

def test_endpoint_approve_candidate_success(test_client):
    client, manager = test_client
    payload = {
        "source_id": "adr_pidaret_bolivar_ordenanza_323_2021",
        "reviewer_id": "revisor_http_01",
        "decision": "approve",
        "review_notes": "Aprobación verificada vía endpoint de revisión humana.",
    }
    response = client.post("/v2/atlas/candidates/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "adr_pidaret_bolivar_ordenanza_323_2021"
    assert data["decision"] == "approve"
    assert data["resulting_status"] == "approved_for_acquisition"
    assert data["pipeline_type"] == "documental"
    assert data["source_type"] == "document_context"
    assert data["document_format"] == "pdf"
    assert data["allowed_for_training"] is False
    assert data["usage_state"] == "context_only"


def test_endpoint_reject_candidate_success(test_client):
    client, manager = test_client
    payload = {
        "source_id": "datos_gov_co_eva_agricola",
        "reviewer_id": "revisor_http_02",
        "decision": "reject",
        "review_notes": "Rechazado temporalmente por incompatibilidad de periodicidad.",
    }
    response = client.post("/v2/atlas/candidates/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["resulting_status"] == "rejected"
    assert data["pipeline_type"] == "api_tabular"
    assert data["source_type"] == "tabular_context"


def test_endpoint_returns_404_for_unknown_source(test_client):
    client, manager = test_client
    payload = {
        "source_id": "inexistente_xyz_123",
        "reviewer_id": "revisor_http_01",
        "decision": "approve",
        "review_notes": "Intento de aprobación.",
    }
    response = client.post("/v2/atlas/candidates/review", json=payload)
    assert response.status_code == 404
    assert "no existe" in response.json()["detail"]


def test_endpoint_returns_409_on_double_review(test_client):
    client, manager = test_client
    payload = {
        "source_id": "adr_pidaret_bolivar_ordenanza_323_2021",
        "reviewer_id": "revisor_http_01",
        "decision": "approve",
        "review_notes": "Primera revisión exitosa.",
    }
    res1 = client.post("/v2/atlas/candidates/review", json=payload)
    assert res1.status_code == 200

    # Segundo intento con el mismo source_id
    payload2 = {
        "source_id": "adr_pidaret_bolivar_ordenanza_323_2021",
        "reviewer_id": "revisor_http_02",
        "decision": "reject",
        "review_notes": "Intento duplicado de revisión.",
    }
    res2 = client.post("/v2/atlas/candidates/review", json=payload2)
    assert res2.status_code == 409
    assert "ya fue revisado" in res2.json()["detail"]


def test_endpoint_returns_422_on_empty_notes_or_extra_fields(test_client):
    client, manager = test_client
    # Notas vacías
    res1 = client.post(
        "/v2/atlas/candidates/review",
        json={
            "source_id": "adr_pidaret_bolivar_ordenanza_323_2021",
            "reviewer_id": "rev_01",
            "decision": "approve",
            "review_notes": "   ",
        },
    )
    assert res1.status_code == 422

    # Campos extra
    res2 = client.post(
        "/v2/atlas/candidates/review",
        json={
            "source_id": "adr_pidaret_bolivar_ordenanza_323_2021",
            "reviewer_id": "rev_01",
            "decision": "approve",
            "review_notes": "Notas válidas.",
            "campo_fantasma": "malicioso",
        },
    )
    assert res2.status_code == 422
