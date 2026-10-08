from __future__ import annotations

from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.main import app

client = TestClient(app)

PILOTS = [
    ("Bolívar", "El Carmen de Bolívar", "13244"),
    ("Bolívar", "San Jacinto", "13654"),
    ("Bolívar", "San Juan Nepomuceno", "13657"),
    ("Bolívar", "María La Baja", "13442"),
    ("Sucre", "San Onofre", "70717"),
]


# ---------------------------------------------------------------------------
# 1. Pruebas de Solicitud Válida para los 5 Municipios Piloto
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("department,municipality,divipola", PILOTS)
def test_discover_endpoint_five_pilots(department: str, municipality: str, divipola: str):
    """El endpoint /v2/atlas/discover debe responder 200 para todos los pilotos oficiales."""
    payload = {
        "department": department,
        "municipality": municipality,
        "divipola": divipola,
        "instrument_types": ["PATR", "PIDARET", "PDT", "ordenanza", "datos_agricolas"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["query"]["divipola"] == divipola
    assert data["resolved_hierarchy"]["municipality_code"] == divipola
    assert data["total_candidates"] >= 3
    assert len(data["candidates"]) == data["total_candidates"]


# ---------------------------------------------------------------------------
# 2. Pruebas de Territorio Específico y Cohesión Multidepartamental
# ---------------------------------------------------------------------------

def test_discover_san_onofre_sucre_association():
    """San Onofre (70717) debe incluir Sucre y excluir PIDARET de Bolívar."""
    payload = {
        "department": "Sucre",
        "municipality": "San Onofre",
        "divipola": "70717",
        "instrument_types": ["PATR", "PIDARET", "PDT", "ordenanza", "datos_agricolas"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 200
    data = response.json()

    source_ids = {c["source_id"] for c in data["candidates"]}
    assert "adr_pidaret_sucre_ordenanza" in source_ids
    assert "adr_pidaret_bolivar_ordenanza_323_2021" not in source_ids
    assert "art_patr_montes_de_maria" in source_ids


def test_discover_montes_de_maria_multidepartmental():
    """Montes de María comparte el PATR entre Bolívar (13244) y Sucre (70717)."""
    resp_bol = client.post("/v2/atlas/discover", json={
        "department": "Bolívar",
        "municipality": "El Carmen de Bolívar",
        "divipola": "13244",
        "instrument_types": ["PATR"],
    })
    resp_suc = client.post("/v2/atlas/discover", json={
        "department": "Sucre",
        "municipality": "San Onofre",
        "divipola": "70717",
        "instrument_types": ["PATR"],
    })

    assert resp_bol.status_code == 200
    assert resp_suc.status_code == 200

    cands_bol = resp_bol.json()["candidates"]
    cands_suc = resp_suc.json()["candidates"]

    patr_bol = [c for c in cands_bol if c["source_id"] == "art_patr_montes_de_maria"]
    patr_suc = [c for c in cands_suc if c["source_id"] == "art_patr_montes_de_maria"]

    assert len(patr_bol) == 1
    assert len(patr_suc) == 1
    assert patr_bol[0]["url"] == patr_suc[0]["url"]


# ---------------------------------------------------------------------------
# 3. Pruebas de Rechazo y Validación Estricta
# ---------------------------------------------------------------------------

def test_discover_rejects_extra_fields():
    """El endpoint debe rechazar payloads con campos extraños (extra='forbid')."""
    payload = {
        "department": "Bolívar",
        "municipality": "El Carmen de Bolívar",
        "divipola": "13244",
        "instrument_types": ["PATR"],
        "campo_malicioso_no_permitido": 12345,
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 422


def test_discover_rejects_invalid_divipola_format():
    """El formato de DIVIPOLA debe ser exactamente 5 dígitos."""
    payload = {
        "department": "Bolívar",
        "municipality": "El Carmen de Bolívar",
        "divipola": "132",  # Inválido: solo 3 dígitos
        "instrument_types": ["PATR"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 422


def test_discover_rejects_unsupported_instruments():
    """Debe rechazar instrumentos no contemplados en InstrumentType."""
    payload = {
        "department": "Bolívar",
        "municipality": "El Carmen de Bolívar",
        "divipola": "13244",
        "instrument_types": ["INSTRUMENTO_INVENTADO_NO_SOPORTADO"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 422


def test_discover_rejects_incompatible_territory():
    """Debe rechazar discrepancias territoriales entre DIVIPOLA y departamento declarado."""
    payload = {
        "department": "Antioquia",  # Incompatible con Bolívar (13244)
        "municipality": "El Carmen de Bolívar",
        "divipola": "13244",
        "instrument_types": ["PATR"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 400
    assert "Incompatibilidad territorial" in response.json()["detail"]


def test_discover_rejects_unknown_divipola():
    """Debe responder 404 si el DIVIPOLA de 5 dígitos no existe en el catálogo."""
    payload = {
        "department": "Bolívar",
        "municipality": "Municipio Ficticio",
        "divipola": "99999",
        "instrument_types": ["PATR"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 4. Pruebas de Aislamiento: Cero Red, Cero Escrituras y Gobernanza
# ---------------------------------------------------------------------------

def test_discover_zero_writes_and_governance_invariants():
    """Confirma cero escrituras en outputs/ y estricta gobernanza en los candidatos."""
    sources_dir = Path("outputs/atlas/sources")
    before_files = set(sources_dir.glob("*")) if sources_dir.exists() else set()

    payload = {
        "department": "Bolívar",
        "municipality": "El Carmen de Bolívar",
        "divipola": "13244",
        "instrument_types": ["PATR", "PIDARET", "PDT", "ordenanza", "datos_agricolas"],
    }
    response = client.post("/v2/atlas/discover", json=payload)
    assert response.status_code == 200

    after_files = set(sources_dir.glob("*")) if sources_dir.exists() else set()
    assert before_files == after_files, "El endpoint escribió indebidamente en outputs/atlas/sources/"

    data = response.json()
    for cand in data["candidates"]:
        assert cand["approval_status"] == "pending_review"
        assert cand["allowed_for_training"] is False
        assert cand["usage_state"] == "context_only"
        assert cand["consent_status"] == "not_applicable"

        # Validación de separación de pipelines
        if cand["pipeline_type"] == "documental":
            assert cand["source_type"] == "document_context"
        elif cand["pipeline_type"] == "api_tabular":
            assert cand["source_type"] == "tabular_context"
