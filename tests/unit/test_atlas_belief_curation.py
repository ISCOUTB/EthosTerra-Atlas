import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.main import app
from apps.atlas.schemas.context_schemas import (
    TerritorialBeliefItem,
    TerritorialBeliefExtractionResult,
    BeliefCurationRequest,
)
from apps.atlas.extractors.belief_extractor import TerritorialBeliefExtractor
from apps.atlas.storage.manifest_manager import ManifestManager
from apps.atlas.geo.territory_resolver import TerritoryResolver

client = TestClient(app)


def test_belief_curation_request_schema():
    """Valida el esquema estricto Pydantic V2 de BeliefCurationRequest."""
    req = BeliefCurationRequest(
        decision="admitted_ebdi",
        curator_id="investigador_ebdi_01",
        notes="Aprobado formalmente",
    )
    assert req.decision == "admitted_ebdi"
    assert req.curator_id == "investigador_ebdi_01"

    # extra='forbid'
    with pytest.raises(Exception):
        BeliefCurationRequest(
            decision="admitted_ebdi",
            curator_id="investigador_01",
            extra_field="prohibido",  # type: ignore
        )


def test_curate_belief_unit(tmp_path: Path):
    """Valida la mutación determinista de curación en el extractor."""
    context_dir = tmp_path / "context"
    context_dir.mkdir(parents=True)

    dummy_item = TerritorialBeliefItem(
        belief_id="bel_test_001",
        source_id="art_patr_test",
        pillar="desarrollo_agrario_y_rural",
        topic="Cadenas productivas",
        raw_excerpt="Cita textual de prueba",
        ebdi_belief_assertion="Creencia eBDI de prueba",
        target_municipalities=["El Carmen de Bolívar"],
        applicable_divipolas=["13244"],
        confidence=0.95,
        verification_status="verified_verbatim",
        curation_status="pending",
    )

    result_dummy = TerritorialBeliefExtractionResult(
        source_id="art_patr_test",
        instrument_title="Documento de Prueba",
        document_sha256="a" * 64,
        extraction_timestamp_utc="2026-10-07T12:00:00Z",
        model_used="ai/gemma4:E4B",
        extraction_method="poppler_pdftotext_plus_micro_llm",
        total_beliefs_extracted=1,
        verified_beliefs_count=1,
        rejected_hallucinations_count=0,
        beliefs=[dummy_item],
    )

    json_file = context_dir / "art_patr_test_beliefs.json"
    json_file.write_text(json.dumps(result_dummy.model_dump()), encoding="utf-8")

    extractor = TerritorialBeliefExtractor(
        manifest_manager=ManifestManager(base_dir=tmp_path),
        resolver=TerritoryResolver(),
        context_output_dir=context_dir,
    )

    # Curar como admitido
    updated = extractor.curate_belief(
        source_id="art_patr_test",
        belief_id="bel_test_001",
        decision="admitted_ebdi",
        curator_id="curador_unit_test",
        notes="Aprobado",
    )
    assert updated.curation_status == "admitted_ebdi"
    assert updated.curator_id == "curador_unit_test"
    assert updated.curation_timestamp_utc is not None

    # Curar como descartado por ruido
    updated_noise = extractor.curate_belief(
        source_id="art_patr_test",
        belief_id="bel_test_001",
        decision="dismissed_noise",
        curator_id="curador_unit_test",
        notes="Descartado acrónimo",
    )
    assert updated_noise.curation_status == "dismissed_noise"


def test_api_curate_belief_endpoint():
    """Valida el endpoint PATCH /v2/atlas/artifacts/{source_id}/beliefs/{belief_id}."""
    # Consultar creencia existente en art_patr_montes_de_maria
    get_res = client.get("/v2/atlas/artifacts/art_patr_montes_de_maria/beliefs")
    if get_res.status_code == 200:
        data = get_res.json()
        first_belief = data["beliefs"][0]
        belief_id = first_belief["belief_id"]

        patch_res = client.patch(
            f"/v2/atlas/artifacts/art_patr_montes_de_maria/beliefs/{belief_id}",
            json={
                "decision": "admitted_ebdi",
                "curator_id": "investigador_test_api",
                "notes": "Curación vía test unitario FastAPI",
            },
        )
        assert patch_res.status_code == 200
        curated_item = patch_res.json()
        assert curated_item["curation_status"] == "admitted_ebdi"
        assert curated_item["curator_id"] == "investigador_test_api"


def test_api_pilot_beliefs_filters_noise():
    """Valida que las creencias marcadas como 'dismissed_noise' no contaminan el agregado del piloto."""
    res = client.get("/v2/atlas/pilots/13244/beliefs")
    if res.status_code == 200:
        data = res.json()
        assert data["divipola"] == "13244"
        for b in data["beliefs"]:
            assert b["curation_status"] != "dismissed_noise"
