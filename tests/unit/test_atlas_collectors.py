from __future__ import annotations

import io
import hashlib
from pathlib import Path
import sys
import pytest
import httpx
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.schemas.document_schemas import (
    DocumentMetadataRecord,
    SourceRegistryEntry,
    AtlasManifestState,
)
from apps.atlas.storage.hashing import (
    compute_bytes_sha256,
    compute_file_sha256,
    compute_stream_sha256,
)
from apps.atlas.storage.manifest_manager import (
    ManifestManager,
    ManifestIntegrityError,
)
from apps.atlas.collectors.policy_verifier import PolicyVerifier
from apps.atlas.collectors.streaming_collector import (
    StreamingDocumentCollector,
    StreamingCollectorError,
)


@pytest.fixture
def temp_atlas_dir(tmp_path: Path) -> Path:
    """Directorio temporal aislado para pruebas de almacenamiento del Atlas."""
    atlas_dir = tmp_path / "atlas_test"
    atlas_dir.mkdir()
    return atlas_dir


@pytest.fixture
def policy_verifier() -> PolicyVerifier:
    """Instancia del verificador cargando el archivo de fuentes oficial del repositorio."""
    return PolicyVerifier(registry_path="apps/atlas/config/sources_registry.yaml")


# ---------------------------------------------------------------------------
# 1. Pruebas de Esquemas Pydantic V2 y Gobernanza
# ---------------------------------------------------------------------------

def test_document_metadata_schema_strictness():
    """El esquema debe rechazar campos extraños (extra='forbid')."""
    valid_data = {
        "source_id": "art_patr_montes_de_maria",
        "entity": "Agencia de Renovación del Territorio (ART)",
        "title": "PATR Montes de María",
        "level": "subregional_pdet",
        "territory_scope": "PDET_01_MONTES_DE_MARIA",
        "pipeline_type": "documental",
        "document_format": "pdf",
        "canonical_url": "https://www.renovacionterritorio.gov.co/descargar.php?idFile=22158",
        "download_date": "2026-10-06T12:00:00Z",
        "sha256": "a" * 64,
        "byte_size": 1024,
        "content_path": "sources/" + "a" * 64 + ".pdf",
        "source_type": "document_context",
        "provenance_class": "official_government",
        "consent_status": "not_applicable",
        "allowed_for_training": False,
        "usage_state": "context_only",
        "approval_status": "pending_review",
    }
    record = DocumentMetadataRecord.model_validate(valid_data)
    assert record.source_type == "document_context"
    assert record.allowed_for_training is False
    assert record.usage_state == "context_only"

    # Rechazo de campo desconocido
    with pytest.raises(ValidationError):
        invalid_data = dict(valid_data, campo_inventado="no_permitido")
        DocumentMetadataRecord.model_validate(invalid_data)

    # Rechazo de allowed_for_training = True (invariante absoluto)
    with pytest.raises(ValidationError):
        invalid_data = dict(valid_data, allowed_for_training=True)
        DocumentMetadataRecord.model_validate(invalid_data)

    # Rechazo de hash SHA-256 no conforme a 64 caracteres hex
    with pytest.raises(ValidationError):
        invalid_data = dict(valid_data, sha256="hash_invalido_demasiado_corto")
        DocumentMetadataRecord.model_validate(invalid_data)


def test_source_registry_schema_and_yaml_integrity(policy_verifier: PolicyVerifier):
    """Verifica que el registro YAML oficial se parsea y cumple con los esquemas Pydantic."""
    sources = policy_verifier.registered_sources
    assert len(sources) >= 5
    assert "art_patr_montes_de_maria" in sources
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in sources
    assert "adr_pidaret_sucre_ordenanza" in sources
    assert "pnd_colombia_2022_2026" in sources
    assert "datos_gov_co_eva_agricola" in sources

    pidaret_bol = sources["adr_pidaret_bolivar_ordenanza_323_2021"]
    assert pidaret_bol.adoption_norm == "Ordenanza 323 de 2021"
    assert pidaret_bol.level == "departamental"
    assert pidaret_bol.territory_scope == "DEP_13_BOLIVAR"


# ---------------------------------------------------------------------------
# 2. Pruebas de Hashing Criptográfico SHA-256
# ---------------------------------------------------------------------------

def test_streaming_sha256_calculation(tmp_path: Path):
    """Verifica el cálculo exacto de SHA-256 en memoria, flujo y archivo en disco."""
    payload = b"Contenido oficial simulado para prueba territorial de Montes de Maria" * 1000
    expected_hash = hashlib.sha256(payload).hexdigest()

    # Hashing directo en memoria
    assert compute_bytes_sha256(payload) == expected_hash

    # Hashing por flujo streaming
    stream = io.BytesIO(payload)
    assert compute_stream_sha256(stream, chunk_size=128) == expected_hash

    # Hashing desde archivo
    test_file = tmp_path / "document_test.pdf"
    test_file.write_bytes(payload)
    assert compute_file_sha256(test_file, chunk_size=256) == expected_hash


# ---------------------------------------------------------------------------
# 3. Pruebas de Almacenamiento, Manifiesto y Puerta Humana
# ---------------------------------------------------------------------------

def test_manifest_manager_lifecycle_and_integrity_check(temp_atlas_dir: Path):
    """Verifica el ciclo de vida del manifiesto y la detección de adulteración."""
    manager = ManifestManager(base_dir=temp_atlas_dir)
    manager.ensure_directories()

    content = b"PDF del PATR oficial de Montes de Maria"
    sha = hashlib.sha256(content).hexdigest()
    doc_path = manager.sources_dir / f"{sha}.pdf"
    doc_path.write_bytes(content)

    record = DocumentMetadataRecord(
        source_id="art_patr_montes_de_maria",
        entity="ART",
        title="PATR Montes de María",
        level="subregional_pdet",
        territory_scope="PDET_01_MONTES_DE_MARIA",
        pipeline_type="documental",
        document_format="pdf",
        canonical_url="https://renovacionterritorio.gov.co/doc",
        download_date="2026-10-06T12:00:00Z",
        sha256=sha,
        byte_size=len(content),
        content_path=f"sources/{sha}.pdf",
        source_type="document_context",
        provenance_class="official_government",
        consent_status="not_applicable",
        allowed_for_training=False,
        usage_state="context_only",
        approval_status="pending_review",
    )

    # 1. Registro exitoso
    manifest = manager.load_manifest()
    manager.register_document(manifest, record, verify_content=True)
    manager.save_manifest(manifest)

    # Cargar y verificar persistencia
    loaded_manifest = manager.load_manifest()
    assert "art_patr_montes_de_maria" in loaded_manifest.documents
    assert loaded_manifest.documents["art_patr_montes_de_maria"].sha256 == sha
    assert loaded_manifest.documents["art_patr_montes_de_maria"].approval_status == "pending_review"

    # 2. Aprobación humana
    manager.approve_document(
        loaded_manifest,
        source_id="art_patr_montes_de_maria",
        reviewer_id="investigador_01",
        notes="Documento oficial validado contra gaceta de ART.",
    )
    manager.save_manifest(loaded_manifest)

    reloaded = manager.load_manifest()
    approved_doc = reloaded.documents["art_patr_montes_de_maria"]
    assert approved_doc.approval_status == "approved"
    assert approved_doc.reviewer_id == "investigador_01"
    assert approved_doc.approval_timestamp is not None

    # 3. Detección de alteración (tampering)
    doc_path.write_bytes(b"CONTENIDO ALTERADO MALICIOSAMENTE")
    with pytest.raises(ManifestIntegrityError):
        manager.register_document(reloaded, record, verify_content=True)


# ---------------------------------------------------------------------------
# 4. Pruebas de Recolección Offline con Mocks (Cero llamadas de red)
# ---------------------------------------------------------------------------

def test_streaming_collector_from_mock_stream(temp_atlas_dir: Path, policy_verifier: PolicyVerifier):
    """Recolecta y valida un documento a partir de un flujo simulado sin tocar la red."""
    manager = ManifestManager(base_dir=temp_atlas_dir)
    collector = StreamingDocumentCollector(verifier=policy_verifier, manifest_manager=manager)

    mock_pdf_content = b"%PDF-1.4 Mock oficial del PIDARET Bolivar Ordenanza 323 de 2021" * 50
    expected_sha256 = hashlib.sha256(mock_pdf_content).hexdigest()
    stream = io.BytesIO(mock_pdf_content)

    record, policy_result = collector.collect_source_from_stream(
        source_id="adr_pidaret_bolivar_ordenanza_323_2021",
        stream_reader=stream,
        download_date_iso="2026-10-06T15:30:00Z",
        expected_sha256=expected_sha256,
    )

    # Validaciones del registro
    assert record.source_id == "adr_pidaret_bolivar_ordenanza_323_2021"
    assert record.sha256 == expected_sha256
    assert record.byte_size == len(mock_pdf_content)
    assert record.source_type == "document_context"
    assert record.allowed_for_training is False
    assert record.usage_state == "context_only"
    assert record.approval_status == "pending_review"

    # Validaciones de la política
    assert policy_result.is_official is True
    assert policy_result.sha256_verified is True
    assert policy_result.governance_verified is True
    assert policy_result.territory_matches is True
    assert policy_result.is_valid is True
    assert len(policy_result.violations) == 0

    # Validar que el archivo físico fue persistido con su hash en disco
    saved_file = temp_atlas_dir / record.content_path
    assert saved_file.is_file()
    assert saved_file.name == f"{expected_sha256}.pdf"
    assert saved_file.read_bytes() == mock_pdf_content


def test_streaming_collector_with_mocked_httpx_transport(temp_atlas_dir: Path, policy_verifier: PolicyVerifier):
    """Verifica que el colector por streaming funcione con transporte HTTP simulado."""
    manager = ManifestManager(base_dir=temp_atlas_dir)

    mock_content = b"JSON simulado para EVA de Evaluaciones Agropecuarias Municipales"
    expected_sha256 = hashlib.sha256(mock_content).hexdigest()

    # Crear mock handler de HTTPX (0 llamadas de red externas)
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert "datos.gov.co" in str(request.url)
        return httpx.Response(200, content=mock_content)

    mock_transport = httpx.MockTransport(mock_handler)
    mock_client = httpx.Client(transport=mock_transport)

    collector = StreamingDocumentCollector(
        verifier=policy_verifier,
        manifest_manager=manager,
        client=mock_client,
    )

    record, policy_result = collector.collect_source(
        source_id="datos_gov_co_eva_agricola",
        expected_sha256=expected_sha256,
    )

    assert record.source_id == "datos_gov_co_eva_agricola"
    assert record.sha256 == expected_sha256
    assert policy_result.is_valid is True
    assert record.approval_status == "pending_review"

    saved_file = temp_atlas_dir / record.content_path
    assert saved_file.is_file()
    assert saved_file.name == f"{expected_sha256}.json"
    assert saved_file.read_bytes() == mock_content


def test_collector_rejects_unregistered_source(temp_atlas_dir: Path, policy_verifier: PolicyVerifier):
    """Rechaza recolectar una fuente que no esté en el registro YAML oficial."""
    manager = ManifestManager(base_dir=temp_atlas_dir)
    collector = StreamingDocumentCollector(verifier=policy_verifier, manifest_manager=manager)

    stream = io.BytesIO(b"Documento de procedencia dudosa")
    with pytest.raises(Exception) as exc_info:
        collector.collect_source_from_stream(
            source_id="fuente_no_registrada_anonima",
            stream_reader=stream,
        )
    assert "Fuente no registrada" in str(exc_info.value)
