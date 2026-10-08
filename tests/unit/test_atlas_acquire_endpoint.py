from __future__ import annotations

import hashlib
import io
from pathlib import Path
import sys
import pytest
import httpx
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.main import app
from apps.atlas.schemas.discovery_schemas import (
    CandidateReviewDecision,
    AcquisitionRequest,
)
from apps.atlas.storage.candidate_review_manager import CandidateReviewManager
from apps.atlas.storage.manifest_manager import ManifestManager
from apps.atlas.collectors.policy_verifier import PolicyVerifier
from apps.atlas.collectors.streaming_collector import (
    StreamingDocumentCollector,
    CHUNK_SIZE,
)
import src.api.atlas_routes as atlas_routes_module


class MockStreamResponse:
    """Mock determinista de respuesta HTTP en streaming para httpx."""

    def __init__(
        self,
        status_code: int = 200,
        content: bytes = b"%PDF-1.4 Mock valid PDF document content for testing",
        content_type: str = "application/pdf",
        content_length: str | None = None,
        chunk_size: int = CHUNK_SIZE,
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": content_type}
        if content_length:
            self.headers["content-length"] = content_length
        self.chunk_size = chunk_size

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter_bytes(self, chunk_size: int = CHUNK_SIZE):
        stream = io.BytesIO(self.content)
        while chunk := stream.read(chunk_size):
            yield chunk


class MockHttpClient:
    """Mock client de httpx para interceptar llamadas de red en pruebas offline."""

    def __init__(self, response_factory=None) -> None:
        self.response_factory = response_factory or (lambda url: MockStreamResponse())
        self.calls: list[str] = []

    def stream(self, method: str, url: str, **kwargs):
        self.calls.append(url)
        return self.response_factory(url)


@pytest.fixture
def atlas_test_env(tmp_path: Path):
    """Configura el entorno de aislamiento completo para las pruebas de adquisición."""
    tmp_atlas_dir = tmp_path / "atlas"
    tmp_atlas_dir.mkdir(parents=True, exist_ok=True)

    # Gestores aislados
    m_manager = ManifestManager(base_dir=tmp_atlas_dir)
    r_manager = CandidateReviewManager(storage_dir=tmp_atlas_dir)
    p_verifier = PolicyVerifier()
    mock_http = MockHttpClient()

    collector = StreamingDocumentCollector(
        verifier=p_verifier,
        manifest_manager=m_manager,
        client=mock_http,  # type: ignore
    )

    # Inyección de dependencias en módulo de rutas
    orig_m_manager = atlas_routes_module.manifest_manager
    orig_r_manager = atlas_routes_module.review_manager
    orig_p_verifier = atlas_routes_module.policy_verifier
    orig_collector = atlas_routes_module.streaming_collector

    atlas_routes_module.manifest_manager = m_manager
    atlas_routes_module.review_manager = r_manager
    atlas_routes_module.policy_verifier = p_verifier
    atlas_routes_module.streaming_collector = collector

    client = TestClient(app)

    yield {
        "client": client,
        "manifest_manager": m_manager,
        "review_manager": r_manager,
        "policy_verifier": p_verifier,
        "collector": collector,
        "mock_http": mock_http,
        "atlas_dir": tmp_atlas_dir,
    }

    # Restauración
    atlas_routes_module.manifest_manager = orig_m_manager
    atlas_routes_module.review_manager = orig_r_manager
    atlas_routes_module.policy_verifier = orig_p_verifier
    atlas_routes_module.streaming_collector = orig_collector


# ==============================================================================
# Casos de Prueba del Flujo de Adquisición
# ==============================================================================

def test_acquire_successful_new_document(atlas_test_env):
    """1. Adquisición exitosa de un candidato documental aprobado."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    atlas_dir = atlas_test_env["atlas_dir"]

    # Paso previo: Aprobar candidato
    source_id = "art_patr_montes_de_maria"
    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="PATR aprobado para adquisición piloto.",
        )
    )

    sample_pdf = b"%PDF-1.4 official PATR content bytes here..."
    mock_http.response_factory = lambda url: MockStreamResponse(content=sample_pdf)

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 200
    data = res.json()
    assert data["source_id"] == source_id
    assert data["requester_id"] == "inv_01"
    assert data["status"] == "acquired_new"
    assert data["pipeline_type"] == "documental"
    assert data["source_type"] == "document_context"
    assert data["document_format"] == "pdf"
    assert data["allowed_for_training"] is False
    assert data["usage_state"] == "context_only"
    assert data["approval_status"] == "pending_review"

    expected_hash = hashlib.sha256(sample_pdf).hexdigest()
    assert data["sha256"] == expected_hash

    # Verificar que el archivo físico fue escrito en sources/ y registrado en manifiesto
    target_file = atlas_dir / data["content_path"]
    assert target_file.is_file()
    assert target_file.read_bytes() == sample_pdf


def test_acquire_rejects_pending_review_candidate(atlas_test_env):
    """2. Candidato pendiente de revisión devuelve HTTP 409."""
    client = atlas_test_env["client"]
    source_id = "art_patr_montes_de_maria"  # existe en registro pero no ha sido aprobado

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 409
    assert "pending_review" in res.json()["detail"]


def test_acquire_rejects_rejected_candidate(atlas_test_env):
    """3. Candidato rechazado devuelve HTTP 409."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    source_id = "pnd_colombia_2022_2026"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="reject",
            review_notes="Rechazado para este experimento.",
        )
    )

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 409
    assert "rejected" in res.json()["detail"]


def test_acquire_rejects_nonexistent_candidate(atlas_test_env):
    """4. Candidato inexistente devuelve HTTP 404."""
    client = atlas_test_env["client"]
    res = client.post("/v2/atlas/acquire", json={"source_id": "fuente_fantasma_999", "requester_id": "inv_01"})
    assert res.status_code == 404


def test_acquire_rejects_tabular_candidate(atlas_test_env):
    """5. Candidato tabular devuelve HTTP 400."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    source_id = "datos_gov_co_eva_agricola"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado en revisión.",
        )
    )

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 400
    assert "incompatible" in res.json()["detail"]


def test_acquire_handles_remote_http_error(atlas_test_env):
    """6. Error remoto HTTP 404/500 devuelve HTTP 502."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    source_id = "art_patr_montes_de_maria"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado.",
        )
    )

    mock_http.response_factory = lambda url: MockStreamResponse(status_code=500)

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 502


def test_acquire_handles_incorrect_content_type(atlas_test_env):
    """7. Content-Type distinto a application/pdf devuelve HTTP 502."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    source_id = "art_patr_montes_de_maria"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado.",
        )
    )

    mock_http.response_factory = lambda url: MockStreamResponse(
        content=b"<html>Portal error</html>",
        content_type="text/html; charset=utf-8",
    )

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 502
    assert "Content-Type" in res.json()["detail"]


def test_acquire_handles_size_exceeding_100mb(atlas_test_env):
    """8. Archivo mayor a 100 MB devuelve HTTP 413 y limpia temporales."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    source_id = "art_patr_montes_de_maria"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado.",
        )
    )

    # Generar iterador que excede 100 MB
    oversized_chunk = b"X" * (101 * 1024 * 1024)
    mock_http.response_factory = lambda url: MockStreamResponse(content=oversized_chunk)

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 413
    assert "100 MB" in res.json()["detail"]


def test_acquire_handles_expected_hash_mismatch(atlas_test_env):
    """9. Hash esperado discrepante devuelve HTTP 502."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    # adr_pidaret_bolivar_ordenanza_323_2021 tiene un SHA-256 verificado en sources_registry.yaml
    source_id = "adr_pidaret_bolivar_ordenanza_323_2021"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado PIDARET.",
        )
    )

    # Contenido con hash diferente al esperado
    corrupted_bytes = b"%PDF-1.4 modified or tampered content"
    mock_http.response_factory = lambda url: MockStreamResponse(content=corrupted_bytes)

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 502
    assert "Discrepancia criptográfica" in res.json()["detail"]


def test_acquire_idempotence_with_existing_intact_file(atlas_test_env):
    """10. Idempotencia: segunda llamada retorna already_present sin re-descarga."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    source_id = "art_patr_montes_de_maria"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado PATR.",
        )
    )

    sample_pdf = b"%PDF-1.4 sample content"
    mock_http.response_factory = lambda url: MockStreamResponse(content=sample_pdf)

    # Primera llamada
    res1 = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res1.status_code == 200
    assert res1.json()["status"] == "acquired_new"
    calls_count_after_first = len(mock_http.calls)

    # Segunda llamada: debe detectar archivo existente
    res2 = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_02"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_present"
    assert res2.json()["requester_id"] == "inv_02"
    # No debe haberse ejecutado una nueva llamada de red
    assert len(mock_http.calls) == calls_count_after_first


def test_acquire_rejects_altered_local_file_with_409(atlas_test_env):
    """11. Archivo local alterado tras el registro devuelve HTTP 409."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    atlas_dir = atlas_test_env["atlas_dir"]
    source_id = "art_patr_montes_de_maria"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado PATR.",
        )
    )

    sample_pdf = b"%PDF-1.4 valid bytes"
    mock_http.response_factory = lambda url: MockStreamResponse(content=sample_pdf)

    # Primera llamada adquiere el archivo
    res1 = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res1.status_code == 200

    # Alterar archivo en disco
    target_path = atlas_dir / res1.json()["content_path"]
    target_path.write_bytes(b"tampered content corrupted")

    # Segunda llamada debe fallar con 409
    res2 = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res2.status_code == 409
    assert "hash está alterado" in res2.json()["detail"]


def test_acquire_cleans_temporary_files_on_failure(atlas_test_env):
    """12. Comprobación de que no quedan archivos temporales tras un fallo."""
    client = atlas_test_env["client"]
    r_manager = atlas_test_env["review_manager"]
    mock_http = atlas_test_env["mock_http"]
    atlas_dir = atlas_test_env["atlas_dir"]
    source_id = "art_patr_montes_de_maria"

    r_manager.review_candidate(
        CandidateReviewDecision(
            source_id=source_id,
            reviewer_id="rev_01",
            decision="approve",
            review_notes="Aprobado PATR.",
        )
    )

    # Simular fallo durante streaming
    class FailingIterator:
        def iter_bytes(self, chunk_size=CHUNK_SIZE):
            yield b"%PDF-1.4 initial chunk"
            raise httpx.RequestError("Network dropped mid-stream")

    class FailingResponse(MockStreamResponse):
        def iter_bytes(self, chunk_size=CHUNK_SIZE):
            return FailingIterator().iter_bytes(chunk_size)

    mock_http.response_factory = lambda url: FailingResponse()

    res = client.post("/v2/atlas/acquire", json={"source_id": source_id, "requester_id": "inv_01"})
    assert res.status_code == 502

    # Verificar que no hay archivos .tmp en ningún subdirectorio de atlas_dir
    tmp_files = list(atlas_dir.rglob("*.tmp"))
    assert len(tmp_files) == 0
