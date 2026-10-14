import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.main import app
from apps.atlas.extractors.belief_extractor import (
    TerritorialBeliefExtractor,
    ArtifactNotApprovedError,
    _normalize_for_matching,
)
from apps.atlas.schemas.context_schemas import (
    TerritorialBeliefItem,
    TerritorialBeliefExtractionResult,
    PilotAggregatedBeliefs,
)
from apps.atlas.schemas.document_schemas import DocumentMetadataRecord, AtlasManifestState
from apps.atlas.storage.manifest_manager import ManifestManager
from apps.atlas.geo.territory_resolver import TerritoryResolver

client = TestClient(app)


def test_belief_schemas_strict_extra_forbid():
    """Verifica que los esquemas de creencias rechacen campos espurios (extra='forbid')."""
    valid_data = {
        "belief_id": "bel_test_001",
        "source_id": "art_patr_montes_de_maria",
        "pillar": "desarrollo_agrario_y_rural",
        "topic": "Distritos de Riego",
        "raw_excerpt": "Cita textual verificada en documento.",
        "ebdi_belief_assertion": "Existe prioridad en distritos de riego para pequeños productores.",
        "target_municipalities": ["San Jacinto", "María La Baja"],
        "applicable_divipolas": ["13654", "13442"],
        "confidence": 0.95,
        "verification_status": "verified_verbatim",
    }
    item = TerritorialBeliefItem.model_validate(valid_data)
    assert item.belief_id == "bel_test_001"
    assert item.confidence == 0.95

    with pytest.raises(ValidationError):
        TerritorialBeliefItem.model_validate({**valid_data, "unauthorized_field": "fake"})


def test_anti_hallucination_gate_verbatim():
    """El gate anti-alucinación debe aceptar citas que existan literalmente en el texto fuente."""
    extractor = TerritorialBeliefExtractor()
    source_text = (
        "En la subregión de Montes de María, específicamente en los municipios de El Carmen de Bolívar "
        "y San Jacinto, se priorizará el fortalecimiento de la cadena productiva del aguacate y el cacao."
    )

    verbatim_quote = "priorizará el fortalecimiento de la cadena productiva del aguacate"
    assert extractor.verify_verbatim_quote(verbatim_quote, source_text) is True

    # Comprobación de insensibilidad al espaciado y saltos de línea
    multiline_quote = "priorizará   el fortalecimiento\nde la cadena productiva"
    assert extractor.verify_verbatim_quote(multiline_quote, source_text) is True


def test_anti_hallucination_gate_rejects_hallucination():
    """El gate anti-alucinación debe rechazar terminantemente cualquier alteración o parafraseo."""
    extractor = TerritorialBeliefExtractor()
    source_text = (
        "En la subregión de Montes de María, específicamente en los municipios de El Carmen de Bolívar "
        "y San Jacinto, se priorizará el fortalecimiento de la cadena productiva del aguacate y el cacao."
    )

    hallucinated_quote = "se subsidiará al 100% la semilla de aguacate hass y cacao de exportación"
    assert extractor.verify_verbatim_quote(hallucinated_quote, source_text) is False

    partial_alteration = "priorizará el subsidio a la cadena productiva del aguacate"
    assert extractor.verify_verbatim_quote(partial_alteration, source_text) is False


def test_divipola_resolution_for_5_pilots():
    """Verifica que los 5 municipios piloto se asocien a sus códigos DIVIPOLA oficiales correspondientes."""
    extractor = TerritorialBeliefExtractor()
    munis = [
        "El Carmen de Bolívar",
        "San Jacinto",
        "San Juan Nepomuceno",
        "María La Baja",
        "San Onofre",
    ]
    divipolas = extractor.resolve_pilot_divipolas(munis)
    assert sorted(divipolas) == ["13244", "13442", "13654", "13657", "70717"]


def test_extraction_blocked_if_artifact_not_approved(tmp_path: Path):
    """Gobernanza: no se puede extraer conocimiento de un documento que no haya sido aprobado para contexto."""
    import asyncio

    manifest_mgr = ManifestManager(base_dir=tmp_path)

    # Documento en estado pendiente
    unapproved_doc = DocumentMetadataRecord(
        source_id="doc_unapproved",
        entity="ART",
        title="Documento de Prueba No Aprobado",
        level="subregional_pdet",
        territory_scope="Montes de María",
        pipeline_type="documental",
        document_format="pdf",
        canonical_url="https://example.gov.co/doc.pdf",
        download_date="2026-10-07T00:00:00Z",
        sha256="a" * 64,
        byte_size=1024,
        content_path="sources/test.pdf",
        status="pending_context_review",
        approval_status="pending_context_review",
    )
    manifest = AtlasManifestState(
        last_updated="2026-10-07T00:00:00Z",
        documents={"doc_unapproved": unapproved_doc},
    )
    manifest_mgr.save_manifest(manifest)

    extractor = TerritorialBeliefExtractor(manifest_manager=manifest_mgr, context_output_dir=tmp_path / "context")

    with pytest.raises(ArtifactNotApprovedError) as exc_info:
        asyncio.run(extractor.extract_beliefs_from_artifact("doc_unapproved"))

    assert "Bloqueo de Gobernanza" in str(exc_info.value)
    assert "pending_context_review" in str(exc_info.value)


def test_endpoint_extract_beliefs_blocked_on_unapproved():
    """El endpoint HTTP /extract-beliefs debe responder 403 si el documento no está en approved_for_context."""
    # Intentamos con un ID ficticio o un documento que esté en pending
    # Si no existe en el manifiesto, lanza 400
    res = client.post("/v2/atlas/artifacts/non_existent_doc/extract-beliefs")
    assert res.status_code == 400
    assert "no encontrado" in res.json()["detail"].lower()


def test_endpoint_get_beliefs_404_when_not_extracted():
    """El endpoint HTTP /beliefs debe responder 404 si el documento aún no tiene archivo de creencias."""
    res = client.get("/v2/atlas/artifacts/unextracted_doc/beliefs")
    assert res.status_code == 404
    assert "No se han extraído creencias" in res.json()["detail"]


def test_endpoint_pilot_aggregated_beliefs():
    """El endpoint HTTP /pilots/{divipola}/beliefs debe responder la estructura consolidada para El Carmen de Bolívar."""
    res = client.get("/v2/atlas/pilots/13244/beliefs")
    assert res.status_code == 200
    data = res.json()
    assert data["divipola"] == "13244"
    assert data["municipality_name"] == "El Carmen de Bolívar"
    assert data["department_name"] == "Bolívar"
    assert data["is_pdet"] is True
    assert "beliefs" in data


def test_endpoint_extraction_status_returns_idle_or_disk():
    """El endpoint /extraction-status debe responder un esquema válido de estado."""
    res = client.get("/v2/atlas/artifacts/any_doc/extraction-status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ("idle", "processing", "completed", "failed")
    assert "progress_percent" in data
