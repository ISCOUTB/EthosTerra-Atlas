from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
import httpx

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.web.schemas import WebDiscoveryQuery
from apps.atlas.web.autonomous_collector import AutonomousWebCollector
from apps.atlas.web.security import validate_url_security


def main():
    contact_email = os.environ.get("ATLAS_CONTACT_EMAIL")
    if not contact_email:
        print(json.dumps({"error": "ATLAS_CONTACT_EMAIL no definida. Abortando operacion."}))
        sys.exit(1)

    start_time = time.time()
    query = WebDiscoveryQuery(
        department="Bolívar",
        municipality="El Carmen de Bolívar",
        divipola="13244",
        subregion="Montes de María",
        instrument_types=["PATR"],
        max_documents_to_acquire=1,
    )

    from apps.atlas.web.adapters.focused_crawler import FocusedHtmlCrawler
    collector = AutonomousWebCollector(
        base_dir=Path("outputs/atlas"),
        adapters=[FocusedHtmlCrawler()],
    )

    # 1. Obtener contenido de robots.txt de la entidad objetivo
    target_host = "www.renovacionterritorio.gov.co"
    robots_url = f"https://{target_host}/robots.txt"
    robots_content = "No disponible"
    try:
        with httpx.Client(timeout=8.0) as client:
            resp_robots = client.get(robots_url, headers={"User-Agent": collector.user_agent})
            if resp_robots.status_code == 200:
                robots_content = resp_robots.text[:800]  # Primeras líneas para reporte
    except Exception as exc:
        robots_content = f"Error al consultar robots.txt: {exc}"

    # 2. Descubrimiento autónomo a través de la cascada web
    candidates = collector.discover_candidates(query)
    if not candidates:
        elapsed = time.time() - start_time
        print(json.dumps({
            "status": "no_candidates_found",
            "requests_count": collector.budget_tracker.requests_count,
            "elapsed_seconds": round(elapsed, 2),
            "discards": collector.budget_tracker.discards_log,
        }, indent=2))
        sys.exit(0)

    # Filtrar el candidato autorizado para adquisición (Opción B)
    candidate_b_list = [c for c in candidates if "PATR%20SUBREGION%20MONTES%20DE%20MARIA.pdf" in c.url or "patr" in c.url.lower() and c.status == "authority_verified"]
    if not candidate_b_list:
        print(json.dumps({
            "status": "aborted",
            "error": "No se localizó la Opción B en los candidatos descubiertos. Abortando según condición 11."
        }, indent=2, ensure_ascii=False))
        sys.exit(1)

    chosen = candidate_b_list[0]

    # Condición 11: Si la URL descubierta no corresponde exactamente a la Opción B, detener
    expected_option_b_url = "https://www.renovacionterritorio.gov.co/sites/default/files/2025-09/PATR%20SUBREGION%20MONTES%20DE%20MARIA.pdf"
    if chosen.url != expected_option_b_url:
        print(json.dumps({
            "status": "aborted",
            "error": f"Condición 11 activada: URL descubierta '{chosen.url}' no coincide exactamente con la Opción B autorizada."
        }, indent=2, ensure_ascii=False))
        sys.exit(1)

    robots_decision_path = collector.robots_mgr.can_fetch(chosen.url)

    # 3. Adquisición del documento
    try:
        result = collector.acquire_document(chosen)
        elapsed = time.time() - start_time

        output_data = {
            "status": "success",
            "candidate_source_id": result.source_id,
            "discovery_adapter": result.discovery_adapter,
            "discovered_url": chosen.url,
            "final_url": result.final_url,
            "provenance_chain": result.provenance_chain,
            "lifecycle_status": result.status,
            "is_superseded": result.is_superseded,
            "http_status": result.http_status,
            "content_type": result.content_type,
            "byte_size": result.byte_size,
            "sha256": result.sha256,
            "content_path": result.content_path,
            "etag": result.etag,
            "last_modified": result.last_modified,
            "robots_txt_sample": robots_content,
            "robots_decision_for_route": "allowed" if robots_decision_path else "disallowed",
            "total_requests": collector.budget_tracker.requests_count,
            "total_bytes_transferred": collector.budget_tracker.bytes_transferred,
            "elapsed_seconds": round(elapsed, 2),
            "discards_log": collector.budget_tracker.discards_log,
            "evaluated_candidates": [
                {
                    "source_id": c.source_id,
                    "url": c.url,
                    "title": c.title,
                    "instrument_type": c.instrument_type,
                    "status": c.status,
                    "is_superseded": c.is_superseded,
                    "discard_reason": c.discard_reason,
                }
                for c in candidates
            ],
        }
        print(json.dumps(output_data, indent=2, ensure_ascii=False))

    except Exception as exc:
        elapsed = time.time() - start_time
        error_data = {
            "status": "acquisition_failed",
            "candidate_url": chosen.url,
            "error": str(exc),
            "total_requests": collector.budget_tracker.requests_count,
            "elapsed_seconds": round(elapsed, 2),
            "discards_log": collector.budget_tracker.discards_log,
        }
        print(json.dumps(error_data, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
