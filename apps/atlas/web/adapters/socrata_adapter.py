from __future__ import annotations

from datetime import datetime, timezone
import httpx

from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.security import validate_url_security
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)


class SocrataCatalogAdapter(BaseDiscoveryAdapter):
    """Adaptador de nivel 1: Consulta APIs SODA y catálogos en datos.gov.co."""

    @property
    def name(self) -> str:
        return "socrata_catalog_adapter"

    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        candidates: list[CandidateProvenanceRecord] = []

        # Solo aplicable si se solicitan datos agrícolas o tabulares
        if not any(inst.lower() in ("datos_agricolas", "eva", "api_tabular") for inst in query.instrument_types):
            return candidates

        host = "www.datos.gov.co"
        api_url = f"https://{host}/api/views/metadata/v1"

        try:
            validate_url_security(api_url, resolve_dns=False)
            if not robots_mgr.can_fetch(api_url, client=client):
                budget.record_discard(api_url, "robots_txt_disallowed")
                return candidates

            if not budget.can_request():
                return candidates

            rate_limiter.wait_for_turn(host)
            # Buscar vistas relacionadas con el municipio/departamento
            params = {"q": f"{query.municipality} {query.department} agricultura"}
            resp = client.get(api_url, params=params, timeout=10.0)
            budget.record_request(str(resp.url), resp.status_code, len(resp.content))

            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                for item in items[:2]:
                    view_id = item.get("id") or item.get("view", {}).get("id")
                    title = item.get("name") or item.get("view", {}).get("name", "Dataset Agrícola")
                    if view_id:
                        canonical_url = f"https://www.datos.gov.co/resource/{view_id}.json"
                        now_iso = datetime.now(timezone.utc).isoformat()
                        record = CandidateProvenanceRecord(
                            source_id=f"socrata_{view_id}",
                            url=canonical_url,
                            final_url=canonical_url,
                            title=title,
                            entity="Datos Abiertos Colombia (MinTIC / MADR)",
                            instrument_type="datos_agricolas",
                            territory_scope=f"MPIO_{query.divipola}",
                            discovery_adapter=self.name,
                            provenance_chain=[api_url, canonical_url],
                            status="authority_verified",
                            http_status=200,
                            content_type="application/json",
                            timestamp_utc=now_iso,
                            source_type="tabular_context",
                            allowed_for_training=False,
                            usage_state="context_only",
                        )
                        candidates.append(record)
        except Exception as exc:
            budget.record_discard(api_url, f"error: {exc}")

        return candidates
