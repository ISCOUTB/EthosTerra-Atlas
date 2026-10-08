from __future__ import annotations

import hashlib
import io
from pathlib import Path
import sys
import pytest
import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.web.schemas import WebDiscoveryQuery
from apps.atlas.web.autonomous_collector import AutonomousWebCollector, AutonomousWebCollectorError
from apps.atlas.web.adapters import NativeSearchAdapter
from apps.atlas.web.security import validate_url_security


class MockStreamingResponse:
    def __init__(
        self,
        status_code: int = 200,
        content: bytes = b"%PDF-1.4 Mock real PATR official document content for testing",
        content_type: str = "application/pdf",
        headers: dict | None = None,
        url: str = "https://www.renovacionterritorio.gov.co/descargar.php?idFile=22158",
    ):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {
            "content-type": content_type,
            "etag": '"mock-etag-12345"',
            "last-modified": "Wed, 21 Oct 2025 07:28:00 GMT",
        }
        self.url = httpx.URL(url)
        self.text = content.decode("utf-8", errors="ignore")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter_bytes(self, chunk_size: int = 65536):
        stream = io.BytesIO(self.content)
        while chunk := stream.read(chunk_size):
            yield chunk


class MockCascadeHttpClient:
    """Mock client que simula respuestas de búsqueda nativa y streaming de PDF."""

    def __init__(self, search_html: str, pdf_bytes: bytes) -> None:
        self.search_html = search_html
        self.pdf_bytes = pdf_bytes
        self.get_calls: list[str] = []
        self.stream_calls: list[str] = []

    def get(self, url: str, **kwargs):
        self.get_calls.append(url)
        # robots.txt
        if "robots.txt" in url:
            return MockStreamingResponse(content=b"User-agent: *\nAllow: /\n", content_type="text/plain")
        # Búsqueda nativa
        return MockStreamingResponse(content=self.search_html.encode("utf-8"), content_type="text/html")

    def stream(self, method: str, url: str, **kwargs):
        self.stream_calls.append(url)
        return MockStreamingResponse(content=self.pdf_bytes, content_type="application/pdf", url=url)


@pytest.fixture
def web_collector_env(tmp_path: Path, monkeypatch):
    """Entorno de prueba aislado para la cascada y el recolector web autónomo."""
    tmp_atlas = tmp_path / "atlas"
    tmp_atlas.mkdir(parents=True, exist_ok=True)

    # Mockear resolución DNS para simular IPs públicas oficiales en pruebas unitarias
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda host, port, proto=0: [(2, 1, 6, "", ("181.143.200.10", 443))],
    )

    sample_search_html = """
    <html>
      <body>
        <div class="search-results">
          <a href="https://www.renovacionterritorio.gov.co/descargar.php?idFile=22158">
            Plan de Accion para la Transformacion Regional PATR Montes de Maria
          </a>
        </div>
      </body>
    </html>
    """
    sample_pdf_bytes = b"%PDF-1.4 Mock official PATR file content verified"

    mock_client = MockCascadeHttpClient(search_html=sample_search_html, pdf_bytes=sample_pdf_bytes)
    collector = AutonomousWebCollector(base_dir=tmp_atlas, user_agent="test-agent", client=mock_client)  # type: ignore

    return {
        "collector": collector,
        "mock_client": mock_client,
        "sample_pdf": sample_pdf_bytes,
        "base_dir": tmp_atlas,
    }


def test_cascade_discovery_and_acquisition_superseded_2019(web_collector_env):
    """Ejecuta la cascada detectando la versión 2019 como superseded_candidate."""
    collector = web_collector_env["collector"]
    sample_pdf = web_collector_env["sample_pdf"]
    base_dir = web_collector_env["base_dir"]

    query = WebDiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        subregion="Montes de María",
        instrument_types=["PATR"],
        max_documents_to_acquire=1,
    )

    # 1. Cascada de descubrimiento autónomo
    candidates = collector.discover_candidates(query)
    assert len(candidates) >= 1
    candidate = candidates[0]

    # Verificar metadatos y estado inicial de descubrimiento
    assert candidate.status == "authority_verified"
    assert candidate.instrument_type == "PATR"
    assert "renovacionterritorio.gov.co" in candidate.url
    assert candidate.discovery_adapter == "native_search_adapter"

    # 2. Adquisición controlada: Al ser versión de 2019, debe transicionar a superseded_candidate
    result = collector.acquire_document(candidate)

    assert result.status in ("superseded_candidate", "pending_context_review")
    assert result.is_superseded is True
    assert result.http_status == 200
    assert result.content_type == "application/pdf"
    assert result.etag == '"mock-etag-12345"'
    assert result.last_modified == "Wed, 21 Oct 2025 07:28:00 GMT"
    assert result.sha256 == hashlib.sha256(sample_pdf).hexdigest()
    assert result.byte_size == len(sample_pdf)

    # Verificar que el artefacto físico reside en cuarentena fuera de git
    assert result.content_path is not None
    target_file = base_dir / result.content_path
    assert target_file.is_file()
    assert target_file.read_bytes() == sample_pdf

    # Verificar registro en el manifiesto
    manifest = collector.manifest_manager.load_manifest()
    assert candidate.source_id in manifest.documents
    meta = manifest.documents[candidate.source_id]
    assert "superseded_candidate" in meta.approval_notes


def test_cascade_acquisition_prioritizes_2026_version(web_collector_env):
    """Verifica que la versión actualizada 2026 transicione a pending_context_review."""
    collector = web_collector_env["collector"]
    mock_client = web_collector_env["mock_client"]

    # Simular versión 2026 (Resolución 000841 de 2026)
    mock_client.search_html = """
    <html><body>
      <a href="https://www.renovacionterritorio.gov.co/descargar.php?idFile=99999">
        PATR Montes de Maria Actualizacion 2026 Resolucion 000841
      </a>
    </body></html>
    """

    query = WebDiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        subregion="Montes de María",
        instrument_types=["PATR"],
        max_documents_to_acquire=1,
    )

    candidates = collector.discover_candidates(query)
    assert len(candidates) >= 1
    candidate = candidates[0]

    result = collector.acquire_document(candidate)
    assert result.status == "pending_context_review"
    assert result.is_superseded is False



def test_reject_magic_bytes_failure(web_collector_env):
    """Rechaza artefacto si el stream no inicia con %PDF-."""
    collector = web_collector_env["collector"]
    mock_client = web_collector_env["mock_client"]

    # Simular servidor retornando HTML disfrazado de PDF
    mock_client.pdf_bytes = b"<html><body>Error 404 No encontrado</body></html>"

    query = WebDiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        subregion="Montes de María",
        instrument_types=["PATR"],
        max_documents_to_acquire=1,
    )

    candidates = collector.discover_candidates(query)
    assert len(candidates) >= 1

    with pytest.raises(AutonomousWebCollectorError) as exc:
        collector.acquire_document(candidates[0])
    assert "Firma mágica inválida" in str(exc.value)
