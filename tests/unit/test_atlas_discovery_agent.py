from __future__ import annotations

from pathlib import Path
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.agents.discovery_agent import DocumentDiscoveryAgent
from apps.atlas.schemas.discovery_schemas import DiscoveryQuery, InstrumentType


ALL_INSTRUMENTS: list[InstrumentType] = [
    "PATR",
    "PIDARET",
    "PDT",
    "EOT",
    "PBOT",
    "POT",
    "ordenanza",
    "acuerdo_municipal",
    "datos_agricolas",
]


@pytest.fixture
def discovery_agent() -> DocumentDiscoveryAgent:
    """Instancia del agente de descubrimiento en modo local offline."""
    return DocumentDiscoveryAgent()


# ---------------------------------------------------------------------------
# 1. Pruebas por Municipio Piloto (Bolívar y Sucre)
# ---------------------------------------------------------------------------

def test_el_carmen_de_bolivar_13244(discovery_agent: DocumentDiscoveryAgent):
    """El Carmen de Bolívar debe resolver fuentes de Montes de María, Bolívar y Nación."""
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        subregion="Montes de María",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)

    assert result.total_candidates >= 3
    source_ids = {c.source_id for c in result.candidates}
    assert "art_patr_montes_de_maria" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in source_ids
    assert "datos_gov_co_eva_agricola" in source_ids

    # Verificar que no incluye fuentes departamentales de Sucre
    assert "adr_pidaret_sucre_ordenanza" not in source_ids


def test_san_jacinto_13654(discovery_agent: DocumentDiscoveryAgent):
    """San Jacinto debe resolver fuentes de Bolívar y Montes de María."""
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="San Jacinto",
        divipola="13654",
        subregion="Montes de María",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)
    source_ids = {c.source_id for c in result.candidates}
    assert "art_patr_montes_de_maria" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in source_ids


def test_san_juan_nepomuceno_13657(discovery_agent: DocumentDiscoveryAgent):
    """San Juan Nepomuceno debe resolver fuentes de Bolívar y Montes de María."""
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="San Juan Nepomuceno",
        divipola="13657",
        subregion="Montes de María",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)
    source_ids = {c.source_id for c in result.candidates}
    assert "art_patr_montes_de_maria" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in source_ids


def test_maria_la_baja_13442(discovery_agent: DocumentDiscoveryAgent):
    """María La Baja debe resolver fuentes de Bolívar y Montes de María."""
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="María La Baja",
        divipola="13442",
        subregion="Montes de María",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)
    source_ids = {c.source_id for c in result.candidates}
    assert "art_patr_montes_de_maria" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" in source_ids


def test_san_onofre_sucre_70717(discovery_agent: DocumentDiscoveryAgent):
    """San Onofre (Sucre) debe resolver PIDARET Sucre y PATR Montes de María, pero NO PIDARET Bolívar."""
    query = DiscoveryQuery(
        department="Sucre",
        municipality="San Onofre",
        divipola="70717",
        subregion="Montes de María",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)
    source_ids = {c.source_id for c in result.candidates}
    assert "art_patr_montes_de_maria" in source_ids
    assert "adr_pidaret_sucre_ordenanza" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" not in source_ids


def test_montes_de_maria_multidepartmental_cohesion(discovery_agent: DocumentDiscoveryAgent):
    """Montes de María comparte el PATR de ART entre Bolívar (13244) y Sucre (70717)."""
    q_bolivar = DiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        instrument_types=["PATR"],
    )
    q_sucre = DiscoveryQuery(
        department="Sucre",
        municipality="San Onofre",
        divipola="70717",
        instrument_types=["PATR"],
    )

    res_bol = discovery_agent.discover_sources(q_bolivar)
    res_suc = discovery_agent.discover_sources(q_sucre)

    patr_bol = [c for c in res_bol.candidates if c.source_id == "art_patr_montes_de_maria"]
    patr_suc = [c for c in res_suc.candidates if c.source_id == "art_patr_montes_de_maria"]

    assert len(patr_bol) == 1
    assert len(patr_suc) == 1
    assert patr_bol[0].url == patr_suc[0].url


# ---------------------------------------------------------------------------
# 2. Pruebas de Seguridad, Dominios y Validación de Content-Type
# ---------------------------------------------------------------------------

def test_unofficial_domains_rejected():
    """Valida la lista blanca estricta de dominios institucionales."""
    assert DocumentDiscoveryAgent.is_official_domain("https://www.adr.gov.co/doc.pdf") is True
    assert DocumentDiscoveryAgent.is_official_domain("https://renovacionterritorio.gov.co/doc.pdf") is True
    assert DocumentDiscoveryAgent.is_official_domain("https://geoportal.dane.gov.co/mgn") is True
    assert DocumentDiscoveryAgent.is_official_domain("https://www.datos.gov.co/resource/2pn8.json") is True

    # Rechazo estricto de dominios no oficiales
    assert DocumentDiscoveryAgent.is_official_domain("https://www.noticias-colombia.com/pidaret.pdf") is False
    assert DocumentDiscoveryAgent.is_official_domain("https://blog-campesino.org/tierras") is False
    assert DocumentDiscoveryAgent.is_official_domain("https://wikipedia.org/wiki/Montes_de_Maria") is False


def test_http_200_with_html_triggers_requires_review_for_pdf():
    """Si una fuente documental responde HTTP 200 pero entrega HTML (ej. portal de login), se cataloga requires_review."""
    def mock_probe(url: str):
        return {"status_code": 200, "content_type": "text/html; charset=UTF-8"}

    agent_with_mock = DocumentDiscoveryAgent(url_probe_fn=mock_probe)
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        instrument_types=["PATR"],
    )
    result = agent_with_mock.discover_sources(query)
    candidate = result.candidates[0]
    assert candidate.status == "requires_review"
    assert candidate.confidence_level == "medium"
    assert "Alerta: Content-Type no corresponde a binario PDF" in candidate.selection_reason


# ---------------------------------------------------------------------------
# 3. Pruebas de Invariantes de Gobernanza y Cero Descargas
# ---------------------------------------------------------------------------

def test_candidates_never_automatically_approved(discovery_agent: DocumentDiscoveryAgent):
    """Todos los candidatos deben conservar approval_status='pending_review' y allowed_for_training=False."""
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)
    for c in result.candidates:
        assert c.approval_status == "pending_review"
        assert c.allowed_for_training is False
        assert c.usage_state == "context_only"
        assert c.consent_status == "not_applicable"


def test_agent_does_not_download_or_write_files(discovery_agent: DocumentDiscoveryAgent):
    """El agente de descubrimiento no debe crear ni modificar archivos en outputs/atlas/sources/."""
    sources_dir = Path("outputs/atlas/sources")
    existing_files_before = set(sources_dir.glob("*")) if sources_dir.exists() else set()

    query = DiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        instrument_types=ALL_INSTRUMENTS,
    )
    discovery_agent.discover_sources(query)

    existing_files_after = set(sources_dir.glob("*")) if sources_dir.exists() else set()
    assert existing_files_before == existing_files_after


def test_pipeline_separation_documental_vs_tabular(discovery_agent: DocumentDiscoveryAgent):
    """Garantiza la separación estricta entre documentos narrativos y fuentes de datos tabulares."""
    query = DiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        instrument_types=ALL_INSTRUMENTS,
    )
    result = discovery_agent.discover_sources(query)

    documental_candidates = [c for c in result.candidates if c.pipeline_type == "documental"]
    tabular_candidates = [c for c in result.candidates if c.pipeline_type == "api_tabular"]

    assert len(documental_candidates) >= 2
    assert len(tabular_candidates) >= 1

    for doc in documental_candidates:
        assert doc.source_type == "document_context"
        assert doc.document_format == "pdf"

    for tab in tabular_candidates:
        assert tab.source_type == "tabular_context"
        assert tab.document_format in ("json_api", "geojson")


def test_candidate_record_rejects_invalid_pipeline_governance_combinations():
    """Verifica que CandidateSourceRecord rechace todas las combinaciones inválidas entre pipeline y gobernanza."""
    from pydantic import ValidationError
    from apps.atlas.schemas.discovery_schemas import CandidateSourceRecord

    base_data = {
        "source_id": "test_src",
        "url": "https://www.adr.gov.co/doc",
        "entity": "ADR",
        "title": "Documento Test",
        "territory_scope": "DEP_13_BOLIVAR",
        "instrument_type": "PIDARET",
        "status": "candidate",
        "confidence_level": "high",
        "selection_reason": "Test",
        "query_date": "2026-10-06T12:00:00Z",
        "allowed_for_training": False,
        "usage_state": "context_only",
        "consent_status": "not_applicable",
        "approval_status": "pending_review",
    }

    # 1. documental + tabular_context -> Rechazado
    with pytest.raises(ValidationError) as exc:
        CandidateSourceRecord.model_validate(dict(
            base_data,
            pipeline_type="documental",
            document_format="pdf",
            source_type="tabular_context",
        ))
    assert "Incompatibilidad de gobernanza" in str(exc.value)

    # 2. api_tabular + document_context -> Rechazado
    with pytest.raises(ValidationError) as exc:
        CandidateSourceRecord.model_validate(dict(
            base_data,
            pipeline_type="api_tabular",
            document_format="json_api",
            source_type="document_context",
        ))
    assert "Incompatibilidad de gobernanza" in str(exc.value)

    # 3. documental + json_api -> Rechazado
    with pytest.raises(ValidationError) as exc:
        CandidateSourceRecord.model_validate(dict(
            base_data,
            pipeline_type="documental",
            document_format="json_api",
            source_type="document_context",
        ))
    assert "Incompatibilidad de formato" in str(exc.value)

    # 4. api_tabular + pdf -> Rechazado
    with pytest.raises(ValidationError) as exc:
        CandidateSourceRecord.model_validate(dict(
            base_data,
            pipeline_type="api_tabular",
            document_format="pdf",
            source_type="tabular_context",
        ))
    assert "Incompatibilidad de formato" in str(exc.value)
