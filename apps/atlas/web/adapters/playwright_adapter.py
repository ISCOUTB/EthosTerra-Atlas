from __future__ import annotations

import importlib.util
import httpx

from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)


class PlaywrightFallbackAdapter(BaseDiscoveryAdapter):
    """Adaptador de nivel 6: Fallback opcional para páginas públicas renderizadas con JS.

    Estrictamente prohibido usar para evadir CAPTCHA, login o controles de acceso.
    """

    @property
    def name(self) -> str:
        return "playwright_fallback_adapter"

    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        # Verificar si playwright está instalado en el entorno
        if importlib.util.find_spec("playwright") is None:
            return []

        # En caso de estar disponible, se invocaría solo para páginas públicas sin contenido en HTML estático
        return []
