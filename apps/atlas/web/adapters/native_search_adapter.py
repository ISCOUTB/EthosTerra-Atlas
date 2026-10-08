from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin, quote_plus
import httpx

from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.security import validate_url_security
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)

NATIVE_SEARCH_TARGETS = [
    {
        "entity": "Agencia de Renovación del Territorio (ART)",
        "host": "www.renovacionterritorio.gov.co",
        "search_url_template": "https://www.renovacionterritorio.gov.co/?s={query}",
        "instruments": ["PATR", "PDET"],
    },
    {
        "entity": "Agencia de Desarrollo Rural (ADR)",
        "host": "www.adr.gov.co",
        "search_url_template": "https://www.adr.gov.co/?s={query}",
        "instruments": ["PIDARET"],
    },
]

# Regex para extraer enlaces en HTML de forma determinista y sin dependencias no auditadas
HREF_PATTERN = re.compile(r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\']([^>]*)>(.*?)</a>', re.IGNORECASE | re.DOTALL)


class NativeSearchAdapter(BaseDiscoveryAdapter):
    """Adaptador de nivel 4: Búsqueda nativa documentada en portales institucionales oficiales."""

    @property
    def name(self) -> str:
        return "native_search_adapter"

    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        candidates: list[CandidateProvenanceRecord] = []
        target_instruments = [inst.upper() for inst in query.instrument_types]

        for target in NATIVE_SEARCH_TARGETS:
            # Comprobar si este portal atiende alguno de los instrumentos solicitados
            matched_instruments = [inst for inst in target["instruments"] if inst in target_instruments]
            if not matched_instruments:
                continue

            for inst in matched_instruments:
                # Construir término de búsqueda según territorio
                territory_term = query.subregion or query.department
                search_query_str = f"{inst} {territory_term}"
                search_url = target["search_url_template"].format(query=quote_plus(search_query_str))

                try:
                    validate_url_security(search_url, resolve_dns=False)
                    if not robots_mgr.can_fetch(search_url, client=client):
                        budget.record_discard(search_url, "robots_txt_disallowed")
                        continue

                    if not budget.can_request():
                        return candidates

                    rate_limiter.wait_for_turn(target["host"])
                    resp = client.get(
                        search_url,
                        headers={"User-Agent": robots_mgr.user_agent},
                        timeout=12.0,
                    )
                    budget.record_request(search_url, resp.status_code, len(resp.content))

                    if resp.status_code == 200:
                        html_text = resp.text
                        for match in HREF_PATTERN.finditer(html_text):
                            raw_href = match.group(1).strip()
                            anchor_text = re.sub(r"<[^>]+>", "", match.group(3)).strip()
                            full_url = urljoin(search_url, raw_href)

                            # Filtrar enlaces relevantes (PDF directo, Drupal files o script de descarga)
                            url_lower = full_url.lower()
                            anchor_lower = anchor_text.lower()
                            is_doc_candidate = (
                                url_lower.endswith(".pdf")
                                or ".pdf" in url_lower
                                or "descargar.php" in url_lower
                                or "idfile=" in url_lower
                                or "wp-content/uploads" in url_lower
                                or "sites/default/files" in url_lower
                            )

                            if is_doc_candidate:
                                # Analizar snippet circundante para rescatar contexto de botones genéricos
                                start_pos = max(0, match.start() - 600)
                                surrounding_snippet = html_text[start_pos:match.start()].lower()

                                is_pertinent = (
                                    inst.lower() in url_lower
                                    or inst.lower() in anchor_lower
                                    or inst.lower() in surrounding_snippet
                                    or "montes" in url_lower
                                    or "montes" in anchor_lower
                                    or "montes" in surrounding_snippet
                                    or "bolivar" in url_lower
                                    or "bolivar" in anchor_lower
                                    or "bolivar" in surrounding_snippet
                                    or "841" in url_lower
                                    or "841" in surrounding_snippet
                                    or "resolucion" in url_lower
                                    or "resolucion" in surrounding_snippet
                                )

                                if is_pertinent:
                                    # Validar seguridad de la URL descubierta
                                    try:
                                        validate_url_security(full_url, resolve_dns=False)
                                    except Exception:
                                        continue

                                    # Si el texto del anchor es genérico, extraer descripción del contenedor circundante
                                    clean_title = anchor_text
                                    if clean_title.lower() in ("ver o descargar", "descargar", "ver", "pdf", ""):
                                        div_matches = re.findall(r"<div[^>]*>(.*?)</div>", html_text[start_pos:match.start()], re.DOTALL)
                                        if div_matches:
                                            cand_title = re.sub(r"<[^>]+>", "", div_matches[-1]).strip()
                                            if len(cand_title) > 10:
                                                clean_title = cand_title
                                    if not clean_title or len(clean_title) < 5:
                                        clean_title = f"{inst} - {target['entity']}"

                                    now_iso = datetime.now(timezone.utc).isoformat()
                                    candidate_id = f"search_{abs(hash(full_url)) % 1000000}"
                                    record = CandidateProvenanceRecord(
                                        source_id=candidate_id,
                                        url=full_url,
                                        final_url=full_url,
                                        title=clean_title,
                                        entity=target["entity"],
                                        instrument_type=inst,
                                        territory_scope=query.subregion or f"DEP_{query.department.upper()}",
                                        discovery_adapter=self.name,
                                        provenance_chain=[search_url, full_url],
                                        status="authority_verified",
                                        timestamp_utc=now_iso,
                                        source_type="document_context",
                                        allowed_for_training=False,
                                        usage_state="context_only",
                                    )

                                    # Máxima prioridad a la Resolución 000841 de 2026 (revisión y actualización oficial del PATR)
                                    if "841" in url_lower or "841" in clean_title.lower() or "000841" in clean_title.lower():
                                        candidates.insert(0, record)
                                    elif "2026" in url_lower or "2026" in clean_title.lower():
                                        insert_pos = 1 if (candidates and ("841" in candidates[0].url.lower() or "841" in candidates[0].title.lower())) else 0
                                        candidates.insert(insert_pos, record)
                                    else:
                                        candidates.append(record)

                                    if len(candidates) >= query.max_documents_to_acquire * 3:
                                        return candidates
                except Exception as exc:
                    budget.record_discard(search_url, f"native_search_error: {exc}")

        return candidates
