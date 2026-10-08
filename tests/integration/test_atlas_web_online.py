from __future__ import annotations

import os
from pathlib import Path
import pytest

from apps.atlas.web.schemas import WebDiscoveryQuery
from apps.atlas.web.autonomous_collector import AutonomousWebCollector


@pytest.mark.skipif(
    not os.environ.get("RUN_ONLINE_TESTS"),
    reason="Prueba online real deshabilitada por defecto. Requiere RUN_ONLINE_TESTS=1 y autorización explícita.",
)
def test_online_real_acquisition_patr_el_carmen_de_bolivar(tmp_path: Path):
    """Prueba de aceptación real online opt-in.

    Entrada: El Carmen de Bolívar, DIVIPOLA 13244, PATR.
    Sin suministrar URL final: el agente debe descubrirla en Internet y descargar 1 PDF real.
    """
    tmp_atlas = tmp_path / "atlas_online"
    collector = AutonomousWebCollector(base_dir=tmp_atlas)

    query = WebDiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        subregion="Montes de María",
        instrument_types=["PATR"],
        max_documents_to_acquire=1,
    )

    # 1. Búsqueda y descubrimiento real
    candidates = collector.discover_candidates(query)
    assert len(candidates) >= 1, "El agente no pudo descubrir candidatos online para el PATR de Montes de María"

    chosen = candidates[0]
    assert "https://" in chosen.url
    assert "renovacionterritorio.gov.co" in chosen.url

    # 2. Descarga real y cuarentena
    result = collector.acquire_document(chosen)

    assert result.status == "pending_context_review"
    assert result.http_status == 200
    assert result.content_type == "application/pdf"
    assert result.sha256 is not None and len(result.sha256) == 64
    assert result.byte_size is not None and result.byte_size > 1000

    # Comprobar existencia física del PDF descargado
    target_path = tmp_atlas / result.content_path
    assert target_path.is_file()
    assert target_path.stat().st_size == result.byte_size
