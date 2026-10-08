from __future__ import annotations

import httpx
from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)


class FeedAdapter(BaseDiscoveryAdapter):
    """Adaptador de nivel 3: RSS/Atom feeds y metadatos estructurados JSON-LD."""

    @property
    def name(self) -> str:
        return "feed_adapter"

    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        # Para el alcance normativo estático, feeds no produce fuentes primarias históricas
        return []
