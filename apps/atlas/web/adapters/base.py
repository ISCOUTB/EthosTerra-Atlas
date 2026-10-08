from __future__ import annotations

from abc import ABC, abstractmethod
import httpx
from apps.atlas.web.schemas import WebDiscoveryQuery, CandidateProvenanceRecord
from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CrawlBudgetTracker,
)


class BaseDiscoveryAdapter(ABC):
    """Interfaz unificada para todos los adaptadores de la cascada de descubrimiento."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre canónico del adaptador en la cascada."""
        pass

    @abstractmethod
    def discover(
        self,
        query: WebDiscoveryQuery,
        client: httpx.Client,
        robots_mgr: RobotsTxtManager,
        rate_limiter: HostRateLimiter,
        budget: CrawlBudgetTracker,
    ) -> list[CandidateProvenanceRecord]:
        """Ejecuta la búsqueda de candidatos oficiales según la especialidad del adaptador."""
        pass
