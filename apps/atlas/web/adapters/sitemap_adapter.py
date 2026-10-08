from __future__ import annotations

from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import httpx

from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.security import validate_url_security
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)

TARGET_AUTHORITY_SITEMAPS = [
    ("Agencia de Renovación del Territorio (ART)", "www.renovacionterritorio.gov.co", "https://www.renovacionterritorio.gov.co/sitemap.xml"),
    ("Agencia de Desarrollo Rural (ADR)", "www.adr.gov.co", "https://www.adr.gov.co/sitemap.xml"),
]


class SitemapAdapter(BaseDiscoveryAdapter):
    """Adaptador de nivel 2: Descubrimiento mediante robots.txt y sitemaps XML oficiales."""

    @property
    def name(self) -> str:
        return "sitemap_adapter"

    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        candidates: list[CandidateProvenanceRecord] = []
        target_instruments = [inst.lower() for inst in query.instrument_types]
        terms = [t.lower() for t in [query.department, query.municipality] if t]
        if query.subregion:
            terms.append(query.subregion.lower())

        for entity, host, sitemap_url in TARGET_AUTHORITY_SITEMAPS:
            try:
                validate_url_security(sitemap_url, resolve_dns=False)
                if not robots_mgr.can_fetch(sitemap_url, client=client):
                    budget.record_discard(sitemap_url, "robots_txt_disallowed")
                    continue

                if not budget.can_request():
                    break

                rate_limiter.wait_for_turn(host)
                resp = client.get(sitemap_url, timeout=10.0)
                budget.record_request(sitemap_url, resp.status_code, len(resp.content))

                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    # Manejar namespaces estándar de sitemaps (ej. {http://www.sitemaps.org/schemas/sitemap/0.9})
                    for elem in root.iter():
                        if elem.tag.endswith("loc") and elem.text:
                            loc_url = elem.text.strip()
                            loc_lower = loc_url.lower()

                            # Comprobar si el link apunta a un PDF o recurso relevante
                            if any(inst in loc_lower for inst in target_instruments) and (
                                any(term in loc_lower for term in terms) or "montes" in loc_lower or "bolivar" in loc_lower
                            ):
                                matched_inst = next((inst for inst in query.instrument_types if inst.lower() in loc_lower), query.instrument_types[0])
                                now_iso = datetime.now(timezone.utc).isoformat()
                                record = CandidateProvenanceRecord(
                                    source_id=f"sitemap_{abs(hash(loc_url)) % 1000000}",
                                    url=loc_url,
                                    final_url=loc_url,
                                    title=f"{matched_inst} detectado en sitemap oficial de {entity}",
                                    entity=entity,
                                    instrument_type=matched_inst,
                                    territory_scope=query.subregion or f"DEP_{query.department.upper()}",
                                    discovery_adapter=self.name,
                                    provenance_chain=[sitemap_url, loc_url],
                                    status="authority_verified",
                                    timestamp_utc=now_iso,
                                    source_type="document_context",
                                    allowed_for_training=False,
                                    usage_state="context_only",
                                )
                                candidates.append(record)
            except Exception as exc:
                budget.record_discard(sitemap_url, f"sitemap_parse_error: {exc}")

        return candidates
