from __future__ import annotations

import httpx
from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)


class DcatAdapter(BaseDiscoveryAdapter):
    """Adaptador de nivel 1: Consulta catálogos DCAT institucional (/data.json)."""

    @property
    def name(self) -> str:
        return "dcat_adapter"

    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        # DCAT se enfoca en catálogos abiertos estructurados
        # Para instrumentos normativos documentales (PATR, PIDARET), cede el paso a sitemaps/search
        return []
